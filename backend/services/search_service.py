"""
Tavily 联网搜索服务：获取公司与岗位相关信息
"""
import os
from typing import List, Dict
from tavily import TavilyClient


def search_company_info(
    company: str, position: str, query_keywords: str = ""
) -> List[Dict]:
    """
    使用 Tavily 搜索公司 / 岗位相关信息。
    失败会抛 RuntimeError，由调用方决定是否继续。

    :return: [{title, content(前500字), url}, ...]
    """
    api_key = os.getenv("TAVILY_API_KEY", "")
    # 占位符检测
    if not api_key or "your_" in api_key or "REPLACE" in api_key or "YOUR" in api_key:
        raise ValueError("TAVILY_API_KEY 未配置")

    max_results = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
    query = f"{company} {position} 公司介绍 业务 文化 面试 技术要求 {query_keywords}".strip()

    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=query,
        search_depth="basic",
        max_results=max_results,
    )
    results = response.get("results", []) or []

    truncated = []
    for r in results[:max_results]:
        truncated.append({
            "title": r.get("title", ""),
            "content": (r.get("content", "") or "")[:500],
            "url": r.get("url", ""),
        })
    return truncated


def format_search_summary(results: List[Dict]) -> str:
    """把搜索结果数组格式化为可读文本，供 LLM Prompt 使用"""
    if not results:
        return ""
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(
            f"[{i}] {r['title']}\n"
            f"来源: {r['url']}\n"
            f"{r['content']}\n"
        )
    return "\n".join(lines)
