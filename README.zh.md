# LIMBO

LIMBO 是一个用于设计、配置和运行生物信息学分析流程(16S/ITS ASV 等)的
Web 环境,内置中英双语界面和环境自愈能力。

**English documentation:** [README.md](README.md)

---

## 1. 初始设置

### 1.1 前置依赖

| 工具 | 是否必须 | 说明 |
|------|----------|------|
| Python 3.9+ | 是 | 系统自带即可 |
| Conda | 是 | 推荐 [conda-forge/miniforge](https://conda-forge.org/) |
| Git | 可选 | 仅在克隆仓库时需要 |

### 1.2 安装步骤

```bash
# 1. 获取代码(或直接下载)
git clone <repo-url> limbo && cd limbo

# 2. 创建 conda 生物信息环境(自动下载安装 vsearch 等)
bash install.sh

# 3. 配置 OpenClaw AI 网关 — 见 §1.4(必须)

# 4. 启动后端,自动打开浏览器
python3 launcher.py
```

启动后,后端监听 `http://127.0.0.1:5002/`,浏览器自动打开该地址。

### 1.3 首次运行配置向导

在新设备上首次启动前,运行跨设备初始化脚本,用于注册路径和 Conda 环境:

```bash
python3 setup.py
```

该脚本会写入 `config.py` 并在项目根目录创建 `user_config.json`。

### 1.4 OpenClaw 网关(必须)

OpenClaw 网关是 LIMBO **必须** 的依赖,承担工作流生成、环境自动修正循环、
智能体对话等核心 AI 功能。网关默认监听 `http://127.0.0.1:18789`,必须在
启动 LIMBO 之前已经在网络上可达。

```bash
# 1. 在可达主机上启动 OpenClaw 网关
# 2. 复制模板并填入你的 token
cp openclaw.json.template ~/.openclaw/openclaw.json
# 3. 编辑 ~/.openclaw/openclaw.json:替换占位符为真实值
```

路径用 `OPENCLAW_TOKEN_PATH` 覆盖,URL 用 `OPENCLAW_URL` 覆盖(见 [配置](#配置))。

---

## 2. 使用说明

### 2.1 切换语言

页面右上角下拉框可在 **English / 中文** 之间实时切换。
选择保存在浏览器 `localStorage` 中,刷新页面仍在生效。
翻译文本通过 `GET /api/i18n/<lang>` 加载,自动应用到所有带
`data-i18n="<key>"` 的元素上。

新增可翻译字符串:

1. 给 HTML 元素加 `data-i18n="<key>"`
2. 在 `i18n.py` 加条目:
   ```python
   "<key>": {"en": "English text", "zh": "中文文本"},
   ```

### 2.2 选择 Conda 环境

侧边栏 → **Conda 环境** → 选中你用 `bash install.sh` 创建的环境。状态栏会高亮显示。

### 2.3 设置工作目录

侧边栏 → **工作目录**。LIMBO 会在此处生成:
- `environment.yml` / `install.sh` / `supplies-list.md` / `MANUAL.md`
- 工作流脚本与运行日志

### 2.4 环境构建流程

1. **Environment Build** tab → 输入工作流描述(中英均可),例如:
   *"合并双端 reads → UNOISE3 去噪 → SILVA 比对去除嵌合体 → 生成 OTU 表"*
2. 点 **生成环境配置**,LIMBO 调用 AI 智能体生成:
   - `supplies-list.md` — 依赖清单
   - `environment.yml` — conda 环境定义
   - `install.sh` — 安装脚本
   - `MANUAL.md` — 非 conda 工具(如参考数据库)的说明
3. 在右侧预览 tab 中查看。
4. 点 **创建 Conda 环境**(失败重试用 **创建环境 (自动修正)**)。
5. 点 **打开目录** 查看生成的文件。

### 2.5 自动修正循环

conda env 创建失败时,可让 AI 智能体诊断并重写 `environment.yml`。

重试次数可由用户配置:

- 默认 3(来自 `config.py` 的 `ENV_FIX_MAX_ATTEMPTS`)
- 范围 1 – 10
- 持久化到 `user_config.json`
- 设置入口:右上角 ⚙ → **环境自动修正最大尝试次数**,或
  `POST /api/settings`

后端 `/api/env-build/create-env-with-fix` 在每次调用时读取该值。

### 2.6 工作流配置

工作流生成后,点步骤旁的 **配置** 查看参数。每个步骤显示:

- ✅ 绿色 — 参数已查询成功
- ❌ 红色 — 参数查询失败(工具可能未安装)

点 **配置** 打开参数表单,分 **必需参数** 和 **可选参数** 两段。
- **外部文件** 徽标 = 用户提供的文件(如 FASTQ 输入、参考库)
- **内部文件** 徽标 = 同一工作流前面步骤生成的文件

### 2.7 SSH / 远程终端

侧边栏 → **终端** → 选择 Local 或一个 SSH 配置。SSH 配置在侧边栏 **工具** → **SSH 管理** 中维护。

### 2.8 R 数据分析

**R Data Analysis** tab 内置 R 模板(alpha/beta 多样性、分类学预处理等),
依赖 `r_plot_agent/` 自带的 R 模块。

---

## 3. 系统架构

### 3.1 总览

```
┌─────────────────────────────────────────────────────────────┐
│ 浏览器 (frontend/index.html)                                │
│   ├─ i18n.js         — 加载翻译、应用 data-i18n              │
│   ├─ xterm.js        — 浏览器内终端                          │
│   └─ socket.io       — 实时终端 + 工作流进度                 │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP / WebSocket
┌────────────────────▼────────────────────────────────────────┐
│ FastAPI + python-socketio 后端 (backend.py)                 │
│   ├─ /api/i18n/{lang}              — 翻译目录                 │
│   ├─ /api/settings                 — 用户设置(user_config)    │
│   ├─ /api/env-build/...            — AI 环境修正循环          │
│   ├─ /api/workflow/render-config   — 配置弹窗 HTML            │
│   ├─ /api/workflow/save-config     — 写参数 + 脚本           │
│   ├─ /api/terminal/...             — PTY 会话桥接             │
│   ├─ /api/rdata/...                — R 会话桥接               │
│   └─ /api/agent/*                 — OpenClaw AI 代理         │
└──────┬───────────────┬─────────────────┬────────────────────┘
       │               │                 │
       ▼               ▼                 ▼
┌─────────────┐  ┌──────────────┐  ┌────────────────┐
│ Conda 环境   │  │ OpenClaw     │  │ r_plot_agent   │
│ (vsearch)   │  │ 网关(必须)   │  │ (R 可视化)    │
│             │  │              │  │                │
└─────────────┘  └──────────────┘  └────────────────┘
```

### 3.2 仓库目录

| 路径 | 用途 |
|------|------|
| `backend.py` | FastAPI + SocketIO 后端 |
| `config.py` | 集中配置(路径、端口、选项) |
| `i18n.py` | 中英翻译字典 |
| `launcher.py` | 启动后端 + 自动打开浏览器 |
| `frontend/` | 静态 HTML/JS UI |
| `frontend/i18n.js` | 前端 i18n 加载/应用模块 |
| `workflows/` | 保存的工作流定义 |
| `templates/` | 工作流模板 |
| `r_plot_agent/` | 自带的 R 可视化模块 |
| `r_plot_integration.py` | Python ↔ R 桥接 |
| `session_manager.py` | 浏览器内终端的 PTY 会话管理 |
| `setup.py` | 跨设备首次运行向导 |
| `install.sh` | 创建 conda 生物信息环境 |
| `environment.yml` | conda 环境定义(vsearch 等) |
| `requirements.txt` | Python 依赖 |
| `MANUAL.md` | 工具安装手册(参考数据库等) |
| `supplies-list.md` | 流水线依赖清单 |
| `openclaw_llm.py` | OpenClaw AI 网关客户端 |
| `openclaw.json.template` | OpenClaw token 配置模板 |

### 3.3 配置

所有路径与设置集中在 [`config.py`](config.py)。常用环境变量覆盖:

| 变量 | 默认值 | 用途 |
|------|--------|------|
| `OPENCLAW_URL` | `http://127.0.0.1:18789` | OpenClaw 网关端点 |
| `OPENCLAW_TOKEN_PATH` | `~/.openclaw/openclaw.json` | token 文件位置 |
| `CONDA_EXECUTABLE` | `conda` | conda 可执行文件 |
| `LIMBO_HOST` | `0.0.0.0` | 后端绑定地址 |
| `LIMBO_PORT` | `5002` | 后端端口 |
| `R_PLOT_AGENT_PATH` | `<project>/r_plot_agent` | R 模块路径 |
| `LIMBO_ENV_FIX_MODEL` | `openclaw/default` | 自动修正使用的 AI 模型 |

### 3.4 用户设置(运行时持久化)

通过 `GET /api/settings` 与 `POST /api/settings` 读写,保存在项目根目录的
`user_config.json`:

| 设置项 | 默认 | 范围 | 说明 |
|--------|------|------|------|
| `language` | `en` | en / zh | 界面语言 |
| `env_fix_max_attempts` | `3` | 1 – 10 | 环境构建失败时 AI 智能体最多重试次数 |

修改入口:右上角 ⚙ → 设置。后端会校验范围,越界返回 HTTP 400。

### 3.5 i18n 流程

- 后端 `GET /api/i18n/<lang>` → 返回 `{locale, supported, strings}`
- 前端 `i18n.js` 加载时拉取,通过 `I18n.applyAll()` 应用到所有
  `[data-i18n]` / `[data-i18n-title]` / `[data-i18n-placeholder]` 元素
- 切换语言时重新拉取并应用,无需刷新页面
- 服务端渲染的 HTML(如工作流配置弹窗)接受 `?lang=` 参数嵌入翻译字符串
- 缺翻译时回退英文,再回退到 key 本身

### 3.6 数据流 — 自动修正循环

```
用户点击「创建环境 (自动修正)」
    │
    ▼
POST /api/env-build/create-env-with-fix
    { working_dir, max_retries? }
    │
    │  max_retries = min(user_config.env_fix_max_attempts, client_hint)
    │                clamp 到 [1, 10]
    ▼
对 attempt 1..max_retries:
    ├─ 执行 `conda env create -p <dir> -f environment.yml`
    ├─ 成功 → 推送 "done" 事件 → 返回
    └─ 失败:
        ├─ 把错误发给 OpenClaw 智能体
        ├─ 智能体重写 environment.yml
        └─ 重试
```

### 3.7 隐私

本仓库**不含任何个人信息**:

- 无个人路径(`/Users/...`、`/home/...`)
- 无 token、API key、密码
- 无 git 历史(`.git/` 未包含)
- 所有 conda 环境路径用占位符 `<PROJECT_DIR>/bioinfo_env`

实际运行时,把 `<PROJECT_DIR>` 替换为你的真实项目路径即可。

### 3.8 许可

遵循上游 LIMBO 项目的许可条款。
