from tdxcomm import TDXData as tdx
import user_config as ucfg

from pyecharts import options as opts
from pyecharts.charts import Bar, Pie, Grid
from pyecharts.commons.utils import JsCode

import numpy as np
from datetime import datetime
import os
import sys

# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
show_templates_html_path = os.path.join(parent_dir, 'templates', ucfg.my_stocks_html_folder_name)

'''
分析通达信数据，生成相对于开盘价格的涨跌价格和涨跌幅分布统计图
输入：股票代码、开始日期、结束日期
统计：价格按每0.1元间隔为一档，幅度按每0.01%间隔为一档
'''

def calculate_price_changes_by_bfclose(data, start_date=None, end_date=None):
    '''
    计算相对于前收盘价格的涨跌价格和涨跌幅
    data: 股票数据列表，格式 [日期, 开盘, 收盘, 最低, 最高, 成交量]
    start_date: 开始日期 (YYYY-MM-DD)
    end_date: 结束日期 (YYYY-MM-DD)
    返回：涨跌价格列表、涨跌幅列表
    '''

    before_close_price = None  # 第一个有效的前收盘价，用于计算基准价格，用于确定区间宽度
    price_changes = []  # 涨跌价格：收盘 - 前收盘价
    price_max_close_pct = []  # 记录相对于前收盘价的最大涨跌幅，后续可以用于调整图表范围
    price_min_close_pct = []  # 记录相对于前收盘价的最小涨跌幅，后续可以用于调整图表范围
    price_changes_with_dates = []  # 包含日期的涨跌价格列表：[(change, date_str), ...]
    price_max_close_with_dates = []  # 包含日期的 max_close 列表：[(max_close, date_str), ...]
    price_min_close_with_dates = []  # 包含日期的 min_close 列表：[(min_close, date_str), ...]
    first_close_price = None  # 第一个有效的前收盘价，用于确定区间宽度

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
            if before_close_price is None:
                before_close_price = close_price  #如果是第一个，为了逻辑简单，则用第一个收盘价作为基准价格
                first_close_price = close_price
               
            change = close_price - before_close_price
            price_changes.append(change)
            price_changes_with_dates.append((change, date_str))

            price_max_close_pct.append(high_price - before_close_price)  # 记录相对于前收盘价的最大涨跌价格
            price_max_close_with_dates.append((high_price - before_close_price, date_str))
            price_min_close_pct.append(low_price - before_close_price)  # 记录相对于前收盘价的最小涨跌价格
            price_min_close_with_dates.append((low_price - before_close_price, date_str))

            
            before_close_price = close_price  # 记录前收盘价，用于下一次计算
    
    return price_changes, price_max_close_pct, price_min_close_pct, price_changes_with_dates, price_max_close_with_dates, price_min_close_with_dates, first_close_price


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
        
