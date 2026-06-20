"""
LIMBO i18n module.

Provides translation catalogs for English (en) and Chinese (zh).
Use t(key, lang) to translate a key in Python; the frontend loads the
catalog via GET /api/i18n/<lang>.
"""
from typing import Dict

# Supported locales
LOCALES = ("en", "zh")
DEFAULT_LOCALE = "en"


STRINGS: Dict[str, Dict[str, str]] = {
    # ============== Sidebar / Navigation ==============
    "nav.environment_build": {
        "en": "Environment Build",
        "zh": "环境构建",
    },
    "nav.workflow": {
        "en": "Workflow",
        "zh": "工作流",
    },
    "sidebar.general": {
        "en": "General",
        "zh": "通用",
    },
    "sidebar.select_server": {
        "en": "Select Server",
        "zh": "选择服务器",
    },
    "sidebar.conda_env": {
        "en": "Conda Environment",
        "zh": "Conda 环境",
    },
    "sidebar.file_input": {
        "en": "File Input",
        "zh": "文件输入",
    },
    "sidebar.metadata": {
        "en": "Metadata",
        "zh": "元数据",
    },
    "sidebar.workflow_file": {
        "en": "Workflow File",
        "zh": "工作流文件",
    },
    "sidebar.tools": {
        "en": "Tools",
        "zh": "工具",
    },
    "sidebar.terminal": {
        "en": "Terminal",
        "zh": "终端",
    },
    "sidebar.run_log": {
        "en": "Run Log",
        "zh": "运行日志",
    },
    "sidebar.working_dir": {
        "en": "Working Directory",
        "zh": "工作目录",
    },
    "sidebar.current_env": {
        "en": "Current Environment",
        "zh": "当前环境",
    },
    "sidebar.not_set": {
        "en": "Not set",
        "zh": "未设置",
    },
    "sidebar.none": {
        "en": "None",
        "zh": "无",
    },

    # ============== Server / env status ==============
    "status.not_connected": {
        "en": "Not connected",
        "zh": "未连接",
    },
    "status.no_env": {
        "en": "No environment selected",
        "zh": "未选择环境",
    },

    # ============== Workflow list ==============
    "workflow.title": {
        "en": "Workflow List",
        "zh": "工作流列表",
    },
    "workflow.refresh": {
        "en": "Refresh",
        "zh": "刷新",
    },
    "workflow.upload": {
        "en": "Upload",
        "zh": "上传",
    },
    "workflow.configure": {
        "en": "Configure",
        "zh": "配置",
    },
    "workflow.run": {
        "en": "Run",
        "zh": "运行",
    },

    # ============== Chat panel ==============
    "chat.title": {
        "en": "Agent Chat",
        "zh": "智能体对话",
    },
    "chat.welcome": {
        "en": "Hello! I am the LIMBO Assistant.<br><br>Please follow these steps to get started:<br>1. Click \"Select Server\" in the sidebar to connect to a server<br>2. Click \"Conda Environment\" to select an analysis environment<br>3. Upload a workflow file or enter a workflow description",
        "zh": "你好！我是 LIMBO 助手。<br><br>请按以下步骤开始：<br>1. 点击侧边栏\"选择服务器\"连接服务器<br>2. 点击\"Conda 环境\"选择分析环境<br>3. 上传工作流文件或输入工作流描述",
    },
    "chat.input_placeholder": {
        "en": "Type your message...",
        "zh": "输入消息...",
    },
    "chat.send": {
        "en": "Send",
        "zh": "发送",
    },

    # ============== Environment Build ==============
    "envbuild.title": {
        "en": "Environment Build",
        "zh": "环境构建",
    },
    "envbuild.working_dir": {
        "en": "Working Directory",
        "zh": "工作目录",
    },
    "envbuild.text_input": {
        "en": "Workflow Description",
        "zh": "工作流描述",
    },
    "envbuild.analyze": {
        "en": "Analyze Workflow",
        "zh": "分析工作流",
    },
    "envbuild.create_env": {
        "en": "Create Conda Environment",
        "zh": "创建 Conda 环境",
    },
    "envbuild.auto_fix": {
        "en": "Create Environment (Auto-Fix)",
        "zh": "创建环境 (自动修正)",
    },
    "envbuild.logs": {
        "en": "Logs",
        "zh": "日志",
    },
    "envbuild.preview": {
        "en": "Preview",
        "zh": "预览",
    },
    "envbuild.supplies_list": {
        "en": "supplies-list.md",
        "zh": "supplies-list.md",
    },
    "envbuild.environment_yml": {
        "en": "environment.yml",
        "zh": "environment.yml",
    },
    "envbuild.install_sh": {
        "en": "install.sh",
        "zh": "install.sh",
    },
    "envbuild.manual": {
        "en": "MANUAL.md",
        "zh": "MANUAL.md",
    },

    # ============== Settings / env-fix attempts ==============
    "settings.title": {
        "en": "Settings",
        "zh": "设置",
    },
    "settings.env_fix_attempts": {
        "en": "Environment Fix Max Attempts",
        "zh": "环境自动修正最大尝试次数",
    },
    "settings.env_fix_attempts_help": {
        "en": "Maximum number of times the AI agent will retry to fix environment creation failures (1-10).",
        "zh": "AI 智能体在创建环境失败时最多重试的次数 (1-10)。",
    },
    "settings.save": {
        "en": "Save",
        "zh": "保存",
    },
    "settings.cancel": {
        "en": "Cancel",
        "zh": "取消",
    },
    "settings.saved": {
        "en": "Settings saved",
        "zh": "设置已保存",
    },
    "settings.invalid_value": {
        "en": "Invalid value. Must be between 1 and 10.",
        "zh": "无效值。必须在 1 到 10 之间。",
    },

    # ============== Language switcher ==============
    "lang.switch": {
        "en": "Language",
        "zh": "语言",
    },
    "lang.english": {
        "en": "English",
        "zh": "English",
    },
    "lang.chinese": {
        "en": "中文",
        "zh": "中文",
    },

    # ============== Modal: Conda ==============
    "modal.conda.title": {
        "en": "Select Conda Environment",
        "zh": "选择 Conda 环境",
    },
    "modal.conda.refresh": {
        "en": "Refresh Environments",
        "zh": "刷新环境列表",
    },
    "modal.conda.select": {
        "en": "Select",
        "zh": "选择",
    },
    "modal.conda.close": {
        "en": "Close",
        "zh": "关闭",
    },

    # ============== Modal: Server ==============
    "modal.server.title": {
        "en": "Select Server",
        "zh": "选择服务器",
    },
    "modal.server.local": {
        "en": "Local",
        "zh": "本地",
    },
    "modal.server.add": {
        "en": "Add Server",
        "zh": "添加服务器",
    },

    # ============== Modal: Workflow file / workflow text ==============
    "modal.workflow.title": {
        "en": "Workflow File",
        "zh": "工作流文件",
    },
    "modal.workflow.text": {
        "en": "Enter workflow text",
        "zh": "输入工作流文本",
    },
    "modal.workflow.submit": {
        "en": "Submit",
        "zh": "提交",
    },

    # ============== Modal: Workflow Configuration ==============
    "wfc.title_prefix": {
        "en": "Workflow Configuration",
        "zh": "工作流配置",
    },
    "wfc.params_retrieved": {
        "en": "Parameters retrieved",
        "zh": "参数已查询",
    },
    "wfc.params_failed": {
        "en": "Parameters query failed",
        "zh": "参数查询失败",
    },
    "wfc.configure_btn": {
        "en": "Configure",
        "zh": "配置",
    },
    "wfc.run_btn": {
        "en": "Run",
        "zh": "运行",
    },
    "wfc.save_configuration": {
        "en": "Save Configuration",
        "zh": "保存配置",
    },
    "wfc.required_params": {
        "en": "Required Parameters",
        "zh": "必需参数",
    },
    "wfc.optional_params": {
        "en": "Optional Parameters",
        "zh": "可选参数",
    },
    "wfc.expand": {
        "en": "Expand",
        "zh": "展开",
    },
    "wfc.collapse": {
        "en": "Collapse",
        "zh": "收起",
    },
    "wfc.external_file": {
        "en": "External File",
        "zh": "外部文件",
    },
    "wfc.internal_file": {
        "en": "Internal File",
        "zh": "内部文件",
    },
    "wfc.cannot_retrieve_params": {
        "en": "Cannot retrieve parameter information",
        "zh": "无法获取参数信息",
    },
    "wfc.configure_step_title": {
        "en": "Configure",
        "zh": "配置",
    },
    "wfc.saved": {
        "en": "Configuration saved",
        "zh": "配置已保存",
    },
    "wfc.save_failed": {
        "en": "Save failed",
        "zh": "保存失败",
    },

    # ============== Terminal ==============
    "terminal.connected": {
        "en": "Connected",
        "zh": "已连接",
    },
    "terminal.disconnected": {
        "en": "Disconnected",
        "zh": "已断开",
    },
    "terminal.clear": {
        "en": "Clear",
        "zh": "清屏",
    },
    "terminal.close": {
        "en": "Close",
        "zh": "关闭",
    },

    # ============== Toast / notification messages ==============
    "toast.select_env_first": {
        "en": "Please select a Conda environment first",
        "zh": "请先选择 Conda 环境",
    },
    "toast.select_server_first": {
        "en": "Please select a server first",
        "zh": "请先选择服务器",
    },
    "toast.workflow_text_required": {
        "en": "Please enter workflow description",
        "zh": "请输入工作流描述",
    },
    "toast.creating_env": {
        "en": "Creating Conda environment...",
        "zh": "正在创建 Conda 环境...",
    },
    "toast.env_created_ok": {
        "en": "Conda environment created successfully",
        "zh": "Conda 环境创建成功",
    },
    "toast.env_create_failed": {
        "en": "Environment creation failed",
        "zh": "环境创建失败",
    },
    "toast.cannot_read_yml": {
        "en": "Cannot read environment.yml",
        "zh": "无法读取 environment.yml",
    },
    "toast.workflow_generated": {
        "en": "Workflow generation complete",
        "zh": "工作流生成完成",
    },
    "toast.workflow_gen_failed": {
        "en": "Workflow generation failed",
        "zh": "工作流生成失败",
    },
    "toast.params_not_loaded": {
        "en": "Parameter data not loaded",
        "zh": "参数数据未加载",
    },
    "toast.config_loaded_failed": {
        "en": "Failed to load configuration",
        "zh": "加载配置失败",
    },

    # ============== Env-build streaming messages ==============
    "envbuild.attempt_run": {
        "en": "Attempt {attempt}/{max_retries}: running conda env create...",
        "zh": "尝试 {attempt}/{max_retries}:运行 conda env create...",
    },
    "envbuild.attempt_ok": {
        "en": "conda environment created successfully!",
        "zh": "conda 环境创建成功!",
    },
    "envbuild.attempt_failed": {
        "en": "Attempt {attempt} failed: {error}",
        "zh": "尝试 {attempt} 失败:{error}",
    },
    "envbuild.max_retries_reached": {
        "en": "Maximum retries reached. Stopping.",
        "zh": "已达最大重试次数,停止。",
    },
    "envbuild.calling_agent": {
        "en": "Attempt {attempt} failed. Sending fix request to Agent...",
        "zh": "尝试 {attempt} 失败,向智能体发送修正请求...",
    },
    "envbuild.agent_no_fix": {
        "en": "Agent did not return a valid fix. Stopping.",
        "zh": "智能体未返回有效修正,停止。",
    },
    "envbuild.agent_fix_done": {
        "en": "Agent fix complete. Retrying...",
        "zh": "智能体修正完成,重新尝试...",
    },
    "envbuild.env_create_failed": {
        "en": "Environment creation failed",
        "zh": "环境创建失败",
    },
    "envbuild.agent_fix_failed": {
        "en": "Agent fix failed",
        "zh": "智能体修正失败",
    },

    # ============== Errors / status (backend) ==============
    "err.token_not_found": {
        "en": "No token found",
        "zh": "未找到令牌",
    },
    "err.gateway_error": {
        "en": "Gateway error",
        "zh": "网关错误",
    },
    "err.params_failed": {
        "en": "Parameters query failed, this tool may not be installed",
        "zh": "参数查询失败,工具可能未安装",
    },
    "action.upload": {
        "en": "Upload",
        "zh": "上传",
    },
    "action.save": {
        "en": "Save",
        "zh": "保存",
    },
    "action.close": {
        "en": "Close",
        "zh": "关闭",
    },
    "action.send": {
        "en": "Send",
        "zh": "发送",
    },
    "action.cancel": {
        "en": "Cancel",
        "zh": "取消",
    },
    "action.confirm": {
        "en": "Confirm",
        "zh": "确定",
    },
    "action.run": {
        "en": "Run",
        "zh": "执行",
    },
    "action.back": {
        "en": "Back",
        "zh": "返回",
    },
    "action.delete": {
        "en": "Delete",
        "zh": "删除",
    },
    "action.rename": {
        "en": "Rename",
        "zh": "重命名",
    },
    "action.clear": {
        "en": "Clear",
        "zh": "清空",
    },
    "action.view": {
        "en": "View",
        "zh": "查看",
    },
    "label.description": {
        "en": "Description",
        "zh": "描述",
    },
    "action.select": {
        "en": "Select",
        "zh": "选择",
    },
    "action.preview": {
        "en": "Preview",
        "zh": "预览",
    },
    "label.tools": {
        "en": "Tools",
        "zh": "工具",
    },
    "label.terminal": {
        "en": "Terminal",
        "zh": "终端",
    },
    "label.settings": {
        "en": "Settings",
        "zh": "设置",
    },
    "label.password": {
        "en": "Password",
        "zh": "密码",
    },
    "label.port": {
        "en": "Port",
        "zh": "端口",
    },
    "label.username": {
        "en": "Username",
        "zh": "用户名",
    },
    "label.host": {
        "en": "Host",
        "zh": "主机地址",
    },
    "label.connection_name": {
        "en": "Connection Name",
        "zh": "连接名称",
    },
    "label.path": {
        "en": "Path:",
        "zh": "路径:",
    },
    "label.steps_count": {
        "en": "Steps:",
        "zh": "步骤数:",
    },
    "sidebar.general": {
        "en": "General",
        "zh": "通用",
    },
    "sidebar.file_input": {
        "en": "File Input",
        "zh": "文件输入",
    },
    "sidebar.select_server": {
        "en": "Select Server",
        "zh": "选择服务器",
    },
    "sidebar.conda_env": {
        "en": "Conda Environment",
        "zh": "Conda 环境",
    },
    "sidebar.select_workflow": {
        "en": "Select Workflow",
        "zh": "选择工作流",
    },
    "sidebar.not_set": {
        "en": "Not set",
        "zh": "未设置",
    },
    "sidebar.current_env": {
        "en": "Current Environment",
        "zh": "当前环境",
    },
    "sidebar.current_project": {
        "en": "Current Project",
        "zh": "当前项目",
    },
    "sidebar.working_dir": {
        "en": "Working Directory",
        "zh": "工作目录",
    },
    "sidebar.analysis_card": {
        "en": "Analysis Card",
        "zh": "分析卡片",
    },
    "sidebar.analysis_text": {
        "en": "Analysis Text",
        "zh": "分析文本",
    },
    "status.not_connected": {
        "en": "Not connected",
        "zh": "未连接",
    },
    "status.not_selected": {
        "en": "Not selected",
        "zh": "未选择",
    },
    "status.no_env": {
        "en": "No environment selected",
        "zh": "未选择环境",
    },
    "status.env_not_found": {
        "en": "Environment not found",
        "zh": "未找到环境",
    },
    "tab.env_build": {
        "en": "Environment Build",
        "zh": "环境构建",
    },
    "tab.workflow": {
        "en": "Workflow",
        "zh": "工作流管理",
    },
    "tab.workflow_list": {
        "en": "Workflow List",
        "zh": "工作流列表",
    },
    "tab.workflow_input": {
        "en": "Workflow Input",
        "zh": "工作流输入",
    },
    "tab.r_data": {
        "en": "R Data Analysis",
        "zh": "R 数据分析",
    },
    "workflow.import_file": {
        "en": "Import File",
        "zh": "导入文件",
    },
    "workflow.create_env": {
        "en": "Create Environment",
        "zh": "创建环境",
    },
    "workflow.save_to_project": {
        "en": "Save to Project",
        "zh": "保存到项目",
    },
    "workflow.run_log": {
        "en": "Run Log",
        "zh": "执行日志",
    },
    "workflow.script_name": {
        "en": "Script Name",
        "zh": "脚本名称",
    },
    "workflow.script_config": {
        "en": "Script Configuration",
        "zh": "脚本配置",
    },
    "workflow.no_workflows": {
        "en": "No workflows yet",
        "zh": "暂无工作流",
    },
    "workflow.run_log_short": {
        "en": "Run Log",
        "zh": "运行日志",
    },
    "workflow.thinking": {
        "en": "Thinking...",
        "zh": "推理过程",
    },
    "workflow.llm_processing": {
        "en": "LLM Processing",
        "zh": "LLM 处理",
    },
    "workflow.workflow_file": {
        "en": "Workflow File",
        "zh": "流程文件",
    },
    "workflow.workflow_input_or_file": {
        "en": "Workflow File / Free Input",
        "zh": "流程文件 / 自由输入",
    },
    "workflow.method_upload": {
        "en": "Method 1: Upload File",
        "zh": "方式一：上传文件",
    },
    "workflow.method_text": {
        "en": "Method 2: Free Text Input",
        "zh": "方式二：自由文本输入",
    },
    "workflow.drop_files_here": {
        "en": "Click or drag files here",
        "zh": "点击或拖拽文件到此处",
    },
    "workflow.supported_formats_long": {
        "en": "Supports .sh, .md, .txt, .yaml, .yml formats",
        "zh": "支持 .sh, .md, .txt, .yaml, .yml 格式",
    },
    "workflow.supported_formats_yaml": {
        "en": "Supports YAML, JSON, SH, MD formats",
        "zh": "支持 YAML, JSON, SH, MD 格式",
    },
    "workflow.input_placeholder": {
        "en": "Enter workflow description...",
        "zh": "输入工作流描述...",
    },
    "workflow.input_example": {
        "en": "e.g. QC FASTQ files, trim adapters, cluster, taxonomic annotation...",
        "zh": "例如：对FASTQ文件进行质量控制，去接头，聚类，物种注释...",
    },
    "workflow.input_help": {
        "en": "Enter any format of workflow description, AI will analyze and extract steps",
        "zh": "输入任意格式的工作流描述，AI会自动分析并提取步骤",
    },
    "workflow.result_placeholder": {
        "en": "Generation results will appear here",
        "zh": "生成结果将显示在这里",
    },
    "workflow.generate_env_config": {
        "en": "Generate Environment Configuration",
        "zh": "生成环境配置",
    },
    "workflow.result_preview": {
        "en": "Result Preview",
        "zh": "生成结果预览",
    },
    "workflow.env_actions": {
        "en": "Environment Actions",
        "zh": "环境操作",
    },
    "workflow.set_work_dir_first": {
        "en": "Please set working directory first...",
        "zh": "请先设置工作目录...",
    },
    "workflow.set_work_dir_first_short": {
        "en": "Set working directory first",
        "zh": "请先设置工作目录",
    },
    "workflow.upload_supplies": {
        "en": "Please upload supplies-list.md or .sh script files",
        "zh": "请上传 supplies-list.md 或 .sh 脚本文件",
    },
    "workflow.select_work_dir": {
        "en": "Select Working Directory",
        "zh": "选择工作目录",
    },
    "r.code": {
        "en": "R Code",
        "zh": "R 代码",
    },
    "r.session": {
        "en": "R Session",
        "zh": "R 会话",
    },
    "r.objects": {
        "en": "R Objects",
        "zh": "R 对象",
    },
    "r.abundance_matrix": {
        "en": "Abundance Matrix",
        "zh": "丰度矩阵",
    },
    "r.taxonomy_file": {
        "en": "Taxonomy File",
        "zh": "注释文件",
    },
    "r.taxonomy_preprocess": {
        "en": "Taxonomy Preprocessing",
        "zh": "注释预处理",
    },
    "r.input_data": {
        "en": "Input Data",
        "zh": "输入数据",
    },
    "r.select_object_to_preview": {
        "en": "Select an object to preview",
        "zh": "选择对象进行预览",
    },
    "r.no_objects": {
        "en": "No objects",
        "zh": "暂无对象",
    },
    "r.view_objects": {
        "en": "View Objects",
        "zh": "查看对象",
    },
    "r.load_session": {
        "en": "Load Session",
        "zh": "加载会话",
    },
    "r.load_failed": {
        "en": "Load failed",
        "zh": "加载失败",
    },
    "r.prompt_example": {
        "en": "Enter prompt, e.g. split annotations by taxonomic level",
        "zh": "输入 prompt，如：按照分类学级别将注释分列",
    },
    "r.no_templates": {
        "en": "No analysis templates",
        "zh": "暂无分析模板",
    },
    "r.please_select": {
        "en": "Please select...",
        "zh": "请选择...",
    },
    "r.select_tax_col": {
        "en": "Select taxonomy column...",
        "zh": "选择注释列...",
    },
    "ssh.management": {
        "en": "SSH Management",
        "zh": "SSH 管理",
    },
    "ssh.connection_management": {
        "en": "SSH Connection Management",
        "zh": "SSH 连接管理",
    },
    "ssh.local": {
        "en": "Local",
        "zh": "本地 (local)",
    },
    "ssh.local_computer": {
        "en": "Local Computer",
        "zh": "本地计算机",
    },
    "ssh.remote_terminal": {
        "en": "Remote Terminal",
        "zh": "远程终端",
    },
    "ssh.auth_method": {
        "en": "Authentication Method",
        "zh": "认证方式",
    },
    "ssh.password_auth": {
        "en": "Password",
        "zh": "密码认证",
    },
    "ssh.key_file": {
        "en": "Key File",
        "zh": "密钥文件",
    },
    "ssh.key_path": {
        "en": "Key File Path",
        "zh": "密钥文件路径",
    },
    "ssh.enter_password": {
        "en": "Enter password",
        "zh": "输入密码",
    },
    "ssh.add_connection": {
        "en": "+ Add New Connection",
        "zh": "+ 添加新连接",
    },
    "ssh.no_connections": {
        "en": "No SSH connections",
        "zh": "暂无SSH连接",
    },
    "ssh.tab_hint": {
        "en": "Tab to complete | Ctrl+C to exit",
        "zh": "按 Tab 补全 | Ctrl+C 退出",
    },
    "chat.agent_chat": {
        "en": "Agent Chat",
        "zh": "Agent 对话",
    },
    "chat.welcome_short": {
        "en": "Hello! I am the LIMBO Assistant.",
        "zh": "您好！我是 LIMBO 助手。",
    },
    "chat.welcome_agent": {
        "en": "Hello! I am the LIMBO Agent. I can read and write files in your working directory.",
        "zh": "您好！我是 LIMBO Agent，可以读写工作目录中的文件。",
    },
    "chat.steps_intro": {
        "en": "Please follow these steps:",
        "zh": "请按以下步骤开始：",
    },
    "chat.step1": {
        "en": "1. Click \"Select Server\" in the sidebar to connect",
        "zh": "1. 点击侧边栏\"选择服务器\"连接服务器",
    },
    "chat.step2": {
        "en": "2. Click \"Conda Environment\" to select an analysis environment",
        "zh": "2. 点击\"Conda 环境\"选择分析环境",
    },
    "chat.step3": {
        "en": "3. Upload a workflow file or enter a workflow description",
        "zh": "3. 上传流程文件或输入工作流描述",
    },
    "chat.input_placeholder": {
        "en": "Type your question...",
        "zh": "输入您的问题...",
    },
    "settings.env_fix_attempts": {
        "en": "Environment Fix Max Attempts",
        "zh": "环境自动修正最大尝试次数",
    },
    "settings.env_fix_attempts_help": {
        "en": "Maximum number of times the AI agent will retry to fix environment creation failures (1-10).",
        "zh": "AI 智能体在创建环境失败时最多重试的次数 (1-10)。",
    },
    "action.refresh": {
        "en": "↻ Refresh",
        "zh": "&#x1F504; 刷新",
    },
    "workflow.enter_new_name": {
        "en": "Please enter a new workflow name",
        "zh": "请输入新的工作流名称",
    },
    "workflow.enter_or_select_path": {
        "en": "Please enter or select a directory path",
        "zh": "请输入或选择目录路径",
    },
    "workflow.see_preview_panel": {
        "en": "See the preview panel on the right",
        "zh": "请查看右侧预览面板",
    },
    "err.cannot_connect_backend": {
        "en": "Cannot connect to backend service",
        "zh": "无法连接到后端服务",
    },
    "wfc.params_config": {
        "en": "Parameter Configuration",
        "zh": "参数配置",
    },
    "wfc.required_params_short": {
        "en": "Required",
        "zh": "必填参数",
    },
    "wfc.optional_params_short": {
        "en": "Optional",
        "zh": "可选参数",
    },
    "wfc.save_config": {
        "en": "Save Configuration",
        "zh": "保存配置",
    },
    "wfc.external_file": {
        "en": "External File",
        "zh": "外部文件",
    },
    "wfc.internal_file": {
        "en": "Internal File",
        "zh": "内部文件",
    },
    "wfc.cannot_retrieve": {
        "en": "Cannot retrieve parameter info",
        "zh": "无法获取参数信息",
    },
    "wfc.cannot_retrieve_params_alert": {
        "en": "⚠ Cannot retrieve parameter info",
        "zh": "&#x26A0; 无法获取参数信息",
    },
    "wfc.params_failed_alert": {
        "en": "⚠ Parameter query failed; the tool may not be installed",
        "zh": "&#x26A0; 参数查询失败，该工具可能未安装",
    },
    "common.empty": {
        "en": "(empty)",
        "zh": "无内容",
    },
    "settings.general": {
        "en": "General Settings",
        "zh": "通用配置",
    },
    "common.script_saved": {
        "en": "Script saved to project",
        "zh": "脚本已保存到项目",
    },
    "env.config_generated": {
        "en": "Environment configuration generated",
        "zh": "环境配置生成完成",
    },
    "env.config_generated_ok": {
        "en": "Environment configuration generated successfully",
        "zh": "环境配置生成成功",
    },
    "workflow.upload_metadata": {
        "en": "Upload Metadata File",
        "zh": "上传 Metadata 文件",
    },
    "workflow.supports_tsv_csv": {
        "en": "Supports TSV, CSV formats",
        "zh": "支持 TSV, CSV 格式",
    },
    "workflow.enter_desc": {
        "en": "Enter workflow description",
        "zh": "请输入工作流描述",
    },
    "analysis.left_cards": {
        "en": "Left: Analysis Cards",
        "zh": "左侧：分析卡片",
    },
    "common.loading": {
        "en": "Loading...",
        "zh": "加载中...",
    },
    "common.loading_alt": {
        "en": "Loading...",
        "zh": "正在加载...",
    },
    "common.connecting": {
        "en": "Connecting...",
        "zh": "正在连接...",
    },
    "r.select_object": {
        "en": "Select Object",
        "zh": "选择对象",
    },
    "workflow.please_select_workflow": {
        "en": "Please select a workflow",
        "zh": "请选择工作流",
    },
    "workflow.working_dir_help": {
        "en": "Used to store environment configuration files and workflow scripts",
        "zh": "用于存放环境配置文件和工作流脚本",
    },
    "env.manual_here": {
        "en": "MANUAL will appear here",
        "zh": "MANUAL 将显示在这里",
    },
    "r.no_scripts": {
        "en": "No scripts yet. Click \"Refresh Templates\" to load.",
        "zh": "暂无脚本，请点击\"刷新模板\"按钮加载",
    },
    "workflow.select_dir": {
        "en": "Select Directory",
        "zh": "选择目录",
    },
    "workflow.result_preview_short": {
        "en": "Result Preview",
        "zh": "生成结果预览",
    },
    "workflow.open_dir": {
        "en": "Open Directory",
        "zh": "打开目录",
    },
}


def t(key: str, lang: str = DEFAULT_LOCALE) -> str:
    """Translate a key. Falls back to English, then to the key itself."""
    if lang not in LOCALES:
        lang = DEFAULT_LOCALE
    catalog = STRINGS.get(key)
    if not catalog:
        return key
    return catalog.get(lang) or catalog.get(DEFAULT_LOCALE) or key


def get_catalog(lang: str) -> dict:
    """Return the full catalog for the given language.

    Missing translations fall back to English so the frontend always has
    a value for every key.
    """
    if lang not in LOCALES:
        lang = DEFAULT_LOCALE
    en = {k: v["en"] for k, v in STRINGS.items()}
    if lang == "en":
        return en
    return {k: v.get(lang) or v["en"] for k, v in STRINGS.items()}