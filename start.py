"""
简历智能打分 Agent - 启动脚本
"""
import subprocess
import sys
import os

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")

def start_backend():
    """启动后端"""
    print("启动后端...")
    subprocess.run([
        VENV_PYTHON, "-m", "uvicorn", 
        "backend.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ], cwd=ROOT_DIR)

def start_frontend():
    """启动前端"""
    print("启动前端...")
    frontend_dir = os.path.join(ROOT_DIR, "frontend")
    subprocess.run(["npm", "run", "dev"], cwd=frontend_dir)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "backend":
            start_backend()
        elif sys.argv[1] == "frontend":
            start_frontend()
        else:
            print("用法: python start.py [backend|frontend]")
    else:
        print("用法: python start.py [backend|frontend]")
        print("  backend  - 启动后端服务")
        print("  frontend - 启动前端服务")
