"""
base_handler.py - Handler 基类

Handler = 函数体 + 参数规范
conductor 制作，r_engine 调用执行。
"""
from abc import ABC, abstractmethod
from pathlib import Path
import uuid

from core.function_body import render_function_body
from core.data_mapper import validate_field_mapping
from core.aesthetic_mapper import AestheticMapping


class Handler(ABC):
    """Handler 基类 - conductor 制作的方案实体"""

    chart_type: str = ""

    def __init__(self, name: str = None):
        self.id = str(uuid.uuid4())[:8]
        self.name = name or f"{self.chart_type}_handler"

    @abstractmethod
    def get_function_body(self) -> dict:
        """返回函数体定义"""
        pass

    def render(
        self,
        data,
        field_mapping: dict,
        aesthetic_config_path: str,
        rproject_path: str,
    ) -> str:
        """
        渲染 R 脚本

        Args:
            data: 数据对象
            field_mapping: 实际字段映射，如 {"x": "gdp", "y": "life_exp"}
            aesthetic_config_path: 美学配置文件路径
            rproject_path: R Project 路径

        Returns:
            str: 渲染后的 R 脚本
        """
        fb = self.get_function_body()

        # 校验字段映射（根据函数体推断参数规范）
        valid, errors = validate_field_mapping(field_mapping, fb)
        if not valid:
            raise ValueError(f"字段映射错误: {errors}")

        # 生成对象名称
        obj_name = f"{self.chart_type}_plot_{self.id}"

        # 构建参数
        params = self._build_params(field_mapping, obj_name, rproject_path)

        # 渲染函数体
        r_code = render_function_body(fb, params)

        # 添加美学映射
        if aesthetic_config_path and Path(aesthetic_config_path).exists():
            aesthetic = AestheticMapping.load_from_file(aesthetic_config_path)
            r_code += "\n" + aesthetic.to_r_code()

        # 添加保存命令
        r_code += self._build_save_code(obj_name, rproject_path)

        return r_code

    @abstractmethod
    def _build_params(self, field_mapping: dict, obj_name: str, rproject_path: str) -> dict:
        """构建参数字典"""
        pass

    @abstractmethod
    def _build_save_code(self, obj_name: str, rproject_path: str) -> str:
        """构建保存代码（.RData + PDF）"""
        pass

    def to_dict(self) -> dict:
        """导出为字典"""
        return {
            "name": self.name,
            "chart_type": self.chart_type,
            "function_body": self.get_function_body(),
        }
