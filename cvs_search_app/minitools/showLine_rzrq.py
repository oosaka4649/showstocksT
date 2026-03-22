from tdxcomm import TDXData as tdx
from typing import List, Union
import user_config as ucfg

from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Grid, Line, Pie, Tab
from pyecharts.options import TitleOpts, DataZoomOpts

import numpy as np
from datetime import datetime
import os
import csv
import pandas as pd
import sys
# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
# 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)
show_templates_comm_html_path = os.path.join(parent_dir, 'templates', ucfg.common_html_folder_name)
rzrq_csv_path = os.path.join(parent_dir, 'data', 'rzrq.csv')


line_date = []
line_rzrq = []   # 存储融资融券数据的内存列表
line_rz = []
line_rq = []
data_lines = []   # 存储CSV文件内容的内存列表 rzrq 数据
sh_chart_data = [] # 上综指数据
sz_chart_data = [] # 深成指数据

sh_all_data = {'categoryData': [], 'values': [], 'closes': [], 'prices': []} # 上综指数据
sz_all_data = {'categoryData': [], 'values': [], 'closes': [], 'prices': []} # 深成指数据
'''
使用 pyecharts 绘制 

融资融券曲线，和 上综指，深成指的 close值和 它们的量线，以便于和融资融券的量线对比，看看是否有关系，是否可以用来预测融资融券的走势

生成html后，被放在 stockhtml 文件夹下，命名为 rzrq_line.html

'''
def split_rzrq_data(data):
    for line in data:
        line_date.append(line[1][0]) # 日期
        line_rz.append(float(line[1][1])) # 融资
        line_rq.append(float(line[1][2])) # 融券
    return {"categoryDate": line_date, "rz": line_rz, "rq": line_rq}

def split_data(data, flag='sh'):
    category_data = []
    values = [] # 存储量数据
    prices = [] # 存储价格数据
    closes = []


    all_category_date = []
    all_values = [] # 存储量数据
    all_prices = [] # 存储价格数据
    all_closes = [] 

    '''
        date         开        收        最低       最高       成交量        金额量
    ["2004-01-02", 10452.74, 10409.85, 10367.41, 10554.96, 168890000, 168890000],
      data 结构
      
    '''
    for i, tick in enumerate(data):
        stock_date = tick[0]
        all_category_date.append(stock_date)
        all_values.append(float(tick[5]) / 100)  # 成交量
        all_prices.append(float(tick[6]) / 100000) # 市场金额
        all_closes.append(float(tick[2])) # 收盘价
        if stock_date in line_date:
            category_data.append(tick[0]) # 日期
            # convert volume to millions and round to 2 decimal places
            values.append(round(float(tick[5]) / 100, 2))  # 成交量
            prices.append(round(float(tick[6]) / 100000, 2)) # 市场金额
            closes.append(float(tick[2])) # 收盘价
    if flag == 'sh':
        sh_all_data.update({"categoryData": all_category_date, "values": all_values, "prices": all_prices, "closes": all_closes})
    elif flag == 'sz':
        sz_all_data.update({"categoryData": all_category_date, "values": all_values, "prices": all_prices, "closes": all_closes})
    return {"categoryData": category_data, "values": values, "prices": prices, "closes": closes}

def add_string_to_csv_memory(csv_file_path):
    """
    读取CSV文件到内存列表，检查字符串是否存在，不存在则添加。
    
    参数:
        csv_file_path (str): CSV文件路径
   
    返回:
        list: 更新后的内存数据列表
    """  
    # 读取CSV文件内容到内存
    try:
        header_flag = 0
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            for fields in csv_reader:
                if header_flag == 0:
                    header_flag = 1
                    continue  # 跳过标题行
                data_lines.append((fields[0], fields))
    except FileNotFoundError:
        print(f"文件 {csv_file_path} 不存在，将创建新列表")

    # 按日期排序
    try:
        # 尝试按日期对象排序
        data_lines.sort(key=lambda x: x[0], reverse=False)
    except:
        # 如果日期对象排序失败，尝试按字符串排序
        data_lines.sort(key=lambda x: str(x[0]), reverse=False)

def line_rzrq_sh_sz_value(sh_data, sz_data, rzrq_data=None) -> Line:
    sh_sz_values = [sh + sz for sh, sz in zip(sh_data['values'], sz_data['values'])]
    c = (Line()
        .add_xaxis(xaxis_data=line_date)
        .add_yaxis(
            series_name="融资",
            y_axis=rzrq_data['rz'],
            is_smooth=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#0000FF"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="融券",
            y_axis=rzrq_data['rq'],
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#FF0000"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="上，深综量",
            y_axis=sh_sz_values,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#22D44E"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis"),
                                yaxis_opts=opts.AxisOpts(
                                    type_="value",
                                    axistick_opts=opts.AxisTickOpts(is_show=True),
                                    splitline_opts=opts.SplitLineOpts(is_show=True),
                                ),
                                xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False),
                                datazoom_opts=[DataZoomOpts()],  # 添加缩放功能
                         )        
    )
    return c

