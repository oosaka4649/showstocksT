# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 13:59:46 2022

@author: bwu
"""

import os
import dateutil as du
import time

class MainUtile:
    STOCK_CODE_NUM = {'6':'sh','3':'sz','0':'sz','4':'bj','8':'bj','9':'bj'}  # 股票代码前缀
    CSV_HEADER_INFO = ['Date','Open','High','Low','Close','Amount','Volume']

    BACK_TEST_1 = """
        股价高于60日均线时，5日均线上穿60日均线买入，5日均线下穿10日均线卖出。    
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