def draw_distribution_charts_by_bfclose(start_date, stock_code='', stock_name='', price_changes=[], price_max_close_pct=[], price_min_close_pct=[], price_changes_with_dates=None, price_max_close_with_dates=None, price_min_close_with_dates=None, first_close_price=None):
    '''
    绘制涨跌价格和涨跌幅分布图表（直方图）
    '''
    '''
    # 涨跌价格分布：动态区间宽度
    if price_changes:
        min_price = min(price_changes) # 计算 price_changes 列表中的最小值 (min_price) 和最大值 (max_price)。
        max_price = max(price_changes)

        # 根据第一个有效的前收盘价来确定区间宽度，确保图表的可读性和适应性
        bin_width = get_bin_width(first_close_price) if first_close_price is not None else 0.1
        # 计算价格区间的边界，确保覆盖所有数据点，并且区间宽度为 bin_width 的倍数
        # 使用 NumPy 的 np.arange 创建直方图的区间数组 (bins_price)，从最小值向下取整到最大值向上取整，确保区间覆盖所有数据。
        bins_price = np.arange(np.floor(min_price / bin_width) * bin_width, np.ceil(max_price / bin_width) * bin_width + bin_width, bin_width)

        # 调用 np.histogram 计算价格变化在这些区间内的分布，返回每个区间的计数 (hist_price) 和区间边缘 (bin_edges_price)。
        hist_price, bin_edges_price = np.histogram(price_changes, bins=bins_price)\
        # 计算每个区间的中心点 (bin_centers_price)，用于后续绘图时显示标签。
        #bin_centers_price = (bin_edges_price[:-1] + bin_edges_price[1:]) / 2
        bin_centers_price = bin_edges_price

        # 保留每个区间内的日期
        bin_to_dates = {}
        bin_to_dates_Values = {}
        if price_changes_with_dates:
            for change, date_str in price_changes_with_dates:
                # 找到change对应的bin索引
                bin_index = np.digitize(change, bins_price) - 1
                if 0 <= bin_index < len(bin_centers_price):
                    bin_center = bin_centers_price[bin_index]
                    if bin_center not in bin_to_dates:
                        bin_to_dates[bin_center] = []
                    bin_to_dates[bin_center].append(date_str)
                    bin_to_dates_Values[date_str] = change
            # 打印或保存bin_to_dates
            print("\n收盘对于前收盘价-每个价格区间内的日期：")
            for bin_center, dates in sorted(bin_to_dates.items()):
                print(f"区间中心 {bin_center:.2f} 元，个数{len(dates)}: {dates}")
    else:
        bin_centers_price = []
        hist_price = []
    ''' 

    if price_max_close_pct:
        # 计算 price_changes 列表中的最小值 (min_price) 和最大值 (max_price)。
        min_price = min(price_max_close_pct)
        max_price = max(price_max_close_pct)
        # 根据第一个有效的前收盘价来确定区间宽度，确保图表的可读性和适应性
        bin_width = get_bin_width(first_close_price) if first_close_price is not None else 0.1
        # 计算价格区间的边界，确保覆盖所有数据点，并且区间宽度为 bin_width 的倍数
        # 使用 NumPy 的 np.arange 创建直方图的区间数组 (bins_price)，从最小值向下取整到最大值向上取整，确保区间覆盖所有数据。        
        bins_price = np.arange(np.floor(min_price / bin_width) * bin_width, np.ceil(max_price / bin_width) * bin_width + bin_width, bin_width)
        # 调用 np.histogram 计算价格变化在这些区间内的分布，返回每个区间的计数 (hist_price) 和区间边缘 (bin_edges_price)。        
        hist_price_m_c, bin_edges_price_m_c = np.histogram(price_max_close_pct, bins=bins_price)
        # 计算每个区间的中心点 (bin_centers_price)，用于后续绘图时显示标签。
        # bin_centers_price_m_c = (bin_edges_price_m_c[:-1] + bin_edges_price_m_c[1:]) / 2
        bin_centers_price_m_c = bin_edges_price_m_c

        # 保留每个区间内的日期 for price_max_close_pct
        bin_to_dates_m_o = {}
        bin_to_dates_Values_m_o = {}
        if price_max_close_with_dates:
            for change, date_str in price_max_close_with_dates:
                bin_index = np.digitize(change, bins_price) - 1
                if 0 <= bin_index < len(bin_centers_price_m_c):
                    bin_center = bin_centers_price_m_c[bin_index]
                    if bin_center not in bin_to_dates_m_o:
                        bin_to_dates_m_o[bin_center] = []
                    bin_to_dates_m_o[bin_center].append(date_str)
                    bin_to_dates_Values_m_o[date_str] = change
            print("\n最高价与前收盘价之差-每个价格区间内的日期：")
            for bin_center, dates in sorted(bin_to_dates_m_o.items()):
                print(f"区间中心 {bin_center:.2f} 元，个数{len(dates)}: {dates}")
    else:
        bin_centers_price_m_c = []
        hist_price_m_c = []

    if price_min_close_pct:
        min_price = min(price_min_close_pct)
        max_price = max(price_min_close_pct)
        bin_width = get_bin_width(first_close_price) if first_close_price is not None else 0.1
        bins_price = np.arange(np.floor(min_price / bin_width) * bin_width, np.ceil(max_price / bin_width) * bin_width + bin_width, bin_width)
        hist_price_m_m, bin_edges_price_m_m = np.histogram(price_min_close_pct, bins=bins_price)
        #bin_centers_price_m_m = (bin_edges_price_m_m[:-1] + bin_edges_price_m_m[1:]) / 2
        bin_centers_price_m_m = bin_edges_price_m_m

        # 保留每个区间内的日期 for price_min_close_pct
        bin_to_dates_m_m = {}
        bin_to_dates_Values_m_m = {}
        if price_min_close_with_dates:
            for change, date_str in price_min_close_with_dates:
                bin_index = np.digitize(change, bins_price) - 1
                if 0 <= bin_index < len(bin_centers_price_m_m):
                    bin_center = bin_centers_price_m_m[bin_index]
                    if bin_center not in bin_to_dates_m_m:
                        bin_to_dates_m_m[bin_center] = []
                    bin_to_dates_m_m[bin_center].append(date_str)
                    bin_to_dates_Values_m_m[date_str] = change
            print("\n最低价与前收盘价之差-每个价格区间内的日期：")
            for bin_center, dates in sorted(bin_to_dates_m_m.items()):
                print(f"区间中心 {bin_center:.2f} 元，个数{len(dates)}: {dates}")
    else:
        bin_centers_price_m_m = []
        hist_price_m_m = []        

    # 价格分布图 - 改为饼图
    #pie_data = [(f"{x:.2f}", int(y)) for x, y in zip(bin_centers_price, hist_price)]
    pie_data_m_c = [
        {
            "name": f"{x:.2f}",
            "value": int(y),
            "dates": bin_to_dates_m_o.get(x, []),
            "values": [f"{bin_to_dates_Values_m_o[d]:.2f}" for d in bin_to_dates_m_o.get(x, [])],
        }
        for x, y in zip(bin_centers_price_m_c, hist_price_m_c)
    ]

    data_custom_m_c = []
    for d in pie_data_m_c:
        # 创建标准的 PieItem
        item = opts.PieItem(name=d["name"], value=d["value"])
        # 【核心点】将额外字段注入到 item 的 opts 字典中
        item.opts["dates"] = d["dates"]
        item.opts["values"] = d["values"]
        data_custom_m_c.append(item) 

    #pie_data_m_m = [(f"{x:.2f}", int(y)) for x, y in zip(bin_centers_price_m_m, hist_price_m_m)]
    pie_data_m_m = [
        {
            "name": f"{x:.2f}",
            "value": int(y),
            "dates": bin_to_dates_m_m.get(x, []),
            "values": [f"{bin_to_dates_Values_m_m[d]:.2f}" for d in bin_to_dates_m_m.get(x, [])],
        }
        for x, y in zip(bin_centers_price_m_m, hist_price_m_m)
    ]

    data_custom_m_m = []
    for d in pie_data_m_m:
        # 创建标准的 PieItem
        item = opts.PieItem(name=d["name"], value=d["value"])
        # 【核心点】将额外字段注入到 item 的 opts 字典中
        item.opts["dates"] = d["dates"]
        item.opts["values"] = d["values"]
        data_custom_m_m.append(item)     

    ''' 
    # 2. 处理数据：使用 PieItem 并手动注入自定义字段
    data_custom = []
    raw_data = [
        {"name": "华为", "value": 100, "growth": "15%", "boss": "张三"},
        {"name": "小米", "value": 80,  "growth": "10%", "boss": "李四"},
        {"name": "苹果", "value": 90,  "growth": "-5%", "boss": "王五"},
    ]
    for d in raw_data:
        # 创建标准的 PieItem
        item = opts.PieItem(name=d["name"], value=d["value"])
        # 【核心点】将额外字段注入到 item 的 opts 字典中
        item.opts["growth"] = d["growth"]
        item.opts["boss"] = d["boss"]
        data_custom.append(item) 
    '''
    bar_price = (
        Pie()
        .add(
            series_name="涨跌价格分布",
            data_pair=data_custom_m_c,
            center=["20%", "53%"], #饼图的中心位置坐标，调整为左侧，以便显示更多的区间
            radius=["15%", "70%"], #饼图的半径调整为 内径15% 外径60%，以便显示更多的区间
            # 小于这个角度（0 ~ 360）的扇区，不显示标签（label 和 labelLine）。
            #    min_show_label_angle: types.Numeric = 0,
            min_show_label_angle = 1,            
            #label_opts=opts.LabelOpts(formatter="{b}: {c}", position="outside"),
        )
        .add(
            series_name="最高价相对前收盘价分布",
            data_pair=data_custom_m_m,
            center=["50%", "53%"],
            radius=["15%", "70%"],
            # 小于这个角度（0 ~ 360）的扇区，不显示标签（label 和 labelLine）。
            #    min_show_label_angle: types.Numeric = 0,
            min_show_label_angle = 1,
            #label_opts=opts.LabelOpts(formatter="{b}: {c}", position="outside"),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"{stock_name}---统计次数={len(price_changes)}---开始日期={start_date}", pos_left="center"),
            tooltip_opts=opts.TooltipOpts(trigger="item", formatter=JsCode("function(params){ return params.seriesName + '<br/>' + params.name + ': ' + params.value + '<br/>日期: ' + params.data.dates.join(', ')+ '<br/>差价: ' + params.data.values.join(', '); }")),
            legend_opts=opts.LegendOpts(pos_bottom="1px"),
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
    )

    # 保存图表
    bar_price.render(f'{show_templates_html_path}/{stock_name}_{stock_code}_price_analysis-list.html')


if __name__ == "__main__":
    '''
    if len(sys.argv) < 3:
        print("用法: python stock_price_analysis.py <股票代码> <开始日期 YYYY-MM-DD> <结束日期 YYYY-MM-DD>")
        sys.exit(1)
    '''
    #stock_code = sys.argv[1]
    
    stock_code = '300215'  # 可以根据需要修改为其他股票代码 by test
    start_date = '2026-01-06'  # 可以根据需要设置开始日期

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

    price_changes, price_max_close_pct, price_min_close_pct, price_changes_with_dates, price_max_close_with_dates, price_min_close_with_dates, first_close_price = calculate_price_changes_by_bfclose(chart_data, start_date)
    draw_distribution_charts_by_bfclose(start_date, stock_code, tdx_datas.stock_name, price_changes, price_max_close_pct, price_min_close_pct, price_changes_with_dates, price_max_close_with_dates, price_min_close_with_dates, first_close_price)
    
    print("分析完成，图表已生成, 统计天数:", len(price_changes))