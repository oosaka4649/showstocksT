import os
import numpy as np
from typing import List, Union
import sys
import requests
import json

# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
# 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minitools.tdxcomm import TDXData as tdx
from minitools import user_config as ucfg
show_templates_html_path = os.path.join(parent_dir, 'templates', ucfg.my_stocks_html_folder_name)
show_templates_comm_html_path = os.path.join(parent_dir, 'templates', ucfg.common_html_folder_name)

# 1. 目标 API URL 和请求头
tdx_url = 'http://127.0.0.1:17709/'
tdx_headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
}

# 当构造这类，没有设定定 start_date 和 end_date 时，默认值为 下面的设定
_start_date="2024-01-01"
_end_date=None

'''
AI平台直接调用方法
在WorkBuddy,CodeX或TdxClaw等AI平台中直接使用自然语言或Skill调取本地的TQ数据。
需要先开启支持TQ的通达信客户端。

POST http://127.0.0.1:17709/

method为TdxQuant中的函数方法，params为函数参数

在7.73版本的通达信客户端中，TQ接口已经支持了get_market_snapshot方法，可以获取股票的市场快照数据。
这个方法可以返回股票的最新价格、涨跌幅、成交量等信息，非常适合用来做实时数据分析和决策。

'''
class TDX_HTTP_API_BaseModel:
    
    def __init__(self, start_date=None, end_date=None):
        if start_date is not None:
            self.start_date = start_date
        else:
            self.start_date = _start_date
        if end_date is not None:
            self.end_date = end_date
        else:
            self.end_date = _end_date

    def _tdx_get_market_snapshot(self, stock_code):
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
        #print(json.dumps(response.json(), indent=4, ensure_ascii=False))  # 美化输出，确保中文显示正常
        result = response.json().get('result', {})
        #print(f"市场快照数据: {result}")
        open_price = result.get('Open')  # 获取 'result' 字段中的 'Open' 值 开盘价
        close_price = result.get('Now')  # 获取 'result' 字段中的 'Now' 值   当前价
        high_price = result.get('Max')  # 获取 'result' 字段中的 'Max' 值 最高价
        low_price = result.get('Min')   # 获取 'result' 字段中的 'Min' 值 最低价
        volume = result.get('Volume')   # 获取 'result' 字段中的 'Volume' 值 成交量
        amount = result.get('Amount')  # 获取 'result' 字段中的 'Amount' 值 金额
        return {
            "open": open_price,
            "close": close_price,
            "high": high_price,
            "low": low_price,
            "volume": volume,
            "amount": amount
        }  # 返回包含所有获取到的数据的字典


if __name__ == "__main__":

    stock_code = '688318.SH'
    start_date = "2025-01-01"
    runner = TDX_HTTP_API_BaseModel()
    chart_data = runner._tdx_get_market_snapshot(stock_code)
    print(f"获取到的市场快照数据: {chart_data}")