"""
LIMBO global configuration.

All cross-device path and setting differences are centralized here.
Before using on a new device, run: python setup.py
"""
import os
import sys
import json
import platform
from pathlib import Path

# ============================================================================
# Device information
# ============================================================================
DEVICE_NAME = platform.node()
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"
IS_UNIX = IS_MACOS or IS_LINUX

# ============================================================================
# Project root
# ============================================================================
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.resolve()

FRONTEND_DIR = BASE_DIR / "frontend"
WORKFLOWS_DIR = BASE_DIR / "workflows"
TEMPLATES_DIR = BASE_DIR / "templates"
STATE_FILE = BASE_DIR / "state.json"

# ============================================================================
# OpenClaw Gateway (AI inference engine)
# ----------------------------------------------------------------------------
# Default values are placeholders. Override via environment variables before
# running, e.g.:
#   export OPENCLAW_URL="http://your-gateway-host:18789"
#   export OPENCLAW_TOKEN_PATH="<path-to>/openclaw.json"
# Without a running OpenClaw Gateway the AI chat features will be disabled.
# ============================================================================
OPENCLAW_URL = os.environ.get("OPENCLAW_URL", "http://127.0.0.1:18789")
OPENCLAW_TOKEN_PATH = Path(
    os.environ.get(
        "OPENCLAW_TOKEN_PATH",
        str(Path.home() / ".openclaw" / "openclaw.json")
    )
)

# ============================================================================
# R visualization module (r_plot_integration)
# ============================================================================
# Path to r_plot_agent (R visualization module).
# Project-internal r_plot_agent is used by default; override via env var.
R_PLOT_AGENT_PATH = os.environ.get(
    "R_PLOT_AGENT_PATH",
    str(BASE_DIR / "r_plot_agent")
)

# ============================================================================
# Conda environment
# ============================================================================
CONDA_EXECUTABLE = os.environ.get("CONDA_EXECUTABLE", "conda")
CONDA_PREFIX = os.environ.get("CONDA_PREFIX", "")

# ============================================================================
# SSH / PTY terminal (Unix only; Windows requires WSL2)
# ============================================================================
SSH_DEFAULT_TIMEOUT = 10
PTY_DEFAULT_ROWS = 40
PTY_DEFAULT_COLS = 120
PTY_TERMINAL_TYPE = "xterm-256color"

# ============================================================================
# Server profiles
# ============================================================================
SERVER_PROFILES_PATH = BASE_DIR / "server_profiles.json"

# ============================================================================
# Logging
# ============================================================================
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "limbo.log"

# ============================================================================
# API
# ============================================================================
API_HOST = os.environ.get("LIMBO_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("LIMBO_PORT", "5002"))
CORS_ORIGINS = "*"

# ============================================================================
# Environment fix loop
# ============================================================================
ENV_FIX_MAX_ATTEMPTS = 3
ENV_FIX_MODEL = os.environ.get("LIMBO_ENV_FIX_MODEL", "openclaw/default")

# ============================================================================
# State management
# ============================================================================
STATE_FILE_PATH = BASE_DIR / "state.json"

# ============================================================================
# Platform-specific settings
# ============================================================================
if IS_WINDOWS:
    PTY_AVAILABLE = False
    TERMINAL_SHELL = ["powershell.exe"]
    DEFAULT_WORKING_DIR = Path.home() / "Documents"
else:
    PTY_AVAILABLE = True
    TERMINAL_SHELL = ["/bin/bash", "-l"]
    DEFAULT_WORKING_DIR = Path.home()

# ============================================================================
# Dependency checks
# ============================================================================
REQUIRED_PYTHON_PACKAGES = [
    "fastapi", "socketio", "paramiko", "yaml", "uvicorn", "pydantic"
]

REQUIRED_SYSTEM_CMD = ["conda"]

def get_openclaw_token():
    """Read OpenClaw Gateway token from config file."""
    if not OPENCLAW_TOKEN_PATH.exists():
        return None
    try:
        with open(OPENCLAW_TOKEN_PATH, "r") as f:
            data = json.load(f)
            return data.get("token", data.get("api_key", ""))
    except Exception:
        return None

def check_dependencies():
    """Check whether system dependencies are satisfied. Returns (ok, messages)."""
    messages = []
    ok = True

    # Python packages
    for pkg in REQUIRED_PYTHON_PACKAGES:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            messages.append(f"Missing Python package: {pkg}. Run: pip install {pkg}")
            ok = False

    # Conda
    import shutil
    if not shutil.which("conda"):
        messages.append("Conda not found. Ensure 'conda' is in PATH or set CONDA_EXECUTABLE.")
        ok = False

    # r_plot_agent path
    if not R_PLOT_AGENT_PATH or not Path(R_PLOT_AGENT_PATH).exists():
        messages.append(f"R visualization module path not set or missing: {R_PLOT_AGENT_PATH}")
        messages.append("  -> Run python setup.py or set R_PLOT_AGENT_PATH environment variable")

    # OpenClaw (advisory, non-blocking)
    if not get_openclaw_token():
        messages.append("Warning: No OpenClaw token found; AI chat features will be unavailable.")
        messages.append(f"  -> Ensure OpenClaw Gateway is running at {OPENCLAW_URL}")

    return ok, messages

def ensure_dirs():
    """Ensure required directories exist."""
    for d in [WORKFLOWS_DIR, TEMPLATES_DIR, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# ============================================================================
# User config (per-device customizations)
# ============================================================================
USER_CONFIG_FILE = BASE_DIR / "user_config.json"

def load_user_config():
    """Load per-user configuration overrides."""
    if USER_CONFIG_FILE.exists():
        try:
            with open(USER_CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_user_config(config: dict):
    """Save per-user configuration overrides."""
    with open(USER_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# ============================================================================
# Initialization (runs on import)
# ============================================================================
ensure_dirs()