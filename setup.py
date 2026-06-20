#!/usr/bin/env python3
"""
LIMBO 设备配置脚本
在新设备上首次使用前运行此脚本进行配置

用法:
    python setup.py              # 交互式配置
    python setup.py --check     # 仅检查依赖
    python setup.py --fix       # 自动修复常见问题
"""
import os
import sys
import json
import platform
import subprocess
import shutil
from pathlib import Path

# ============================================================================
# 颜色输出（跨平台）
# ============================================================================
if platform.system() == "Windows":
    # Windows PowerShell 支持 ANSI，但 cmd.exe 不支持
    RESET = RED = GREEN = YELLOW = BLUE = ""
    TRY = ""
else:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    TRY = "\033[3m"

def info(msg): print(f"{BLUE}[INFO]{RESET} {msg}")
def ok(msg): print(f"{GREEN}[OK]{RESET} {msg}")
def warn(msg): print(f"{YELLOW}[WARN]{RESET} {msg}")
def error(msg): print(f"{RED}[ERROR]{RESET} {msg}")
def step(n, msg): print(f"\n{BLUE}─── 步骤 {n}: {msg}{RESET}")
def divider(): print("─" * 60)

# ============================================================================
# 路径与基础设置
# ============================================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_PY = SCRIPT_DIR / "config.py"
USER_CONFIG = SCRIPT_DIR / "user_config.json"
SERVER_PROFILES = SCRIPT_DIR / "server_profiles.json"
REQUIREMENTS_FILE = SCRIPT_DIR / "requirements.txt"

# ============================================================================
# 依赖检查函数
# ============================================================================
def check_python_version():
    info(f"Python 版本: {platform.python_version()}")
    if sys.version_info < (3, 9):
        error("需要 Python 3.9 或更高版本")
        return False
    return True

def check_conda():
    if not shutil.which("conda"):
        error("未找到 conda。请安装 Miniconda 或 Anaconda：")
        error("  https://docs.conda.io/en/latest/miniconda.html")
        return False
    result = subprocess.run(["conda", "--version"], capture_output=True, text=True)
    ok(f"Conda 已安装: {result.stdout.strip()}")
    return True

def check_openclaw():
    """检查 OpenClaw Gateway 是否正在运行"""
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:18789", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            ok("OpenClaw Gateway 运行正常")
            return True
    except Exception:
        warn("OpenClaw Gateway 未运行或无法访问 (http://127.0.0.1:18789)")
        info("  如果只需要工作流管理和终端功能，可以继续配置")
        info("  启动 OpenClaw: 在另一个终端运行 openclaw 或 openclaw-gateway")
        return False

def check_r_plot_agent(path: str) -> bool:
    """检查 r_plot_agent 是否存在且结构完整"""
    p = Path(path)
    if not p.exists():
        return False
    required = ["agent.py", "core"]
    for item in required:
        if not (p / item).exists():
            return False
    return True

def find_r_plot_agent() -> str:
    """自动搜索 r_plot_agent 常见位置（项目内嵌优先）"""
    # 1. 项目内嵌（默认，内置后优先使用）
    embedded = SCRIPT_DIR / "r_plot_agent"
    if check_r_plot_agent(str(embedded)):
        return str(embedded)

    candidates = [
        # 2. iCloud 旧路径（兼容）
        Path.home() / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents" / "temp" / "下游R" / "r_plot_agent",
        # 3. 用户自定义路径
        SCRIPT_DIR.parent / "r_plot_agent",
        Path.home() / "r_plot_agent",
    ]
    for c in candidates:
        if check_r_plot_agent(str(c)):
            return str(c)
    return ""

def check_r():
    """检查 R 是否安装"""
    if not shutil.which("R"):
        warn("未找到 R (http://r-project.org)")
        info("  R 可视化模块需要 R 3.6+，请安装后重试")
        return False
    result = subprocess.run(["R", "--version"], capture_output=True, text=True)
    ok(f"R 已安装: {result.stdout.splitlines()[0]}")
    return True

