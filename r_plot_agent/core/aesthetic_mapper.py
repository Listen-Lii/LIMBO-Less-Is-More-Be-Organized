"""
aesthetic_mapper.py - 美学映射（全局共享）

提供美学映射配置，独立文件存储。
"""
import json
from pathlib import Path
from typing import List, Dict, Any


class AestheticMapping:
    """美学映射基类 — 封装视觉配置"""

    def __init__(
        self,
        theme: str = "classic",
        color_palette: List[str] = None,
        font_family: str = "Helvetica",
        font_size: float = 12,
        plot_width: float = 8,
        plot_height: float = 6,
        legend_position: str = "right",
        grid_lines: str = "major",
        colorblind_safe: bool = True,
        axis_label_size: float = 11,
        title_size: float = 14,
        **kwargs,
    ):
        self.theme = theme
        self.color_palette = color_palette or [
            "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2",
            "#D55E00", "#CC79A7", "#999999"
        ]
        self.font_family = font_family
        self.font_size = font_size
        self.plot_width = plot_width
        self.plot_height = plot_height
        self.legend_position = legend_position
        self.grid_lines = grid_lines
        self.colorblind_safe = colorblind_safe
        self.axis_label_size = axis_label_size
        self.title_size = title_size
        self.extra = kwargs

    def to_r_code(self) -> str:
        """生成 R 美学配置代码"""
        parts = []

        # 主题
        if self.theme == "minimal":
            parts.append("theme_minimal()")
        elif self.theme == "bw":
            parts.append("theme_bw()")
        elif self.theme == "dark":
            parts.append("theme_dark()")
        else:
            parts.append("theme_classic()")

        # 图形尺寸
        parts.append(f'ggsave(width={self.plot_width}, height={self.plot_height})')

        return "\n".join(parts)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "theme": self.theme,
            "color_palette": self.color_palette,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "plot_width": self.plot_width,
            "plot_height": self.plot_height,
            "legend_position": self.legend_position,
            "grid_lines": self.grid_lines,
            "colorblind_safe": self.colorblind_safe,
            "axis_label_size": self.axis_label_size,
            "title_size": self.title_size,
            **self.extra,
        }

    def save_to_file(self, path: str):
        """保存为 JSON 文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def load_from_file(path: str) -> "AestheticMapping":
        """从文件加载"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AestheticMapping(**data)

    @staticmethod
    def get_color_palette_r() -> str:
        """获取 R 配色的调色板名称"""
        # 色觉友好配色
        return '"Set2"'  # R 中的色觉友好调色板
