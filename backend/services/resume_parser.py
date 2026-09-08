"""
简历文件解析：支持 PDF / DOCX / TXT
"""
import re
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


def slim_resume(content: str, max_length: int = 2000) -> str:
    """
    简历内容瘦身：提取关键字段，去掉废话，节省 token
    
    策略：
    1. 去掉页眉页脚、重复空行、无意义符号
    2. 识别并提取：个人信息、工作经历、技能、项目、教育背景
    3. 截断过长内容
    
    :param content: 简历原文
    :param max_length: 最大字符数（默认2000，约500-800 token）
    :return: 瘦身后的简历内容
    """
    if not content:
        return ""
    
    # 第一步：基础清理
    text = content.strip()
    
    # 去掉页眉页脚常见模式
    text = re.sub(r'第\s*\d+\s*页\s*/\s*共\s*\d+\s*页', '', text)
    text = re.sub(r'Page\s*\d+\s*of\s*\d+', '', text, flags=re.IGNORECASE)
    
    # 去掉多余空行（保留最多2个连续换行）
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 去掉行首行尾空格
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # 第二步：识别关键段落（启发式）
    key_sections = []
    current_section = []
    section_keywords = {
        'personal': ['个人信息', '基本信息', '个人资料', '联系方式', '姓名', '性别', '年龄'],
        'education': ['教育背景', '教育经历', '学历', '毕业院校', '教育'],
        'experience': ['工作经历', '工作经验', '项目经验', '实习经历', '工作经验'],
        'skills': ['专业技能', '技能特长', '技术栈', '技能', '掌握'],
        'project': ['项目经历', '项目经验', '项目', '代表项目'],
    }
    
    found_sections = set()
    for line in text.split('\n'):
        line_lower = line.lower().strip()
        
        # 检测是否是新的段落标题
        is_header = False
        for section_type, keywords in section_keywords.items():
            for kw in keywords:
                if kw in line_lower and len(line) < 30:  # 标题通常较短
                    # 保存上一个段落
                    if current_section:
                        key_sections.append('\n'.join(current_section))
                    current_section = [line]
                    found_sections.add(section_type)
                    is_header = True
                    break
            if is_header:
                break
        
        if not is_header:
            current_section.append(line)
    
    # 保存最后一个段落
    if current_section:
        key_sections.append('\n'.join(current_section))
    
    # 第三步：如果识别到了关键段落，优先使用
    if key_sections and len(found_sections) >= 2:
        text = '\n\n'.join(key_sections)
    
    # 第四步：截断
    if len(text) > max_length:
        text = text[:max_length] + "\n...(内容已截断)"
    
    return text


def slim_job_description(jd: str, max_length: int = 800) -> str:
    """
    JD 内容瘦身：只保留核心要求，去掉公司介绍废话
    
    :param jd: 招聘信息原文
    :param max_length: 最大字符数（默认800，约200-300 token）
    :return: 瘦身后的 JD
    """
    if not jd:
        return ""
    
    text = jd.strip()
    
    # 提取关键要求部分的常见模式
    key_patterns = [
        r'(?:岗位要求|任职要求|职位要求|任职资格|岗位职责|工作要求)[：:](.*?)(?=\n\n|\Z)',
        r'(?:职位描述|岗位描述|工作内容)[：:](.*?)(?=\n\n|\Z)',
        r'(?:任职条件|招聘要求)[：:](.*?)(?=\n\n|\Z)',
    ]
    
    extracted_parts = []
    for pattern in key_patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            extracted_parts.extend(matches)
    
    # 如果成功提取到关键部分，使用提取结果
    if extracted_parts:
        text = '\n'.join(extracted_parts)
    
    # 去掉常见的公司介绍废话
    noise_patterns = [
        r'公司简介[：:].*?(?=\n\n|\Z)',
        r'关于我们[：:].*?(?=\n\n|\Z)',
        r'公司福利[：:].*?(?=\n\n|\Z)',
        r'联系方式[：:].*?(?=\n\n|\Z)',
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 清理空行
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    
    # 截断
    if len(text) > max_length:
        text = text[:max_length] + "\n...(内容已截断)"
    
    return text
