from tdxcomm import TDXData as tdx
import user_config as ucfg

from pyecharts import options as opts
from pyecharts.charts import Bar, Pie, Page, Grid
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
    
    return {
        "price_changes": price_changes,
        "price_max_close_pct": price_max_close_pct,
        "price_min_close_pct": price_min_close_pct,
        "price_changes_with_dates": price_changes_with_dates,
        "price_max_close_with_dates": price_max_close_with_dates,
        "price_min_close_with_dates": price_min_close_with_dates,
        "first_close_price": first_close_price
    }


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
        

def calculate_histogram_and_dates(price_list, price_with_dates, first_close_price, label):
    '''
    计算价格列表的直方图和日期映射
    price_list: 价格变化列表
    price_with_dates: 带日期的价格变化列表 [(change, date_str), ...]
    first_close_price: 用于确定区间宽度
    label: 打印标签
    返回: bin_centers, hist, bin_to_dates, bin_to_dates_Values
    '''
    if price_list:
        min_price = min(price_list)
        max_price = max(price_list)
        bin_width = get_bin_width(first_close_price) if first_close_price is not None else 0.1
        bins_price = np.arange(np.floor(min_price / bin_width) * bin_width, np.ceil(max_price / bin_width) * bin_width + bin_width, bin_width)
        hist, bin_edges = np.histogram(price_list, bins=bins_price)
        bin_centers = bin_edges

        # 保留每个区间内的日期
        bin_to_dates = {}
        bin_to_dates_Values = {}
        if price_with_dates:
            for change, date_str in price_with_dates:
                bin_index = np.digitize(change, bins_price) - 1
                if 0 <= bin_index < len(bin_centers):
                    bin_center = bin_centers[bin_index]
                    if bin_center not in bin_to_dates:
                        bin_to_dates[bin_center] = []
                    bin_to_dates[bin_center].append(date_str)
                    bin_to_dates_Values[date_str] = change
            print(f"\n{label}-每个价格区间内的日期：")
            for bin_center, dates in sorted(bin_to_dates.items()):
                print(f"区间中心 {bin_center:.2f} 元，个数{len(dates)}: {dates}")
        return {"bin_centers": bin_centers, "hist": hist, "bin_to_dates": bin_to_dates, "bin_to_dates_Values": bin_to_dates_Values}
    else:
        return {"bin_centers": [], "hist": [], "bin_to_dates": {}, "bin_to_dates_Values": {}}


# 创建饼图数据和自定义字段,
# bin_centers 是区间中心点列表，hist 是每个区间的计数列表，
# bin_to_dates 是一个字典，键是区间中心点，值是该区间内的日期列表，
# bin_to_dates_Values 是一个字典，键是日期字符串，值是对应的价格变化值
# 这个函数将这些数据整合成适合 pyecharts 饼图的数据格式，同时将日期和价格变化值注入到每个数据项的 opts 字典中，以便在 tooltip 中使用
# 实现，当鼠标悬停在饼图的某个扇区时，tooltip 能显示该区间内的所有日期和对应的价格变化值
def create_pie_data_and_custom(price_data):
    bin_centers = price_data["bin_centers"]
    hist = price_data["hist"]
    bin_to_dates = price_data["bin_to_dates"]
    bin_to_dates_Values = price_data["bin_to_dates_Values"]

    pie_data = [
        {
            "name": f"{x:.2f}",
            "value": int(y),
            "dates": bin_to_dates.get(x, []),
            "values": [f"{bin_to_dates_Values[d]:.2f}" for d in bin_to_dates.get(x, [])],
        }
        for x, y in zip(bin_centers, hist)
    ]
    
    data_custom = []
    for d in pie_data:
        item = opts.PieItem(name=d["name"], value=d["value"])
        item.opts["dates"] = d["dates"]
        item.opts["values"] = d["values"]
        data_custom.append(item)
    
    return data_custom
    

