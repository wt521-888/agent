"""
配置路由：支持在线修改 API Key 和模型
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv, set_key

load_dotenv()

router = APIRouter()

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


class ConfigResponse(BaseModel):
    openai_api_key: str
    openai_base_url: str
    openai_model: str
    vision_model: str
    tavily_api_key: str


class ConfigUpdateRequest(BaseModel):
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: Optional[str] = None
    vision_model: Optional[str] = None
    tavily_api_key: Optional[str] = None


def _mask_key(key: str) -> str:
    if not key or len(key) < 10:
        return "未配置"
    return key[:6] + "****" + key[-4:]


@router.get("", response_model=ConfigResponse)
async def get_config():
    return ConfigResponse(
        openai_api_key=_mask_key(os.getenv("OPENAI_API_KEY", "")),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        vision_model=os.getenv("VISION_MODEL", "gpt-4o-mini"),
        tavily_api_key=_mask_key(os.getenv("TAVILY_API_KEY", "")),
    )


@router.put("")
async def update_config(req: ConfigUpdateRequest):
    try:
        if req.openai_api_key is not None:
            set_key(ENV_FILE, "OPENAI_API_KEY", req.openai_api_key)
            os.environ["OPENAI_API_KEY"] = req.openai_api_key
        
        if req.openai_base_url is not None:
            set_key(ENV_FILE, "OPENAI_BASE_URL", req.openai_base_url)
            os.environ["OPENAI_BASE_URL"] = req.openai_base_url
        
        if req.openai_model is not None:
            set_key(ENV_FILE, "OPENAI_MODEL", req.openai_model)
            os.environ["OPENAI_MODEL"] = req.openai_model
        
        if req.vision_model is not None:
            set_key(ENV_FILE, "VISION_MODEL", req.vision_model)
            os.environ["VISION_MODEL"] = req.vision_model
        
        if req.tavily_api_key is not None:
            set_key(ENV_FILE, "TAVILY_API_KEY", req.tavily_api_key)
            os.environ["TAVILY_API_KEY"] = req.tavily_api_key
        
        return {"message": "配置更新成功"}
    except Exception as e:
        raise HTTPException(500, f"更新配置失败: {e}")


@router.post("/test-openai")
async def test_openai_connection():
    """测试 API 连接，确保 Key 真实可用"""
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or "your_" in api_key:
            return {"success": False, "error": "API Key 未配置或为占位符"}
        
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=30.0)
        
        # 发送真实请求验证 Key 可用性
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "请回复'连接成功'两个字"}],
            max_tokens=20,
        )
        
        content = response.choices[0].message.content or ""
        return {
            "success": True,
            "model": model,
            "response": content[:50]
        }
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "invalid" in error_msg.lower():
            return {"success": False, "error": "API Key 无效，请检查是否正确"}
        elif "404" in error_msg or "not found" in error_msg.lower():
            return {"success": False, "error": f"模型不存在，请检查模型名称"}
        elif "timeout" in error_msg.lower():
            return {"success": False, "error": "连接超时，请检查网络或 Base URL"}
        else:
            return {"success": False, "error": error_msg[:200]}

