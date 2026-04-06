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
    price_max_open_pct = []  # 记录相对于开盘价的最大涨跌幅，后续可以用于调整图表范围
    price_max_min_pct = []  # 记录相对于最低价的最大涨跌幅，后续可以用于调整图表范围
    price_changes_with_dates = []  # 包含日期的涨跌价格列表：[(change, date_str), ...]
    price_max_open_with_dates = []  # 包含日期的 max_open 列表：[(max_open, date_str), ...]
    price_max_min_with_dates = []  # 包含日期的 max_min 列表：[(max_min, date_str), ...]
    first_open_price = None  # 第一个有效的开盘价，用于确定区间宽度

    for tick in data:
        date_str = tick[0]
        if start_date and date_str < start_date:
            continue
        if end_date and date_str > end_date:
            continue
        
        open_price = float(tick[1])
        close_price = float(tick[2])
        high_price = float(tick[4])
        low_price = float(tick[3])
        
        if open_price != 0:  # 避免除零错误
            if first_open_price is None:
                first_open_price = open_price
            change = close_price - open_price
            change_pct = (change / open_price) * 100
            price_changes.append(change)
            price_changes_pct.append(change_pct)
            price_changes_with_dates.append((change, date_str))

            
            price_max_open_pct.append(high_price - open_price)  # 记录相对于开盘价的最大涨跌价格
            price_max_open_with_dates.append((high_price - open_price, date_str))
            price_max_min_pct.append(high_price - low_price)  # 记录相对于最低价的最大涨跌价格
            price_max_min_with_dates.append((high_price - low_price, date_str))
    
    return price_changes, price_changes_pct, price_max_open_pct, price_max_min_pct, price_changes_with_dates, price_max_open_with_dates, price_max_min_with_dates, first_open_price

