import sys
import json
from pathlib import Path

# r_plot_agent 路径：从 config.py 读取，支持用户配置覆盖
from config import R_PLOT_AGENT_PATH, BASE_DIR, load_user_config

_user_cfg = load_user_config()
_r_plot_path = _user_cfg.get("r_plot_agent_path", None)
if _r_plot_path is None:
    _r_plot_path = R_PLOT_AGENT_PATH  # 使用 config.py 中的默认值（项目内嵌 r_plot_agent）

if _r_plot_path:
    sys.path.insert(0, str(Path(_r_plot_path).resolve()))

from agent import RPlotAgent
from core.aesthetic_mapper import AestheticMapping


class VisualizationManager:
    """连接 RSessionManager 的可视化管理层"""

    def __init__(self, r_session_manager):
        self.r_session_manager = r_session_manager
        self.plot_projects = {}

    def create_project(self, session_id: str, project_dir: str) -> dict:
        """创建可视化项目"""
        viz_dir = Path(project_dir) / "viz_project"
        viz_dir.mkdir(parents=True, exist_ok=True)

        agent = RPlotAgent(str(viz_dir))
        result = agent.create_rproject(str(viz_dir), "plots")

        if result['success']:
            self.plot_projects[session_id] = str(viz_dir)
        return result

    def execute_plot(self, session_id: str, chart_type: str,
                     data_var_name: str, field_mapping: dict,
                     aesthetic_config: dict = None) -> dict:
        """执行绘图"""
        if session_id not in self.plot_projects:
            return {"success": False, "error": "请先创建可视化项目"}

        rproject_path = self.plot_projects[session_id]
        agent = RPlotAgent(rproject_path)

        aesthetic_path = None
        if aesthetic_config:
            config_path = Path(rproject_path) / "aesthetic_config.json"
            aesthetic = AestheticMapping(**aesthetic_config)
            aesthetic.save_to_file(str(config_path))
            aesthetic_path = str(config_path)

        return agent.execute_plot(
            chart_type=chart_type,
            data_name=data_var_name,
            field_mapping=field_mapping,
            aesthetic_config_path=aesthetic_path
        )

    def list_objects(self, session_id: str) -> list:
        """获取 R 会话中的可用对象"""
        return self.r_session_manager.list_objects(session_id)

    def list_figures(self, session_id: str) -> list:
        """列出生成的图片"""
        if session_id not in self.plot_projects:
            return []
        figures_dir = Path(self.plot_projects[session_id]) / "figures"
        if not figures_dir.exists():
            return []
        return [{"name": f.name, "path": str(f), "size": f.stat().st_size}
                for f in figures_dir.glob("*.pdf")]