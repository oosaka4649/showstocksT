# showstocksT
用于读取网站爬取的T王或其他的历史数据保存到cvs文件里，并通过浏览器显示
csv_search_app/
├── app.py                # Flask 主程序
├── data.csv              # 示例CSV数据文件
└── templates/
    ├── index.html        # 查询页面
    └── results.html      # 结果展示页面
    
解压后运行：
unzip csv_search_app.zip
cd
 csv_search_app
python app.py
2. 访问浏览器：
打开 `http://127.0.0.1:5000` 即可使用
3. 替换数据：
修改 `data.csv` 或替换为您自己的CSV文件（保持列名不变）
￼
技术栈
• 后端：Python + Flask
• 前端：HTML + Bootstrap 5
• 数据处理：pandas