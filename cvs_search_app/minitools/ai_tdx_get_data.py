import os
import numpy as np
from tdxcomm import TDXData as tdx
from typing import List, Union
import user_config as ucfg
import sys
import requests
import json

# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
# 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)
show_templates_html_path = os.path.join(parent_dir, 'templates', ucfg.my_stocks_html_folder_name)
show_templates_comm_html_path = os.path.join(parent_dir, 'templates', ucfg.common_html_folder_name)

# 1. 目标 API URL 和请求头
tdx_url = 'http://127.0.0.1:17709/'
tdx_headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
}


'''
AI平台直接调用方法
在WorkBuddy,CodeX或TdxClaw等AI平台中直接使用自然语言或Skill调取本地的TQ数据。
需要先开启支持TQ的通达信客户端。

POST http://127.0.0.1:17709/

method为TdxQuant中的函数方法，params为函数参数

还在测试阶段，目前还不能用，报 错
requests.exceptions.ConnectionError: HTTPConnectionPool(host='127.0.0.1', port=17709):
Max retries exceeded with url: / (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000001960238C650>:
 Failed to establish a new connection: [WinError 10061] 由于目标计算机积极拒绝，无法连接。'))

'''
class TDX_AI_BaseModel:
    
    def __init__(self, start_date=None):
        self.start_date = start_date
        #self.end_date = end_date

    def _get_tdx_market_snapshot(self, stock_code):
        # 1. 目标 API URL 和请求头
        url = tdx_url
        headers = tdx_headers
        # 2. 准备要提交的数据（字典格式）
        payload = {
            "id":1,
            "method": "get_market_snapshot",
            "params": {
                "stock_code": stock_code
            }
        }

        # 3. 发送 POST 请求，使用 json= 参数自动编码为 JSON
        #response = requests.post(url, headers=headers, json=payload)

        response = requests.post(url, json=payload)

        # 4. 打印返回的结果
        print(response.json()) 


if __name__ == "__main__":

    '''
    
    # ---- 🚀 执行标准的两阶段定制化回测工作流 ----
    # 第一阶段：用默认配置获取股票基础特征
        # 指定你的实际股票数据
    stock_code = "300215"  # 替换为你想分析的股票代码
    stock_code = sys.argv[1]
    start_date = "2025-01-01" #日线级别最佳数据量：250 天 到 500 天（即 1 到 2 年的历史数据）。
    tdx_datas = tdx(stock_code)
    tdx_datas.getStockDayFile()
    tdx_datas.creatstocKDataList()
    all_data = tdx_datas.getTDXStockDWMDatas()
    '''
    stock_code = '688318.SH'
    start_date = "2025-01-01"
    runner = TDX_AI_BaseModel(start_date=start_date)
    chart_data = runner._get_tdx_market_snapshot(stock_code)