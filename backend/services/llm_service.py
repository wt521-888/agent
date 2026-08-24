"""
OpenAI LLM 服务：构造提示词并调用 LLM 产出结构化打分结果
"""
import os
import re
import json
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


SYSTEM_PROMPT = """你是一个资深的简历评估与求职顾问。
你的任务是根据用户提供的【招聘信息】、【公司与岗位搜索摘要】和【候选人简历】，
对候选人与该岗位的匹配度进行评估，并以严格合法的 JSON 格式返回结果。

# 输出 JSON 结构（必须严格遵守，不要返回任何额外文字或 Markdown 围栏）：
{
  "overall_score": 0-100 的整数,
  "dimension_scores": {
    "skills": 0-100,
    "experience": 0-100,
    "education": 0-100,
    "project": 0-100
  },
  "strengths": ["优势1", "优势2", "..."],
  "weaknesses": ["不足1", "不足2", "..."],
  "resume_improvements": ["针对简历本身的修改建议1", "..."],
  "knowledge_areas": ["需要强化的知识领域1", "..."],
  "learning_resources": [
    {"title": "资源名", "type": "网站|视频|书籍|课程", "url": "https://...", "description": "简短说明"},
    ...至少 5 条，URL 必须是真实可访问的
  ]
}

# 评分参考：
- 90+：高度匹配，强烈推荐面试
- 75-89：较好匹配
- 60-74：基本匹配，存在补强空间
- 60 以下：明显不匹配

# 严格要求：
1. 仅返回 JSON，不输出任何解释或 Markdown
2. 所有评分必须是 0-100 的整数
3. learning_resources 至少 5 条，URL 真实可点
4. 数组内容使用中文短句，便于直接展示
"""


def extract_json(text: str) -> Dict[str, Any]:
    """从 LLM 输出中提取 JSON（兼容 ```json ... ``` 围栏或夹带前后文字的情况）"""
    if not text:
        raise ValueError("LLM 返回内容为空")
    text = text.strip()
    # 去掉 markdown 围栏
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    # 提取最外层 {...}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def score_resume(
    job_description: str,
    search_summary: str,
    resume_content: str,
) -> Dict[str, Any]:
    """
    调用 LLM 进行打分。

    :raises ValueError: API key 未配置
    :raises RuntimeError: LLM 调用失败或返回无法解析
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or "your_" in api_key or "REPLACE" in api_key or "YOUR" in api_key:
        raise ValueError("OPENAI_API_KEY 未配置")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    client = OpenAI(api_key=api_key, base_url=base_url)

    # 组装 User Message
    parts = ["## 招聘信息\n" + job_description]
    if search_summary:
        parts.append("## 公司与岗位搜索摘要\n" + search_summary)
    parts.append("## 候选人简历\n" + resume_content)
    parts.append("请严格按系统要求的 JSON 结构返回结果，不要任何其他文字。")
    user_msg = "\n\n".join(parts)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
        )
    except Exception as e:
        raise RuntimeError(f"LLM 接口调用失败: {e}")

    raw = response.choices[0].message.content or ""
    try:
        return extract_json(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM 返回内容无法解析为 JSON: {e}\n原始内容: {raw[:300]}")


# ===================================================================
# 提取公司名 / 岗位（用于历史记录命名）
# ===================================================================
EXTRACT_SYSTEM_PROMPT = """你是招聘信息解析助手。
从用户给定的【招聘信息】文本中，提取出：
1. company: 招聘公司名（去掉"有限公司"等后缀也保留原样即可，无则填空字符串）
2. position: 招聘岗位名（如"Python 后端开发工程师"）

只返回严格 JSON：{"company": "...", "position": "..."}，不要其他文字。"""


def extract_job_info(job_description: str) -> Dict[str, str]:
    """
    从 JD 文本里提取公司名和岗位名。
    LLM 失败时返回空 dict，前端可手动输入。
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or "your_" in api_key or "REPLACE" in api_key or "YOUR" in api_key:
        return {"company": "", "position": ""}
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
                {"role": "user", "content": job_description[:2000]},  # 截断省 token
            ],
            temperature=0.0,
        )
        data = extract_json(resp.choices[0].message.content or "{}")
        return {
            "company": str(data.get("company", "")).strip()[:200],
            "position": str(data.get("position", "")).strip()[:200],
        }
    except Exception:
        return {"company": "", "position": ""}


def extract_candidate_name(resume_content: str, filename: str = "") -> str:
    """
    从简历正文或文件名中猜候选人姓名。
    启发式：取第一行非空文本中第一个像中文姓名（2-4 个汉字）的片段；
    失败时回退到文件名（去掉后缀）。
    """
    # 优先从正文
    if resume_content:
        first_line = resume_content.strip().splitlines()[0].strip() if resume_content.strip() else ""
        m = re.search(r"[\u4e00-\u9fa5]{2,4}", first_line)
        if m:
            return m.group(0)
    # 回退到文件名
    if filename:
        stem = re.sub(r"\.[^.]+$", "", filename)
        stem = re.sub(r"[-_—–]\s*(简历|resume|CV).*$", "", stem, flags=re.IGNORECASE).strip()
        if stem:
            return stem[:100]
    return "未知候选人"


def make_record_name(candidate_name: str, company: str, position: str) -> str:
    """组合：人名_公司_岗位；缺失部分用占位符"""
    cn = candidate_name or "未知候选人"
    co = company or "未知公司"
    po = position or "未知岗位"
    # 文件名安全字符
    safe = lambda s: re.sub(r'[\\/:*?"<>|]+', "_", s).strip()
    return f"{safe(cn)}_{safe(co)}_{safe(po)}"
