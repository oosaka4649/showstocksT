import os
import numpy as np
from typing import List, Union
import sys
import requests
import json
import time
from datetime import datetime, timedelta

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

  
class TDX_Tools:
 
    def info2file(quant_result_file = None, quant_result_info = None):
        if quant_result_file is None:
            quant_result_file = 'ai_all_quant_today.txt'

        # 打开目标文件，后缀名为CSV
        target_file = open(quant_result_file, 'a', encoding='utf-8')
        target_file.write(quant_result_info)
        target_file.close()

    def get_Today_Str():
        time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        return time_str

    def print_trades_log(*reports):
        """
        过滤策略结果，如果有当日交易，输出，否则，只打印最大交易次数和每个策略结果
        打印到控制台（支持 3 列及以上任意多列）
        
        :param reports: 变长参数，传入多个策略输出交易
        :return info 每个股票的交易概略
                boolean 策略是否命中 true 命中
        """
        result = "\n"
        is_order = False
        if not reports:
            return
        
        indx = 1

        #总收益
        total_return = []
        #总计开仓次数 
        total_trades = []
        trades_logs = []
        last_trades_log = []
        for idx, total_info in enumerate(reports):
            total_return.append(total_info['total_return'])
            total_trades.append(total_info['total_trades'])
            trades_logs.append(total_info['trade_logs'])

        result += "最大总收益: " + str(max(total_return)) + "%\n"
        result += "最大交易次数: " + str(max(total_trades)) +  " 最小交易次数: " + str(min(total_trades)) + "\n"
        today_str = time.strftime('%Y-%m-%d')
        date_obj = datetime.strptime(today_str, '%Y-%m-%d')
        targte_day = date_obj + timedelta(days=-5)
        for idx, log in enumerate(trades_logs):
            trades_date = []
            for date_info in log:
                trades_date.append( date_info['date'])
            last_day = datetime.strptime(trades_date[-1], '%Y-%m-%d')
            found = last_day > targte_day
            if found:
                is_order = True
                result += str(idx) + "\n" + json.dumps(log[-2], ensure_ascii=False) + "\n" + json.dumps(log[-1], ensure_ascii=False) + "\n"
                last_trades_log.append(json.dumps(log[-1], ensure_ascii=False))

        return result, is_order, last_trades_log
    

    def print_folder_trades_log(*reports):
        """
由于扫描全部文件夹里面文件，而且是极端策略，本来内容不多，所以将所有策略的交易日志都打印出来，方便分析。
        
        :param reports: 变长参数，传入多个策略输出交易
        :return info 每个股票的交易概略
                boolean 策略是否命中 true 命中
        """
        result = "\n"
        is_order = False
        if not reports:
            return
        
        indx = 1

        #总收益
        total_return = []
        #总计开仓次数 
        total_trades = []
        trades_logs = []
        last_trades_log = []
        for idx, total_info in enumerate(reports):
            total_return.append(total_info['total_return'])
            total_trades.append(total_info['total_trades'])
            trades_logs.append(total_info['trade_logs'])

        result += "最大总收益: " + str(max(total_return)) + "%\n"
        result += "最大交易次数: " + str(max(total_trades)) +  " 最小交易次数: " + str(min(total_trades)) + "\n"
        for idx, log in enumerate(trades_logs):
            trades_date = []
            for date_info in log:
                trades_date.append( date_info['date'])
            if len(trades_date) > 0:
                is_order = True
                last_trades_log = log

        return result, is_order, last_trades_log    

if __name__ == "__main__":

    stock_code = '688318.SH'
    start_date = "2025-01-01"
    runner = TDX_HTTP_API_BaseModel()
    chart_data = runner._tdx_get_market_snapshot(stock_code)
    print(f"获取到的市场快照数据: {chart_data}")