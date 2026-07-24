# utils/helpers.py
import os
import sys
import platform
import subprocess
from pathlib import Path

def get_data_dir():
    """يرجع مجلد بيانات التطبيق حسب نظام التشغيل."""
    if platform.system() == "Linux":
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    elif platform.system() == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.path.expanduser("~/.snipkeep")
    
    data_dir = Path(base) / "snipkeep"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def copy_to_clipboard(text):
    """ينسخ النص للحافظة عبر أنظمة مختلفة."""
    try:
        if sys.platform == 'linux':
            subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode(), check=False)
        elif sys.platform == 'darwin':
            subprocess.run(['pbcopy'], input=text.encode(), check=False)
    except Exception:
        pass  # فشل صامت، ليست نهاية العالم
