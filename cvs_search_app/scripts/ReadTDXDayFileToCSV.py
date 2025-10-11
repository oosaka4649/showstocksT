# -*- coding: utf-8 -*-
"""
Created on Sat Jun 25 20:12:07 2022

@author: bwu
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.RootInfo import MainUtile as utile

#直接对通达信下载的数据 二进制day文件进行转换成csv文件
import time
import pandas as pd
from struct import unpack


current_dir = os.path.dirname(os.path.abspath(__file__))
# 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)
stocks_csv_path = os.path.join(parent_dir, 'stockscsv')

class DayFileToCsv:
    def __init__(self, day_file=''):
        self.target_dir = stocks_csv_path
        self.day_file = day_file
        self.csv_file = ''
        self.target_csv_file = ''

    # 将通达信的日线文件转换成CSV格式
    def day2csv(self, day_file):
        # 以二进制方式打开源文件
        source_file = open(day_file, 'rb')
        buf = source_file.read()
        source_file.close()

        # 打开目标文件，后缀名为CSV
        target_file = open(self.target_csv_file, 'w', encoding='utf-8')
        buf_size = len(buf)
        rec_count = int(buf_size / 32)
        begin = 0
        end = 32
        header = str(utile.CSV_HEADER_INFO[0]) + ','\
                 + str(utile.CSV_HEADER_INFO[1]) + ','\
                 + str(utile.CSV_HEADER_INFO[2]) + ','\
                 + str(utile.CSV_HEADER_INFO[3]) + ',' \
                    + str(utile.CSV_HEADER_INFO[4]) + ','\
                        + str(utile.CSV_HEADER_INFO[5]) + ',' \
                        + str(utile.CSV_HEADER_INFO[6]) + '\n'
        target_file.write(header)
        for i in range(rec_count):
            # 将字节流转换成Python数据格式
            # I: unsigned int
            # f: float
            a = unpack('IIIIIfII', buf[begin:end])
            # 处理date数据
            year = a[0] // 10000
            month = (a[0] % 10000) // 100
            day = (a[0] % 10000) % 100
            date = '{}-{:02d}-{:02d}'.format(year, month, day)

            line = date + ',' + str(a[1] / 100.0) + ',' + str(a[2] / 100.0) + ',' \
                   + str(a[3] / 100.0) + ',' + str(a[4] / 100.0) + ',' + str(a[5]) + ',' \
                   + str(a[6]) + '\n'
            target_file.write(line)
            begin += 32
            end += 32
        target_file.close()
        
       
    def transform_data_one(self, day_file, csv_file_path):
        # 保存csv文件的目录
        # 获取当前目录
        target = csv_file_path
        
        if not os.path.exists(target):
            os.makedirs(target)
            
        self.csv_file = utile.get_filename_without_extension(day_file) + '.csv'
        self.target_csv_file = target + '\\' + self.csv_file
                        
        source = day_file
        #day文件中，每32个字节存储了一根日线数据，各字节存储数据如下：
        #
        #00 ~ 03 字节：年月日, 整型
        #04 ~ 07 字节：开盘价*100，整型
        #08 ~ 11 字节：最高价*100，整型
        #12 ~ 15 字节：最低价*100，整型
        #16 ~ 19 字节：收盘价*100，整型
        #20 ~ 23 字节：成交额（元），float型
        #24 ~ 27 字节：成交量（股），整型
        #28 ~ 31 字节：（保留）
        self.day2csv(source)
        
    def getCsvFilePath(self):
        return self.target_csv_file
        
if __name__ == '__main__':
    t_day_file = 'C:\\zd_zsone\\vipdoc\\sh\\lday\\sh600475.day'
    tocsv = DayFileToCsv(t_day_file)
    # 程序开始时的时间
    time_start = time.time()

    tocsv.transform_data_one(tocsv.day_file, tocsv.target_dir)

    # 程序结束时系统时间
    time_end = time.time()

    print('程序所耗时间：', time_end - time_start)


