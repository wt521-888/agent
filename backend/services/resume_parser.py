"""
简历文件解析：五级兜底文档解析引擎
解析优先级：LiteParse → markitdown → PyPDF2/python-docx → pdfplumber → 视觉 LLM OCR
支持格式：PDF/DOCX/DOC/TXT/PPTX/XLSX/HTML/MD/图片(JPG/PNG/BMP/TIFF)
"""
import os
import re
import io
import base64
from typing import Optional

# 设置 TESSDATA_PREFIX 环境变量（liteparse OCR 需要）
_TESSDATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tessdata")
if os.path.exists(_TESSDATA_DIR):
    os.environ["TESSDATA_PREFIX"] = _TESSDATA_DIR


# 设置 TESSDATA_PREFIX 环境变量（liteparse OCR 需要）
_TESSDATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tessdata")
if os.path.exists(_TESSDATA_DIR):
    os.environ["TESSDATA_PREFIX"] = _TESSDATA_DIR


# ==================== 解析统计 ====================
_parse_stats = {
    "total": 0,
    "success": 0,
    "fail": 0,
    "by_engine": {
        "liteparse": 0,
        "markitdown": 0,
        "pypdf2_docx": 0,
        "pdfplumber": 0,
        "vision_ocr": 0,
    },
    "by_format": {},
}


def get_parse_stats() -> dict:
    """获取解析统计数据"""
    total = _parse_stats["total"]
    success = _parse_stats["success"]
    return {
        "total": total,
        "success": success,
        "fail": _parse_stats["fail"],
        "success_rate": f"{success / total * 100:.1f}%" if total > 0 else "N/A",
        "by_engine": _parse_stats["by_engine"].copy(),
        "by_format": _parse_stats["by_format"].copy(),
    }


def _record_parse(file_type: str, engine: str, success: bool):
    """记录一次解析结果"""
    _parse_stats["total"] += 1
    if success:
        _parse_stats["success"] += 1
        _parse_stats["by_engine"][engine] = _parse_stats["by_engine"].get(engine, 0) + 1
    else:
        _parse_stats["fail"] += 1
    _parse_stats["by_format"][file_type] = _parse_stats["by_format"].get(file_type, 0) + 1


# ==================== 第一级：LiteParse ====================
def _try_liteparse(path: str, file_type: str) -> Optional[str]:
    """
    第一级解析：LiteParse（LlamaIndex 出品）
    支持 PDF/DOCX/PPTX/XLSX/HTML/图片等，输出结构化 Markdown
    """
    try:
        from liteparse import LiteParse
        parser = LiteParse(ocr_enabled=True, ocr_language="eng", quiet=True)
        result = parser.parse(path)
        text = result.text if hasattr(result, "text") else str(result)
        if text and len(text.strip()) > 20:
            return text.strip()
    except ImportError:
        pass  # liteparse 未安装，跳过
    except Exception as e:
        print(f"[parser] liteparse 失败 ({file_type}): {e}")
    return None


# ==================== 第二级：markitdown ====================
def _try_markitdown(path: str, file_type: str) -> Optional[str]:
    """
    第二级解析：markitdown（微软开源）
    支持 PDF/DOCX/PPTX/XLSX/HTML/图片等，统一转 Markdown
    """
    try:
        from markitdown import MarkItDown
        md = MarkItDown()
        result = md.convert(path)
        text = result.text_content if hasattr(result, "text_content") else str(result)
        if text and len(text.strip()) > 20:
            return text.strip()
    except ImportError:
        pass  # markitdown 未安装，跳过
    except Exception as e:
        print(f"[parser] markitdown 失败 ({file_type}): {e}")
    return None


