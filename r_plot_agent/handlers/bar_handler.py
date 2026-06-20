"""
bar_handler.py - 条形图 Handler
"""
from .base_handler import Handler


class BarHandler(Handler):
    """条形图 Handler"""

    chart_type = "bar"

    def get_function_body(self) -> dict:
        return {
            "name": "bar_plot",
            "description": "条形图，用于展示分类变量的数值分布",
            "r_code": """
{obj_name} <- ggplot2::ggplot({data}, ggplot2::aes(x={x}, y={y}{fill_clause})) +
    ggplot2::geom_bar(stat="identity", position="dodge") +
    ggplot2::labs(title="{title}", x="{xlab}", y="{ylab}") +
    ggplot2::theme_minimal()
""",
            "required_params": ["x", "y"],
            "optional_params": ["fill", "title", "xlab", "ylab"],
        }

    def _build_params(self, field_mapping: dict, obj_name: str, rproject_path: str) -> dict:
        data_name = f"{obj_name}_data"
        return {
            "data": data_name,
            "x": field_mapping.get("x", "x"),
            "y": field_mapping.get("y", "y"),
            "fill_clause": f', fill="{field_mapping.get("fill", "NULL")}"' if "fill" in field_mapping else "",
            "title": field_mapping.get("title", "Bar Plot"),
            "xlab": field_mapping.get("xlab", field_mapping.get("x", "X")),
            "ylab": field_mapping.get("ylab", field_mapping.get("y", "Y")),
        }

    def _build_save_code(self, obj_name: str, rproject_path: str) -> str:
        rproject = Path(rproject_path)
        return f'''
save({obj_name}, file="{rproject}/.RData")
ggplot2::ggsave(
    filename="{rproject}/figures/{obj_name}.pdf",
    plot={obj_name},
    width=8, height=6
)
'''
