# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 13:59:46 2022

@author: bwu
"""

import os
import dateutil as du
import time
import numpy as np

class MainUtile:
    STOCK_CODE_NUM = {'6':'sh','3':'sz','0':'sz','4':'bj','8':'bj','9':'bj'}  # 股票代码前缀
    CSV_HEADER_INFO = ['Date','Open','High','Low','Close','Amount','Volume']

    BACK_TEST_1 = """
        股价高于60日均线时，5日均线上穿60日均线买入，5日均线下穿10日均线卖出。    
    """

    BACK_TEST_ALL_1 = """
        股价高于10日均线时，5日均线上穿10日均线买入，5日均线下穿10日均线卖出。    
    """

    BACK_TEST_Ma_Week = """
        5日均线，上穿 5日周均线买入，股价跌破5日均线卖    
    """

    def __init__(self):
        pass

    @staticmethod 
    def get_project_path():
        project_path = os.path.abspath(os.path.join(
                        os.path.dirname(__file__), ".."))
        return project_path
    
    def get_file_base_dir(self, file_full_path):
        base_dir = os.path.dirname(os.path.abspath(file_full_path))
        return base_dir
    
    @staticmethod
    def get_file_dir_name(self, file_full_path):
        base_dir = os.path.dirname(os.path.abspath(file_full_path))
        file_name = os.path.split(file_full_path)[-1]
        return base_dir, file_name  
    
    @staticmethod
    def get_filename_without_extension(file_path):
        # 获取文件名（包括后缀）
        filename_with_extension = os.path.basename(file_path)
        # 去掉后缀
        filename_without_extension = os.path.splitext(filename_with_extension)[0]
        return filename_without_extension
    
    def get_stock_prefix(stock_code):
        """根据股票代码获取前缀 第一位数字 6=sh 0,3=sz 9=bj"""
        if len(stock_code) != 6 or not stock_code.isdigit():
            raise ValueError("股票代码应为6位数字")
        prefix = MainUtile.STOCK_CODE_NUM.get(stock_code[0], 'unknown')
        return prefix
    
    def get_backtest_info(back_type):
        if back_type == 1:
            return MainUtile.BACK_TEST_ALL_1
        elif back_type == 2:
            return "均线策略二"
        elif back_type == 3:
            return "均线策略三"
        else:
            return "未知策略"
        
    def generate_report(back_test_info, total_return, total_profit, pf_stats, stack_info):
        
        """生成报告字符串"""
        report = f"""
============================================
        股票分析报告 分析日期: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}
============================================
回测策略: 
{back_test_info}
当前数据总数及价格: 
{stack_info}
--------------------------------------------
[主要财务指标]
总收益: {total_profit}
汇总: 
{pf_stats}
"""        
        report += "============================================"
        return report.strip()
    

    # 这是一个经典的线性插值（Linear Interpolation）问题。为了实现这个逻辑，我们需要找到每一段由 None 组成的“空洞”，获取空洞前后的边界值，然后计算步长进行填充。
    @staticmethod
    def fill_all_missing(data):
        if not data or len(data) < 2:
            return data

        # 定义一个内部函数，统一判断 None 或 NaN
        def is_missing(x):
            if x is None:
                return True
            try:
                return np.isnan(x)
            except:
                return False

        # 1. 寻找第一个有效数字的索引
        first_val_idx = -1
        for k in range(len(data)):
            if not is_missing(data[k]):
                first_val_idx = k
                break
                
        if first_val_idx == -1: # 全是空值
            return data

        # 2. 填充中间部分 (线性插值)
        i = first_val_idx
        while i < len(data) - 1:
            if not is_missing(data[i]) and is_missing(data[i+1]):
                left_idx = i
                right_idx = i + 1
                # 寻找右侧下一个有效值
                while right_idx < len(data) and is_missing(data[right_idx]):
                    right_idx += 1
                
                if right_idx < len(data): # 找到了右边界
                    count = right_idx - left_idx
                    step = (data[right_idx] - data[left_idx]) / count
                    for j in range(1, count):
                        data[left_idx + j] = round(float(data[left_idx] + step * j), 2)
                    i = right_idx
                else: # 后面全是空值，退出中间填充
                    break
            else:
                i += 1

        # 3. 处理开头部分的 None/NaN (根据第一段趋势逆推)
        if first_val_idx > 0:
            # 找到填充后的第二个有效值来确定步长
            next_val_idx = first_val_idx + 1
            if next_val_idx < len(data) and not is_missing(data[next_val_idx]):
                step = data[next_val_idx] - data[first_val_idx]
                # 向前逆推
                for j in range(first_val_idx - 1, -1, -1):
                    data[j] = round(float(data[j + 1] - step), 2)
                    
        return data