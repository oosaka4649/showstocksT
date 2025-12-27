from flask import Flask, request, render_template
import pandas as pd
import re
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import subprocess  # 用于调用外部Python脚本
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
import minitools.user_config as ucfg
from scripts.RootInfo import MainUtile as utile
from scripts.ReadTDXDayFileToCSV import DayFileToCsv as DayToCsv
from scripts.vectorbt_backtest import simple_backtest as simple_backtest
from scripts.vectorbt_backtest_all import vectorbt_back_test as all_backtest
'''
project/
├── app.py                # 主程序
├── data.csv              # CSV数据文件
├── scripts/              # 存放可调用的Python脚本
│   ├── script1.py        # 示例脚本1
└── templates/
    ├── index.html        # 主页面
    └── results.html      # CSV查询结果页

'''
app = Flask(__name__)

# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
aijinggu_csv_path = os.path.join(current_dir, 'data', 'aijinggu.csv')
scripts_path = os.path.join(current_dir, 'scripts', 'getaijinggu_byall.py')
scripts_k_line_path = os.path.join(current_dir, 'minitools', 'showKLine.py')
scripts_mystocks_k_line_path = os.path.join(current_dir, 'minitools', 'showKLine_week.py')
stocks_csv_dir = os.path.join(current_dir, 'stockscsv')
tdx_day_file_path = 'C:\\zd_zsone\\vipdoc\\'  # tdx路径

my_stocks_list = ucfg.my_stocks_list
my_stocks_html_folder_name = ucfg.my_stocks_html_folder_name

#在画面显示一个个check box，返回选择的（和配置的config 文件对应的 list key），并生成k线html，并显示
#后面可以添加项目
checkbox_items = [
    {'id': 'my_stocks_list', 'name': '我的自选'},
    {'id': 'neng_yuan_list', 'name': '能源金属'},
    {'id': 'you_se_list', 'name': '有色金属'},
    {'id': 'ban_dao_ti_list', 'name': '半导体'}
]

@app.route("/", methods=["GET", "POST"])
def index():
    selected_script = None
    if request.method == "POST":
        # 处理CSV查询
        if "search_key" in request.form:
            search_key = request.form.get("search_key")
            df = pd.read_csv(aijinggu_csv_path, dtype=str)
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
                    ["python", scripts_path], 
                    capture_output=True, 
                    text=True
                )
                output = result.stdout if result.returncode == 0 else f"错误: {result.stderr}"
                if output == None or output.strip() == '':
                    output = '游资信息已经更新，请在上面输入查询内容或直接点击上面查询按钮。'
                return render_template("index.html", items=checkbox_items, script_output=output)
            except Exception as e:
                return render_template("index.html", items=checkbox_items, script_output=f"执行失败: {str(e)}")

    return render_template("index.html", items=checkbox_items)

@app.route("/sortbydateandcode", methods=["GET", "POST"])
def sortbydateandcode():
    try:
        search_key = None
        df = pd.read_csv(aijinggu_csv_path, dtype=str)
        results = df
        # 处理CSV查询
        if "search_key" in request.form:
            search_key = request.form.get("search_key")
            # 保留过滤结果
            if search_key:
                # 在多个列中搜索（Name和City列）
                columns_to_search = ['上榜日期', '证券号码', '游资名称']
                results = df[df[columns_to_search].apply(lambda row: any(str(search_key).lower() in str(cell).lower() for cell in row), 
                    axis=1)]
                
                #显示该股票的k line图
                # 调用外部Python脚本（例如：scripts/selected_script.py）
                result = subprocess.run(
                    ["python", scripts_k_line_path, search_key], 
                    capture_output=True, 
                    text=True
                )
                output = result.stdout if result.returncode == 0 else f"错误: {result.stderr}"
                print(f"showKLine.py output: {output}")
                stock_dashboard_div = stock_dashboard(search_key)
                
        #按请求排序
        sort_by = '上榜日期'  # 你可以根据需要更改排序列'
        if sort_by in df.columns:
            results = results.sort_values(by=['上榜日期', '证券号码'], ascending=[False, False]) # 你可以根据需要更改排序列'
            
            
        # 按分组列分组并计算指定列
        group_column=['游资名称']
        calc_column='净买入（万）'
        # 清洗计算列中的汉字字符
        results[calc_column] = results[calc_column].apply(clean_numeric_string)
        sum_result = results.groupby(group_column)[calc_column].sum().reset_index()
        sum_result_date = results.groupby(['上榜日期'])[calc_column].sum().reset_index()
        sum_result_date = sum_result_date.sort_values(by=['上榜日期'], ascending=[False]) # 你可以根据需要更改排序列'
        
        return render_template("results.html", results=results.to_html(classes="table"), search_key=search_key, kline_div=stock_dashboard_div,
                               script_output=f"按游资名称统计结果: {str(sum_result)}", script_output_date=f"按日期统计结果: {str(sum_result_date)}")
    except Exception as e:
        return render_template("index.html", script_output=f"执行失败: {str(e)}")

