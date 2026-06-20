"""
scatter_handler.py - 散点图 Handler
"""
from .base_handler import Handler


class ScatterHandler(Handler):
    """散点图 Handler"""

    chart_type = "scatter"

    def get_function_body(self) -> dict:
        return {
            "name": "scatter_plot",
            "description": "二维散点图，用于展示两个变量之间的关系",
            "r_code": """
# 散点图
{obj_name} <- ggplot2::ggplot({data}, ggplot2::aes(x={x}, y={y}{color_clause}{size_clause})) +
    ggplot2::geom_point(alpha=0.7) +
    ggplot2::labs(title="{title}", x="{xlab}", y="{ylab}") +
    ggplot2::theme_minimal()
""",
            "required_params": ["x", "y"],
            "optional_params": ["color", "size", "title", "xlab", "ylab"],
        }

    def _build_params(self, field_mapping: dict, obj_name: str, rproject_path: str) -> dict:
        data_name = f"{obj_name}_data"
        return {
            "data": data_name,
            "x": field_mapping.get("x", "x"),
            "y": field_mapping.get("y", "y"),
            "color_clause": f', color={field_mapping.get("color", "NULL")}' if "color" in field_mapping else "",
            "size_clause": f', size={field_mapping.get("size", "NULL")}' if "size" in field_mapping else "",
            "title": field_mapping.get("title", "Scatter Plot"),
            "xlab": field_mapping.get("xlab", field_mapping.get("x", "X")),
            "ylab": field_mapping.get("ylab", field_mapping.get("y", "Y")),
        }

    def _build_save_code(self, obj_name: str, rproject_path: str) -> str:
        rproject = Path(rproject_path)
        return f'''
# 保存到 .RData
save({obj_name}, file="{rproject}/.RData")

# 保存为 PDF
ggplot2::ggsave(
    filename="{rproject}/figures/{obj_name}.pdf",
    plot={obj_name},
    width=8, height=6
)
'''
