"""
handlers/registry.py - Handler 注册表

r_engine 根据图表类型查找对应 handler。
"""
from .scatter_handler import ScatterHandler
from .bar_handler import BarHandler
from .line_handler import LineHandler


# Handler 注册表
HANDLER_REGISTRY = {
    "scatter": ScatterHandler,
    "bar": BarHandler,
    "line": LineHandler,
}


def get_handler(chart_type: str):
    """获取指定图表类型的 Handler 类"""
    handler_class = HANDLER_REGISTRY.get(chart_type)
    if handler_class is None:
        raise ValueError(f"Unknown chart type: {chart_type}")
    return handler_class()


def list_chart_types() -> list:
    """列出所有支持的图表类型"""
    return list(HANDLER_REGISTRY.keys())