def line_rzrq_sh_value(sh_data, sz_data, rzrq_data=None) -> Line:
    v_sh = tdx.standardize(sh_data['values'])
    v_rz = tdx.standardize(rzrq_data['rz'])
    c_sh = tdx.standardize(sh_data['closes'])

    p_sh = tdx.standardize(sh_data['prices'])
    c = (Line()
        .add_xaxis(xaxis_data=line_date)
        .add_yaxis(
            series_name="融资",
            y_axis=v_rz,
            is_smooth=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#0000FF"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="上市综量",
            y_axis=v_sh,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#22D44E"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="上市交易金额",
            y_axis=p_sh,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#CBDF1A"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )        
        .add_yaxis(
            series_name="上市综收盘价",
            y_axis=c_sh,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#E41426"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )        
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis"),
                                yaxis_opts=opts.AxisOpts(
                                    type_="value",
                                    axistick_opts=opts.AxisTickOpts(is_show=True),
                                    splitline_opts=opts.SplitLineOpts(is_show=True),
                                ),
                                xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False),
                                datazoom_opts=[DataZoomOpts()],  # 添加缩放功能
                         )         
    )
    return c

def line_rzrq_sz_value(sh_data, sz_data, rzrq_data=None) -> Line:
    v_sz = tdx.standardize(sz_data['values'])
    v_rz = tdx.standardize(rzrq_data['rz'])
    c_sz = tdx.standardize(sz_data['closes'])

    p_sz = tdx.standardize(sz_data['prices'])
    c = (Line()
        .add_xaxis(xaxis_data=line_date)
        .add_yaxis(
            series_name="融资",
            y_axis=v_rz,
            is_smooth=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#0000FF"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="深证综量",
            y_axis=v_sz,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#22D44E"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="深证交易金额",
            y_axis=p_sz,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#CBDF1A"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )            
        .add_yaxis(
            series_name="深证综收盘价",
            y_axis=c_sz,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#E41426"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )        
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis"),
                                yaxis_opts=opts.AxisOpts(
                                    type_="value",
                                    axistick_opts=opts.AxisTickOpts(is_show=True),
                                    splitline_opts=opts.SplitLineOpts(is_show=True),
                                ),
                                xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False),
                                datazoom_opts=[DataZoomOpts()],  # 添加缩放功能
                         )         
    )
    return c


def line_sh_all(sh_data) -> Line:
    v_sh = tdx.standardize(sh_data['values'])
    c_sh = tdx.standardize(sh_data['closes'])
    p_sh = tdx.standardize(sh_data['prices'])

    d_sh = sh_data['categoryData']
    c = (Line()
        .add_xaxis(xaxis_data=d_sh)
        .add_yaxis(
            series_name="上证综量",
            y_axis=v_sh,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#2EE95D"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )        
        .add_yaxis(
            series_name="上证交易金额",
            y_axis=p_sh,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#CDE020"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )                   
        .add_yaxis(
            series_name="上证综收盘价",
            y_axis=c_sh,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#EC2132"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )                   
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis"),
                                yaxis_opts=opts.AxisOpts(
                                    type_="value",
                                    axistick_opts=opts.AxisTickOpts(is_show=True),
                                    splitline_opts=opts.SplitLineOpts(is_show=True),
                                ),
                                xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False),
                                datazoom_opts=[DataZoomOpts()],  # 添加缩放功能
                         )         
    )
    return c

def line_sz_all(sz_data) -> Line:
    v_sz = tdx.standardize(sz_data['values'])
    c_sz = tdx.standardize(sz_data['closes'])

    p_sz = tdx.standardize(sz_data['prices'])
    d_sz = sz_data['categoryData']
    c = (Line()
        .add_xaxis(xaxis_data=d_sz)
        .add_yaxis(
            series_name="深证综量",
            y_axis=v_sz,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#22D44E"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="深证交易金额",
            y_axis=p_sz,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#CBDF1A"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="深证综收盘价",
            y_axis=c_sz,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#E41426"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )              
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis"),
                                yaxis_opts=opts.AxisOpts(
                                    type_="value",
                                    axistick_opts=opts.AxisTickOpts(is_show=True),
                                    splitline_opts=opts.SplitLineOpts(is_show=True),
                                ),
                                xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False),
                                datazoom_opts=[DataZoomOpts()],  # 添加缩放功能
                         )         
    )
    # 将注释添加到HTML模板中
    c.add_js_funcs("""
        var comment = document.createElement('div');
        comment.innerHTML = '在<p style="color: red;">两市的单纯量和金额标准化对比中</p>，<br>注意观察 <br>1999-10到2001-10 <br>2006-04到2008-9  <br>2014-04到2015-11  <br>2024-08到现在 <p style="color: red;"><br>这段时间，量和金额及收盘点的走势，它们之间的上穿，下穿，间隔幅度，等相对关系来判断现在大致处于哪个阶段，来判断大盘整体的走势</p>';
        comment.style.position = 'absolute';
        comment.style.top = '600px'; // 根据需要调整位置
        comment.style.left = '250px'; // 根据需要调整位置
        document.body.appendChild(comment);
    """)    
    return c    

