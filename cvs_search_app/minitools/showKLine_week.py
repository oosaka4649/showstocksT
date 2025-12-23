from tdxcomm import TDXData as tdx
from typing import List, Union

from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Grid

import talib
import numpy as np
from datetime import datetime
import os
import pandas as pd

# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
# 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)
show_html_path = os.path.join(parent_dir, 'stockhtml')


'''
使用 pyecharts 绘制 k线图 
使用 talib 计算均线 

标准的 k线数据格式  用作后面扩展base
'''

def split_data(data):
    category_data = []
    values = []
    volumes = []
    closes = []

    '''
        date         开        收        最低       最高       量
    ["2004-01-02", 10452.74, 10409.85, 10367.41, 10554.96, 168890000],
      data 结构
      
    '''

    for i, tick in enumerate(data):
        category_data.append(tick[0]) # 日期
        values.append(tick) # 全部内容
        closes.append(tick[2]) # 收盘价
        # 元代码 是 tick 4 错了，应该是 tick 5 因为 4是 最高价，5才是量
        volumes.append([i, tick[5], 1 if tick[1] > tick[2] else -1])  # i 是序号 从 0 开始，如果 开始大于收盘 1 ，反之 -1 估计是标 量线颜色用 红 绿
    return {"categoryData": category_data, "values": values, "volumes": volumes, "closes": closes}

'''
  手动算出 均线， day count是输入要算的几日均线 tudo 后面要搞搞 其他macd，rsi，cci，bolling什么的

  我修改了原来单纯的计算方法，改用 talib 库来计算均线，这样后面要计算其他指标也方便
'''
def calculate_ma(day_count: int, data):
    '''
      ta lib 使用 np.array 作为输入，但 pyecharts 需要 list 作为输出，所以这里做了转换，而且 数据类型为 double
    '''
    
    result = talib.SMA(np.array(data["closes"], dtype='double'), timeperiod=day_count)
    return result

def calculate_ma_list(day_count: int, w_data, chart_all_data):
    '''
      ta lib 使用 np.array 作为输入，但 pyecharts 需要 list 作为输出，所以这里做了转换，而且 数据类型为 double
    '''
    temp_closes = [row[2] for row in w_data if row[2] is not np.nan]
    temp_date = [(row[0] - + pd.Timedelta(days=2)).strftime("%Y-%m-%d") for row in w_data if row[2] is not np.nan]
    temp_w_ma = talib.SMA(np.array(temp_closes, dtype='double'), timeperiod=day_count)

    week_ma_dataes = []
    for dt in chart_all_data['categoryData']:
        if dt in temp_date:
            idx = temp_date.index(dt)
            if not np.isnan(temp_w_ma[idx]):
                week_ma_dataes.append(temp_w_ma[idx])
            else:
                week_ma_dataes.append(np.float64(np.nan))
        else:
            week_ma_dataes.append(np.float64(np.nan))
    return week_ma_dataes

