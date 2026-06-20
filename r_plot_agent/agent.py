"""
agent.py - R Plot Agent 主入口

协调 conductor 和 r_engine 执行绘图任务。
"""
import uuid
from pathlib import Path

from core.function_body import extract_function_body
from core.aesthetic_mapper import AestheticMapping
from handlers.registry import get_handler
from utils.r_runner import RRunner


class RPlotAgent:
    """R 绘图 Agent"""

    def __init__(self, rproject_path: str = None):
        if rproject_path:
            self.rproject_path = Path(rproject_path)
        else:
            self.rproject_path = None
        self.r_runner = RRunner()

    @staticmethod
    def create_rproject(project_path: str, project_name: str = None) -> dict:
        """
        创建新的 RStudio Project

        Args:
            project_path: 项目路径
            project_name: 项目名称（默认使用目录名）

        Returns:
            dict: 创建结果
        """
        project_path = Path(project_path)

        if project_name is None:
            project_name = project_path.name

        try:
            # 创建目录结构
            project_path.mkdir(parents=True, exist_ok=True)
            (project_path / "figures").mkdir(exist_ok=True)
            (project_path / "scripts").mkdir(exist_ok=True)
            (project_path / "data").mkdir(exist_ok=True)

            # 创建 .Rproj 文件
            rproj_content = f'''Version: 1.0

RestoreWorkspace: default
SaveWorkspace: default
AlwaysSaveHistory: default

EnableCodeIndexing: yes
UseSpacesForTab: yes
NumSpacesForTab: 4
Encoding: UTF-8

RnwWeave: Sweave
LaTeK: pdfLaTeK
'''
            rproj_path = project_path / f"{project_name}.Rproj"
            rproj_path.write_text(rproj_content, encoding="utf-8")

            # 创建 .RData（空的 R 工作空间）
            (project_path / ".RData").write_bytes(b"")

            # 创建 .Rhistory
            (project_path / ".Rhistory").write_text("", encoding="utf-8")

            return {
                "success": True,
                "project_path": str(project_path),
                "rproj_path": str(rproj_path),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def set_rproject(self, rproject_path: str):
        """设置当前 R Project 路径"""
        self.rproject_path = Path(rproject_path)
        self._setup_rproject()

    def _setup_rproject(self):
        """初始化 R Project 目录结构"""
        if self.rproject_path is None:
            raise ValueError("R Project 路径未设置，请先调用 create_rproject() 或 set_rproject()")
        (self.rproject_path / "figures").mkdir(parents=True, exist_ok=True)
        (self.rproject_path / "scripts").mkdir(parents=True, exist_ok=True)
        (self.rproject_path / "data").mkdir(parents=True, exist_ok=True)

    def execute_plot(
        self,
        chart_type: str,
        data_name: str,
        field_mapping: dict,
        aesthetic_config_path: str = None,
    ) -> dict:
        """
        执行绘图

        Args:
            chart_type: 图表类型（如 scatter, bar, line）
            data_name: 数据对象名称
            field_mapping: 字段映射，如 {"x": "gdp", "y": "life_exp"}
            aesthetic_config_path: 美学配置文件路径

        Returns:
            dict: 执行结果
        """
        try:
            # 1. 获取 handler
            handler = get_handler(chart_type)

            # 2. 生成 R 脚本
            r_code = handler.render(
                data=data_name,
                field_mapping=field_mapping,
                aesthetic_config_path=str(aesthetic_config_path) if aesthetic_config_path else None,
                rproject_path=str(self.rproject_path),
            )

            # 3. 保存脚本
            script_path = self.rproject_path / "scripts" / f"{handler.name}.r"
            script_path.parent.mkdir(parents=True, exist_ok=True)
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(r_code)

            # 4. 执行脚本
            success, stdout, stderr = self.r_runner.run_script(
                str(script_path),
                str(self.rproject_path),
            )

            return {
                "success": success,
                "script_path": str(script_path),
                "stdout": stdout,
                "stderr": stderr,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def create_aesthetic_config(
        self,
        output_path: str = None,
        theme: str = "minimal",
        **kwargs,
    ) -> str:
        """
        创建美学配置文件

        Args:
            output_path: 输出路径，默认保存到 R Project
            **kwargs: AestheticMapping 的其他参数

        Returns:
            str: 配置文件路径
        """
        if output_path is None:
            output_path = self.rproject_path / "aesthetic_config.json"

        aesthetic = AestheticMapping(theme=theme, **kwargs)
        aesthetic.save_to_file(str(output_path))

        return str(output_path)
