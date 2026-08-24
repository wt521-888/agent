"""
简历文件解析：支持 PDF / DOCX / TXT
"""
from PyPDF2 import PdfReader
from docx import Document


def parse_pdf(path: str) -> str:
    """提取 PDF 全部页文本"""
    reader = PdfReader(path)
    pages_text = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception:
            # 单页解析失败不影响整体
            continue
    return "\n".join(pages_text).strip()


def parse_docx(path: str) -> str:
    """提取 DOCX 全部段落文本"""
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs).strip()


def parse_txt(path: str) -> str:
    """尝试多种编码读取 TXT"""
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read().strip()
        except UnicodeDecodeError:
            continue
    # 实在不行用二进制忽略错误
    with open(path, "rb") as f:
        return f.read().decode("utf-8", errors="ignore").strip()


def parse_resume(path: str, file_type: str) -> str:
    """
    根据文件类型分发到对应解析器
    :param path: 文件磁盘路径
    :param file_type: 扩展名（pdf/docx/txt）
    :raises RuntimeError: 不支持的格式或解析失败
    """
    ext = file_type.lower()
    if ext == "pdf":
        return parse_pdf(path)
    if ext in ("docx", "doc"):
        return parse_docx(path)
    if ext == "txt":
        return parse_txt(path)
    raise ValueError(f"不支持的文件类型: {file_type}")
