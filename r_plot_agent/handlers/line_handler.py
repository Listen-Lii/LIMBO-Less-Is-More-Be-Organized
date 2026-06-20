"""
line_handler.py - 折线图 Handler
"""
from .base_handler import Handler


class LineHandler(Handler):
    """折线图 Handler"""

    chart_type = "line"

    def get_function_body(self) -> dict:
        return {
            "name": "line_plot",
            "description": "折线图，用于展示趋势变化",
            "r_code": """
{obj_name} <- ggplot2::ggplot({data}, ggplot2::aes(x={x}, y={y}{group_clause}{color_clause})) +
    ggplot2::geom_line() +
    ggplot2::geom_point() +
    ggplot2::labs(title="{title}", x="{xlab}", y="{ylab}") +
    ggplot2::theme_minimal()
""",
            "required_params": ["x", "y"],
            "optional_params": ["group", "color", "title", "xlab", "ylab"],
        }

    def _build_params(self, field_mapping: dict, obj_name: str, rproject_path: str) -> dict:
        data_name = f"{obj_name}_data"
        return {
            "data": data_name,
            "x": field_mapping.get("x", "x"),
            "y": field_mapping.get("y", "y"),
            "group_clause": f', group={field_mapping.get("group", "NULL")}' if "group" in field_mapping else "",
            "color_clause": f', color={field_mapping.get("color", "NULL")}' if "color" in field_mapping else "",
            "title": field_mapping.get("title", "Line Plot"),
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