def draw_charts(stock_code='', stock_name=''):
    weekly_MA_data = calculate_ma_list(5, all_data['Week_Data'], chart_data)
    kline_data = [data[1:-1] for data in chart_data["values"]]
    kline = (
        Kline()
        .add_xaxis(xaxis_data=chart_data["categoryData"])
        .add_yaxis(
            series_name=stock_name,
            y_axis=kline_data,
            itemstyle_opts=opts.ItemStyleOpts(color="#ec0000", color0="#00da3c"),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f'{stock_name}_{stock_code}_K线周期图表', pos_left="500"),
            legend_opts=opts.LegendOpts(
                is_show=False, pos_bottom=10, pos_left="center"
            ),
            datazoom_opts=[
                opts.DataZoomOpts(   # https://pyecharts.org/#/zh-cn/global_options?id=datazoomopts%ef%bc%9a%e5%8c%ba%e5%9f%9f%e7%bc%a9%e6%94%be%e9%85%8d%e7%bd%ae%e9%a1%b9
                    is_show=False,
                    type_="inside",
                    xaxis_index=[0, 1],
                    range_start=98,
                    range_end=100,
                ),
                opts.DataZoomOpts(
                    is_show=True,
                    xaxis_index=[0, 1],
                    type_="slider",
                    pos_top="85%",
                    range_start=98,
                    range_end=100,
                ),
            ],
            yaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitarea_opts=opts.SplitAreaOpts(
                    is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                ),
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="axis",
                axis_pointer_type="cross",
                background_color="rgba(245, 245, 245, 0.8)",
                border_width=1,
                border_color="#ccc",
                textstyle_opts=opts.TextStyleOpts(color="#000"),
            ),
            visualmap_opts=opts.VisualMapOpts(
                is_show=False,
                dimension=2,
                series_index=5,
                is_piecewise=True,
                pieces=[
                    {"value": 1, "color": "#00da3c"},
                    {"value": -1, "color": "#ec0000"},
                ],
            ),
            axispointer_opts=opts.AxisPointerOpts(
                is_show=True,
                link=[{"xAxisIndex": "all"}],
                label=opts.LabelOpts(background_color="#777"),
            ),
            brush_opts=opts.BrushOpts(
                x_axis_index="all",
                brush_link="all",
                out_of_brush={"colorAlpha": 0.1},
                brush_type="lineX",
            ),
        )
    )

    line = (
        Line()
        .add_xaxis(xaxis_data=chart_data["categoryData"])
        .add_yaxis(
            series_name="MA5",
            y_axis=calculate_ma(day_count=5, data=chart_data),
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="MA10",
            y_axis=calculate_ma(day_count=10, data=chart_data),
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
        #tdx_weekly_data
        .add_yaxis(
            series_name="Weekly Close",
            y_axis=weekly_MA_data,
            is_smooth=True,
            is_hover_animation=False,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
        #
        .set_global_opts(xaxis_opts=opts.AxisOpts(type_="category"))
    )

    bar = (
        Bar()
        .add_xaxis(xaxis_data=chart_data["categoryData"])
        .add_yaxis(
            series_name="Volume",
            y_axis=chart_data["volumes"],
            xaxis_index=1,
            yaxis_index=1,
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                type_="category",
                is_scale=True,
                grid_index=1,
                boundary_gap=False,
                axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                axistick_opts=opts.AxisTickOpts(is_show=False),
                splitline_opts=opts.SplitLineOpts(is_show=False),
                axislabel_opts=opts.LabelOpts(is_show=False),
                split_number=20,
                min_="dataMin",
                max_="dataMax",
            ),
            yaxis_opts=opts.AxisOpts(
                grid_index=1,
                is_scale=True,
                split_number=2,
                axislabel_opts=opts.LabelOpts(is_show=False),
                axisline_opts=opts.AxisLineOpts(is_show=False),
                axistick_opts=opts.AxisTickOpts(is_show=False),
                splitline_opts=opts.SplitLineOpts(is_show=False),
            ),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )

    # Kline And Line
    overlap_kline_line = kline.overlap(line)

    # Grid Overlap + Bar
    grid_chart = Grid(
        init_opts=opts.InitOpts(
            width="1000px",
            height="800px",
            animation_opts=opts.AnimationOpts(animation=False),
        )
    )
    grid_chart.add(
        overlap_kline_line,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", height="50%"),
    )
    grid_chart.add(
        bar,
        grid_opts=opts.GridOpts(
            pos_left="10%", pos_right="8%", pos_top="63%", height="16%"
        ),
    )
    create_date = datetime.today().strftime("%Y%m%d%H%M%S")
    #grid_chart.render(f'{show_html_path}/{stock_code}_kline_{create_date}.html')
    grid_chart.render(f'{show_html_path}/{stock_code}_kline.html')


if __name__ == "__main__":
    s_codes = ['300215', '301246', '000686', '600526', '600158','600233', '300251', '002303', '002852']
    for stock_code in s_codes:
        tdx_datas = tdx(stock_code)
        tdx_datas.getStockDayFile()
        tdx_datas.creatstocKDataList()
        all_data = tdx_datas.getTDXStockDWDatas()
        chart_data = split_data(tdx_datas.getTDXStockKDatas())
        draw_charts(stock_code, tdx_datas.stock_name)
