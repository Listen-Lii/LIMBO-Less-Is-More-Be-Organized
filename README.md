# LIMBO

LIMBO is a web-based environment for designing, configuring, and running
bioinformatics analysis workflows (16S/ITS ASV pipelines, etc.).

**中文文档:** [README.zh.md](README.zh.md)

---

## 1. Initial Setup

### 1.1 Prerequisites

| Tool         | Required       | Notes                                                    |
|--------------|----------------|----------------------------------------------------------|
| Python 3.9+  | yes            | system Python is fine                                    |
| Conda        | yes            | install from [conda-forge/miniforge](https://conda-forge.org/) |
| Git          | optional       | only for cloning the repo                                |

### 1.2 Install

```bash
# Clone (or download) the project
git clone <repo-url> limbo && cd limbo

# Create the conda bioinfo environment (vsearch, etc.)
bash install.sh

# Configure OpenClaw AI gateway — see §1.4 below (required)

# Launch: starts backend and opens browser automatically
python3 launcher.py
```

The launcher starts a FastAPI backend on `http://127.0.0.1:5002/` and
opens the page in your default browser.

### 1.3 First-Run Configuration Wizard

When you launch on a new device for the first time, run the cross-device
setup helper to register paths and Conda environments:

```bash
python3 setup.py
```

`setup.py` writes to `config.py` and creates `user_config.json` in the
project root.

### 1.4 OpenClaw Gateway (Required)

OpenClaw Gateway is **required** for LIMBO's core AI features
(workflow generation, environment auto-fix loop, agent chat). The
gateway listens at `http://127.0.0.1:18789` by default and must be
running and reachable before you launch LIMBO.

```bash
# 1. Run an OpenClaw Gateway reachable from this machine.
# 2. Copy the template and fill in your token.
cp openclaw.json.template ~/.openclaw/openclaw.json
# 3. Edit ~/.openclaw/openclaw.json: replace placeholders.
```

Override the path with `OPENCLAW_TOKEN_PATH` and the URL with
`OPENCLAW_URL` (see [Configuration](#configuration)).

---

## 2. Usage

### 2.1 Choose Language

Top-right corner has a **English / 中文** switcher. The choice is
persisted in browser `localStorage` and survives reloads. Strings are
loaded from `GET /api/i18n/<lang>` and applied to elements marked with
`data-i18n="<key>"`.

To add a new translatable string:

1. Add `data-i18n="<key>"` to the HTML element.
2. Add the entry to `i18n.py`:
   ```python
   "<key>": {"en": "English text", "zh": "中文文本"},
   ```

### 2.2 Pick a Conda Environment

Sidebar → **Conda Environment** → choose the environment you created with
`bash install.sh`. The selection is reflected in the status bar.

### 2.3 Set a Working Directory

Sidebar → **Working Directory**. LIMBO stores generated files
(`environment.yml`, `install.sh`, `supplies-list.md`, `MANUAL.md`,
workflow scripts, run logs) here.

### 2.4 Environment Build Workflow

1. **Environment Build** tab → enter a free-text workflow description
   (e.g. *"merge paired reads, denoise with UNOISE3, filter chimeras
   against SILVA, generate OTU table"*).
2. Click **Generate Environment Configuration**. LIMBO calls the AI agent
   to produce:
   - `supplies-list.md` — dependency checklist
   - `environment.yml` — conda environment spec
   - `install.sh` — installer
   - `MANUAL.md` — instructions for any non-conda tools (e.g. reference DBs)
3. Review the preview tabs on the right.
4. Click **Create Conda Environment** (or **Create Environment (Auto-Fix)**
   to let the agent retry on failure).
5. **Open Directory** to inspect the generated files.

### 2.5 Auto-Fix Loop

When conda env creation fails, the agent can be invoked to diagnose
and rewrite `environment.yml`. The retry count is user-configurable:

- Default: 3 (from `config.py` `ENV_FIX_MAX_ATTEMPTS`)
- Range: 1 – 10
- Persisted to `user_config.json`
- Set via ⚙ (top-right) → **Environment Fix Max Attempts**, or via
  `POST /api/settings`

The endpoint `POST /api/env-build/create-env-with-fix` reads this value
on every invocation.

### 2.6 Workflow Configuration

After a workflow is generated, click **Configure** on a step to inspect
its parameters. Each step shows:

- ✅ green check — parameters successfully retrieved
- ❌ red cross — parameters query failed (tool may not be installed)

Clicking **Configure** opens the parameter form, with **Required** and
**Optional** sections. **External File** badges mark user-supplied
files (e.g. FASTQ input, reference DB); **Internal File** badges mark
files produced by earlier steps in the same workflow.

### 2.7 SSH / Remote Terminal

Sidebar → **Terminal** → choose Local or an SSH profile. Configure
profiles via the **SSH Management** modal (sidebar → Tools).

### 2.8 R Data Analysis

The **R Data Analysis** tab hosts bundled R templates (alpha/beta
diversity, taxonomic preprocessing, etc.). Requires the R installation
under `r_plot_agent/`.

---

## 3. System Architecture

### 3.1 High-Level Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Browser (frontend/index.html)                               │
│   ├─ i18n.js          — fetch catalog, apply data-i18n      │
│   ├─ xterm.js         — in-browser terminal                 │
│   └─ socket.io client — live terminal + workflow progress   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP / WebSocket
┌────────────────────▼────────────────────────────────────────┐
│ FastAPI + python-socketio backend (backend.py)             │
│   ├─ /api/i18n/{lang}             — translation catalog     │
│   ├─ /api/settings                — user_config.json        │
│   ├─ /api/env-build/...           — AI env fix loop         │
│   ├─ /api/workflow/render-config  — HTML for config modal   │
│   ├─ /api/workflow/save-config    — write params + scripts  │
│   ├─ /api/terminal/...            — PTY session bridge      │
│   ├─ /api/rdata/...               — R session bridge        │
│   └─ /api/agent/*                 — OpenClaw AI proxy       │
└──────┬───────────────┬─────────────────┬────────────────────┘
       │               │                 │
       ▼               ▼                 ▼
┌─────────────┐  ┌──────────────┐  ┌────────────────┐
│ Conda env   │  │ OpenClaw     │  │ r_plot_agent   │
│ (vsearch)   │  │ Gateway      │  │ (R visualizer) │
│             │  │ (required)   │  │                │
└─────────────┘  └──────────────┘  └────────────────┘
```

### 3.2 Repository Layout

| Path                        | Purpose                                          |
|-----------------------------|--------------------------------------------------|
| `backend.py`                | FastAPI + SocketIO backend                       |
| `config.py`                 | Centralized configuration (paths, ports, options)|
| `i18n.py`                   | Bilingual (en/zh) translation catalog            |
| `launcher.py`               | Start backend and open browser                   |
| `frontend/`                 | Static HTML/JS UI                                |
| `frontend/i18n.js`          | Frontend i18n loader / applier                   |
| `workflows/`                | Saved workflow definitions                       |
| `templates/`                | Workflow templates                               |
| `r_plot_agent/`             | Bundled R visualization module                   |
| `r_plot_integration.py`     | Python ↔ R bridge                                |
| `session_manager.py`        | PTY session handling for in-browser terminal     |
| `setup.py`                  | Cross-device first-run setup wizard              |
| `install.sh`                | Creates the conda bioinfo environment            |
| `environment.yml`           | Conda env spec (vsearch, etc.)                   |
| `requirements.txt`          | Python package dependencies                      |
| `MANUAL.md`                 | Tool installation manual (reference DBs, etc.)   |
| `supplies-list.md`          | Pipeline dependency checklist                    |
| `openclaw_llm.py`           | Client for OpenClaw AI gateway                  |
| `openclaw.json.template`    | Template for OpenClaw token config              |

### 3.3 Configuration

All paths and settings live in [`config.py`](config.py). Common
overrides via environment variables:

| Variable                   | Default                              | Purpose                       |
|----------------------------|--------------------------------------|-------------------------------|
| `OPENCLAW_URL`             | `http://127.0.0.1:18789`             | OpenClaw Gateway endpoint     |
| `OPENCLAW_TOKEN_PATH`      | `~/.openclaw/openclaw.json`          | Token file location           |
| `CONDA_EXECUTABLE`         | `conda`                              | Conda binary                  |
| `LIMBO_HOST`               | `0.0.0.0`                            | Backend bind address          |
| `LIMBO_PORT`               | `5002`                               | Backend port                  |
| `R_PLOT_AGENT_PATH`        | `<project>/r_plot_agent`             | R module path                 |
| `LIMBO_ENV_FIX_MODEL`      | `openclaw/default`                   | AI model for env fix loop     |

### 3.4 User Settings (Runtime, Persisted)

Runtime settings live in `user_config.json` (project root) and are managed
via `GET /api/settings` and `POST /api/settings`:

| Setting                  | Default | Range     | Description                                                |
|--------------------------|---------|-----------|------------------------------------------------------------|
| `language`               | `en`    | en / zh   | UI language                                                |
| `env_fix_max_attempts`   | `3`     | 1 – 10    | Max retries for AI-driven environment fix loop             |

Edit via the ⚙ button (top-right). Values are validated server-side
and rejected with HTTP 400 if out of range.

### 3.5 i18n Pipeline

- Backend exposes `GET /api/i18n/<lang>` → returns `{locale, supported, strings}`
- Frontend `i18n.js` fetches on load, applies to `[data-i18n]` /
  `[data-i18n-title]` / `[data-i18n-placeholder]` attributes via
  `I18n.applyAll()`
- Switching language re-fetches and re-applies without page reload
- Server-rendered HTML (e.g. workflow config modal) accepts a `?lang=`
  query param to embed localized strings
- Missing keys fall back to English, then to the key itself

### 3.6 Data Flow — Auto-Fix Loop

```
User clicks "Create Environment (Auto-Fix)"
    │
    ▼
POST /api/env-build/create-env-with-fix
    { working_dir, max_retries? }
    │
    │  max_retries = min(user_config.env_fix_max_attempts, client_hint)
    │                clamped to [1, 10]
    ▼
For attempt 1..max_retries:
    ├─ Run `conda env create -p <dir> -f environment.yml`
    ├─ If success → emit "done" event → return
    └─ If failure:
        ├─ Send error to OpenClaw Agent
        ├─ Agent rewrites environment.yml
        └─ Retry
```

### 3.7 Privacy

This repository contains **no personal data**:

- No personal file paths (`/Users/...`, `/home/...`).
- No tokens, API keys, or passwords.
- No git history (the `.git/` directory is not included in the
  publishable copy).
- All conda env paths use the placeholder `<PROJECT_DIR>/bioinfo_env`.

Replace `<PROJECT_DIR>` with your actual project path when running the
generated scripts.

### 3.8 License

See upstream LIMBO project for license terms.