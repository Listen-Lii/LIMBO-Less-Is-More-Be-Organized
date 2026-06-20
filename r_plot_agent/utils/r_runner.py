"""
r_runner.py - R 脚本执行器

使用 Rscript 执行 R 脚本。
"""
import subprocess
from pathlib import Path


class RRunner:
    """R 脚本执行器"""

    def __init__(self, rscript_path: str = "Rscript"):
        self.rscript_path = rscript_path

    def run_script(self, script_path: str, rproject_path: str = None) -> tuple:
        """
        执行 R 脚本

        Args:
            script_path: R 脚本路径
            rproject_path: R Project 路径（用于设置工作目录）

        Returns:
            tuple: (是否成功, stdout, stderr)
        """
        script_path = Path(script_path)
        if not script_path.exists():
            return (False, "", f"Script not found: {script_path}")

        cmd = [self.rscript_path, str(script_path)]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(rproject_path) if rproject_path else None,
            )
            success = result.returncode == 0
            return (success, result.stdout, result.stderr)
        except Exception as e:
            return (False, "", str(e))

    def run_code(self, r_code: str, rproject_path: str = None) -> tuple:
        """
        直接执行 R 代码

        Args:
            r_code: R 代码字符串
            rproject_path: R Project 路径

        Returns:
            tuple: (是否成功, stdout, stderr)
        """
        # 将代码写入临时脚本
        temp_script = Path(rproject_path or ".") / "scripts" / f"temp_{id(r_code)}.r"
        temp_script.parent.mkdir(parents=True, exist_ok=True)

        with open(temp_script, "w", encoding="utf-8") as f:
            f.write(r_code)

        result = self.run_script(str(temp_script), rproject_path)

        # 清理临时脚本
        try:
            temp_script.unlink()
        except:
            pass

        return result