def draw_distribution_charts_by_bfclose(start_date, x_axis_list, pice_data_list) -> Pie:
    '''
    绘制涨跌价格和涨跌幅分布图表（直方图）
    '''
    # 价格分布图 - 改为饼图，并注入日期和价格变化值到 tooltip 中

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
    def get_name(item, info_key):
        return item['tdx_datas'].stock_name + '-------------------------------' + info_key
    
    bar_price = Pie()
    stock_name_str = ''
    for index, (item) in enumerate(pice_data_list):
        bar_price.add(
            series_name=get_name(pice_data_list[index], "max_收盘价分布"),
            data_pair=create_pie_data_and_custom(calculate_histogram_and_dates(pice_data_list[index]['price_data']['price_max_close_pct'], pice_data_list[index]['price_data']['price_max_close_with_dates'], pice_data_list[index]['price_data']['first_close_price'], "最高价与前收盘价之差")),
            center=[f"{x_axis_list[index]}%", "30%"], #饼图的中心位置坐标，调整为左侧，以便显示更多的区间
            radius=["10%", "30%"], #饼图的半径调整为 内径15% 外径60%，以便显示更多的区间
            # 小于这个角度（0 ~ 360）的扇区，不显示标签（label 和 labelLine）。
            #    min_show_label_angle: types.Numeric = 0,
            min_show_label_angle = 1,            
        ).add(
            series_name=get_name(pice_data_list[index], "min_收盘价分布"),
            data_pair=create_pie_data_and_custom(calculate_histogram_and_dates(pice_data_list[index]['price_data']['price_min_close_pct'], pice_data_list[index]['price_data']['price_min_close_with_dates'], pice_data_list[index]['price_data']['first_close_price'], "最低价与前收盘价之差")),
            center=[f"{x_axis_list[index]}%", "75%"],
            radius=["10%", "30%"],
            # 小于这个角度（0 ~ 360）的扇区，不显示标签（label 和 labelLine）。
            #    min_show_label_angle: types.Numeric = 0,
            min_show_label_angle = 1,
        )
        stock_name_str += get_name(pice_data_list[index], '-') + '  '
                
    bar_price.set_global_opts(
        title_opts=opts.TitleOpts(title=f"{stock_name_str} \n 统计次数={len(pice_data_list[0]['price_data']['price_changes'])}---开始日期={start_date}", pos_left="center"),
        tooltip_opts=opts.TooltipOpts(trigger="item", formatter=JsCode("function(params){ info = '日期: --------- 差价:' ;" \
        " for (let i = 0; i < params.data.values.length; i++) { " \
        "     b = i +1 ;" \
        "     if (i%3 == 0) { " \
        "         info += '<br/>' +  b +  '    ' + params.data.dates[i] + ': ' + params.data.values[i] ;" \
        "     } else {" \
        "         info += ' -- ' +  b +  '    ' + params.data.dates[i] + ': ' + params.data.values[i] ;" \
        "     }" \
        " } " \
        " return params.seriesName + '<br/>' + params.name + ': ' + params.value + '<br/>' + info ; }")),
    )
    bar_price.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))

    return bar_price



def page_simple_layout(page, start_date, stock_chart_list, x_axis_list):
    pice_data_list = []
    temp_count = 0
    for index, (tdx_datas, chart_data) in enumerate(stock_chart_list):
        pice_data_list.append({'tdx_datas': tdx_datas, 'price_data': calculate_price_changes_by_bfclose(chart_data, start_date)})  # 计算相对于前收盘价的涨跌价格和涨跌幅
        temp_count  += 1
        if (len(pice_data_list) == len(x_axis_list)) or temp_count == len(stock_chart_list):
            page.add(
                draw_distribution_charts_by_bfclose(start_date, x_axis_list, pice_data_list)    
            )
            pice_data_list = []
        else:
            continue

    print("分析完成，图表已生成, 统计天数:", len(stock_chart_list))
    return len(stock_chart_list)

def main():
    start_date = '2025-04-06'  # 可以根据需要设置开始日期
    price_day_length = 0
    x_axis_list = [8, 25, 45, 65, 85]
    stock_chart_list = []
    page = Page(layout=Page.DraggablePageLayout, page_title="相对于前收盘价的涨跌价格分布图表")
    for stock_code in ucfg.my_stocks_min_max_list:
        tdx_datas = tdx(stock_code)
        tdx_datas.getStockDayFile()
        tdx_datas.creatstocKDataList()
        chart_data = tdx_datas.getTDXStockKDatas()  # 获取日线数据
        stock_chart_list.append((tdx_datas, chart_data))
    
    page_simple_layout(page, start_date, stock_chart_list, x_axis_list)

    # 保存图表
    page.render(f'{show_templates_html_path}/{start_date}_price_analysis-list_H.html')

if __name__ == "__main__":
    main()
    