def chart_table_data(sh_data=None, sz_data=None, rzrq_data=None):
    # prefer explicit data instead of relying on globals
    if sh_data is None:
        sh_data = {'categoryData': [], 'values': [], 'closes': [], 'prices': []}
    if sz_data is None:
        sz_data = {'categoryData': [], 'values': [], 'closes': [], 'prices': []}
    if rzrq_data is None:
        rzrq_data = {'categoryDate': [], 'rz': [], 'rq': []}
    tab = Tab()
    tab.add(line_rzrq_sh_sz_value(sh_data, sz_data, rzrq_data), "融资融券量和市场量")
    tab.add(line_rzrq_sh_value(sh_data, sz_data, rzrq_data), "融资和上证量及上证指数对比标准化")
    tab.add(line_rzrq_sz_value(sh_data, sz_data, rzrq_data), "融资和深证量及深证指数对比标准化")
    tab.add(line_rzrq_all_value(sh_data, sz_data, rzrq_data), "归一化后的融资和上证、深证量及指数对比")

    tab.add(line_sh_all(sh_all_data), "上证量及金额对比标准化")
    tab.add(line_sz_all(sz_all_data), "深证量及金额对比标准化")
    tab.render(f'{show_templates_comm_html_path}/rzrq_line.html')


def line_rzrq_all_value(sh_data, sz_data, rzrq_data=None) -> Line:
    sh_sz_values = [sh + sz for sh, sz in zip(sh_data['values'], sz_data['values'])]
    sh_sz_prices = [sh + sz for sh, sz in zip(sh_data['prices'], sz_data['prices'])]
    v_sz_sh = tdx.normalize(sh_sz_values)
    v_rz = tdx.normalize(rzrq_data['rz'])
    c_sz = tdx.normalize(sz_data['closes'])
    c_sh = tdx.normalize(sh_data['closes'])
    p_sz_sh = tdx.normalize(sh_sz_prices)
    c = (Line()
        .add_xaxis(xaxis_data=line_date)
        .add_yaxis(
            series_name="融资",
            y_axis=v_rz,
            is_smooth=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#0000FF"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="sz综收盘价",
            y_axis=c_sz,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#FF0000"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="sh综收盘价",
            y_axis=c_sh,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#D31BE4B2"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )        
        .add_yaxis(
            series_name="上，深综量",
            y_axis=v_sz_sh,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#22D44E"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="上，深金额",
            y_axis=p_sz_sh,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#B6DB0F"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )        
        .set_global_opts(tooltip_opts=opts.TooltipOpts(trigger="axis"),
                                yaxis_opts=opts.AxisOpts(
                                    type_="value",
                                    axistick_opts=opts.AxisTickOpts(is_show=True),
                                    splitline_opts=opts.SplitLineOpts(is_show=True),
                                ),
                                xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False),
                         )        
    )
    return c

def main():
    '''
    sh999999.day 上综指
    sz399001.day 深成指
    '''
    # 读取已有CSV文件内容到内存
    csv_file_path = rzrq_csv_path
    add_string_to_csv_memory(csv_file_path)
    all_rzrq_data = split_rzrq_data(data_lines)
  
#    print(f"融资融券数据点数量: {line_date}")

    tdx_sh_datas = tdx('999999')
    tdx_sh_datas.getStockDayFile()
    tdx_sh_datas.creatstocKDataList()
    sh_data = split_data(tdx_sh_datas.getTDXStockKDatas(), flag='sh')

    tdx_sz_datas = tdx('399001')
    tdx_sz_datas.getStockDayFile()
    tdx_sz_datas.creatstocKDataList()
    sz_data = split_data(tdx_sz_datas.getTDXStockKDatas(), flag='sz')
    chart_table_data(sh_data=sh_data, sz_data=sz_data, rzrq_data=all_rzrq_data)

if __name__ == "__main__":
    main()
    
