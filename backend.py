"""
FastAPI backend for LIMBO
Tab-based UI with Workflow Management and Environment Building
"""
import os
import sys
import json
import asyncio
import threading
import time
import subprocess
import re
import platform
import urllib.request
import urllib.error
import paramiko
import pty
import fcntl
import struct
import signal
from pathlib import Path
from typing import Optional

# 加载 LIMBO 配置（集中管理跨设备路径差异）
from config import (
    BASE_DIR, FRONTEND_DIR, IS_UNIX, IS_WINDOWS,
    OPENCLAW_URL, OPENCLAW_TOKEN_PATH,
    CONDA_EXECUTABLE, CONDA_PREFIX,
    ENV_FIX_MAX_ATTEMPTS,
    PTY_DEFAULT_ROWS, PTY_DEFAULT_COLS, PTY_TERMINAL_TYPE,
    API_HOST, API_PORT, CORS_ORIGINS,
    LOG_DIR, LOG_FILE,
    STATE_FILE, SERVER_PROFILES_PATH,
    PTY_AVAILABLE, DEFAULT_WORKING_DIR,
    load_user_config, save_user_config,
    USER_CONFIG_FILE
)
from i18n import t as i18n_t, get_catalog as i18n_get_catalog, LOCALES as I18N_LOCALES, DEFAULT_LOCALE as I18N_DEFAULT

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
import socketio
import yaml
import select

# ============================================================================
# Configuration（保留原有内联配置作为向后兼容，优先使用 config.py）
# ============================================================================
if getattr(sys, 'frozen', False):
    _BASE_DIR = Path(sys.executable).parent
    _FRONTEND_DIR = _BASE_DIR / 'Resources' / 'frontend'
else:
    _BASE_DIR = Path(__file__).parent
    _FRONTEND_DIR = _BASE_DIR / "frontend"

# ============================================================================
# Socket.IO Server (python-socketio)
# ============================================================================
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*"
)

