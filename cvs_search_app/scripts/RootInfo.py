# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 13:59:46 2022

@author: bwu
"""

import os

class MainUtile:
    STOCK_CODE_NUM = {'6':'sh','3':'sz','0':'sz','4':'bj','8':'bj','9':'bj'}  # 股票代码前缀
    CSV_HEADER_INFO = ['Date','Open','High','Low','Close','Amount','Volume']

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