@app.route("/help", methods=["GET", "POST"])
def help():
    return render_template("help.html")


#####  ################################ show multiple stock html ##################################################
# 将批处理生成的html，读取 templates/stockhtml 文件夹下的所有 HTML 文件，并显示在一个页面中
# todo 下步，添加一个 爬虫 script，生成各种 股票的 代码 list 集中生成html文件
@app.route("/showhtml", methods=["GET", "POST"])
def showhtml():
    selected_ids = request.form.getlist('item_checkbox')
    folder_path = os.path.join(current_dir, 'templates', 'stockhtml') # 目标文件夹路径
    extension = '.html'            # 指定后缀名
    # 清空获取文件名列表
    html_files = [f'{f}' for f in os.listdir(folder_path) if f.endswith(extension)]
    for f in html_files:
        os.remove(os.path.join(folder_path, f))       
    # 获取文件名列表
    html_files = [f'stockhtml/{f}' for f in os.listdir(folder_path) if f.endswith(extension)]    
    return render_template('showhtmllist.html', files_list=html_files)

#####  ################################ show multiple stock html ##################################################
# 调用 showkline_week.py 生成我关注的股票的html，然后显示在一个页面中
@app.route("/showmyhtml", methods=["GET", "POST"])
def showmyhtml():
    selected_ids = request.form.getlist('item_checkbox')

    show_list = my_stocks_list

    if selected_ids and len(selected_ids) > 0:
        show_list = []
        for list_id in selected_ids:
            if hasattr(ucfg, list_id):
                show_list.extend(getattr(ucfg, list_id))

    folder_path = os.path.join(current_dir, 'templates', my_stocks_html_folder_name) # 目标文件夹路径
    extension = '.html'            # 指定后缀名
    # 清空获取文件名列表
    html_files = [f'{f}' for f in os.listdir(folder_path) if f.endswith(extension)]
    for f in html_files:
        os.remove(os.path.join(folder_path, f))    
    # 调用 showKLine_week.py 生成我关注的股票的html
    try: 
        for file_name in show_list :
            result = subprocess.run(
                ["python", scripts_mystocks_k_line_path , file_name], 
                capture_output=True, 
                text=True
            )
        output = result.stdout if result.returncode == 0 else f"错误: {result.stderr}"
        print(f"showKLine_week.py output: {output}")
    except Exception as e:
        return render_template("showhtmllist.html", script_output=f"执行失败: {str(e)}")
    html_files = [f'{my_stocks_html_folder_name}/{f}' for f in os.listdir(folder_path) if f.endswith(extension)]
    return render_template('showhtmllist.html', files_list=html_files, script_output=f"执行股票数：{len(show_list)} \n执行结果: {str(output)}")
    
def clean_numeric_string(value):
    """
    清洗包含汉字的数值字符串，转换为浮点数，保留负号
    
    参数:
    value (str): 可能包含汉字的数值字符串
    
    返回:
    float: 转换后的数值
    """
    # 使用正则表达式提取数字部分（包括负号和小数点）
    match = re.search(r'-?\d+\.?\d*', str(value))
    if match:
        return float(match.group())
    return 0.0

#################################### back test detail ##################################################
@app.route("/backtest", methods=["GET", "POST"])
def vectorbt_backtest():
    try:
        if request.args['search_key'] is not None and request.args['search_key'] != '':
            search_key = request.args['search_key']
            if len(search_key) != 6 or not search_key.isdigit():
                return render_template("index.html", script_output="请输入正确的6位股票代码，例如：600475")
            
            stock_prefix = utile.get_stock_prefix(search_key)

            # 调用 backtest 脚本
            file_path = os.path.join(stocks_csv_dir, f'{stock_prefix}{search_key}.csv')  # 假设文件名格式为 sh600475.csv
            if not os.path.exists(file_path):
                return render_template("index.html", script_output=f"股票数据文件不存在: {file_path}")
            sum_result, pf = simple_backtest(file_path)
            if pf is None:
                return render_template("index.html", script_output=f"回测失败: {str(sum_result)}")  
     
            #显示该股票的回测结果图
            stock_back_test_div = pf.plot().to_html(include_plotlyjs='cdn')
            # 读取回测结果详细
            backtest_detail = pf.trades.records_readable
        return render_template("results_backtest_detail.html", results_detail=backtest_detail.to_html(classes="table"), search_key=search_key, back_test_div=stock_back_test_div,
                               script_output=f"{str(sum_result)}")
    except Exception as e:
        return render_template("index.html", script_output=f"执行失败: {str(e)}")
    
#################################### back test detail ##################################################

