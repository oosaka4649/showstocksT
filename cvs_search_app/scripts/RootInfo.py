# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 13:59:46 2022

@author: bwu
"""

import os

class MainUtile:
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
    
    
    
    '''
    
    print(__file__)
    print(sys.argv[0])
    print(os.path.dirname(__file__))
    print(os.path.split(__file__)[-1])
    print(os.path.split(__file__)[-1].split('.')[0])
    对应的返回结果：
    
    D:/office3/python/python_py/compare/test.py
    D:/office3/python/python_py/compare/test.py
    D:/office3/python/python_py/compare
    test.py
    test  
    '''
    
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