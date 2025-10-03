# -*- coding: utf-8 -*-
"""
Created on Sat Jun 25 20:12:07 2022

@author: bwu
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import constant as constant
from RootInfo import MainUtile as utile

#直接对通达信下载的数据 二进制day文件进行转换成csv文件
import time
import pandas as pd
from struct import unpack

class DayFileToCsv:
    def __init__(self, day_file='', target_dir=''):
        self.target_dir = target_dir
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
        header = str(constant.CSV_HEADER_INFO[0]) + ','\
                 + str(constant.CSV_HEADER_INFO[1]) + ','\
                 + str(constant.CSV_HEADER_INFO[2]) + ','\
                 + str(constant.CSV_HEADER_INFO[3]) + ',' \
                    + str(constant.CSV_HEADER_INFO[4]) + ','\
                        + str(constant.CSV_HEADER_INFO[5]) + ',' \
                        + str(constant.CSV_HEADER_INFO[6]) + '\n'
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
        
        
    # 将通达信的日线文件转换成CSV格式object
    '''
        另外，用户可能希望这个方法灵活，能够处理不同的数据类型，并且允许指定CSV的格式参数，比如分隔符、编码等。因此，方法需要参数来接收这些选项。

        可能的步骤：

        1. 创建一个StringIO或BytesIO对象。

        2. 将数据转换为CSV格式并写入这个内存对象。

        3. 将内存对象的指针移动到起始位置，以便读取内容。

        4. 返回这个内存对象。

        需要考虑到用户是否使用pandas。如果用户的数据是DataFrame，使用to_csv是最直接的方式。如果不是，可能需要将数据转换为CSV格式的字符串，再写入内存对象。或者使用csv模块的writer来处理。

        另外，是否需要处理不同的数据类型？比如，如果用户传入的是一个字典列表，可能需要更复杂的处理来生成CSV的头部和行。

        可能的代码结构：

        def create_csv_in_memory(data, **kwargs):

        import io

        # 处理数据，生成CSV内容

        # 返回StringIO或BytesIO对象

        参数方面，可能需要data作为必选参数，以及分隔符、编码、是否包含头部等选项。如果用户想要BytesIO，可能需要指定返回类型，或者根据编码自动选择。

        例如，如果用户需要字节流，可以使用BytesIO，并将字符串编码为指定格式（如utf-8）。否则，使用StringIO。

        测试案例方面，可能需要传入一个DataFrame或列表数据，检查返回的对象是否正确包含CSV内容。

        可能的问题：如果用户的数据结构复杂，比如嵌套结构，可能需要更复杂的处理。但根据用户的问题描述，可能只需要处理二维表格式数据。

        总结，方法需要：

        - 支持多种数据输入（DataFrame、列表的列表、字典列表等）

        - 使用StringIO或BytesIO

        - 允许自定义CSV参数（如分隔符、是否包含索引等）

        - 返回内存对象，可以调用getvalue()获取内容

        现在需要编写具体的代码，并确保示例能够运行。

        以下是一个 Python 方法，可将数据转换为 CSV 格式并保存在内存对象中（使用 io.StringIO 或 io.BytesIO），支持 pandas.DataFrame 和原生 Python 数据结构：

        python
        Copy
        import io
        import csv
        from typing import Union, Any
        import pandas as pd

        def create_csv_in_memory(
            data: Union[pd.DataFrame, list],
            use_bytes: bool = False,
            **csv_kwargs: Any
        ) -> Union[io.StringIO, io.BytesIO]:
            """
            将数据转换为 CSV 格式并保存在内存对象中

            :param data: 输入数据，支持 pandas.DataFrame 或 Python 二维列表/字典列表
            :param use_bytes: 是否返回字节流对象 (BytesIO)，默认为文本流 (StringIO)
            :param csv_kwargs: 传递给 csv.writer 或 DataFrame.to_csv() 的参数
                        (例如 delimiter=',', index=False, encoding='utf-8')
            :return: io.StringIO 或 io.BytesIO 对象，包含 CSV 数据
            """
            # 创建内存对象
            if use_bytes:
                memory_obj = io.BytesIO()
                csv_encoding = csv_kwargs.get('encoding', 'utf-8')
            else:
                memory_obj = io.StringIO()
                csv_encoding = None

            # 处理 pandas.DataFrame
            if isinstance(data, pd.DataFrame):
                data.to_csv(memory_obj, **csv_kwargs)
            
            # 处理 Python 原生数据结构（二维列表或字典列表）
            else:
                # 如果是字典列表，自动提取表头
                if data and isinstance(data[0], dict):
                    headers = list(data[0].keys())
                    rows = [list(item.values()) for item in data]
                else:
                    headers = None
                    rows = data

                # 写入 CSV
                writer = csv.writer(memory_obj, **csv_kwargs)
                if headers:
                    writer.writerow(headers)
                writer.writerows(rows)

            # 重置指针到起始位置以便读取
            memory_obj.seek(0)

            # 如果是字节流需要编码
            if use_bytes and isinstance(memory_obj, io.BytesIO):
                memory_obj.write(memory_obj.getvalue().encode(csv_encoding))
                memory_obj.seek(0)

            return memory_obj
        使用示例
        示例 1: 处理 pandas DataFrame
        python
        Copy
        import pandas as pd

        # 创建测试 DataFrame
        df = pd.DataFrame({
            "Name": ["Alice", "Bob", "Charlie"],
            "Age": [25, 30, 35],
            "City": ["New York", "London", "Tokyo"]
        })

        # 生成 CSV 内存对象
        csv_memory = create_csv_in_memory(df, index=False)

        # 读取内容
        print(csv_memory.getvalue())

        # 输出结果：
        # Name,Age,City
        # Alice,25,New York
        # Bob,30,London
        # Charlie,35,Tokyo
        示例 2: 处理原生 Python 数据结构
        python
        Copy
        # 二维列表数据
        data_list = [
            ["Name", "Age", "City"],
            ["Alice", 25, "New York"],
            ["Bob", 30, "London"]
        ]

        # 字典列表数据（自动提取表头）
        data_dicts = [
            {"Name": "Alice", "Age": 25, "City": "New York"},
            {"Name": "Bob", "Age": 30, "City": "London"}
        ]

        # 生成 CSV 字节流（指定分隔符）
        csv_bytes = create_csv_in_memory(
            data_dicts,
            use_bytes=True,
            delimiter='|',
            encoding='utf-8'
        )

        print(csv_bytes.getvalue().decode('utf-8'))

        # 输出结果：
        # Name|Age|City
        # Alice|25|New York
        # Bob|30|London
        关键特性
        双模式返回

        use_bytes=False → 返回 io.StringIO（文本流，默认）

        use_bytes=True → 返回 io.BytesIO（字节流，适合二进制传输）

        数据兼容性

        支持 pandas.DataFrame（自动调用 to_csv()）

        支持 Python 原生数据：

        二维列表（例如 [[header1, header2], [row1, row2]]）

        字典列表（自动提取表头）

        参数透传
        可通过 **csv_kwargs 指定 CSV 格式参数：

        python
        Copy
        create_csv_in_memory(
            data,
            delimiter=';',   # 自定义分隔符
            index=True,       # 保留 DataFrame 索引
            quoting=csv.QUOTE_NONNUMERIC  # 非数字内容加引号
        )
        内存高效
        直接操作内存对象，避免磁盘 I/O 开销，适合网络传输或临时处理。    
    '''        
        
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
    t_day_file = 'C:\\zd_zsone\\vipdoc\\sh\\lday\\sh600168.day'
    t_csv_path = 'C:\\tmp\\csv'
    tocsv = DayFileToCsv(t_day_file, t_csv_path)
    # 程序开始时的时间
    time_start = time.time()

    tocsv.transform_data_one(tocsv.day_file, tocsv.target_dir)

    # 程序结束时系统时间
    time_end = time.time()

    print('程序所耗时间：', time_end - time_start)