def check_python_packages():
    """检查 requirements.txt 中的 Python 包"""
    if not REQUIREMENTS_FILE.exists():
        warn("未找到 requirements.txt，跳过包检查")
        return True
    missing = []
    with open(REQUIREMENTS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkg = line.split("==")[0].split(">=")[0].strip()
            try:
                __import__(pkg.replace("-", "_").replace(".","_"))
            except ImportError:
                missing.append(line)
    if missing:
        error("缺少以下 Python 包:")
        for m in missing:
            print(f"  - {m}")
        info("运行以下命令安装:")
        info(f"  pip install -r {REQUIREMENTS_FILE}")
        return False
    ok("所有 Python 依赖已满足")
    return True

# ============================================================================
# 交互式配置
# ============================================================================
def ask_r_plot_agent_path():
    """询问 r_plot_agent 路径"""
    auto_path = find_r_plot_agent()
    default = auto_path or os.environ.get("R_PLOT_AGENT_PATH", "")

    print()
    print("请设置 r_plot_agent 路径（用于 R 可视化功能）")
    print(f"  自动检测到: {GREEN}{auto_path}{RESET}" if auto_path else "  自动检测: 未找到")
    print(f"  直接回车使用默认: {default if default else '(未设置)'}")

    while True:
        user_input = input(f"\n{R_PLOT_AGENT_PATH}> ").strip()
        path = user_input if user_input else default
        if not path:
            print(f"{YELLOW}跳过（R 可视化功能将不可用）{RESET}")
            return ""
        p = Path(path)
        if check_r_plot_agent(path):
            ok(f"路径有效: {path}")
            return path
        print(f"{RED}目录不存在或结构不完整: {path}{RESET}")
        print("  请确保目录内包含 agent.py 和 core/ 文件夹")

def ask_conda_prefix():
    """询问 Conda 安装路径"""
    auto = os.environ.get("CONDA_PREFIX", "")
    if not auto:
        # 尝试自动检测
        result = subprocess.run(["conda", "info", "--base"], capture_output=True, text=True)
        if result.returncode == 0:
            auto = result.stdout.strip()

    print()
    print("Conda 环境路径（直接回车使用系统默认 conda）:")
    print(f"  自动检测: {auto}" if auto else "  自动检测: 无")
    user_input = input(f"  > ").strip()
    return user_input if user_input else ""

def ask_openclaw():
    """询问 OpenClaw 配置"""
    print()
    print("OpenClaw Gateway 地址（直接回车使用默认: http://127.0.0.1:18789）:")
    user_input = input("  > ").strip()
    return user_input if user_input else "http://127.0.0.1:18789"

def ask_server_profiles():
    """询问是否配置 SSH 服务器"""
    print()
    print("是否配置 SSH 服务器连接？（y/N）")
    choice = input("  > ").strip().lower()
    if choice != "y":
        return []
    profiles = []
    while True:
        print()
        print(f"  添加服务器 #{len(profiles)+1}（留空结束）:")
        name = input("    名称: ").strip()
        if not name:
            break
        host = input("    主机: ").strip()
        port = input("    端口 [22]: ").strip() or "22"
        user = input("    用户名: ").strip()
        print("    密钥路径（直接回车使用默认 ~/.ssh/id_rsa）:")
        key_path = input("    > ").strip() or "~/.ssh/id_rsa"
        profiles.append({
            "name": name,
            "host": host,
            "port": int(port),
            "user": user,
            "key_path": key_path
        })
        print()
    ok(f"已添加 {len(profiles)} 个服务器配置")
    return profiles

# ============================================================================
# 配置写入
# ============================================================================
def write_user_config(config: dict):
    with open(USER_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    ok(f"配置已保存到: {USER_CONFIG}")

def write_server_profiles(profiles: list):
    with open(SERVER_PROFILES, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)
    ok(f"服务器配置已保存到: {SERVER_PROFILES}")

# ============================================================================
# 主流程
# ============================================================================
def run_setup():
    print()
    divider()
    print(f"{BLUE}  LIMBO 设备配置向导{RESET}")
    print(f"  目标设备: {platform.node()} ({platform.system()} {platform.release()})")
    divider()

    config = {}

    # 步骤 1: Python 版本
    step(1, "检查 Python 版本")
    if not check_python_version():
        sys.exit(1)
    ok("Python 版本满足要求")

    # 步骤 2: Conda
    step(2, "检查 Conda")
    if not check_conda():
        sys.exit(1)
    config["conda_prefix"] = ask_conda_prefix()

    # 步骤 3: Python 包
    step(3, "检查 Python 依赖")
    check_python_packages()

    # 步骤 4: R（可选）
    step(4, "检查 R（可选）")
    check_r()

    # 步骤 5: r_plot_agent 路径
    step(5, "配置 r_plot_agent 路径")
    config["r_plot_agent_path"] = ask_r_plot_agent_path()

    # 步骤 6: OpenClaw
    step(6, "检查 OpenClaw Gateway")
    config["openclaw_url"] = ask_openclaw()
    check_openclaw()

    # 步骤 7: SSH 服务器（可选）
    step(7, "配置 SSH 服务器（可选）")
    profiles = ask_server_profiles()

    # 写入配置
    divider()
    print()
    step(8, "保存配置")
    write_user_config(config)
    if profiles:
        write_server_profiles(profiles)

    # 总结
    divider()
    print()
    ok("配置完成！")
    print()
    print(f"  {GREEN}下一步:{RESET}")
    print(f"    启动平台:  python3 launcher.py")
    print(f"    或直接:    python3 backend.py")
    print(f"    访问:      http://localhost:5001")
    print()
    print(f"  如需重新配置，运行: python3 setup.py")
    print()

def run_check():
    """仅检查依赖，不交互配置"""
    print()
    divider()
    print(f"{BLUE}  依赖检查{RESET}")
    divider()

    checks = [
        ("Python 版本", check_python_version),
        ("Conda", check_conda),
        ("Python 包", check_python_packages),
        ("R", check_r),
        ("OpenClaw Gateway", lambda: check_openclaw() or True),
    ]

    all_pass = True
    for name, fn in checks:
        print(f"\n{BLUE}检查: {name}{RESET}")
        try:
            result = fn()
            if result is False:
                all_pass = False
        except Exception as e:
            error(f"检查出错: {e}")
            all_pass = False

    divider()
    print()
    if all_pass:
        ok("所有检查通过")
    else:
        warn("部分检查未通过，请修复后重试")
    print()

def run_fix():
    """自动修复常见问题"""
    info("自动修复功能正在开发中...")
    info("建议手动运行: pip install -r requirements.txt")

# ============================================================================
# 入口
# ============================================================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--check":
            run_check()
        elif cmd == "--fix":
            run_fix()
        else:
            print(f"未知参数: {cmd}")
            print("用法: python setup.py [--check|--fix]")
    else:
        run_setup()