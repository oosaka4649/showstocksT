from tdxcomm import TDXData as tdx
from typing import List, Union
import user_config as ucfg

from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Grid

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

def split_data(data):
    category_data = []
    values = []
    closes = []

    '''
        date         开        收        最低       最高       量
    ["2004-01-02", 10452.74, 10409.85, 10367.41, 10554.96, 168890000],
      data 结构
      
    '''
    for i, tick in enumerate(data):
        stock_date = tick[0]
        if stock_date in line_date:
            category_data.append(tick[0]) # 日期
            # convert volume to millions and round to 2 decimal places
            values.append(round(float(tick[6]) / 1000000, 2))  # 量
            closes.append(float(tick[2])) # 收盘价
    return {"categoryData": category_data, "values": values, "closes": closes}

def draw_charts(stock_name='融资融券', sh_data=None, sz_data=None):
    # prefer explicit data instead of relying on globals
    if sh_data is None:
        sh_data = {'categoryData': [], 'values': [], 'closes': []}
    if sz_data is None:
        sz_data = {'categoryData': [], 'values': [], 'closes': []}

    line = (
        Line()
        .add_xaxis(xaxis_data=line_date)
        .add_yaxis(
            series_name="融资",
            y_axis=line_rz,
            is_smooth=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#0000FF"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="融券",
            y_axis=line_rq,
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#FF0000"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="上海综指",
            y_axis=sh_data['values'],
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#22D44E"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="深综指",
            y_axis=sz_data['values'],
            is_smooth=True,
            is_connect_nones=True,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            itemstyle_opts=opts.ItemStyleOpts(color="#E2BB0E"),  # 添加这一行定义颜色
            label_opts=opts.LabelOpts(is_show=False),
        )        
        #
        .set_global_opts(title_opts=opts.TitleOpts(title=f"{stock_name}与上综指、深成指对比"),
                                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                                yaxis_opts=opts.AxisOpts(
                                    type_="value",
                                    axistick_opts=opts.AxisTickOpts(is_show=True),
                                    splitline_opts=opts.SplitLineOpts(is_show=True),
                                ),
                                xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False),
                         )
    )

    # Grid Overlap + Bar
    grid_chart = Grid(
        init_opts=opts.InitOpts(
            width="1000px",
            height="800px",
            animation_opts=opts.AnimationOpts(animation=False),
        )
    )
    
    grid_chart.add(
        line,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", height="50%"),
    )
    grid_chart.render(f'{show_templates_comm_html_path}/rzrq_line.html')


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

def main():
    '''
    sh999999.day 上综指
    sz399001.day 深成指
    '''
    # 读取已有CSV文件内容到内存
    csv_file_path = rzrq_csv_path
    add_string_to_csv_memory(csv_file_path)
    split_rzrq_data(data_lines)
  
#    print(f"融资融券数据点数量: {line_date}")

    tdx_sh_datas = tdx('999999')
    tdx_sh_datas.getStockDayFile()
    tdx_sh_datas.creatstocKDataList()
    sh_data = split_data(tdx_sh_datas.getTDXStockKDatas())
 #   print(f"上综指数据点数量: {len(sh_data['categoryData'])}")
 #   print(f"上综指日期范围: {sh_data['categoryData']}")
    tdx_sz_datas = tdx('399001')
    tdx_sz_datas.getStockDayFile()
    tdx_sz_datas.creatstocKDataList()
    sz_data = split_data(tdx_sz_datas.getTDXStockKDatas())
    # pass processed data explicitly
    draw_charts(sh_data=sh_data, sz_data=sz_data)

if __name__ == "__main__":
    main()
    
