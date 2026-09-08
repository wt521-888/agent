"""
模拟面试服务：根据简历和岗位生成面试问题，评估回答
"""
import os
import re
import json
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 面试问题生成提示词
INTERVIEW_QUESTION_PROMPT = """你是一位资深的技术面试官。根据候选人的简历和目标岗位，生成专业的面试问题。

# 要求
1. 生成 5 个面试问题，涵盖：
   - 技术能力（2题）
   - 项目经验（1题）
   - 问题解决能力（1题）
   - 综合素质（1题）
2. 问题难度要匹配岗位要求
3. 问题要具体、有针对性

# 输出格式（严格 JSON）
{
  "questions": [
    {
      "id": 1,
      "category": "技术能力|项目经验|问题解决|综合素质",
      "question": "问题内容",
      "difficulty": "简单|中等|困难",
      "key_points": ["考察要点1", "考察要点2"]
    }
  ]
}

只返回 JSON，不要其他文字。"""

# 回答评估提示词
INTERVIEW_EVALUATE_PROMPT = """你是一位资深的技术面试官。评估候选人对面试问题的回答。

# 评估维度
1. 准确性（0-100）：答案是否正确
2. 完整性（0-100）：是否覆盖关键点
3. 深度（0-100）：理解是否深入
4. 表达（0-100）：逻辑是否清晰

# 输出格式（严格 JSON）
{
  "overall_score": 0-100,
  "scores": {
    "accuracy": 0-100,
    "completeness": 0-100,
    "depth": 0-100,
    "expression": 0-100
  },
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["不足1", "不足2"],
  "improvement_suggestions": ["改进建议1", "改进建议2"],
  "reference_answer": "参考答案（简要）"
}

只返回 JSON，不要其他文字。"""


def _get_client():
    """获取 OpenAI 客户端"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or "your_" in api_key:
        raise ValueError("OPENAI_API_KEY 未配置")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    return OpenAI(api_key=api_key, base_url=base_url, timeout=120.0)


def _get_model():
    """获取模型名称"""
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _extract_json(text: str) -> Dict[str, Any]:
    """从 LLM 输出中提取 JSON"""
    if not text:
        raise ValueError("LLM 返回内容为空")
    text = text.strip()
    text = re.sub(r"^`(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*`$", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 尝试修复截断的 JSON
    open_braces = text.count('{') - text.count('}')
    open_brackets = text.count('[') - text.count(']')
    text = text.rstrip().rstrip(',')
    text += ']' * max(0, open_brackets)
    text += '}' * max(0, open_braces)
    
    return json.loads(text)


def generate_interview_questions(
    resume_content: str,
    job_description: str,
    num_questions: int = 5
) -> Dict[str, Any]:
    """
    根据简历和岗位生成面试问题
    
    :param resume_content: 简历内容
    :param job_description: 岗位描述
    :param num_questions: 问题数量
    :return: 面试问题列表
    """
    client = _get_client()
    model = _get_model()
    
    user_msg = f"""## 候选人简历
{resume_content[:2000]}

## 目标岗位
{job_description[:1000]}

请生成 {num_questions} 个面试问题。"""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": INTERVIEW_QUESTION_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        content = response.choices[0].message.content or ""
        result = _extract_json(content)
        return result
    except Exception as e:
        raise RuntimeError(f"生成面试问题失败: {e}")


def evaluate_answer(
    question: str,
    answer: str,
    job_description: str = "",
    key_points: List[str] = None
) -> Dict[str, Any]:
    """
    评估面试回答
    
    :param question: 面试问题
    :param answer: 候选人回答
    :param job_description: 岗位描述（可选）
    :param key_points: 考察要点（可选）
    :return: 评估结果
    """
    client = _get_client()
    model = _get_model()
    
    user_msg = f"""## 面试问题
{question}

## 候选人回答
{answer}

## 考察要点
{', '.join(key_points) if key_points else '无特定要求'}

## 目标岗位
{job_description[:500] if job_description else '无特定岗位'}

请评估候选人的回答。"""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": INTERVIEW_EVALUATE_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        content = response.choices[0].message.content or ""
        result = _extract_json(content)
        return result
    except Exception as e:
        raise RuntimeError(f"评估回答失败: {e}")
