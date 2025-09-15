from flask import Flask, request, render_template
import pandas as pd
import subprocess  # 用于调用外部Python脚本

'''
project/
├── app.py                # 主程序
├── data.csv              # CSV数据文件
├── scripts/              # 存放可调用的Python脚本
│   ├── script1.py        # 示例脚本1
│   ├── script2.py        # 示例脚本2
│   └── script3.py        # 示例脚本3
└── templates/
    ├── index.html        # 主页面
    └── results.html      # CSV查询结果页

'''
app = Flask(__name__)

# 示例元组数据（可替换为你的实际数据）
options_data = (
    ("getaijinggu_byall", "多个游资"),
    ("getaijinggu_byname", "T 王"),
    ("script3", "执行脚本3")
)

@app.route("/", methods=["GET", "POST"])
def index():
    selected_script = None
    if request.method == "POST":
        # 处理CSV查询
        if "search_key" in request.form:
            search_key = request.form.get("search_key")
            df = pd.read_csv("D:\\python\\showstocksT\\cvs_search_app\\aijinggu_all.csv", dtype=str)
            if search_key:
                # 在多个列中搜索（Name和City列）
                columns_to_search = ['上榜日期', '证券号码', '游资名称']
                results = df[df[columns_to_search].apply(lambda row: any(str(search_key).lower() in str(cell).lower() for cell in row), 
                    axis=1)]
            else:
                results = df  # all结果
            return render_template("results.html", results=results.to_html(classes="table"), search_key=search_key)
        
        # 处理脚本执行
        elif "script_name" in request.form:
            selected_script = request.form.get("script_name")          
            try:
                # 调用外部Python脚本（例如：scripts/selected_script.py）
                result = subprocess.run(
                    ["python", f"D:\\python\\showstocksT\\cvs_search_app\\scripts/{selected_script}.py"], 
                    capture_output=True, 
                    text=True
                )
                output = result.stdout if result.returncode == 0 else f"错误: {result.stderr}"
                return render_template("index.html", options=options_data, script_output=output)
            except Exception as e:
                return render_template("index.html", options=options_data, script_output=f"执行失败: {str(e)}")

    return render_template("index.html", options=options_data)

if __name__ == "__main__":
    import os
    os.makedirs("scripts", exist_ok=True)  # 确保scripts目录存在
    app.run(debug=True)