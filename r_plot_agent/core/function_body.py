"""
function_body.py - 函数体提取/解析规则

conductor 使用这些规则从材料中提取函数体。
"""


def extract_function_body(material: dict) -> dict:
    """
    从材料中提取函数体：解析 R 代码、参数列表

    Args:
        material: 包含 R 代码的材料

    Returns:
        dict: 函数体定义
    """
    return {
        "name": material.get("name", "unnamed"),
        "description": material.get("description", ""),
        "r_code": material.get("r_code", ""),
        "required_params": material.get("params", []),
        "optional_params": material.get("optional_params", {}),
    }


def validate_function_body(fb: dict) -> bool:
    """验证函数体完整性"""
    required_fields = ["name", "r_code", "required_params"]
    return all(field in fb and fb[field] for field in required_fields)


def render_function_body(fb: dict, params: dict) -> str:
    """
    根据参数渲染函数体 R 代码

    Args:
        fb: 函数体定义
        params: 参数字典

    Returns:
        str: 渲染后的 R 代码
    """
    r_code = fb["r_code"]
    for key, value in params.items():
        placeholder = "{" + key + "}"
        if placeholder in r_code:
            r_code = r_code.replace(placeholder, str(value))
    return r_code