def draw_distribution_charts(stock_code='', stock_name='', price_changes=[], price_changes_pct=[], price_max_open_pct=[], price_max_min_pct=[], price_changes_with_dates=None, price_max_open_with_dates=None, price_max_min_with_dates=None, first_open_price=None):
    '''
    绘制涨跌价格和涨跌幅分布图表（直方图）
    '''
    def get_bin_width(price):
        if price < 10:
            return 0.1
        elif price < 20:
            return 0.2
        elif price < 50:
            return 0.3        
        elif price < 150:
            return 0.5
        elif price < 250:
            return 0.8      
        else:
            return 1
    # 涨跌价格分布：动态区间宽度
    if price_changes:
        min_price = min(price_changes)
        max_price = max(price_changes)
        bin_width = get_bin_width(first_open_price) if first_open_price is not None else 0.1
        bins_price = np.arange(np.floor(min_price / bin_width) * bin_width, np.ceil(max_price / bin_width) * bin_width + bin_width, bin_width)
        hist_price, bin_edges_price = np.histogram(price_changes, bins=bins_price)
        bin_centers_price = (bin_edges_price[:-1] + bin_edges_price[1:]) / 2

        # 保留每个区间内的日期
        bin_to_dates = {}
        if price_changes_with_dates:
            for change, date_str in price_changes_with_dates:
                # 找到change对应的bin索引
                bin_index = np.digitize(change, bins_price) - 1
                if 0 <= bin_index < len(bin_centers_price):
                    bin_center = bin_centers_price[bin_index]
                    if bin_center not in bin_to_dates:
                        bin_to_dates[bin_center] = []
                    bin_to_dates[bin_center].append(date_str)
            # 打印或保存bin_to_dates
            print("\n收盘对于开盘-每个价格区间内的日期：")
            for bin_center, dates in sorted(bin_to_dates.items()):
                print(f"区间中心 {bin_center:.2f} 元，个数{len(dates)}: {dates}")
    else:
        bin_centers_price = []
        hist_price = []

    if price_max_open_pct:
        min_price = min(price_max_open_pct)
        max_price = max(price_max_open_pct)
        bin_width = get_bin_width(first_open_price) if first_open_price is not None else 0.1
        bins_price = np.arange(np.floor(min_price / bin_width) * bin_width, np.ceil(max_price / bin_width) * bin_width + bin_width, bin_width)
        hist_price_m_o, bin_edges_price_m_o = np.histogram(price_max_open_pct, bins=bins_price)
        bin_centers_price_m_o = (bin_edges_price_m_o[:-1] + bin_edges_price_m_o[1:]) / 2

        # 保留每个区间内的日期 for price_max_open_pct
        bin_to_dates_m_o = {}
        if price_max_open_with_dates:
            for change, date_str in price_max_open_with_dates:
                bin_index = np.digitize(change, bins_price) - 1
                if 0 <= bin_index < len(bin_centers_price_m_o):
                    bin_center = bin_centers_price_m_o[bin_index]
                    if bin_center not in bin_to_dates_m_o:
                        bin_to_dates_m_o[bin_center] = []
                    bin_to_dates_m_o[bin_center].append(date_str)
            print("\n最高价与开盘价之差-每个价格区间内的日期：")
            for bin_center, dates in sorted(bin_to_dates_m_o.items()):
                print(f"区间中心 {bin_center:.2f} 元，个数{len(dates)}: {dates}")
    else:
        bin_centers_price_m_o = []
        hist_price_m_o = []

    if price_max_min_pct:
        min_price = min(price_max_min_pct)
        max_price = max(price_max_min_pct)
        bin_width = get_bin_width(first_open_price) if first_open_price is not None else 0.1
        bins_price = np.arange(np.floor(min_price / bin_width) * bin_width, np.ceil(max_price / bin_width) * bin_width + bin_width, bin_width)
        hist_price_m_m, bin_edges_price_m_m = np.histogram(price_max_min_pct, bins=bins_price)
        bin_centers_price_m_m = (bin_edges_price_m_m[:-1] + bin_edges_price_m_m[1:]) / 2

        # 保留每个区间内的日期 for price_max_min_pct
        bin_to_dates_m_m = {}
        if price_max_min_with_dates:
            for change, date_str in price_max_min_with_dates:
                bin_index = np.digitize(change, bins_price) - 1
                if 0 <= bin_index < len(bin_centers_price_m_m):
                    bin_center = bin_centers_price_m_m[bin_index]
                    if bin_center not in bin_to_dates_m_m:
                        bin_to_dates_m_m[bin_center] = []
                    bin_to_dates_m_m[bin_center].append(date_str)
            print("\n最低价与最高价之差-每个价格区间内的日期：")
            for bin_center, dates in sorted(bin_to_dates_m_m.items()):
                print(f"区间中心 {bin_center:.2f} 元，个数{len(dates)}: {dates}")
    else:
        bin_centers_price_m_m = []
        hist_price_m_m = []        


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
        .add_xaxis([f"{x:.2f}" for x in bin_centers_price])
        .add_yaxis(
            series_name="涨跌价格出现次数",
            y_axis=hist_price.tolist(),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"开始日期={ucfg.stocks_analysis_start_date}", pos_left="right"),
            xaxis_opts=opts.AxisOpts(name="价格变化 (元)"),
            yaxis_opts=opts.AxisOpts(name="出现次数_当日相对于开盘价的涨跌"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
        )
    )

    # 价格分布图
    bar_price_m_o = (
        Bar()
        .add_xaxis([f"{x:.2f}" for x in bin_centers_price_m_o])
        .add_yaxis(
            series_name="涨跌价格出现次数",
            y_axis=hist_price_m_o.tolist(),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(name="价格变化 (元)"),
            yaxis_opts=opts.AxisOpts(name="出现次数_距离开盘价的最大涨跌"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
        )
    )   

    # 价格分布图
    bar_price_m_m = (
        Bar()
        .add_xaxis([f"{x:.2f}" for x in bin_centers_price_m_m])
        .add_yaxis(
            series_name="涨跌价格出现次数",
            y_axis=hist_price_m_m.tolist(),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"\n{stock_name}\n统计次数={len(price_changes)}", pos_left="left"),
            xaxis_opts=opts.AxisOpts(name="价格变化 (元)"),
            yaxis_opts=opts.AxisOpts(name="出现次数_最高价与最低价之差"),
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
            title_opts=opts.TitleOpts(title=f"\n{stock_name}\n统计次数={len(price_changes)}", pos_left="left"),
            xaxis_opts=opts.AxisOpts(name="涨跌幅 (%)"),
            yaxis_opts=opts.AxisOpts(name="出现次数"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
        )
    )

    # 合并图表
    grid_chart = Grid(
        init_opts=opts.InitOpts(
            width="1200px",
            height="1500px",
            animation_opts=opts.AnimationOpts(animation=False),
        )
    )
    grid_chart.add(
        bar_price,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="5%", height="20%"),
    )
    grid_chart.add(
        bar_price_m_o,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="5%", pos_top="30%", height="20%"),
    )
    grid_chart.add(
        bar_price_m_m,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="5%", pos_top="55%", height="20%"),
    )        
    ''' 
    grid_chart.add(
        bar_pct,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", pos_top="77%", height="13%"),
    )
    '''

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
    
    #stock_code = '300215'  # 可以根据需要修改为其他股票代码 by test
    #start_date = '2026-01-01'  # 可以根据需要设置开始日期

    end_date = None  # 可以根据需要设置结束日期

    if len(sys.argv) >= 3:
        start_date = sys.argv[2]
        if start_date == 'other' or start_date == '':
            start_date = ucfg.stocks_analysis_start_date
    if len(sys.argv) >= 4:
        end_date = sys.argv[3]
    
    tdx_datas = tdx(stock_code)
    tdx_datas.getStockDayFile()
    tdx_datas.creatstocKDataList()
    chart_data = tdx_datas.getTDXStockKDatas()  # 获取日线数据
    
    price_changes, price_changes_pct, price_max_open_pct, price_max_min_pct, price_changes_with_dates, price_max_open_with_dates, price_max_min_with_dates, first_open_price = calculate_price_changes(chart_data, start_date)
    
    draw_distribution_charts(stock_code, tdx_datas.stock_name, price_changes, price_changes_pct, price_max_open_pct, price_max_min_pct, price_changes_with_dates, price_max_open_with_dates, price_max_min_with_dates, first_open_price)
    
    print("分析完成，图表已生成, 统计天数:", len(price_changes))