# ==================== 第三级：PyPDF2 / python-docx / python-pptx / openpyxl ====================
def _parse_pdf_pypdf2(path: str) -> Optional[str]:
    """PyPDF2 解析 PDF"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(path)
        pages_text = []
        for page in reader.pages:
            try:
                pages_text.append(page.extract_text() or "")
            except Exception:
                continue
        text = "\n".join(pages_text).strip()
        return text if len(text) > 20 else None
    except Exception as e:
        print(f"[parser] PyPDF2 失败: {e}")
        return None


def _parse_docx_native(path: str) -> Optional[str]:
    """python-docx 解析 DOCX"""
    try:
        from docx import Document
        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs).strip()
        return text if len(text) > 20 else None
    except Exception as e:
        print(f"[parser] python-docx 失败: {e}")
        return None


def _parse_pptx_native(path: str) -> Optional[str]:
    """python-pptx 解析 PPTX（可选依赖）"""
    try:
        from pptx import Presentation
    except ImportError:
        print("[parser] python-pptx 未安装，跳过原生PPTX解析")
        return None
    try:
        from pptx import Presentation
        prs = Presentation(path)
        texts = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    texts.append(shape.text.strip())
        text = "\n".join(texts).strip()
        return text if len(text) > 20 else None
    except Exception as e:
        print(f"[parser] python-pptx 失败: {e}")
        return None


def _parse_xlsx_native(path: str) -> Optional[str]:
    """openpyxl 解析 XLSX（可选依赖）"""
    try:
        from openpyxl import load_workbook
    except ImportError:
        print("[parser] openpyxl 未安装，跳过原生XLSX解析")
        return None
    try:
        from openpyxl import load_workbook
        wb = load_workbook(path, data_only=True)
        texts = []
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                row_text = " | ".join(str(cell) for cell in row if cell is not None)
                if row_text.strip():
                    texts.append(row_text.strip())
        text = "\n".join(texts).strip()
        return text if len(text) > 20 else None
    except Exception as e:
        print(f"[parser] openpyxl 失败: {e}")
        return None


def _parse_txt_native(path: str) -> str:
    """TXT 多编码解析"""
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read().strip()
        except UnicodeDecodeError:
            continue
    with open(path, "rb") as f:
        return f.read().decode("utf-8", errors="ignore").strip()


def _try_native(path: str, file_type: str) -> Optional[str]:
    """第三级：原生库解析"""
    ext = file_type.lower()
    if ext == "pdf":
        return _parse_pdf_pypdf2(path)
    elif ext in ("docx", "doc"):
        return _parse_docx_native(path)
    elif ext == "pptx":
        return _parse_pptx_native(path)
    elif ext == "xlsx":
        return _parse_xlsx_native(path)
    elif ext == "txt":
        return _parse_txt_native(path)
    elif ext in ("html", "htm"):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            # 简单去 HTML 标签
            text = re.sub(r"<[^>]+>", " ", content)
            text = re.sub(r"\s+", " ", text).strip()
            return text if len(text) > 20 else None
        except Exception:
            return None
    elif ext == "md":
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
        except Exception:
            return None
    return None


# ==================== 第四级：pdfplumber ====================
def _try_pdfplumber(path: str) -> Optional[str]:
    """第四级：pdfplumber 解析 PDF（表格提取更强）"""
    try:
        import pdfplumber
        texts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        texts.append(page_text)
                    # 尝试提取表格
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            row_text = " | ".join(str(cell or "") for cell in row)
                            if row_text.strip():
                                texts.append(row_text)
                except Exception:
                    continue
        text = "\n".join(texts).strip()
        return text if len(text) > 20 else None
    except ImportError:
        pass
    except Exception as e:
        print(f"[parser] pdfplumber 失败: {e}")
    return None


# ==================== 第五级：视觉 LLM OCR ====================
def _render_page_to_base64(page, max_width: int = 1600) -> Optional[str]:
    """将 PDF 页面渲染为 base64 图片"""
    try:
        import pymupdf as fitz  # pymupdf
        from PIL import Image

        # 渲染为 pixmap（2x 分辨率）
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)

        # 转 PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # 缩放
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        # 转 base64
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"[parser] 页面渲染失败: {e}")
        return None


def _try_vision_ocr(path: str) -> Optional[str]:
    """
    第五级：视觉 LLM OCR
    将 PDF 页面渲染为图片，调用视觉模型识别文字
    """
    try:
        import pymupdf as fitz  # pymupdf
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        vision_model = os.getenv("VISION_MODEL", "gpt-4o-mini")

        if not api_key or "your_" in api_key:
            return None

        client = OpenAI(api_key=api_key, base_url=base_url, timeout=60.0)

        doc = fitz.open(path)
        all_texts = []

        # 最多处理前 10 页
        max_pages = min(len(doc), 10)
        for page_num in range(max_pages):
            page = doc[page_num]
            b64_img = _render_page_to_base64(page)
            if not b64_img:
                continue

            try:
                response = client.chat.completions.create(
                    model=vision_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "请提取这张图片中的所有文字内容，保持原始排版格式。只返回文字，不要任何解释。",
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{b64_img}"
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=2000,
                )
                page_text = response.choices[0].message.content or ""
                if page_text.strip():
                    all_texts.append(f"--- 第 {page_num + 1} 页 ---\n{page_text.strip()}")
            except Exception as e:
                print(f"[parser] 视觉OCR第{page_num + 1}页失败: {e}")
                continue

        doc.close()
        text = "\n\n".join(all_texts).strip()
        return text if len(text) > 20 else None
    except ImportError:
        pass
    except Exception as e:
        print(f"[parser] 视觉OCR整体失败: {e}")
    return None


def _try_image_ocr(path: str) -> Optional[str]:
    """
    图片文件 OCR：直接调用视觉模型识别
    """
    try:
        from PIL import Image
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        vision_model = os.getenv("VISION_MODEL", "gpt-4o-mini")

        if not api_key or "your_" in api_key:
            return None

        # 读取图片并转 base64
        with open(path, "rb") as f:
            img_data = f.read()
        b64_img = base64.b64encode(img_data).decode("utf-8")

        # 判断 MIME 类型
        ext = path.lower().rsplit(".", 1)[-1]
        mime_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "bmp": "bmp", "tiff": "tiff", "tif": "tiff"}
        mime = mime_map.get(ext, "png")

        client = OpenAI(api_key=api_key, base_url=base_url, timeout=60.0)
        response = client.chat.completions.create(
            model=vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请提取这张图片中的所有文字内容，保持原始排版格式。只返回文字，不要任何解释。",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/{mime};base64,{b64_img}"},
                        },
                    ],
                }
            ],
            max_tokens=2000,
        )
        text = response.choices[0].message.content or ""
        return text.strip() if len(text.strip()) > 10 else None
    except ImportError:
        pass
    except Exception as e:
        print(f"[parser] 图片OCR失败: {e}")
    return None


# ==================== 主入口：五级兜底 ====================
IMAGE_EXTS = {"jpg", "jpeg", "png", "bmp", "tiff", "tif"}


def parse_resume(path: str, file_type: str) -> str:
    """
    五级兜底文档解析引擎

    解析优先级：
    1. LiteParse（LlamaIndex，多格式，结构化 Markdown）
    2. markitdown（微软，多格式，Markdown）
    3. PyPDF2 / python-docx / python-pptx / openpyxl（原生库）
    4. pdfplumber（PDF 表格提取更强）
    5. 视觉 LLM OCR（扫描件兜底）

    :param path: 文件磁盘路径
    :param file_type: 扩展名（pdf/docx/txt/pptx/xlsx/html/md/jpg/png 等）
    :return: 解析出的文本内容
    :raises ValueError: 不支持的格式
    :raises RuntimeError: 所有解析方式均失败
    """
    ext = file_type.lower().strip(".")

    # 图片文件走 OCR
    if ext in IMAGE_EXTS:
        text = _try_image_ocr(path)
        if text:
            _record_parse(ext, "vision_ocr", True)
            return text
        _record_parse(ext, "vision_ocr", False)
        raise RuntimeError(f"图片 OCR 解析失败: {path}")

    # 图片型 PDF 检测（扫描件）
    def _is_scanned_pdf(file_path: str) -> bool:
        """检测 PDF 是否为扫描件（每页文字极少）"""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            total_chars = 0
            sample_pages = min(len(reader.pages), 3)
            for i in range(sample_pages):
                text = reader.pages[i].extract_text() or ""
                total_chars += len(text.strip())
            # 平均每页少于 50 字，认为是扫描件
            return total_chars / max(sample_pages, 1) < 50
        except Exception:
            return False

    is_scanned = ext == "pdf" and _is_scanned_pdf(path)

    # 扫描件 PDF 直接跳到视觉 OCR
    if is_scanned:
        text = _try_vision_ocr(path)
        if text:
            _record_parse(ext, "vision_ocr", True)
            return text
        _record_parse(ext, "vision_ocr", False)
        raise RuntimeError(f"扫描件 PDF 视觉 OCR 解析失败: {path}")

    # 五级兜底
    errors = []

    # 第一级：LiteParse
    text = _try_liteparse(path, ext)
    if text:
        _record_parse(ext, "liteparse", True)
        return text
    errors.append("liteparse")

    # 第二级：markitdown
    text = _try_markitdown(path, ext)
    if text:
        _record_parse(ext, "markitdown", True)
        return text
    errors.append("markitdown")

    # 第三级：原生库
    text = _try_native(path, ext)
    if text:
        _record_parse(ext, "pypdf2_docx", True)
        return text
    errors.append("native")

    # 第四级：pdfplumber（仅 PDF）
    if ext == "pdf":
        text = _try_pdfplumber(path)
        if text:
            _record_parse(ext, "pdfplumber", True)
            return text
        errors.append("pdfplumber")

    # 第五级：视觉 LLM OCR（仅 PDF）
    if ext == "pdf":
        text = _try_vision_ocr(path)
        if text:
            _record_parse(ext, "vision_ocr", True)
            return text
        errors.append("vision_ocr")

    _record_parse(ext, "all_failed", False)
    _record_parse(ext, "all_failed", False)
    raise RuntimeError("所有解析方式均失败 (" + ", ".join(errors) + "): " + path)


# ==================== 内容瘦身（保留原有功能）====================
def slim_resume(content: str, max_length: int = 2000) -> str:
    """
    简历内容瘦身：提取关键字段，去掉废话，节省 token
    """
    if not content:
        return ""

    text = content.strip()

    # 去掉页眉页脚常见模式
    text = re.sub(r"第\s*\d+\s*页\s*/\s*共\s*\d+\s*页", "", text)
    text = re.sub(r"Page\s*\d+\s*of\s*\d+", "", text, flags=re.IGNORECASE)

    # 去掉多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 去掉行首行尾空格
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # 识别关键段落
    key_sections = []
    current_section = []
    section_keywords = {
        "personal": ["个人信息", "基本信息", "个人资料", "联系方式", "姓名", "性别", "年龄"],
        "education": ["教育背景", "教育经历", "学历", "毕业院校", "教育"],
        "experience": ["工作经历", "工作经验", "项目经验", "实习经历"],
        "skills": ["专业技能", "技能特长", "技术栈", "技能", "掌握"],
        "project": ["项目经历", "项目经验", "项目", "代表项目"],
    }

    found_sections = set()
    for line in text.split("\n"):
        line_lower = line.lower().strip()
        is_header = False
        for section_type, keywords in section_keywords.items():
            for kw in keywords:
                if kw in line_lower and len(line) < 30:
                    if current_section:
                        key_sections.append("\n".join(current_section))
                    current_section = [line]
                    found_sections.add(section_type)
                    is_header = True
                    break
            if is_header:
                break
        if not is_header:
            current_section.append(line)

    if current_section:
        key_sections.append("\n".join(current_section))

    if key_sections and len(found_sections) >= 2:
        text = "\n\n".join(key_sections)

    if len(text) > max_length:
        text = text[:max_length] + "\n...(内容已截断)"

    return text


def slim_job_description(jd: str, max_length: int = 800) -> str:
    """
    JD 内容瘦身：只保留核心要求
    """
    if not jd:
        return ""

    text = jd.strip()

    key_patterns = [
        r"(?:岗位要求|任职要求|职位要求|任职资格|岗位职责|工作要求)[：:](.*?)(?=\n\n|\Z)",
        r"(?:职位描述|岗位描述|工作内容)[：:](.*?)(?=\n\n|\Z)",
        r"(?:任职条件|招聘要求)[：:](.*?)(?=\n\n|\Z)",
    ]

    extracted_parts = []
    for pattern in key_patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            extracted_parts.extend(matches)

    if extracted_parts:
        text = "\n".join(extracted_parts)

    noise_patterns = [
        r"公司简介[：:].*?(?=\n\n|\Z)",
        r"关于我们[：:].*?(?=\n\n|\Z)",
        r"公司福利[：:].*?(?=\n\n|\Z)",
        r"联系方式[：:].*?(?=\n\n|\Z)",
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)

    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if len(text) > max_length:
        text = text[:max_length] + "\n...(内容已截断)"

    return text
