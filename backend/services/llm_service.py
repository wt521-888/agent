"""
OpenAI LLM 服务：构造提示词并调用 LLM 产出结构化打分结果
优化策略：
1. 简历/JD 内容瘦身，减少输入 token
2. 限制重试次数，避免无效消耗
3. 正则优先提取，失败才调 LLM（零 token 消耗）
4. 内容质量校验，太短直接拒绝
5. 返回 token 使用量，便于前端展示
"""
import os
import re
import json
from typing import Dict, Any, Optional, Tuple, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 重试配置
MAX_RETRIES = 2  # 最多重试2次

# 内容质量阈值
MIN_RESUME_LENGTH = 50   # 简历最少50字
MIN_JD_LENGTH = 30       # JD最少30字

# Token 价格（美元/1M token）- 用于估算成本
TOKEN_PRICES = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "default": {"input": 0.15, "output": 0.60},
}


SYSTEM_PROMPT = """你是一个资深的简历评估与求职顾问。
你的任务是根据用户提供的【招聘信息】和【候选人简历】，
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
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["不足1", "不足2"],
  "resume_improvements": ["针对简历本身的修改建议1"],
  "knowledge_areas": ["需要强化的知识领域1"],
  "learning_resources": [
    {"title": "资源名", "type": "网站|视频|书籍|课程", "url": "https://...", "description": "简短说明"}
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
3. learning_resources 至少 3 条，URL 真实可点
4. 数组内容使用中文短句，便于直接展示
"""


def extract_json(text: str) -> Dict[str, Any]:
    """从 LLM 输出中提取 JSON（兼容 `json ... ` 围栏或夹带前后文字的情况）"""
    if not text:
        raise ValueError("LLM 返回内容为空")
    text = text.strip()
    # 去掉 markdown 围栏
    text = re.sub(r"^`(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*`$", "", text)
    # 提取最外层 {...}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def validate_content(resume_content: str, job_description: str) -> Optional[str]:
    """
    内容质量校验（置信度阈值）
    太短的内容直接拒绝，避免浪费 LLM 调用
    
    :return: None 表示通过，否则返回错误信息
    """
    if not resume_content or len(resume_content.strip()) < MIN_RESUME_LENGTH:
        return f"简历内容太短（{len(resume_content.strip())}字），至少需要{MIN_RESUME_LENGTH}字才能准确评估"
    
    if not job_description or len(job_description.strip()) < MIN_JD_LENGTH:
        return f"招聘信息太短（{len(job_description.strip())}字），至少需要{MIN_JD_LENGTH}字才能准确评估"
    
    return None


def extract_job_info_regex(jd_text: str) -> Dict[str, str]:
    """
    用正则从 JD 提取公司名和岗位名（零 token 消耗）
    失败返回空字符串，调用方决定是否 fallback 到 LLM
    """
    company = ""
    position = ""
    
    # 提取公司名的常见模式
    company_patterns = [
        r'(?:公司名称|公司简介|企业名称)[：:]\s*(.+?)(?:\n|$)',
        r'(?:招聘公司|所属公司)[：:]\s*(.+?)(?:\n|$)',
        r'^([^\n]{2,20}?)(?:公司|集团|科技|技术|信息|网络)',
    ]
    for pattern in company_patterns:
        match = re.search(pattern, jd_text, re.MULTILINE)
        if match:
            company = match.group(1).strip()[:50]
            break
    
    # 提取岗位名的常见模式
    position_patterns = [
        r'(?:职位名称|岗位名称|招聘岗位|岗位)[：:]\s*(.+?)(?:\n|$)',
        r'(?:职位|岗位)[：:]\s*(.+?)(?:\n|$)',
        r'(?:招聘|诚聘)\s*(.+?)(?:\n|$)',
    ]
    for pattern in position_patterns:
        match = re.search(pattern, jd_text, re.MULTILINE)
        if match:
            position = match.group(1).strip()[:50]
            break
    
    # 如果正则没提取到，尝试从第一行提取
    if not position:
        first_line = jd_text.strip().split('\n')[0].strip()
        if len(first_line) < 30:  # 第一行可能是岗位名
            position = first_line
    
    return {"company": company, "position": position}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """计算 token 成本（美元）"""
    prices = TOKEN_PRICES.get(model, TOKEN_PRICES["default"])
    input_cost = (prompt_tokens / 1_000_000) * prices["input"]
    output_cost = (completion_tokens / 1_000_000) * prices["output"]
    return round(input_cost + output_cost, 6)


