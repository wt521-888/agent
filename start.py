"""
简历智能打分 Agent - 一键启动脚本
====================================
用法：
    py start.py backend    # 只启动后端
    py start.py frontend   # 只启动前端
    py start.py all        # 同时启动后端和前端（前台运行，按 Ctrl+C 全停）
    py start.py stop       # 停止所有服务

特点：
- 自动检测 Python 解释器
- 自动 install 依赖
- 编码安全（纯 Python，无 bat 兼容问题）
"""
import os
import sys
import subprocess
import time
from pathlib import Path

# 强制 UTF-8 输出（Windows CMD 默认 GBK 会卡 emoji/中文）
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

# 用户机器上的 Python 绝对路径（pip/python 在 PATH 里识别不到）
PYTHON_EXE = Path(r"C:\Users\MECHREVO\AppData\Local\Programs\Python\Python314\python.exe")


def find_python() -> str:
    """检测 Python 解释器"""
    if PYTHON_EXE.exists():
        return str(PYTHON_EXE)
    # 退路：尝试 py / python
    for name in ("py", "python", "python3"):
        try:
            r = subprocess.run([name, "--version"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return name
        except Exception:
            continue
    print("[错误] 找不到 Python，请先安装 Python 3.10+")
    sys.exit(1)


def run(cmd: list, cwd: Path = None, check: bool = True) -> int:
    """执行命令并打印"""
    print(f"\n>>> {' '.join(cmd)}  (cwd={cwd or os.getcwd()})")
    return subprocess.call(cmd, cwd=str(cwd) if cwd else None)


def install_backend(py: str) -> None:
    req = BACKEND_DIR / "requirements.txt"
    if not req.exists():
        print(f"[错误] 找不到 {req}")
        sys.exit(1)
    run([py, "-m", "pip", "install", "-r", str(req)], cwd=BACKEND_DIR)


def start_backend(py: str, background: bool = True) -> subprocess.Popen | None:
    """启动后端"""
    if background:
        print("\n=== 启动后端 (后台) ===")
        # CREATE_NEW_CONSOLE = 0x10，新开窗口
        return subprocess.Popen(
            [py, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
            cwd=str(BACKEND_DIR),
            creationflags=0x10 if sys.platform == "win32" else 0,
        )
    else:
        # 前台运行
        return subprocess.Popen(
            [py, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(BACKEND_DIR),
        )


def install_frontend() -> None:
    pkg = FRONTEND_DIR / "package.json"
    if not pkg.exists():
        print(f"[错误] 找不到 {pkg}")
        sys.exit(1)
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        # 用国内镜像
        env = os.environ.copy()
        env["npm_config_registry"] = "https://registry.npmmirror.com"
        print("\n=== npm install（首次）===")
        subprocess.call(["npm", "install"], cwd=str(FRONTEND_DIR), env=env)
    else:
        print("node_modules 已存在，跳过安装")


def start_frontend(background: bool = True) -> subprocess.Popen | None:
    """启动前端"""
    if background:
        print("\n=== 启动前端 (后台，新窗口) ===")
        return subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(FRONTEND_DIR),
            creationflags=0x10 if sys.platform == "win32" else 0,
        )
    else:
        return subprocess.Popen(["npm", "run", "dev"], cwd=str(FRONTEND_DIR))


def stop_all() -> None:
    """停止所有服务"""
    print("正在停止后端 (uvicorn)...")
    subprocess.call(["taskkill", "/IM", "uvicorn.exe", "/F"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("正在停止前端 (node)...")
    subprocess.call(["taskkill", "/IM", "node.exe", "/F"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("已停止。")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "stop":
        stop_all()
        return

    py = find_python()
    print(f"使用 Python: {py}")

    if cmd == "backend":
        install_backend(py)
        p = start_backend(py, background=True)
        print(f"\n[OK] 后端已启动 (PID={p.pid if p else 'N/A'})")
        print("     访问 http://127.0.0.1:8000/docs")
        print("     停止: py start.py stop")

    elif cmd == "frontend":
        install_frontend()
        p = start_frontend(background=True)
        print(f"\n[OK] 前端已启动 (PID={p.pid if p else 'N/A'})")
        print("     访问 http://127.0.0.1:5173")
        print("     停止: py start.py stop")

    elif cmd == "all":
        print("=== 安装后端依赖 ===")
        install_backend(py)
        print("=== 安装前端依赖 ===")
        install_frontend()
        print("=== 启动后端 (后台) ===")
        bp = start_backend(py, background=True)
        time.sleep(2)
        print("=== 启动前端 (后台) ===")
        fp = start_frontend(background=True)
        print("\n" + "=" * 50)
        print("[OK] 全部启动完成！")
        print("     后端 API:  http://127.0.0.1:8000/docs")
        print("     前端界面:  http://127.0.0.1:5173")
        print("     停止服务:  py start.py stop")
        print("=" * 50)
        try:
            # 前台等待
            while True:
                time.sleep(1)
                if bp.poll() is not None or fp.poll() is not None:
                    print("\n[提示] 有服务已退出，按 Ctrl+C 结束")
                    break
        except KeyboardInterrupt:
            print("\n正在停止所有服务...")
            stop_all()

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
