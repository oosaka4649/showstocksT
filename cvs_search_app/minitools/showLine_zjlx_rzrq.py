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
dpzjlx_csv_path = os.path.join(parent_dir, 'data', 'dpzjlx.csv') # 大盘资金流向历史数据(沪深两市) csv文件路径

rzrq_csv_path = os.path.join(parent_dir, 'data', 'rzrq.csv')

data_lines = []   # 存储CSV文件内容的内存列表 dpzjlx 数据

#日期,上证收盘价,上证涨跌幅,深证收盘价,深证涨跌幅,主力净流入净额,主力净流入净占比,超大单净流入净额,超大单净流入净占比,大单净流入净额,大单净流入净占比,中单净流入净额,中单净流入净占比,小单净流入净额,小单净流入净占比

zjlx_sh_close = [] # 大盘资金流向数据中的上证收盘价
zjlx_sh_close_change = [] # 大盘资金流向数据中的上证涨跌幅
zjlx_sz_close = [] # 大盘资金流向数据中的深证收盘价
zjlx_sz_close_change = [] # 大盘资金流向数据中的深证涨跌幅

zjlx_date = []      # 大盘资金流向日期数据

zjlx_inflow_main = []    # 大盘资金流向净流入数据  主力净流入数据
zjlx_inflow_super_large = []    # 大盘资金流向净流入数据  超大单净流入数据
zjlx_inflow_large = []    # 大盘资金流向净流入数据  大单净流入数据
zjlx_inflow_medium = []    # 大盘资金流向净流入数据  中单净流入数据
zjlx_inflow_small = []    # 大盘资金流向净流入数据  小单净流入数据


data_lines_rzrq = []   # 存储CSV文件内容的内存列表 rzrq 数据
rzrq_date = []
rzrq_line_rz = []
rzrq_line_rq = []

'''
使用 pyecharts 绘制 

大盘资金流向曲线，和 上综指，深成指的 close值和 它们的量线，以便于和大盘资金流向的量线对比，看看是否有关系，是否可以用来预测大盘资金流向的走势

生成html后，被放在 stockhtml 文件夹下，命名为 zjlx_line.html

'''
def split_zjlx_data(data):
    for line in data:
        zjlx_date.append(line[0]) # 日期
        zjlx_sh_close.append(float(line[1][1])) # 上证收盘价
        #zjlx_sh_close_change.append(float(line[1][2])) # 上证涨跌幅
        zjlx_sz_close.append(float(line[1][3])) # 深证收盘价
        #zjlx_sz_close_change.append(float(line[1][4])) # 深证涨跌幅
        zjlx_inflow_main.append(float(line[1][5])) # 主力净流入净额
        zjlx_inflow_super_large.append(float(line[1][7])) # 超大单净流入净额
        zjlx_inflow_large.append(float(line[1][9])) # 大单净流入净额
        zjlx_inflow_medium.append(float(line[1][11])) # 中单净流入净额
        zjlx_inflow_small.append(float(line[1][13])) # 小单净流入净额
    return {"categoryDate": zjlx_date, "sh_close": zjlx_sh_close, "sz_close": zjlx_sz_close, "main": zjlx_inflow_main, "super_large": zjlx_inflow_super_large, "large": zjlx_inflow_large, "medium": zjlx_inflow_medium, "small": zjlx_inflow_small}


def split_rzrq_data(data):
    for line in data:
        if line[1][0] in zjlx_date:
            rzrq_date.append(line[1][0]) # 日期
            rzrq_line_rz.append(float(line[1][1])) # 融资
            rzrq_line_rq.append(float(line[1][2])) # 融券
    return {"categoryDate": rzrq_date, "rz": rzrq_line_rz, "rq": rzrq_line_rq}