def _call_llm(
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_msg: str,
    temperature: float = 0.3,
    max_retries: int = MAX_RETRIES,
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """
    调用 LLM 并解析 JSON 结果，带重试限制
    
    :return: (解析后的JSON, token使用量dict)
    :raises RuntimeError: 重试耗尽仍失败
    """
    last_error = None
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    for attempt in range(max_retries + 1):  # 0, 1, 2共3次尝试
        try:
            # 第二次尝试时调整提示词，要求修正格式
            if attempt > 0:
                user_msg_retry = user_msg + f"\n\n[系统提示：上次输出格式有误，请严格返回合法JSON，不要任何额外文字。这是第{attempt+1}次尝试。]"
            else:
                user_msg_retry = user_msg
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg_retry},
                ],
                temperature=temperature,
            )
            
            # 累加 token 使用量
            if response.usage:
                total_usage["prompt_tokens"] += response.usage.prompt_tokens
                total_usage["completion_tokens"] += response.usage.completion_tokens
                total_usage["total_tokens"] += response.usage.total_tokens
            
            raw = response.choices[0].message.content or ""
            return extract_json(raw), total_usage
            
        except json.JSONDecodeError as e:
            last_error = f"JSON解析失败: {e}"
            print(f"[LLM] 第{attempt+1}次尝试失败: {last_error}")
            if attempt < max_retries:
                continue  # 重试
            else:
                raise RuntimeError(f"重试{max_retries}次后仍失败: {last_error}\n原始输出: {raw[:200]}")
                
        except Exception as e:
            last_error = str(e)
            print(f"[LLM] 第{attempt+1}次尝试失败: {last_error}")
            if attempt < max_retries:
                continue  # 重试
            else:
                raise RuntimeError(f"重试{max_retries}次后仍失败: {last_error}")
    
    raise RuntimeError(f"重试耗尽: {last_error}")


def score_resume(
    job_description: str,
    search_summary: str,
    resume_content: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    调用 LLM 进行打分。
    输入内容已预处理（瘦身），减少 token 消耗。

    :return: (打分结果dict, token使用量dict)
    :raises ValueError: API key 未配置
    :raises RuntimeError: LLM 调用失败或返回无法解析
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or "your_" in api_key or "REPLACE" in api_key or "YOUR" in api_key:
        raise ValueError("OPENAI_API_KEY 未配置")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    client = OpenAI(api_key=api_key, base_url=base_url)

    # 组装 User Message（内容已瘦身）
    parts = ["## 招聘信息\n" + job_description]
    if search_summary:
        # 搜索摘要也截断，只保留前500字
        parts.append("## 公司与岗位背景\n" + search_summary[:500])
    parts.append("## 候选人简历\n" + resume_content)
    parts.append("请严格按系统要求的 JSON 结构返回结果，不要任何其他文字。")
    user_msg = "\n\n".join(parts)

    result, usage = _call_llm(client, model, SYSTEM_PROMPT, user_msg)
    
    # 计算成本
    cost = calculate_cost(model, usage["prompt_tokens"], usage["completion_tokens"])
    usage["estimated_cost_usd"] = cost
    
    return result, usage


# ===================================================================
# 提取公司名 / 岗位（用于历史记录命名）
# 优化：先用正则提取，失败才调 LLM
# ===================================================================
EXTRACT_SYSTEM_PROMPT = """你是招聘信息解析助手。
从用户给定的【招聘信息】文本中，提取出：
1. company: 招聘公司名（去掉"有限公司"等后缀也保留原样即可，无则填空字符串）
2. position: 招聘岗位名（如"Python 后端开发工程师"）

只返回严格 JSON：{"company": "...", "position": "..."}，不要其他文字。"""


def extract_job_info(job_description: str) -> Dict[str, str]:
    """
    从 JD 文本里提取公司名和岗位名。
    优化：先用正则提取（零 token），失败才调 LLM
    """
    # 第一步：正则提取（零 token 消耗）
    result = extract_job_info_regex(job_description)
    
    # 如果正则成功提取到至少一个字段，直接返回
    if result["company"] or result["position"]:
        print(f"[extract_job_info] 正则提取成功: {result}")
        return result
    
    # 第二步：正则失败，fallback 到 LLM
    print(f"[extract_job_info] 正则提取失败，调用 LLM")
    
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
                {"role": "user", "content": job_description[:1500]},
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


# ===================================================================
# 简历优化功能
# ===================================================================
OPTIMIZE_SYSTEM_PROMPT = """你是一个专业的简历优化师。根据用户提供的简历内容和改进建议，重写简历使其更加完善。

# 要求：
1. 保留简历的核心信息（姓名、联系方式、教育背景等）
2. 根据改进建议优化内容表达
3. 使用更专业的描述方式
4. 突出亮点和成就
5. 保持格式整洁

# 输出 JSON 结构：
{
  "modified_content": "优化后的完整简历文本",
  "applied_improvements": ["已应用的改进1", "已应用的改进2"]
}

只返回 JSON，不要其他文字。"""


def optimize_resume(resume_content: str, improvements: List[str]) -> Dict[str, Any]:
    """
    根据改进建议优化简历内容
    
    :param resume_content: 原简历内容
    :param improvements: 改进建议列表
    :return: {"modified_content": str, "applied_improvements": list}
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or "your_" in api_key or "REPLACE" in api_key or "YOUR" in api_key:
        raise ValueError("OPENAI_API_KEY 未配置")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    client = OpenAI(api_key=api_key, base_url=base_url)

    # 构建用户消息
    improvements_text = "\n".join([f"- {imp}" for imp in improvements])
    user_msg = f"""## 原简历内容
{resume_content}

## 改进建议
{improvements_text}

请根据以上改进建议优化简历，返回优化后的完整简历内容。"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": OPTIMIZE_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
        )
        
        raw = response.choices[0].message.content or ""
        result = extract_json(raw)
        
        # 确保返回格式正确
        return {
            "modified_content": result.get("modified_content", resume_content),
            "applied_improvements": result.get("applied_improvements", improvements)
        }
    except Exception as e:
        raise RuntimeError(f"简历优化失败: {e}")

