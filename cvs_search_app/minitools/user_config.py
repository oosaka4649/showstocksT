#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
用户设置文件

"""

# 配置部分开始
debug = False  # 是否开启调试日志输出  开=True  关=False

# 目录需要事先手动建立好，不然程序会出错
tdx = {
    'tdx_path': 'c:/zd_zsone',  # 指定通达信目录  tdx_day_file_path = 'C:\\zd_zsone\\vipdoc\\'

    #下面是元代码，后面根据实际修改
    'csv_lday': 'd:/TDXdata/lday_qfq',  # 指定csv格式日线数据保存目录
    'pickle': 'd:/TDXdata/pickle',  # 指定pickle格式日线数据保存目录
    'csv_index': 'd:/TDXdata/index',  # 指定指数保存目录
    'csv_cw': 'd:/TDXdata/cw',  # 指定专业财务保存目录
    'csv_gbbq': 'd:/TDXdata',  # 指定股本变迁保存目录
    'pytdx_ip': '218.6.170.55',  # 指定pytdx的通达信服务器IP
    'pytdx_port': 7709,  # 指定pytdx的通达信服务器端口。int类型
}

# 将来这里放我的股票池
my_stocks_list = [  # 通达信需要转换的指数文件。通达信按998查看重要指数
    #'999999',  # 上证指数
    #'000300',  # 沪深300
    #'399001',  # 深成指
    '300215', '301246', '000686', '600526', '600158','600233', '300251', '002303', '002852'
]

# 配置部分结束