def add_string_to_csv_memory(csv_file_path, csv_file_path_rzrq=None):
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

    try:
        header_flag = 0
        with open(csv_file_path_rzrq, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            for fields in csv_reader:
                if header_flag == 0:
                    header_flag = 1
                    continue  # 跳过标题行
                data_lines_rzrq.append((fields[0], fields))                
    except FileNotFoundError:
        print(f"文件 {csv_file_path} 不存在，将创建新列表")

    # 按日期排序
    try:
        # 尝试按日期对象排序
        data_lines.sort(key=lambda x: x[0], reverse=False)
        data_lines_rzrq.sort(key=lambda x: x[0], reverse=False)
    except:
        # 如果日期对象排序失败，尝试按字符串排序
        data_lines.sort(key=lambda x: str(x[0]), reverse=False)
        data_lines_rzrq.sort(key=lambda x: str(x[0]), reverse=False)


def line_zjlx_sh_sz_value(zjlx_data) -> Line:
    c = (Line()
        .add_xaxis(xaxis_data=zjlx_date)
        .add_yaxis(
            series_name="主力净流入",
            y_axis=zjlx_data['main'],
            is_smooth=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#0000FF"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="大单净流入",
            y_axis=zjlx_data['large'],
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#FF0000"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="超大单净流入",
            y_axis=zjlx_data['super_large'],
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#22D44E"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="中单净流入",
            y_axis=zjlx_data['medium'],
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#22D44E"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="小单净流入",
            y_axis=zjlx_data['small'],
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#A50C8494"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="上海综指收盘价涨跌幅",
            y_axis=zjlx_data['sh_close'],
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#E7F70C"),  # 添加这一行定义颜色
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


def line_zjlx_standardize_sh_sz_value(zjlx_data, rzrq_data) -> Line:
    v_rz = tdx.standardize(rzrq_data['rz'])

    c = (Line()
        .add_xaxis(xaxis_data=zjlx_date)
        .add_yaxis(
            series_name="融资余额",
            y_axis=v_rz,
            is_smooth=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#12011D"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )        
        .add_yaxis(
            series_name="主力净流入-汇总",
            y_axis=tdx.standardize(zjlx_data['main']),
            is_smooth=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5, type_="dashed"),
            itemstyle_opts=opts.ItemStyleOpts(color="#0000FF"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="大单净流入",
            y_axis=tdx.standardize(zjlx_data['large']),
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#FF0000"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="超大单净流入",
            y_axis=tdx.standardize(zjlx_data['super_large']),
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#22D44E"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="小单净流入",
            y_axis=tdx.standardize(zjlx_data['small']),
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#8B0B7093"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="上海综指收盘价涨跌幅",
            y_axis=tdx.standardize(zjlx_data['sh_close']),
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5, type_="dashed"),
            itemstyle_opts=opts.ItemStyleOpts(color="#E7F70C"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        ) 
        .add_yaxis(
            series_name="深成指收盘价涨跌幅",
            y_axis=tdx.standardize(zjlx_data['sz_close']),
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5, type_="dashed"),
            itemstyle_opts=opts.ItemStyleOpts(color="#C4D10D"),  # 添加这一行定义颜色
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
    '''
    # 将注释添加到HTML模板中
    c.add_js_funcs("""
        var comment = document.createElement('div');
        comment.innerHTML = '在两市的收盘价和金额 <p style="color: red;">标准化对比中</p>，<br>注意观察  小单，大单 > +-2的情况 和收盘价上穿下穿 0轴的情况<br>2026-01-12到2026-01-13  <br>2026-02-27到2026-03-03 <p style="color: red;"><br>这段时间，金额及收盘点的走势，它们之间的上穿，下穿，间隔幅度，等相对关系来判断现在大致处于哪个阶段，来判断大盘整体的走势</p>';
        comment.style.position = 'absolute';
        comment.style.top = '600px'; // 根据需要调整位置
        comment.style.left = '250px'; // 根据需要调整位置
        document.body.appendChild(comment);
    """)    
    '''
    return c

def chart_table_data(zjlx_data=None, rzrq_data=None):
    # prefer explicit data instead of relying on globals
    if zjlx_data is None:
        zjlx_data = {'categoryDate': [], 'main': [], 'super_large': [], 'large': [], 'medium': [], 'small': []}

    if rzrq_data is None:
        rzrq_data = {'categoryDate': [], 'rz': [], 'rq': []}

    tab = Tab()

    tab.add(line_zjlx_sh_sz_value(zjlx_data), "大盘资金流向与上综深综量对比-原始值")
    tab.add(line_zjlx_standardize_sh_sz_value(zjlx_data, rzrq_data), "融资和大盘资金流向与上综深综量对比-标准化")
    tab.render(f'{show_templates_comm_html_path}/zjlx_rzrq_line.html')



def main():
    # 读取已有CSV文件内容到内存
    zjlx_csv_file_path = dpzjlx_csv_path
    rzrq_csv_file_path = rzrq_csv_path
    add_string_to_csv_memory(zjlx_csv_file_path, rzrq_csv_file_path)
    all_zjlx_data = split_zjlx_data(data_lines)


    all_rzrq_data = split_rzrq_data(data_lines_rzrq)
  
    chart_table_data(zjlx_data=all_zjlx_data, rzrq_data=all_rzrq_data)

if __name__ == "__main__":
    main()
    
