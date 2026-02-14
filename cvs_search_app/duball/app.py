"""
独立的 duball Flask 应用示例。
- 放在 cvs_search_app/duball/app.py
- 可与主目录下的 app.py 并存并分别运行（默认端口 5001）
用法：
    python app.py
或设置环境变量修改端口：
    set DUBALL_APP_PORT=5002 && python app.py    (Windows PowerShell/CMD)
"""

import os
import sys
from pathlib import Path
from flask import Flask, jsonify, render_template, request

''' 
# 可选：把项目根目录加入 sys.path，以便按需导入上级模块
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# 将模板目录指向主工程的 templates 文件夹，这样可以复用主应用的 index.html
templates_dir = str(project_root / 'templates')

app = Flask(__name__, template_folder=templates_dir)
'''
app = Flask(__name__)


# 尝试导入共享配置（非必须）
try:
    from minitools import user_config as ucfg  # type: ignore
except Exception:
    ucfg = None

@app.route("/", methods=["GET", "POST"])
def index():
    script_output = "test"
    return render_template('index.html', script_output=script_output)

if __name__ == '__main__':
    port = int(os.environ.get('DUBALL_APP_PORT', 5001))
    # debug=True 仅在本地开发时使用，生产请关闭
    app.run(host='127.0.0.1', port=port, debug=True)
