# core/sandbox.py
import subprocess
import tempfile
import os
import shutil
from pathlib import Path

class Sandbox:
    TIMEOUT = 10  # ثواني
    MAX_OUTPUT = 10000  # حروف

    def __init__(self):
        self.allowed_languages = {
            "python": {
                "ext": ".py",
                "cmd": ["python3", "{file}"],
                "check": lambda: shutil.which("python3") is not None,
            },
            "bash": {
                "ext": ".sh",
                "cmd": ["bash", "{file}"],
                "check": lambda: shutil.which("bash") is not None,
            },
            "javascript": {
                "ext": ".js",
                "cmd": ["node", "{file}"],
                "check": lambda: shutil.which("node") is not None,
            },
        }

    def run(self, code, language):
        """ينفذ الكود في بيئة معزولة."""
        if language not in self.allowed_languages:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"لغة غير مدعومة: {language}. اللغات المدعومة: {list(self.allowed_languages.keys())}",
                "exit_code": -1,
            }
        
        lang_info = self.allowed_languages[language]
        
        if not lang_info["check"]():
            return {
                "success": False,
                "stdout": "",
                "stderr": f"مفسر {language} غير موجود على النظام.",
                "exit_code": -1,
            }

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / f"script{lang_info['ext']}"
            
            with open(filepath, 'w') as f:
                f.write(code)
            
            filepath.chmod(0o700)
            
            try:
                cmd = [arg.format(file=str(filepath)) for arg in lang_info["cmd"]]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.TIMEOUT,
                    cwd=tmpdir,
                    env={
                        "HOME": tmpdir,
                        "PATH": "/usr/bin:/bin:/usr/local/bin",
                        "USER": "sandbox",
                        "LANG": "C.UTF-8",
                    },
                )
                
                stdout = result.stdout[:self.MAX_OUTPUT]
                stderr = result.stderr[:self.MAX_OUTPUT]
                
                if len(result.stdout) > self.MAX_OUTPUT:
                    stdout += "\n... (مقتطع)"
                if len(result.stderr) > self.MAX_OUTPUT:
                    stderr += "\n... (مقتطع)"
                
                return {
                    "success": result.returncode == 0,
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": result.returncode,
                }
                
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"⏰ المقتطف استغرق أكثر من {self.TIMEOUT} ثواني وتم إنهاؤه.",
                    "exit_code": -1,
                }
            except Exception as e:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"خطأ في التشغيل: {str(e)}",
                    "exit_code": -1,
                }
