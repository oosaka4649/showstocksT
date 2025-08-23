# app.py
from flask import Flask, request, render_template
import pandas as pd

app = Flask(__name__)

# 读取CSV文件（确保data.csv在同一目录）
df = pd.read_csv("data.csv")

@app.route("/", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        search_key = request.form.get("search_key")
        results = df[df.apply(lambda row: str(search_key).lower() in str(row).lower(), axis=1)]
        return render_template("results.html", results=results.to_html(classes="table"), search_key=search_key)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)