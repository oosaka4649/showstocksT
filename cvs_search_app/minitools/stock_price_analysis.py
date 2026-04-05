from tdxcomm import TDXData as tdx
import user_config as ucfg

from pyecharts import options as opts
from pyecharts.charts import Bar, Grid

import numpy as np
from datetime import datetime
import os
import sys

# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
show_templates_html_path = os.path.join(parent_dir, 'templates', ucfg.my_stocks_html_folder_name)
show_templates_comm_html_path = os.path.join(parent_dir, 'templates', ucfg.common_html_folder_name)

'''
分析通达信数据，生成相对于开盘价格的涨跌价格和涨跌幅分布统计图
输入：股票代码、开始日期、结束日期
统计：价格按每0.1元间隔为一档，幅度按每0.01%间隔为一档
'''

def calculate_price_changes(data, start_date=None, end_date=None):
    '''
    计算相对于开盘价格的涨跌价格和涨跌幅
    data: 股票数据列表，格式 [日期, 开盘, 收盘, 最低, 最高, 成交量]
    start_date: 开始日期 (YYYY-MM-DD)
    end_date: 结束日期 (YYYY-MM-DD)
    返回：涨跌价格列表、涨跌幅列表
    '''
    price_changes = []  # 涨跌价格：收盘 - 开盘
    price_changes_pct = []  # 涨跌幅：(收盘 - 开盘) / 开盘 * 100%

    for tick in data:
        date_str = tick[0]
        if start_date and date_str < start_date:
            continue
        if end_date and date_str > end_date:
            continue
        
        open_price = float(tick[1])
        close_price = float(tick[2])
        
        if open_price != 0:  # 避免除零错误
            change = close_price - open_price
            change_pct = (change / open_price) * 100
            price_changes.append(change)
            price_changes_pct.append(change_pct)
    
    return price_changes, price_changes_pct

def draw_distribution_charts(stock_code='', stock_name='', price_changes=[], price_changes_pct=[]):
    '''
    绘制涨跌价格和涨跌幅分布图表（直方图）
    '''
    # 涨跌价格分布：每0.1元间隔
    if price_changes:
        min_price = min(price_changes)
        max_price = max(price_changes)
        bins_price = np.arange(np.floor(min_price * 10) / 10, np.ceil(max_price * 10) / 10 + 0.1, 0.1)
        hist_price, bin_edges_price = np.histogram(price_changes, bins=bins_price)
        bin_centers_price = (bin_edges_price[:-1] + bin_edges_price[1:]) / 2
    else:
        bin_centers_price = []
        hist_price = []

    # 涨跌幅分布：每0.01%间隔
    if price_changes_pct:
        min_pct = min(price_changes_pct)
        max_pct = max(price_changes_pct)
        bins_pct = np.arange(np.floor(min_pct * 100) / 100, np.ceil(max_pct * 100) / 100 + 0.01, 0.01)
        hist_pct, bin_edges_pct = np.histogram(price_changes_pct, bins=bins_pct)
        bin_centers_pct = (bin_edges_pct[:-1] + bin_edges_pct[1:]) / 2
    else:
        bin_centers_pct = []
        hist_pct = []

    # 价格分布图
    bar_price = (
        Bar()
        .add_xaxis([f"{x:.1f}" for x in bin_centers_price])
        .add_yaxis(
            series_name="涨跌价格出现次数",
            y_axis=hist_price.tolist(),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"开始日期={ucfg.stocks_analysis_start_date}", pos_left="right"),
            xaxis_opts=opts.AxisOpts(name="价格变化 (元)"),
            yaxis_opts=opts.AxisOpts(name="出现次数"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
        )
    )

    # 幅度分布图
    bar_pct = (
        Bar()
        .add_xaxis([f"{x:.2f}%" for x in bin_centers_pct])
        .add_yaxis(
            series_name="涨跌幅出现次数",
            y_axis=hist_pct.tolist(),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"统计次数={len(price_changes)}", pos_left="left"),
            xaxis_opts=opts.AxisOpts(name="涨跌幅 (%)"),
            yaxis_opts=opts.AxisOpts(name="出现次数"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
        )
    )

    # 合并图表
    grid_chart = Grid(
        init_opts=opts.InitOpts(
            width="1200px",
            height="800px",
            animation_opts=opts.AnimationOpts(animation=False),
        )
    )
    grid_chart.add(
        bar_price,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", height="40%"),
    )
    grid_chart.add(
        bar_pct,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", pos_top="55%", height="35%"),
    )

    # 保存图表
    grid_chart.render(f'{show_templates_html_path}/{stock_name}_{stock_code}_price_analysis.html')
    grid_chart.render(f'{show_templates_comm_html_path}/stock_price_kline.html')    

if __name__ == "__main__":
    '''
    if len(sys.argv) < 3:
        print("用法: python stock_price_analysis.py <股票代码> <开始日期 YYYY-MM-DD> <结束日期 YYYY-MM-DD>")
        sys.exit(1)
    '''
    stock_code = sys.argv[1]
    start_date = ucfg.stocks_analysis_start_date
    end_date = None  # 可以根据需要设置结束日期
    
    tdx_datas = tdx(stock_code)
    tdx_datas.getStockDayFile()
    tdx_datas.creatstocKDataList()
    chart_data = tdx_datas.getTDXStockKDatas()  # 获取日线数据
    
    price_changes, price_changes_pct = calculate_price_changes(chart_data, start_date)
    
    draw_distribution_charts(stock_code, tdx_datas.stock_name, price_changes, price_changes_pct)
    
    print("分析完成，图表已生成, 统计天数:", len(price_changes))