# ============================================================================
# FastAPI App
# ============================================================================
app = FastAPI(title="LIMBO API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """Pre-warm the agent session so it's ready before first chat request."""
    try:
        token = _load_openclaw_token()
        if not token:
            print("[startup] No OpenClaw token, skipping session pre-warm")
            return
        session_key = "agent:limbo:startup"
        url = f"http://{OPENCLAW_GATEWAY_HOST}:{OPENCLAW_GATEWAY_PORT}/v1/chat/completions"
        payload = {
            "model": "openclaw/default",
            "messages": [{"role": "user", "content": "ping"}],
            "stream": False,
            "max_tokens": 1,
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "x-openclaw-session-key": session_key,
        }
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
                print(f"[startup] Agent session pre-warmed: {session_key}")
        except Exception as e:
            print(f"[startup] Agent session pre-warm failed: {e}")
    except Exception as e:
        print(f"[startup] Session pre-warm error: {e}")




# ============================================================================
# State Management
# ============================================================================
class StateManager:
    def __init__(self):
        self.state_file = BASE_DIR / "state.json"
        self.state = self._load()

    def _load(self):
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get(self, key, default=None):
        return self.state.get(key, default)

    def set(self, key, value):
        self.state[key] = value
        self.save()

state_manager = StateManager()

# ============================================================================
# SSH Connection Manager with PTY Support
# ============================================================================
class SSHConnectionManager:
    def __init__(self):
        self.connections = {}
        self.sessions = {}
        self.lock = threading.Lock()

    def add_connection(self, name, config):
        self.connections[name] = config

    def remove_connection(self, name):
        if name in self.connections:
            del self.connections[name]

    def get_connections(self):
        return {name: {
            'name': name,
            'host': conn.get('host', ''),
            'port': conn.get('port', 22),
            'user': conn.get('user', ''),
            'status': conn.get('status', 'disconnected')
        } for name, conn in self.connections.items()}

    def test_connection(self, name):
        config = self.connections.get(name, {})
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if config.get('key_file'):
                client.connect(hostname=config['host'], port=config['port'],
                             username=config['user'], key_filename=config['key_file'])
            else:
                client.connect(hostname=config['host'], port=config['port'],
                             username=config['user'], password=config['password'])
            client.close()
            return True, "连接成功"
        except Exception as e:
            return False, str(e)

    def create_session(self, name, env_path=None):
        """Create interactive PTY session"""
        session_id = None

        if name == 'local':
            pid, fd = pty.fork()
            if pid == 0:
                env = os.environ.copy()
                env['TERM'] = 'xterm-256color'
                if env_path:
                    conda_sh = '/opt/anaconda3/etc/profile.d/conda.sh'
                    if not os.path.exists(conda_sh):
                        conda_sh = os.path.expanduser('~/miniconda3/etc/profile.d/conda.sh')
                    os.execvp('bash', ['bash', '-c', f'source {conda_sh} 2>/dev/null && conda activate "{env_path}" && exec bash'])
                else:
                    os.execvp('bash', ['bash'])
            else:
                session_id = f"local_{fd}"
                self.sessions[session_id] = {'pid': pid, 'fd': fd, 'name': name, 'client': None, 'channel': None}
        else:
            config = self.connections.get(name, {})
            if not config:
                return None

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            try:
                if config.get('key_file'):
                    client.connect(
                        hostname=config['host'],
                        port=config['port'],
                        username=config['user'],
                        key_filename=config['key_file']
                    )
                else:
                    client.connect(
                        hostname=config['host'],
                        port=config['port'],
                        username=config['user'],
                        password=config['password']
                    )

                channel = client.get_transport().open_session()
                channel.get_pty(width=120, height=40, term='xterm-256color')
                channel.invoke_shell()

                session_id = f"{name}_{id(channel)}"
                self.sessions[session_id] = {'client': client, 'channel': channel, 'name': name, 'pid': None, 'fd': None}

                if env_path:
                    time.sleep(0.2)
                    conda_sh = '/opt/anaconda3/etc/profile.d/conda.sh'
                    if not os.path.exists(conda_sh):
                        conda_sh = os.path.expanduser('~/miniconda3/etc/profile.d/conda.sh')
                    channel.send(f'source {conda_sh} 2>/dev/null && conda activate "{env_path}"\n')

            except Exception as e:
                return None

        return session_id

    def send_input(self, session_id, data):
        if session_id not in self.sessions:
            return
        session = self.sessions[session_id]
        if session.get('channel'):
            session['channel'].send(data)
        elif session.get('fd') is not None:
            os.write(session['fd'], data.encode())

    def recv_output(self, session_id):
        if session_id not in self.sessions:
            return ''
        session = self.sessions[session_id]
        if session.get('channel'):
            if session['channel'].recv_ready():
                try:
                    return session['channel'].recv(65536).decode('utf-8')
                except:
                    return ''
        elif session.get('fd') is not None:
            r, _, _ = select.select([session['fd']], [], [], 0)
            if r:
                try:
                    return os.read(session['fd'], 65536).decode('utf-8')
                except:
                    return ''
        return ''

    def resize_pty(self, session_id, rows, cols):
        if session_id not in self.sessions:
            return
        session = self.sessions[session_id]
        if session.get('channel'):
            session['channel'].resize_pty(width=cols, height=rows)

    def close_session(self, session_id):
        if session_id not in self.sessions:
            return
        session = self.sessions[session_id]
        if session.get('channel'):
            session['channel'].close()
            if session.get('client'):
                session['client'].close()
        elif session.get('fd') is not None:
            try:
                os.close(session['fd'])
            except:
                pass
        del self.sessions[session_id]

# ============================================================================
# OpenClaw Gateway Client
# ============================================================================

OPENCLAW_GATEWAY_HOST = '127.0.0.1'
OPENCLAW_GATEWAY_PORT = 18789

def _load_openclaw_token() -> str:
    """Load OpenClaw gateway token from config file."""
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if config_path.exists():
        try:
            raw = config_path.read_text()
            import re
            m = re.search(r'"token"\s*:\s*"([^"]+)"', raw)
            if m:
                return m.group(1)
        except Exception:
            pass
    return os.environ.get("OPENCLAW_TOKEN", "")


def _gateway_request(method: str, path: str, body: dict = None, session_key: str = None) -> dict:
    """Make HTTP request to OpenClaw Gateway."""
    token = _load_openclaw_token()
    url = f"http://{OPENCLAW_GATEWAY_HOST}:{OPENCLAW_GATEWAY_PORT}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if session_key:
        headers["x-openclaw-session-key"] = session_key

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8") if body else None,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# R Session Manager
# ============================================================================

class RSessionManager:
    """Manages persistent R sessions for matrix calculations."""

    def __init__(self):
        self.sessions = {}  # session_id -> R process
        self.lock = threading.Lock()

    def _find_r_executable(self):
        """Find R executable in common locations."""
        possible_paths = [
            '/usr/local/bin/R',
            '/usr/bin/R',
            '/opt/homebrew/bin/R',
            '/opt/anaconda3/bin/R',
            os.path.expanduser('~/anaconda3/bin/R'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return 'R'  # fallback to PATH

    def create_session(self, session_id: str, project_dir: str = "") -> bool:
        """Create a new R session for the given session_id."""
        with self.lock:
            if session_id in self.sessions:
                return True

            r_path = self._find_r_executable()
            try:
                process = subprocess.Popen(
                    [r_path, '--interactive', '--vanilla'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=project_dir or None,
                    bufsize=1,
                    text=False
                )
                self.sessions[session_id] = {
                    'process': process,
                    'project_dir': project_dir,
                    'objects': []
                }
                return True
            except Exception as e:
                print(f"Failed to start R session: {e}")
                return False

    def send_command(self, session_id: str, command: str) -> dict:
        """Send a command to R session and return the result."""
        if session_id not in self.sessions:
            return {'error': f'Session {session_id} not found'}

        session = self.sessions[session_id]
        proc = session['process']

        try:
            # Send command to R
            cmd_bytes = (command + '\n').encode('utf-8')
            proc.stdin.write(cmd_bytes)
            proc.stdin.flush()

            # Read output until we get a prompt back
            output_lines = []
            start_time = time.time()
            timeout = 120  # 2 minutes for most operations

            while True:
                if time.time() - start_time > timeout:
                    return {'error': 'Command timeout', 'output': '\n'.join(output_lines)}

                # Use select for non-blocking read
                ready, _, _ = select.select([proc.stdout], [], [], 0.5)

                if ready:
                    line = proc.stdout.readline()
                    if not line:
                        return {'error': 'R process terminated', 'output': '\n'.join(output_lines)}

                    decoded = line.decode('utf-8', errors='replace')

                    # R prompt is usually '>' or '+' (continuation)
                    if decoded.strip() in ('>', '+'):
                        if output_lines:
                            break
                    else:
                        output_lines.append(decoded.rstrip())
                else:
                    # No output, check if process is still alive
                    if proc.poll() is not None:
                        return {'error': 'R process terminated', 'output': '\n'.join(output_lines)}

            return {'output': '\n'.join(output_lines), 'error': None}

        except Exception as e:
            return {'error': str(e), 'output': ''}

    def list_objects(self, session_id: str) -> list:
        """List objects in R session."""
        result = self.send_command(session_id, "ls()")
        if result.get('error'):
            return []
        # Parse ls() output
        objects = []
        for line in result.get('output', '').split('\n'):
            line = line.strip().strip('"').strip("'")
            if line and line != 'character(0)':
                objects.append(line)
        return objects

    def save_session(self, session_id: str, filepath: str) -> bool:
        """Save R session to .RData file."""
        result = self.send_command(session_id, f'save.image("{filepath}")')
        return result.get('error') is None

    def load_session(self, session_id: str, filepath: str) -> bool:
        """Load R session from .RData file."""
        result = self.send_command(session_id, f'load("{filepath}")')
        return result.get('error') is None

    def close_session(self, session_id: str):
        """Close R session."""
        with self.lock:
            if session_id in self.sessions:
                proc = self.sessions[session_id]['process']
                try:
                    proc.stdin.write(b'q()\n')
                    proc.stdin.flush()
                    proc.terminate()
                except:
                    pass
                del self.sessions[session_id]

from r_plot_integration import VisualizationManager
from openclaw_llm import get_default_client, get_token_from_gateway

# Global R session manager
r_session_manager = RSessionManager()

# Global visualization manager
viz_manager = VisualizationManager(r_session_manager)


ssh_manager = SSHConnectionManager()

saved_connections = state_manager.get('ssh_connections', {})
for name, config in saved_connections.items():
    ssh_manager.add_connection(name, config)

# ============================================================================
# Pydantic Models
# ============================================================================
class SSHConnection(BaseModel):
    name: str
    host: str
    port: int = 22
    user: str
    password: Optional[str] = None
    key_file: Optional[str] = None

class LocalCondaListRequest(BaseModel):
    pass

class LocalCondaActivateRequest(BaseModel):
    env_path: str

class WorkflowAnalyzeRequest(BaseModel):
    steps: list

class GenerateWorkflowRequest(BaseModel):
    content: str
    filename: str
    env_path: Optional[str] = None

# ============================================================================
# API Routes
# ============================================================================

@app.get("/")
async def root():
    index_path = FRONTEND_DIR / 'index.html'
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html; charset=utf-8")
    return {"status": "ok", "service": "LIMBO API"}


@app.get("/i18n.js")
async def frontend_i18n_js():
    """Serve the frontend i18n module."""
    p = FRONTEND_DIR / 'i18n.js'
    if p.exists():
        return FileResponse(str(p), media_type="application/javascript; charset=utf-8")
    return JSONResponse(status_code=404, content={"error": "i18n.js not found"})


@app.get("/{filename}")
async def frontend_static(filename: str):
    """Serve other static files from the frontend directory (html, css, js, png, etc.)."""
    if "/" in filename or filename.startswith(".") or filename.startswith("api"):
        return JSONResponse(status_code=404, content={"error": "not found"})
    p = FRONTEND_DIR / filename
    if p.exists() and p.is_file():
        # Pick a media type by extension
        suffix = p.suffix.lower()
        media = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
        }.get(suffix, "application/octet-stream")
        return FileResponse(str(p), media_type=media)
    return JSONResponse(status_code=404, content={"error": "not found"})

@app.get("/api/status")
async def status():
    return {
        "status": "running",
        "connections": ssh_manager.get_connections()
    }

# SSH Connections
@app.get("/api/ssh/connections")
async def get_ssh_connections():
    return ssh_manager.get_connections()

@app.post("/api/ssh/connections")
async def add_ssh_connection(conn: SSHConnection):
    config = {
        'host': conn.host,
        'port': conn.port,
        'user': conn.user,
        'password': conn.password,
        'key_file': conn.key_file
    }
    ssh_manager.add_connection(conn.name, config)
    connections = state_manager.get('ssh_connections', {})
    connections[conn.name] = config
    state_manager.set('ssh_connections', connections)
    return {"success": True, "name": conn.name}

@app.delete("/api/ssh/connections/{name}")
async def delete_ssh_connection(name: str):
    ssh_manager.remove_connection(name)
    connections = state_manager.get('ssh_connections', {})
    if name in connections:
        del connections[name]
        state_manager.set('ssh_connections', connections)
    return {"success": True}

@app.post("/api/ssh/connections/{name}/test")
async def test_ssh_connection(name: str):
    success, message = ssh_manager.test_connection(name)
    return {"success": success, "message": message}

# Local Conda
@app.get("/api/local/conda/list")
async def local_conda_list():
    try:
        conda_bin = '/opt/anaconda3/bin/conda'
        # Try multiple ways to find conda
        cmd = (
            f'source /opt/anaconda3/etc/profile.d/conda.sh 2>/dev/null && {conda_bin} info --envs 2>/dev/null || '
            f'source ~/.bashrc 2>/dev/null && conda info --envs 2>/dev/null || '
            f'conda env list'
        )
        result = subprocess.run(['bash', '-c', cmd], capture_output=True, text=True, timeout=30)
        output = result.stdout
        seen = set()
        envs = []
        for line in output.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split()
                name = None
                if len(parts) == 1:
                    name = parts[0]
                elif len(parts) >= 2:
                    for part in parts:
                        if part.startswith('/'):
                            name = part
                            break
                    else:
                        name = parts[-1]
                if name and name not in seen:
                    seen.add(name)
                    envs.append(name)
        return {"environments": envs}
    except Exception as e:
        return {"environments": []}

# Folder Picker
@app.get("/api/dialog/select-folder")
async def select_folder():
    import platform
    system = platform.system()
    try:
        if system == 'Darwin':
            script = 'POSIX path of (choose folder)'
            result = subprocess.run(['osascript', '-e', script],
                                 capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                path = result.stdout.strip()
                if path:
                    return {"success": True, "path": path}
                return {"success": False, "error": "No folder selected"}
            return {"success": False, "error": result.stderr or "Dialog cancelled"}
        elif system == 'Windows':
            return {"success": False, "error": "Windows not supported"}
        else:
            result = subprocess.run(['zenity', '--directory'],
                                 capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                return {"success": True, "path": result.stdout.strip()}
            return {"success": False, "error": "Dialog cancelled"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Dialog timeout"}
    except FileNotFoundError:
        return {"success": False, "error": "Dialog tool not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# Env Build Routes
# ============================================================================

def classify_tool(tool_name):
    """Classify tool as CLI or Python package"""
    cli_tools = {
        'vsearch', 'usearch', 'fastp', 'cutadapt', 'bwa', 'samtools', 'bowtie2',
        'muscle', 'mafft', 'clustalo', 'blast+', 'makeblastdb', 'diamond',
        'kraken2', 'bracken', 'metaphlan', 'humann', 'strainphlan', 'snp-eff',
        'gatk', 'freebayes', 'bcftools', 'picard', 'bedtools', 'bedops',
        'fastqc', 'trimmomatic', 'cd-hit', 'mothur', 'qiime2'
    }
    python_packages = {
        'biopython', 'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn',
        'sklearn', 'scikit-learn', 'biom-format', 'ete3', 'pysam', 'pyvcf'
    }
    tool_lower = tool_name.lower()
    if tool_lower in cli_tools:
        return 'conda'
    elif tool_lower in python_packages:
        return 'pip'
    return 'conda'

def parse_workflow_steps(workflow_text):
    """Parse workflow text to extract steps. Supports two formats:

    1. Free-text: lines like "step 2.1 description | software vsearch"
    2. Markdown table: | step | description | software | option/etc. | ...
       (typical output of env-build LLM, the supplies-list.md format)
    """
    steps = []
    lines = workflow_text.strip().split('\n')
    software_pattern = re.compile(
        r'\b(vsearch|usearch|fastp|cutadapt|bwa|samtools|qiime2|mothur|fastqc|'
        r'trimmomatic|cd-hit|muscle|mafft|blast\+?|diamond|kraken2|metaphlan|'
        r'python|perl|awk|sed)\b', re.IGNORECASE
    )

    # Detect markdown table format
    table_rows = []
    for line in lines:
        s = line.strip()
        if s.startswith('|') and s.endswith('|') and s.count('|') >= 3:
            cells = [c.strip() for c in s.strip('|').split('|')]
            table_rows.append(cells)
    if len(table_rows) >= 2:
        header = None
        data_start = 0
        for i, row in enumerate(table_rows):
            if row and row[0].lower() in ('step', '#', 'no.'):
                header = [c.lower() for c in row]
                data_start = i + 1
                break
        if header is None:
            for i, row in enumerate(table_rows):
                if len(row) >= 3 and any(k in c.lower() for c in row for k in ('description', 'software', 'step')):
                    header = [c.lower() for c in row]
                    data_start = i + 1
                    break
        if header is not None:
            if data_start < len(table_rows) and all(set(c.replace(':','').replace('-','').strip()) <= set() for c in table_rows[data_start]):
                data_start += 1
            idx_step = next((i for i, c in enumerate(header) if 'step' in c or '#' in c), 0)
            idx_desc = next((i for i, c in enumerate(header) if 'description' in c or 'name' in c), 1)
            idx_sw = next((i for i, c in enumerate(header) if 'software' in c or 'tool' in c), 2)
            for row in table_rows[data_start:]:
                if not row or all(not c for c in row):
                    continue
                if len(row) <= max(idx_step, idx_desc, idx_sw):
                    continue
                step_num = row[idx_step].strip()
                if not re.match(r'^\d+(?:\.\d+)*$', step_num):
                    continue
                desc = row[idx_desc].strip()
                software = row[idx_sw].strip() if idx_sw < len(row) else 'unknown'
                if re.match(r'^\d+$', software):
                    for alt in range(idx_sw + 1, len(row)):
                        if row[alt].strip() and not re.match(r'^[\d\.\:]+$', row[alt].strip()):
                            software = row[alt].strip()
                            break
                if not software or software == 'unknown':
                    m = software_pattern.search(desc)
                    software = m.group(1) if m else 'unknown'
                steps.append({
                    'step': step_num,
                    'name': desc,
                    'software': software,
                    'description': desc,
                })
            if steps:
                return steps

    # Fallback: free-text format with "step N. xxx" lines
    step_pattern = re.compile(r'^(?:step\s*)?(\d+(?:\.\d+)*)[\.\):\s]+(.+)$', re.IGNORECASE)
    current_step = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('//'):
            continue
        step_match = step_pattern.match(line)
        if step_match:
            if current_step:
                steps.append(current_step)
            step_num = step_match.group(1)
            desc = step_match.group(2).strip()
            software_match = software_pattern.search(desc)
            current_step = {
                'step': step_num,
                'name': desc,
                'software': software_match.group(1) if software_match else 'unknown',
                'description': desc
            }
        elif current_step and ('--' in line or '-' in line):
            pass

    if current_step:
        steps.append(current_step)
    return steps

LLM_PROMPT_TEMPLATE = """你是一个生物信息学专家和环境配置助手。请分析以下工作流描述，生成完整的配置文件。

## 工作流描述：
{workflow_text}

## 你的任务：

### 1. 生成 supplies-list.md (pipeline checklist)
严格按照以下格式生成：
```markdown
# pipeline checklist

| step | description | software | option/etc. | input | output | check | method |
| ---- | ----------- | -------- | ------------------------------------------------- | ------------------------ | ---------------------------- | ----- | ---------------------------------------------------- |
| 2.1  | merge paired-end reads | vsearch | --fastq_mergepairs | paired FASTQ | merged FASTQ | yes | conda |

## dependencies

| database | purpose | download |
|----------|---------|---------|
| refdb.fa | alignment template | https://... |

## pipeline connectivity

[ASCII diagram showing data flow between steps]
```

**列说明：**
- step: 步骤编号——**使用输入工作流描述中的原始编号，不要重新编号**（输入若是 1, 2, 3, ... 就用 1, 2, 3, ...；若输入已是 2.1, 2.2, 3, 4.2 就保持）
- description: 步骤描述
- software: 软件名称
- option/etc.: 主要命令行选项
- input: 输入文件格式
- output: 输出文件格式
- check: yes/no — 输出格式是否与下一步输入兼容
- method: conda / pip / manual:url / github:url

**方法分类规则：**
- CLI 生物信息学工具 (vsearch, fastp, cutadapt, bwa, samtools, qiime2, mothur 等) → conda
- 纯 Python 库 (biopython, pandas, numpy 等) → pip
- 商业软件 (usearch) → manual:https://www.drive5.com/usearch/download.html

### 2. 生成 environment.yml
从 supplies-list.md 中提取所有 conda 和 pip 包，生成 conda 环境文件。

### 3. 生成 install.sh
包含所有可通过命令行自动安装的包。

**conda 环境创建命令必须使用 `-p` 参数指定完整路径**：
```bash
conda env create -p {working_dir}/bioinfo_env -f environment.yml
```

**install.sh 模板**：
```bash
#!/bin/bash
set -e

# 创建 conda 环境（使用 -p 指定工作目录下的路径）
conda env create -p {working_dir}/bioinfo_env -f environment.yml

# 激活环境（仅供后续命令参考，conda 自动处理）
# conda activate ./{bioinfo_env}

# 安装其他 CLI 工具（如有）
# ...

# 下载数据库（如有）
# ...
```

### 4. 生成 MANUAL.md
包含需要手动下载安装的包（如商业软件、大的数据库等）。

## 输出要求：
1. supplies-list.md 必须包含完整的 checklist 表格、dependencies 表格和 pipeline connectivity 图
2. environment.yml 只包含 conda 和 pip 包
3. install.sh 包含 conda install 和 pip install 命令
4. MANUAL.md 只包含需要手动操作的包

请生成这4个文件的内容，直接输出，不要有其他解释文字。输出格式如下：
---SUPPLIES---
[supplies-list.md 内容]
---ENVIRONMENT---
[environment.yml 内容]
---INSTALL---
[install.sh 内容]
---MANUAL---
[MANUAL.md 内容]
"""
@app.post("/api/env-build/process")
async def env_build_process(req: Request):
    """Process workflow text using LLM and generate environment files"""
    data = await req.json()
    workflow_text = data.get('workflow_text', '')
    working_dir = data.get('working_dir', '')
    session_id = data.get('session_id', 'default')

    if not workflow_text:
        return JSONResponse(status_code=400, content={"error": "workflow_text required"})
    if not working_dir:
        return JSONResponse(status_code=400, content={"error": "working_dir required"})

    env_build_dir = os.path.join(working_dir, 'env-build')
    os.makedirs(env_build_dir, exist_ok=True)

    output_lines = []
    output_lines.append('$ 正在使用 AI 分析工作流...')

    try:
        # Call LLM to generate all files
        prompt = LLM_PROMPT_TEMPLATE.format(workflow_text=workflow_text, working_dir=working_dir)

        llm_call_start = time.time()
        result = subprocess.run(
            ['claude', '-p', '--output-format', 'text', '--no-session-persistence'],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=300
        )
        llm_call_sec = round(time.time() - llm_call_start, 3)
        print(f"[env-build] session={session_id} llm_call_sec={llm_call_sec}s")

        llm_output = result.stdout
        print(f"[LLM Output length] {len(llm_output)}")

        if not llm_output:
            return JSONResponse(status_code=500, content={"error": "LLM 返回为空", "output": '\n'.join(output_lines)})

        # Parse LLM output to extract each file
        supplies_match = re.search(r'---SUPPLIES---\s*([\s\S]*?)---ENVIRONMENT---', llm_output)
        env_match = re.search(r'---ENVIRONMENT---\s*([\s\S]*?)---INSTALL---', llm_output)
        install_match = re.search(r'---INSTALL---\s*([\s\S]*?)---MANUAL---', llm_output)
        manual_match = re.search(r'---MANUAL---\s*([\s\S]*?)$', llm_output)

        # Save supplies-list.md
        if supplies_match:
            supplies_content = supplies_match.group(1).strip()
            md_path = os.path.join(env_build_dir, 'supplies-list.md')
            with open(md_path, 'w') as f:
                f.write(supplies_content)
            output_lines.append(f'$ 已生成: supplies-list.md')
        else:
            output_lines.append('$ 警告: 无法解析 supplies-list.md')
            md_path = os.path.join(env_build_dir, 'supplies-list.md')

        # Save environment.yml
        if env_match:
            env_content = env_match.group(1).strip()
            yml_path = os.path.join(env_build_dir, 'environment.yml')
            with open(yml_path, 'w') as f:
                f.write(env_content)
            output_lines.append(f'$ 已生成: environment.yml')
        else:
            # Try to parse as YAML directly
            env_content = env_match.group(1).strip() if env_match else llm_output
            yml_path = os.path.join(env_build_dir, 'environment.yml')
            with open(yml_path, 'w') as f:
                f.write(env_content)
            output_lines.append(f'$ 已生成: environment.yml')

        # Save install.sh
        if install_match:
            install_content = install_match.group(1).strip()
            sh_path = os.path.join(env_build_dir, 'install.sh')
            with open(sh_path, 'w') as f:
                f.write(install_content)
            os.chmod(sh_path, 0o755)
            output_lines.append(f'$ 已生成: install.sh')

        # Save MANUAL.md
        if manual_match:
            manual_content = manual_match.group(1).strip()
            manual_path = os.path.join(env_build_dir, 'MANUAL.md')
            with open(manual_path, 'w') as f:
                f.write(manual_content)
            output_lines.append(f'$ 已生成: MANUAL.md')

        output_lines.append('')
        output_lines.append('$ 完成!')

        return {
            "success": True,
            "output": '\n'.join(output_lines),
            "host_arch": {
                "arch": platform.machine().lower(),
                "system": platform.system().lower(),
                "display": f"{platform.system()} {platform.machine()}"
            },
            "files": [
                {"name": "environment.yml", "path": yml_path},
                {"name": "install.sh", "path": sh_path},
                {"name": "supplies-list.md", "path": md_path},
                {"name": "MANUAL.md", "path": manual_path}
            ],
            "usage": {},  # local CLI doesn't return token counts
            "phases": {
                "llm_call_sec": llm_call_sec,
            },
        }

    except subprocess.TimeoutExpired:
        return JSONResponse(status_code=504, content={"error": "AI 分析超时 (5分钟)", "output": '\n'.join(output_lines)})
    except FileNotFoundError:
        return JSONResponse(status_code=500, content={"error": "claude 命令未找到", "output": '\n'.join(output_lines)})
    except Exception as e:
        output_lines.append(f'$ [错误] {str(e)}')
        return JSONResponse(status_code=500, content={"error": str(e), "output": '\n'.join(output_lines)})

@app.post("/api/env-build/create-env")
async def env_build_create_env(req: Request):
    """Create conda environment from generated environment.yml"""
    data = await req.json()
    working_dir = data.get('working_dir', '')

    if not working_dir:
        return JSONResponse(status_code=400, content={"error": "working_dir required"})

    yml_path = os.path.join(working_dir, 'env-build', 'environment.yml')
    print(f"[CreateEnv] yml_path: {yml_path}")
    print(f"[CreateEnv] exists: {os.path.exists(yml_path)}")
    if not os.path.exists(yml_path):
        return JSONResponse(status_code=400, content={"error": "environment.yml not found. Please run '生成环境配置' first."})

    try:
        print(f"[CreateEnv] Running conda env create...")
        import shutil
        conda_bin = shutil.which('conda') or '/opt/anaconda3/bin/conda'
        print(f"[CreateEnv] conda_bin: {conda_bin}")
        result = subprocess.run(
            [conda_bin, 'env', 'create', '-p', working_dir, '-f', yml_path],
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode == 0:
            return {"success": True, "message": "Conda环境创建成功", "output": result.stdout[-500:] if len(result.stdout) > 500 else result.stdout}
        else:
            print(f"[CreateEnv] conda failed: {result.stderr}")
            return JSONResponse(status_code=500, content={"success": False, "error": "环境创建失败", "output": result.stderr})

    except subprocess.TimeoutExpired:
        return JSONResponse(status_code=504, content={"error": "环境创建超时 (10分钟)"})
    except FileNotFoundError:
        return JSONResponse(status_code=500, content={"error": "conda not found"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/env-build/create-env-with-fix")
async def env_build_create_env_with_fix(req: Request):
    """Create conda environment with agent-assisted yml fixing loop (SSE streaming)."""
    data = await req.json()
    working_dir = data.get('working_dir', '')

    # Use client-supplied max_retries only as a hint; clamp to user-configured
    # value (from /api/settings) which itself is bounded by [1, 10].
    user_max = _resolve_env_fix_max_attempts()
    client_max = data.get('max_retries')
    try:
        client_max = int(client_max) if client_max is not None else user_max
    except (TypeError, ValueError):
        client_max = user_max
    max_retries = max(1, min(user_max, client_max))

    if not working_dir:
        return JSONResponse(status_code=400, content={"error": "working_dir required"})

    yml_path = os.path.join(working_dir, 'env-build', 'environment.yml')
    if not os.path.exists(yml_path):
        return JSONResponse(status_code=400, content={"error": "environment.yml not found. Please run '生成环境配置' first."})

    try:
        import shutil
        conda_bin = shutil.which('conda') or '/opt/anaconda3/bin/conda'
    except Exception:
        conda_bin = '/opt/anaconda3/bin/conda'

    def _call_agent_fix(yml_content: str, error_msg: str = "") -> str:
        import urllib.request
        token = _load_openclaw_token()
        if not token:
            return ""
        system_prompt = (
            "你是一个生物信息学环境配置专家。你的任务是修正 environment.yml 文件使其能被 conda env create 正确执行。\n"
            "规则：\n"
            "1. 只修正语法错误、版本不兼容、包名错误等问题\n"
            "2. 保持文件结构为标准 conda environment.yml\n"
            "3. 返回完整的修正后文件内容，不要有其他解释\n"
            "4. 只返回文件内容本身，不要 markdown 代码块标记"
        )
        user_prompt = (
            f"当前 environment.yml 内容：\n```\n{yml_content}\n```\n\n"
            + (f"上次尝试创建失败，错误信息：\n{error_msg}\n\n" if error_msg else "")
            + "请修正上述 environment.yml，返回修正后的完整内容（不要代码块），直接输出文件正文。"
        )
        url = f"http://{OPENCLAW_GATEWAY_HOST}:{OPENCLAW_GATEWAY_PORT}/v1/chat/completions"
        payload = {
            "model": "openclaw/default",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "x-openclaw-session-key": "agent:limbo:env-build",
        }
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
        try:
            resp = urllib.request.urlopen(req, timeout=180)
            resp_body = json.loads(resp.read().decode("utf-8", errors="replace"))
            resp.close()
            choices = resp_body.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                content = re.sub(r'^```yaml\s*', '', content, flags=re.IGNORECASE)
                content = re.sub(r'^```\s*', '', content)
                content = re.sub(r'\s*```$', '', content)
                return content.strip()
            elif resp_body.get("error"):
                print(f"[_call_agent_fix] API error: {resp_body['error']}")
            else:
                print(f"[_call_agent_fix] No choices: {resp_body}")
        except Exception as e:
            print(f"[_call_agent_fix] error: {e}")
        return ""

async def stream_response():
        with open(yml_path, 'r') as f:
            yml_content = f.read()

        def _post_to_session(role: str, msg: str, token: str) -> bool:
            import urllib.request
            url = f"http://{OPENCLAW_GATEWAY_HOST}:{OPENCLAW_GATEWAY_PORT}/v1/chat/completions"
            payload = {
                "model": "openclaw/default",
                "messages": [{"role": role, "content": msg}],
                "stream": False,
            }
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "x-openclaw-session-key": "agent:limbo:env-build",
            }
            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=30) as resp:
                    resp.read()
                return True
            except Exception as e:
                print(f"[_post_to_session] error: {e}")
                return False

        token = _load_openclaw_token()
        for attempt in range(1, max_retries + 1):
            log_msg = f'⏳ 尝试 {attempt}/{max_retries}：运行 conda env create...'
            yield f"data: {json.dumps({'type': 'log', 'text': log_msg})}\n\n"
            _post_to_session('system', f'[环境构建] {log_msg}', token)
            import subprocess
            result = subprocess.run(
                [conda_bin, 'env', 'create', '-p', working_dir, '-f', yml_path],
                capture_output=True, text=True, timeout=600
            )
            if result.returncode == 0:
                ok_msg = '✅ conda 环境创建成功！'
                yield f"data: {json.dumps({'type': 'log', 'text': ok_msg})}\n\n"
                _post_to_session('system', ok_msg, token)
                yield f"data: {json.dumps({'type': 'done', 'success': True, 'attempts': attempt})}\n\n"
                return

            error_msg = result.stderr or result.stdout
            fail_msg = f'❌ 尝试 {attempt} 失败：{error_msg[:500]}'
            yield f"data: {json.dumps({'type': 'log', 'text': fail_msg})}\n\n"
            _post_to_session('system', fail_msg, token)

            if attempt == max_retries:
                stop_msg = '🚫 已达最大重试次数，停止。'
                yield f"data: {json.dumps({'type': 'log', 'text': stop_msg})}\n\n"
                _post_to_session('system', stop_msg, token)
                yield f"data: {json.dumps({'type': 'done', 'success': False, 'error': '环境创建失败'})}\n\n"
                break

            call_msg = f'🤖 尝试 {attempt} 失败，向 Agent 发送修正请求...'
            yield f"data: {json.dumps({'type': 'log', 'text': call_msg})}\n\n"
            _post_to_session('system', call_msg, token)
            fixed = _call_agent_fix(yml_content, error_msg)
            if not fixed:
                warn_msg = '⚠️ Agent 未返回有效修正，停止。'
                yield f"data: {json.dumps({'type': 'log', 'text': warn_msg})}\n\n"
                _post_to_session('system', warn_msg, token)
                yield f"data: {json.dumps({'type': 'done', 'success': False, 'error': 'Agent修正失败'})}\n\n"
                break

            yml_content = fixed
            with open(yml_path, 'w') as f:
                f.write(fixed)
            done_msg = '✅ Agent 修正完成，重新尝试...'
            yield f"data: {json.dumps({'type': 'log', 'text': done_msg})}\n\n"
            _post_to_session('system', done_msg, token)


# ============================================================================
# i18n (translation catalogs)
# ============================================================================
@app.get("/api/i18n/{lang}")
async def i18n_catalog(lang: str):
    """Return the translation catalog for the requested language.

    Falls back to English for unknown locales or missing keys.
    """
    return {
        "locale": lang if lang in I18N_LOCALES else I18N_DEFAULT,
        "supported": list(I18N_LOCALES),
        "strings": i18n_get_catalog(lang),
    }

# ============================================================================
# User settings (persisted in user_config.json)
# ============================================================================
def _default_user_settings() -> dict:
    return {
        "language": I18N_DEFAULT,
        "env_fix_max_attempts": ENV_FIX_MAX_ATTEMPTS,
    }


def _resolve_env_fix_max_attempts() -> int:
    """Read user setting, clamp to [1, 10], fall back to config default."""
    cfg = load_user_config()
    value = cfg.get("env_fix_max_attempts", ENV_FIX_MAX_ATTEMPTS)
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = ENV_FIX_MAX_ATTEMPTS
    return max(1, min(10, value))


@app.get("/api/settings")
async def get_settings():
    """Return current user settings merged with defaults."""
    cfg = load_user_config()
    defaults = _default_user_settings()
    merged = dict(defaults)
    for k, v in cfg.items():
        if k in defaults:
            merged[k] = v
    return {"settings": merged}


@app.post("/api/settings")
async def update_settings(req: Request):
    """Persist user settings (partial update)."""
    data = await req.json()
    if not isinstance(data, dict):
        return JSONResponse(status_code=400, content={"error": "settings must be an object"})

    cfg = load_user_config()
    defaults = _default_user_settings()

    # language
    if "language" in data:
        lang = str(data["language"])
        if lang not in I18N_LOCALES:
            return JSONResponse(
                status_code=400,
                content={"error": f"unsupported language: {lang}. Supported: {list(I18N_LOCALES)}"},
            )
        cfg["language"] = lang

    # env_fix_max_attempts
    if "env_fix_max_attempts" in data:
        try:
            v = int(data["env_fix_max_attempts"])
        except (TypeError, ValueError):
            return JSONResponse(
                status_code=400,
                content={"error": "env_fix_max_attempts must be an integer between 1 and 10"},
            )
        if v < 1 or v > 10:
            return JSONResponse(
                status_code=400,
                content={"error": "env_fix_max_attempts must be between 1 and 10"},
            )
        cfg["env_fix_max_attempts"] = v

    save_user_config(cfg)
    merged = dict(defaults)
    for k, v in cfg.items():
        if k in defaults:
            merged[k] = v
    return {"success": True, "settings": merged}


@app.get("/api/env-build/read-file")
async def env_build_read_file(path: str):
    """Read generated file content"""
    try:
        with open(path, 'r') as f:
            content = f.read()
        return {"success": True, "content": content}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/env-build/save-environment")
async def env_build_save_environment(req: Request):
    """Save environment.yml content (e.g., after agent fixes)"""
    data = await req.json()
    working_dir = data.get('working_dir', '')
    content = data.get('content', '')

    if not working_dir:
        return JSONResponse(status_code=400, content={"error": "working_dir required"})
    if not content:
        return JSONResponse(status_code=400, content={"error": "content required"})

    env_build_dir = os.path.join(working_dir, 'env-build')
    os.makedirs(env_build_dir, exist_ok=True)

    yml_path = os.path.join(env_build_dir, 'environment.yml')
    try:
        with open(yml_path, 'w') as f:
            f.write(content)
        return {"success": True, "path": yml_path}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/env-build/check-existing")
async def env_build_check_existing(working_dir: str):
    """Check if env-build directory exists and list generated files"""
    if not working_dir:
        return JSONResponse(status_code=400, content={"error": "working_dir required"})

    env_build_dir = os.path.join(working_dir, 'env-build')
    if not os.path.exists(env_build_dir):
        return {"exists": False, "files": []}

    expected_files = ['supplies-list.md', 'environment.yml', 'install.sh', 'MANUAL.md']
    files = []
    for fname in expected_files:
        fpath = os.path.join(env_build_dir, fname)
        if os.path.exists(fpath):
            files.append({"name": fname, "path": fpath})

    return {"exists": True, "files": files}

# ============================================================================

@app.get("/api/workflow/list")
async def list_workflows():
    """List all workflows from workflows/ directory"""
    workflows_dir = BASE_DIR / "workflows"
    if not workflows_dir.exists():
        return {"success": True, "workflows": []}

    workflows = []
    for wf_dir in workflows_dir.iterdir():
        if wf_dir.is_dir():
            config_path = wf_dir / "config.json"
            params_path = wf_dir / "params.json"
            config = {}
            params = {}
            if config_path.exists():
                config = json.loads(config_path.read_text())
            if params_path.exists():
                params = json.loads(params_path.read_text())
            workflows.append({
                "name": wf_dir.name,
                "path": str(wf_dir),
                "params": params,
                "config": config
            })
    return {"success": True, "workflows": workflows}

@app.get("/api/workflow/render-config/{workflow_name}")
async def render_workflow_config(workflow_name: str, lang: str = I18N_DEFAULT):
    """Render config form HTML for a workflow based on params.json"""
    if lang not in I18N_LOCALES:
        lang = I18N_DEFAULT

    params_file = BASE_DIR / 'workflows' / workflow_name / 'params.json'
    if not params_file.exists():
        raise HTTPException(status_code=404, detail='Workflow not found')

    with open(params_file, 'r') as f:
        params_data = json.load(f)

    html_parts = ['<form id="workflow-config-form">']

    for i, step in enumerate(params_data.get('steps', [])):
        step_name = step.get('name', '')
        step_software = step.get('software', '')
        query_status = step.get('query_status', 'success')

        status_icon = '&#x2705;' if query_status == 'success' else '&#x274C;'
        status_text = i18n_t('wfc.params_retrieved' if query_status == 'success' else 'wfc.params_failed', lang)
        configure_label = i18n_t('wfc.configure_btn', lang)
        run_label = i18n_t('wfc.run_btn', lang)

        html_parts.append(f'<div class="config-step" style="margin-bottom: 12px; padding: 12px; border: 1px solid #e2e8f0; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">')
        html_parts.append(f'<div style="display: flex; justify-content: space-between; align-items: center; width: 100%;"><div><strong>{step.get("step", i+1)} {step_name}</strong> <span style="color: #64748b;">({step_software})</span></div><div><span title="{status_text}" style="margin-right: 12px;">{status_icon}</span><button type="button" class="btn btn-primary btn-small" onclick="configureStepParams(\'{workflow_name}\', {i})">{configure_label}</button><button type="button" class="btn btn-success btn-small" style="margin-left: 8px;" onclick="runWorkflowStep(\'{workflow_name}\', {i})">{run_label}</button></div></div>')
        html_parts.append(f'</div>')

    html_parts.append('</form>')

    return {
        "success": True,
        "html": '\n'.join(html_parts),
        "params": params_data
    }

@app.post("/api/workflow/save-config/{workflow_name}")
async def save_workflow_config(workflow_name: str, req: Request):
    """Save workflow config values and generate filled scripts"""
    data = await req.json()
    workflow_dir = BASE_DIR / 'workflows' / workflow_name
    working_dir = data.get('_working_dir', None)

    config_file = workflow_dir / 'config.json'
    with open(config_file, 'w') as f:
        json.dump(data, f, indent=2)

    params_file = workflow_dir / 'params.json'
    if params_file.exists():
        with open(params_file, 'r') as f:
            params_data = json.load(f)

        if working_dir:
            scripts_dir = Path(working_dir) / 'scripts'
        else:
            scripts_dir = workflow_dir / 'scripts'
        os.makedirs(scripts_dir, exist_ok=True)

        env_path = data.get('_env_path', '/opt/anaconda3')

        for i, step in enumerate(params_data.get('steps', [])):
            step_script_path = scripts_dir / f'step_{i}.sh'
            step_params = [p for p in step.get('params', []) if p.get('source') == 'workflow']

            script_lines = ['#!/bin/bash', f'# Step {step.get("step", i+1)}: {step.get("name", "")}', f'conda activate {env_path}', '']

            for param in step_params:
                param_name = param.get('name', '')
                param_value = data.get(param_name, param.get('default', ''))
                if param_value:
                    script_lines.append(f'{param_name}="{param_value}"')
            step_config = {p.get('name'): data.get(p.get('name'), p.get('default', '')) for p in step_params}
            script_lines.append(f'vsearch \\')
            for param in step_params:
                param_name = param.get('name', '')
                param_value = step_config.get(param_name, '')
                if param_value:
                    script_lines.append(f'    {param_name} {param_value} \\')

            with open(step_script_path, 'w') as f:
                f.write('\n'.join(script_lines))
            os.chmod(step_script_path, 0o755)

    return {"success": True}

@app.post("/api/workflow/run-step/{workflow_name}/{step_index}")
async def run_workflow_step(workflow_name: str, step_index: int):
    """Execute a specific step's filled script"""
    workflow_dir = BASE_DIR / 'workflows' / workflow_name
    script_path = workflow_dir / 'scripts' / f'step_{step_index}.sh'
    if not script_path.exists():
        raise HTTPException(status_code=404, detail='Script not found. Please configure and save the step first.')

    with open(script_path, 'r') as f:
        script = f.read()

    try:
        result = subprocess.run(
            ['bash', '-c', script],
            capture_output=True,
            text=True,
            timeout=3600
        )
        return {
            "success": True,
            "output": result.stdout,
            "error": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workflow/get-tool-help")
async def get_tool_help(req: Request):
    """Execute `conda run` to get tool --help text (local connection)."""
    data = await req.json()
    tool = data.get('tool', '')
    env_path = data.get('env_path', '')

    if not tool:
        return {"help": "", "error": "tool name required"}

    try:
        conda_sh = '/opt/anaconda3/etc/profile.d/conda.sh'
        if not os.path.exists(conda_sh):
            conda_sh = os.path.expanduser('~/miniconda3/etc/profile.d/conda.sh')

        if env_path:
            cmd = f'source {conda_sh} 2>/dev/null && conda activate "{env_path}" && {tool} --help 2>&1 | head -150'
        else:
            cmd = f'source {conda_sh} 2>/dev/null && {tool} --help 2>&1 | head -150'

        result = subprocess.run(['bash', '-c', cmd], capture_output=True, text=True, timeout=30)
        return {"help": result.stdout, "error": result.stderr, "tool": tool}
    except Exception as e:
        return {"help": "", "error": str(e), "tool": tool}


@app.post("/api/workflow/analyze-parameters")
async def analyze_workflow_parameters(req: Request):
    """LLM analyzes workflow steps and classifies params into essential/optional."""
    data = await req.json()
    steps = data.get('steps', [])

    if not steps:
        return JSONResponse(status_code=400, content={"error": "steps required"})

    steps_md = '\n'.join([
        f"- Step {s.get('step', i+1)}: {s.get('name', '')}\n"
        f"  Software: {s.get('software', '')}\n"
        f"  Options: {s.get('option/etc.', '')}\n"
        f"  Input: {s.get('input', '')}\n"
        f"  Output: {s.get('output', '')}"
        for i, s in enumerate(steps)
    ])

    prompt = f"""你是一个生物信息学专家。请分析以下工作流的软件参数，将其分类为必要参数和可选参数，并确定参数类型。

工作流步骤：
{steps_md}

请为每个软件生成参数配置面板JSON，格式如下：
{{
  "software_name": {{
    "essential_params": [
      {{"name": "--param", "type": "string|numeric|categorical|flag", "label": "中文标签", "default": "默认值", "description": "参数说明"}}
    ],
    "optional_params": [
      {{"name": "--param", "type": "string|numeric|categorical|flag", "label": "中文标签", "default": "默认值", "description": "参数说明"}}
    ]
  }}
}}

只输出JSON，不要有其他文字。"""

    try:
        messages = [{"role": "user", "content": prompt}]
        client = get_default_client()
        llm_result = client.complete_raw(messages, max_tokens=4096, temperature=0.2)
        llm_output = llm_result.get("text", "")
        if llm_result.get("error"):
            return JSONResponse(status_code=500, content={"error": f"LLM error: {llm_result['error']}"})

        # Parse JSON from LLM output
        import re as regex_re
        param_config = None
        json_match = regex_re.search(r'\{[\s\S]*\}', llm_output)
        if json_match:
            try:
                param_config = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        if not param_config:
            return {"success": False, "error": "JSON parse failed", "raw": llm_output[:500]}

        return {"success": True, "param_config": param_config}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/agent/status")
async def agent_status():
    """Check OpenClaw Gateway connectivity"""
    try:
        token = get_token_from_gateway()
        if not token:
            return {"status": "error", "message": "No token found"}
        import urllib.request
        req = urllib.request.Request(
            "http://127.0.0.1:18789/v1/models",
            headers={"Authorization": "Bearer " + token}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return {"status": "ok", "gateway": "connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/agent/session-key")
async def agent_session_key():
    """Return the session key prefix for OpenClaw Gateway"""
    return {"session_key_prefix": "agent:limbo:"}

@app.post("/api/agent/chat")
async def agent_chat(req: Request):
    """Proxy agent chat to OpenClaw Gateway with SSE streaming"""
    data = await req.json()
    message = data.get("message", "")
    session_id = data.get("session_id", "default")
    working_dir = data.get("working_dir", "")

    if not message:
        return {"error": "message required"}

    prompt = message
    if working_dir:
        prompt = "[Working directory: " + working_dir + "]\n\n" + prompt

    async def stream_response():
        try:
            token = get_token_from_gateway()
            session_key = "agent:limbo:" + session_id
            import json, urllib.request, urllib.error

            payload = {
                "model": "openclaw",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "max_tokens": 4096
            }
            body = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                "http://127.0.0.1:18789/v1/chat/completions",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + token,
                    "x-openclaw-session-key": session_key
                },
                method="POST"
            )

            with urllib.request.urlopen(request, timeout=120) as resp:
                raw = json.loads(resp.read().decode("utf-8"))

            text = ""
            if "choices" in raw:
                text = raw["choices"][0]["message"]["content"]

            yield "data: " + json.dumps({"token": text}) + "\n\n"
            yield "data: " + json.dumps({"done": True, "session_id": session_id}) + "\n\n"

        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            err_msg = "HTTP " + str(e.code) + ": " + err_body[:200]
            yield "data: " + json.dumps({"error": err_msg}) + "\n\n"
        except Exception as e:
            yield "data: " + json.dumps({"error": str(e)}) + "\n\n"

    from starlette.responses import StreamingResponse
    return StreamingResponse(stream_response(), media_type="text/event-stream")

@app.post("/api/agent/generate-workflow")
async def agent_generate_workflow(req: Request):
    "Generate workflow params.json and script.sh from text (LIMBO scheme)."
    data = await req.json()
    script_content = data.get('content', '')
    filename = data.get('filename', 'workflow.md')
    env_path = data.get('env_path', '') or data.get('env', '')
    working_dir = data.get('working_dir', '') or data.get('work_dir', '')

    if not script_content:
        return JSONResponse(status_code=400, content={"error": "content required"})

    try:
        import re as re2

        # Step 1: Rule-based step extraction (from LIMBO parse_workflow_steps)
        steps = parse_workflow_steps(script_content)

        # Step 2: For each software, call tool --help via conda run
        for step in steps:
            software = step.get('software', '').strip()
            if not software or software == 'unknown':
                continue
            tool = software.split()[0]

            try:
                conda_sh = '/opt/anaconda3/etc/profile.d/conda.sh'
                if not os.path.exists(conda_sh):
                    conda_sh = os.path.expanduser('~/miniconda3/etc/profile.d/conda.sh')

                if env_path:
                    help_cmd = 'source ' + conda_sh + ' 2>/dev/null && conda run -p "' + env_path + '" ' + tool + ' --help 2>&1 | head -150'
                else:
                    help_cmd = 'source ' + conda_sh + ' 2>/dev/null && ' + tool + ' --help 2>&1 | head -150'

                help_result = subprocess.run(['bash', '-c', help_cmd], capture_output=True, text=True, timeout=30)
                # Prepend explicit STATUS marker so the LLM can reliably tell
                # successful help from failed (instead of guessing from raw output).
                if help_result.returncode == 0 and help_result.stdout.strip():
                    help_text = '[STATUS: SUCCESS]\n\n' + help_result.stdout[:2000]
                else:
                    err = help_result.stderr.strip() if help_result.stderr.strip() else f'non-zero exit code {help_result.returncode}'
                    help_text = '[STATUS: FAILED]\n' + err[:200]
            except Exception as e:
                help_text = '[STATUS: FAILED]\n' + str(e)

            step['help_text'] = help_text

        # Step 3: LLM analyzes help text and generates params.json
        steps_with_help_md = '\n'.join([
            '### Step ' + s['step'] + ': ' + s['name'] + '\n'
            'Software: ' + s['software'] + '\n'
            'Tool Help Output:\n```\n' + s.get('help_text', 'N/A')[:2000] + '\n```'
            for s in steps
        ])

        gen_params_prompt = (
            'You are a bioinformatics expert and script generation assistant.\n\n'
            'User provided the following workflow description file:\n\n'
            '```\n' + script_content[:4000] + '\n```\n\n'
            '**Capability limits:**\n'
            '1. No network queries allowed\n'
            '2. Only use locally installed tools\n'
            '3. If a tool help cannot be queried, keep params as empty array []\n'
            '4. Only report information confirmed by actual command execution\n\n'
            '**Task:**\n'
            '1. Analyze workflow steps, preserve original step numbers (e.g. 2.1, 3, 4.2)\n'
            '2. For each software tool, parse the provided help text below\n'
            '3. Extract real parameters and variables from help text\n'
            '4. Generate params.json:\n\n'
            '{\n'
            '  "steps": [\n'
            '    {\n'
            '      "step": "original step number",\n'
            '      "name": "step name",\n'
            '      "software": "software name",\n'
            '      "query_status": "success" | "failed",\n'
            '      "params": [\n'
            '        {\n'
            '          "name": "variable name",\n'
            '          "label": "label",\n'
            '          "type": "string|numeric|boolean|flag|select",\n'
            '          "required": true|false,\n'
            '          "default": "default value or empty string",\n'
            '          "options": [],\n'
            '          "description": "parameter description",\n'
            '          "file_role": "input|output|both",\n'
            '          "source": "user|workflow"\n'
            '        }\n'
            '      ]\n'
            '    }\n'
            '  ]\n'
            '}\n\n'
            '**Important:**\n'
            '- query_status: "success" means params retrieved, "failed" means query failed\n'
            '- If tool help fails, params must be [] and query_status must be "failed"\n'
            '- type only: string, numeric, boolean, flag, select\n'
            '- For file parameters, add file_role and source\n'
            '- file_role: "input" for input files, "output" for output files, "both" for both\n'
            '- source: "user" for user-provided files (fastq, fasta, reference db), "workflow" for workflow-generated files (merged, otutab, unique, nonchimeras)\n\n'
            '**Already extracted workflow steps and help text:**\n'
            + steps_with_help_md + '\n\n'
            'Output JSON only, no other text.'
        )

        messages = [{"role": "user", "content": gen_params_prompt}]
        client = get_default_client()
        llm_result = client.complete_raw(messages, max_tokens=8192, temperature=0.2)
        params_output = llm_result.get("text", "")
        if llm_result.get("error"):
            return JSONResponse(status_code=500, content={"error": "LLM error: " + llm_result["error"]})

        json_match = re2.search(r'\{[\s\S]*\}', params_output)
        if not json_match:
            return JSONResponse(status_code=500, content={"error": "cannot generate params JSON", "raw": params_output[:500]})

        try:
            params_data = json.loads(json_match.group())
        except json.JSONDecodeError:
            cleaned = re2.sub(r',(\s*[\}\]])', r'\1', params_output)
            json_match2 = re2.search(r'\{[\s\S]*\}', cleaned)
            if json_match2:
                params_data = json.loads(json_match2.group())
            else:
                return JSONResponse(status_code=500, content={"error": "cannot parse params JSON", "raw": params_output[:500]})

        # Step 4: Generate script.sh + per-step independent scripts
        base_name = os.path.basename(filename)
        workflow_name = re2.sub(r'\.(md|sh|yml|yaml)$', '', base_name, flags=re2.IGNORECASE)

        # Prefer request's working_dir (per-run isolation) over the global fallback
        if working_dir:
            workflow_dir = Path(working_dir) / 'workflows' / workflow_name
        else:
            workflow_dir = BASE_DIR / 'workflows' / workflow_name
        os.makedirs(workflow_dir, exist_ok=True)
        scripts_dir = workflow_dir / 'scripts'
        os.makedirs(scripts_dir, exist_ok=True)

        # Save params.json
        with open(workflow_dir / 'params.json', 'w', encoding='utf-8') as f:
            json.dump(params_data, f, indent=2, ensure_ascii=False)

        # Save config.json
        config_data = {
            "workflow_name": workflow_name,
            "env_path": env_path,
            "source_file": filename,
            "steps_count": len(params_data.get('steps', []))
        }
        with open(workflow_dir / 'config.json', 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        # Build per-step independent scripts (matching LIMBO/workflows/workflow04/scripts/step_N.sh)
        steps = params_data.get('steps', [])
        for i, step in enumerate(steps):
            software = step.get('software', 'unknown')
            step_name = step.get('name', 'step_' + str(i+1))
            step_label = step.get('step', str(i+1))
            params_list = step.get('params', [])

            step_lines = [
                '#!/bin/bash',
                f'# Step {step_label}: {step_name}',
                f'# Software: {software}',
                '',
            ]
            if env_path:
                step_lines += [f"conda activate {env_path}", '']

            cmd_parts = [software]
            for p in params_list:
                raw_name = p.get('name', '')
                var_name = raw_name.lstrip('-')  # bash-legal var name in ${VAR}
                default = p.get('default', '')
                ptype = p.get('type', 'string')
                label = p.get('label', '')
                if ptype == 'flag':
                    cmd_parts.append(raw_name)
                else:
                    if label:
                        step_lines.append(f'# {raw_name}: {label}')
                    cmd_parts.append(raw_name + ' ${' + var_name + ':-' + default + '}')

            step_lines.append(' '.join(cmd_parts))
            step_lines.append('')

            step_path = scripts_dir / f'step_{i}.sh'
            with open(step_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(step_lines))
            os.chmod(step_path, 0o755)

        # Generate top-level script.sh as orchestrator (calls each step_N.sh in order)
        script_lines = [
            '#!/bin/bash',
            f'# Workflow: {workflow_name}',
            f'# Generated from: {filename}',
            '',
            'set -e',
            'SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"',
            '',
        ]
        for i, step in enumerate(steps):
            step_label = step.get('step', str(i+1))
            step_name = step.get('name', 'step_' + str(i+1))
            script_lines += [
                f'# Step {step_label}: {step_name}',
                f'echo "[Step {i+1}/{len(steps)}] {step_name}..."',
                f'bash "$SCRIPT_DIR/scripts/step_{i}.sh" "$@"',
                f'echo "[Step {i+1}/{len(steps)}] Done"',
                '',
            ]
        script_lines.append('echo "Workflow complete!"')

        script_path = workflow_dir / 'script.sh'
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(script_lines))
        os.chmod(script_path, 0o755)

        return {
            "success": True,
            "workflow_name": workflow_name,
            "workflow_dir": str(workflow_dir),
            "steps_found": len(params_data.get('steps', [])),
            "params": params_data
        }

    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})
# ============================================================================
# RData API Routes (R session management & template execution)
# ============================================================================

@app.get("/api/rdata/templates/list")
async def rdata_templates_list():
    """Return list of analysis templates from the templates/ directory."""
    templates_dir = Path(__file__).parent / "templates"
    if not templates_dir.exists():
        return {"templates": []}
    templates = []
    for item in sorted(templates_dir.iterdir()):
        if item.is_dir():
            json_path = item / "template.json"
            if json_path.exists():
                try:
                    with open(json_path) as f:
                        tpl = json.load(f)
                    templates.append({
                        "name": tpl.get("name", item.name),
                        "dir": str(item),
                        "type": tpl.get("type", ""),
                        "description": tpl.get("description", ""),
                        "config": {
                            "inputs": tpl.get("inputs", []),
                            "params": tpl.get("params", []),
                            "outputs": tpl.get("outputs", [])
                        }
                    })
                except Exception as e:
                    print(f"[WARN] Failed to load template {json_path}: {e}")
    return {"templates": templates}


@app.get("/api/rdata/session/objects")
async def rdata_session_objects(session_id: str = "rdata"):
    """Return list of objects in an R session."""
    if not r_session_manager.create_session(session_id):
        return {"objects": [], "error": "Failed to create R session"}
    objects = r_session_manager.list_objects(session_id)
    return {"objects": objects}


@app.post("/api/rdata/session/command")
async def rdata_session_command(req: Request):
    """Send a command to an R session."""
    data = await req.json()
    session_id = data.get("session_id", "rdata")
    command = data.get("command", "")
    if not command:
        return {"error": "command required"}
    if not r_session_manager.create_session(session_id):
        return {"error": "Failed to create R session"}
    result = r_session_manager.send_command(session_id, command)
    return result


@app.post("/api/rdata/run")
async def rdata_run(req: Request):
    """Execute R script in a session."""
    data = await req.json()
    session_id = data.get("session_id", "rdata")
    script = data.get("script", "")
    project_dir = data.get("project_dir", "")
    if not script:
        return {"error": "script required"}
    if not r_session_manager.create_session(session_id, project_dir):
        return {"error": "Failed to create R session"}
    result = r_session_manager.send_command(session_id, script)
    return result


@app.post("/api/rdata/project/create")
async def rdata_project_create(req: Request):
    """Create an R visualization project."""
    data = await req.json()
    session_id = data.get("session_id", "rdata")
    project_dir = data.get("project_dir", "")
    if not project_dir:
        return {"success": False, "error": "project_dir required"}
    result = viz_manager.create_project(session_id, project_dir)
    return result


@app.post("/api/rdata/session/load")
async def rdata_session_load(req: Request):
    """Load .RData file into session."""
    data = await req.json()
    session_id = data.get("session_id", "rdata")
    filepath = data.get("filepath", "")
    if not filepath:
        return {"error": "filepath required"}
    if not r_session_manager.create_session(session_id):
        return {"error": "Failed to create R session"}
    success = r_session_manager.load_session(session_id, filepath)
    return {"success": success, "error": None if success else "Failed to load"}


# ============================================================================
# Socket.IO Events
# ============================================================================
@sio.event
async def terminal_connect(sid, data):
    name = data.get('connection')
    env_path = data.get('env')

    if not name:
        await sio.emit('terminal_error', {'error': 'connection required'}, to=sid)
        return

    session_id = ssh_manager.create_session(name, env_path)
    if session_id:
        await sio.emit('terminal_session', {'session_id': session_id}, to=sid)
    else:
        await sio.emit('terminal_error', {'error': 'Failed to create session'}, to=sid)

@sio.event
async def terminal_input(sid, data):
    session_id = data.get('session_id')
    input_data = data.get('data', '')

    if session_id:
        ssh_manager.send_input(session_id, input_data)

@app.get("/api/terminal/output/{session_id}")
async def get_terminal_output(session_id: str):
    """Get PTY output for polling"""
    if session_id not in ssh_manager.sessions:
        return {"output": ""}
    output = ssh_manager.recv_output(session_id)
    return {"output": output}

@sio.event
async def terminal_resize(sid, data):
    session_id = data.get('session_id')
    rows = data.get('rows', 40)
    cols = data.get('cols', 120)

    if session_id:
        try:
            ssh_manager.resize_pty(session_id, rows, cols)
        except Exception as e:
            print(f"[WARN] resize failed: {e}")

@sio.event
async def terminal_disconnect(sid, data):
    session_id = data.get('session_id')
    if session_id:
        ssh_manager.close_session(session_id)

# ============================================================================
# ASGI App (Socket.IO + FastAPI)
# ============================================================================
app = socketio.ASGIApp(sio, app)

# Reorder routes so catch-all /{path:path} is AFTER agent routes
# Starlette Router matches routes in order; catch-all must not intercept /api/agent/*
_inner = app.other_asgi_app
_routes = list(_inner.router.routes)
_agent_routes = [r for r in _routes if hasattr(r, 'path') and r.path in (
    '/api/agent/status', '/api/agent/session-key', '/api/agent/chat'
)]
_catchall = next((r for r in _routes if hasattr(r, 'path') and r.path == '/{path:path}'), None)
if _catchall is not None and _agent_routes:
    _others = [r for r in _routes if r not in _agent_routes and r != _catchall]
    _inner.router.routes = _others + _agent_routes + [_catchall]
    print(f"[Route reorder] catch-all moved to index {len(_inner.router.routes) - 1} (after {len(_agent_routes)} agent routes)")

# ============================================================================
# Run Server
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    print("Starting LIMBO on http://localhost:5001")
    uvicorn.run(app, host='0.0.0.0', port=5001)