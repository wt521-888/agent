"""
按原格式输出修改后的简历（TXT / DOCX / PDF）
- 模板沿用：保留原扩展名，不强制重排版
- 不会触碰原文件
"""
import os
from typing import List

from docx import Document
from fpdf import FPDF


# 中文字体路径（按需替换；fpdf2 默认不支持中文）
# 优先单 TTF，TTC 集合体可能触发 fonttools "MERG NOT subset" 警告
_DEFAULT_CN_FONT_CANDIDATES = [
    # Windows 单 TTF（最稳）
    r"C:\Windows\Fonts\msyh.ttf",       # 微软雅黑（部分 Win10+ 上是 TTC，下面会先匹配）
    r"C:\Windows\Fonts\msyhl.ttf",
    r"C:\Windows\Fonts\simhei.ttf",     # 黑体
    r"C:\Windows\Fonts\simsun.ttf",     # 宋体（部分为 TTC）
    r"C:\Windows\Fonts\simkai.ttf",     # 楷体
    # Windows TTC（最后兜底）
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyhl.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
    # Linux
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]


def _find_cn_font() -> str | None:
    """在常见路径里找一个可用的中文字体；找不到返回 None"""
    for p in _DEFAULT_CN_FONT_CANDIDATES:
        if p and os.path.exists(p):
            return p
    return None


def _detect_chinese_ratio(text: str) -> float:
    """粗略估算中文字符占比"""
    if not text:
        return 0.0
    cn = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return cn / max(len(text), 1)


def _wrap_text_for_pdf(text: str, max_chars: int = 90) -> List[str]:
    """简单按字符数软换行（PDF 写入用）"""
    lines: List[str] = []
    for raw in text.splitlines() or [""]:
        if not raw:
            lines.append("")
            continue
        # 保留用户原始换行；超长行按 max_chars 切
        buf = ""
        for ch in raw:
            buf += ch
            if len(buf) >= max_chars:
                lines.append(buf)
                buf = ""
        if buf:
            lines.append(buf)
    return lines


def _write_txt(content: str, output_path: str) -> None:
    """TXT 直接写（UTF-8 with BOM 兼容 Windows 记事本）"""
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(content)


def _write_docx(content: str, output_path: str) -> None:
    """DOCX：每行作为一段（简单版，保留段落顺序）"""
    doc = Document()
    # 设置中文字体（如果系统装了）
    try:
        from docx.oxml.ns import qn
        style = doc.styles["Normal"]
        style.font.name = "Microsoft YaHei"
        rpr = style.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            from docx.oxml import OxmlElement
            rfonts = OxmlElement("w:rFonts")
            rpr.append(rfonts)
        rfonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    except Exception:
        pass

    for line in content.splitlines():
        doc.add_paragraph(line if line else "")
    doc.save(output_path)


def _sanitize_for_latin_pdf(text: str) -> str:
    """
    兜底方案：当系统没有任何中文字体时，
    把不兼容 latin-1 的字符替换成 ?，避免 fpdf 报错。
    """
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _write_pdf(content: str, output_path: str) -> None:
    """PDF：尝试加载中文字体，失败则用 latin-1 兜底"""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    font_path = _find_cn_font()
    if font_path:
        try:
            # fpdf2 支持 .ttc 时用 font_family 区分子字体
            if font_path.lower().endswith(".ttc"):
                # 取第一个字体子表
                pdf.add_font("CN_FONT", "", font_path)
            else:
                pdf.add_font("CN_FONT", "", font_path)
            pdf.set_font("CN_FONT", size=11)
            for line in _wrap_text_for_pdf(content, max_chars=85):
                # 空行也要画出来
                pdf.cell(0, 6, txt=line, ln=1)
        except Exception as e:
            print(f"[resume_writer] 中文字体加载失败，回退 latin-1: {e}")
            font_path = None

    if not font_path:
        # 兜底：替换为 latin-1 可表示的字符（中文会变 ?，但文件能生成）
        pdf.set_font("Helvetica", size=11)
        for line in _wrap_text_for_pdf(_sanitize_for_latin_pdf(content), max_chars=110):
            pdf.cell(0, 6, txt=line, ln=1)

    pdf.output(output_path)


def write_resume(content: str, file_type: str, output_path: str) -> None:
    """
    按 file_type 把简历写到 output_path。
    :param content: 修改后的纯文本
    :param file_type: 扩展名（pdf/docx/doc/txt），小写
    :param output_path: 目标磁盘路径
    """
    ext = (file_type or "txt").lower()
    # doc 与 docx 用同一套处理
    if ext in ("docx", "doc"):
        _write_docx(content, output_path)
    elif ext == "pdf":
        _write_pdf(content, output_path)
    elif ext == "txt":
        _write_txt(content, output_path)
    else:
        # 未知格式降级为 txt
        _write_txt(content, output_path)
