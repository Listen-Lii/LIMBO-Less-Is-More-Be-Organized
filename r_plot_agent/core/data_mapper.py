"""
data_mapper.py - 数据映射规范提取工具

从函数体中提取数据映射规范的方法。
"""

def extract_from_function_body(function_body: dict) -> dict:
    """
    从函数体中提取数据映射规范

    分析函数体的参数列表和 R 代码，推断各参数的数据类型和含义。

    Args:
        function_body: 函数体定义

    Returns:
        dict: 数据映射规范 {参数名: {type, description}}
    """
    required_params = function_body.get("required_params", [])
    r_code = function_body.get("r_code", "")

    datamapper = {}

    for param in required_params:
        # 根据参数名和代码上下文推断类型和含义
        spec = _infer_param_spec(param, r_code)
        datamapper[param] = spec

    return datamapper


def _infer_param_spec(param: str, r_code: str) -> dict:
    """
    根据参数名和 R 代码推断参数规范

    Args:
        param: 参数名
        r_code: R 代码

    Returns:
        dict: {type, description}
    """
    # 常见参数名到类型的映射
    type_map = {
        "x": {"type": "numeric", "description": "X轴变量"},
        "y": {"type": "numeric", "description": "Y轴变量"},
        "z": {"type": "numeric", "description": "Z轴变量（三维图）"},
        "color": {"type": "categorical", "description": "颜色分组"},
        "fill": {"type": "categorical", "description": "填充颜色"},
        "size": {"type": "numeric", "description": "大小映射"},
        "shape": {"type": "categorical", "description": "形状分组"},
        "alpha": {"type": "numeric", "description": "透明度（0-1）"},
        "group": {"type": "categorical", "description": "分组变量"},
        "label": {"type": "string", "description": "标签文本"},
        "weight": {"type": "numeric", "description": "权重变量"},
        "bins": {"type": "integer", "description": "分箱数量"},
        "width": {"type": "numeric", "description": "宽度"},
        "height": {"type": "numeric", "description": "高度"},
    }

    # 位置参数推断
    if param in ["x", "y", "z"]:
        if "aes" in r_code or "ggplot" in r_code:
            if param == "x":
                return {"type": "numeric", "description": "X轴变量（通常是连续变量）"}
            elif param == "y":
                return {"type": "numeric", "description": "Y轴变量"}

    return type_map.get(param, {"type": "unknown", "description": f"参数{param}"})


def validate_field_mapping(field_mapping: dict, function_body: dict) -> tuple:
    """
    根据数据映射规范校验字段映射

    Args:
        field_mapping: 实际字段映射，如 {"x": "gdp", "y": "life_exp"}
        function_body: 函数体定义（从中提取 datamapper）

    Returns:
        tuple: (是否有效, 错误信息列表)
    """
    datamapper = extract_from_function_body(function_body)
    errors = []

    for param, spec in datamapper.items():
        if param in field_mapping:
            expected_type = spec.get("type", "unknown")
            if expected_type == "unknown":
                errors.append(f"参数 {param} 类型未知")

    return (len(errors) == 0, errors)