#################################### back test all ##################################################
@app.route("/backtestall", methods=["GET", "POST"])
def backtestall():
    try:
        if "search_key" in request.form:
            search_key = request.form.get("search_key")
            back_type = request.form.get("back_type", default=1, type=int)
            if len(search_key) != 6 or not search_key.isdigit():
                return render_template("index.html", script_output="请输入正确的6位股票代码，例如：600475")
            
            stock_prefix = utile.get_stock_prefix(search_key)

            # 调用 backtest 股票数据文件
            file_path = os.path.join(stocks_csv_dir, f'{stock_prefix}{search_key}.csv')  # 假设文件名格式为 sh600475.csv
            if not os.path.exists(file_path):
                return render_template("index.html", script_output=f"股票数据文件不存在: {file_path}")
            
            #该股票的回测
            vect_back_test_all = all_backtest(file_path, back_type)
            sum_result, pf = vect_back_test_all.simple_backtest()
            if pf is None:
                return render_template("index.html", script_output=f"回测失败: {str(sum_result)}")  
     
            #显示该股票的回测结果图
            stock_back_test_div = pf.plot().to_html(include_plotlyjs='cdn')
            # 读取回测结果详细
            backtest_detail = pf.trades.records_readable
        return render_template("results_backtest_detail.html", results_detail=backtest_detail.to_html(classes="table"), search_key=search_key, back_test_div=stock_back_test_div,
                               script_output=f"{str(sum_result)}")
    except Exception as e:
        return render_template("index.html", script_output=f"执行失败: {str(e)}")
    
#################################### back test all ##################################################

'''
根据股票代码，读取通达信day文件，转换成csv文件，并生成K线图的HTML
'''
def convert_day_to_csv(stock_prefix, stock_code):
    # 这里可以添加转换逻辑，将TDX文件转换为CSV格式
    # 例如，读取TDX文件并将其转换为DataFrame，然后保存为CSV
    t_day_file = f"{tdx_day_file_path}\\{stock_prefix}\\lday\\{stock_prefix}{stock_code}.day"  # 示例路径，{0}为市场前缀，{1}为股票代码 'C:\\zd_zsone\\vipdoc\\sh\\lday\\sh600475.day'
    tocsv = DayToCsv(t_day_file)
    tocsv.transform_data_one(tocsv.day_file, tocsv.target_dir)
    csv_file_full_path = tocsv.getCsvFilePath()
    return csv_file_full_path


'''
将生成的 Plotly K线图嵌入到现有 HTML 文件的 div 中，而不是生成完整的 HTML 文件。
'''
# 读取股票CSV文件（示例路径，请替换为实际文件路径）
def load_stock_data(file_path):
    """
    读取股票CSV文件并处理为适合绘图的格式
    要求CSV包含列：Date, Open, High, Low, Close, Volume (大小写不敏感)
    """
    df = pd.read_csv(file_path)
    # 统一列名大小写
    #df.columns = df.columns.str.lower()
    # 转换日期格式
    #if 'date' in df.columns:
    df[utile.CSV_HEADER_INFO[0]] = pd.to_datetime(df[utile.CSV_HEADER_INFO[0]])
    df.set_index(utile.CSV_HEADER_INFO[0], inplace=True)
    return df

def stock_dashboard(stock_code):
    if len(stock_code) != 6 or not stock_code.isdigit():
        return None
    print(f"读取股票数据文件: kline.html")

    kline_div = os.path.join(current_dir, 'templates'), 'kline.html'
            
    #stock_prefix = utile.get_stock_prefix(stock_code)
    
    # 转换day文件到csv文件
    #t_csv_path = convert_day_to_csv(stock_prefix, stock_code)
    """生成股票K线图的HTML div字符串"""
    #print(f"读取股票数据文件: {t_csv_path}")
    #stock_df = load_stock_data(t_csv_path)
    #kline_div = get_kline_div_string(stock_df)
    return kline_div

#不用了
def get_kline_div_string(df):
    """
    生成K线图的HTML div字符串（不包含完整HTML结构）
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        specs=[[{"type": "scatter"}], [{"type": "bar"}]]
    )
    
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df[utile.CSV_HEADER_INFO[1]],
        high=df[utile.CSV_HEADER_INFO[2]],
        low=df[utile.CSV_HEADER_INFO[3]],
        close=df[utile.CSV_HEADER_INFO[4]],
        name='K线'
    ), row=1, col=1)
    
    fig.add_trace(go.Bar(
        x=df.index,
        y=df[utile.CSV_HEADER_INFO[6]],
        name='成交量',
        marker_color=[
                        f'rgba(255,0,0,0.6)' if close < open else f'rgba(0,255,0,0.6)'
                        for open, close in zip(df[utile.CSV_HEADER_INFO[1]], df[utile.CSV_HEADER_INFO[4]])
                    ]
    ), row=2, col=1)
    
    fig.update_layout(
        title=f'股票K线图',
        xaxis_title='日期',
        yaxis_title='价格',
        template='plotly_dark',
        hovermode='x unified',
        xaxis_rangeslider_visible=False
    )
    
    fig.update_yaxes(title_text="价格", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)
    
    # 返回div字符串（不包含完整HTML结构）
    return fig.to_html(full_html=False, include_plotlyjs='cdn')


if __name__ == "__main__":
    os.makedirs("scripts", exist_ok=True)  # 确保scripts目录存在
    app.run(debug=True)