# setup dos pacotes

import subprocess
import sys
from pathlib import Path

req = Path("requirements.txt")
if req.exists():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req)])
    
# rodar popdados.py
# streamlit run interface.py
