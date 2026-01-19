import os
import pandas as pd
import sys
# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from tdxcomm import TDXData as tdx
from typing import List, Union
import user_config as ucfg

from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Grid

import talib
import numpy as np
from datetime import datetime


# 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)
show_templates_html_path = os.path.join(parent_dir, 'templates', ucfg.my_stocks_html_folder_name)
show_templates_comm_html_path = os.path.join(parent_dir, 'templates', ucfg.common_html_folder_name)

'''
这py脚本，用于给个股票代码，通过tdx，读取通达信的日线数据，计算，5 10 日均线，和周线，月线的5日均线
然后，将股票价格和各个均线的最后值进行比较，符合策略的，返回 true，否则返回 false
策略的英文是：strategy
    策略是：当前价格 + 5% > 5日均线 > 10日均线 > 周线5日均线 > 月线5日均线
'''


class StockMA_Strategy:
    def __init__(self, stock_code: str, startDay=None):
        self.stock_code = stock_code
        self.tdx_data = tdx(stock_code)
        self.tdx_data.getStockDayFile()
        self.tdx_data.creatstocKDataList(startDay)
        self.all_data = self.tdx_data.getTDXStockDWMDatas()
        self.chart_data = self.split_data(self.tdx_data.getTDXStockKDatas())
        self.stock_name = self.tdx_data.stock_name

    def evaluate_strategy(self) -> bool:
        # chart_data categoryData 全部日期  
        # values 全部日线数据 时间，开 收，低，高 量，金额  # output 'Date','Open','Close','Low','High','Volume','Amount'
        # volumes closes
        # 获取收盘价列表
        close_prices = self.chart_data["closes"]
        if len(close_prices) < 1:
            return False

        current_price = close_prices[-1]
        ma5 = self.calculate_ma(5, self.chart_data)[-1]
        ma10 = self.calculate_ma(10, self.chart_data)[-1]

        # all_data 包含 'Day_Data', 'Week_Data', 'Month_Data'
        # Day_Data
        # output 'Date','Open','Close','Low','High','Volume','Amount'
        # week, month 
        # 'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
        weekly_ma5 = self.calculate_ma_list(5, self.all_data['Week_Data'])[-1]
        monthly_ma5 = self.calculate_ma_list(5, self.all_data['Month_Data'])[-1]

        # 取得最后一天股价，计算涨幅，输出到画面
        last_data_str = self.all_data['Day_Data'][-1]
        last_before_date_close = float(self.all_data['Day_Data'][-2][2])  # 前一天收盘价
        last_close_price = float(last_data_str[2])
        price_change = ((last_close_price - last_before_date_close) / last_before_date_close) * 100
        #当前策略价格 = 当前价格 * 1.05
        strategy_prices = float(current_price) * 1.05

        print(f"股票代码: {self.stock_code}, 当前价格: {current_price}, 当前策略价格: {strategy_prices}, 5日均线: {ma5}, 10日均线: {ma10}, 周线5日均线: {weekly_ma5}, 月线5日均线: {monthly_ma5}")
        if (strategy_prices > ma5 and strategy_prices > ma10 and strategy_prices > weekly_ma5 and strategy_prices > monthly_ma5):
            return True, last_close_price, price_change
        return False, last_close_price, price_change

    def split_data(self, data):
        category_data = []
        values = []
        volumes = []
        closes = []

        '''
            date         开        收        最低       最高       量
        ["2004-01-02", 10452.74, 10409.85, 10367.41, 10554.96, 168890000],
        data 结构
        
        '''

        for i, tick in enumerate(data):
            category_data.append(tick[0]) # 日期
            values.append(tick) # 全部内容
            closes.append(tick[2]) # 收盘价
            # 元代码 是 tick 4 错了，应该是 tick 5 因为 4是 最高价，5才是量
            volumes.append([i, tick[5], 1 if tick[1] > tick[2] else -1])  # i 是序号 从 0 开始，如果 开始大于收盘 1 ，反之 -1 估计是标 量线颜色用 红 绿
        return {"categoryData": category_data, "values": values, "volumes": volumes, "closes": closes}

    '''
    手动算出 均线， day count是输入要算的几日均线 tudo 后面要搞搞 其他macd，rsi，cci，bolling什么的

    我修改了原来单纯的计算方法，改用 talib 库来计算均线，这样后面要计算其他指标也方便
    '''
    def calculate_ma(self, day_count: int, data):
        '''
        ta lib 使用 np.array 作为输入，但 pyecharts 需要 list 作为输出，所以这里做了转换，而且 数据类型为 double
        '''
        
        result = talib.SMA(np.array(data["closes"], dtype='double'), timeperiod=day_count)
        return result

    def calculate_ma_list(self, day_count: int, w_m_data):
        '''
        ta lib 使用 np.array 作为输入，但 pyecharts 需要 list 作为输出，所以这里做了转换，而且 数据类型为 double
        '''
        temp_closes = [row[4] for row in w_m_data if row[4] is not None]
        temp_w_m_ma = talib.SMA(np.array(temp_closes, dtype='double'), timeperiod=day_count)
        return temp_w_m_ma  

if __name__ == "__main__":
    stock_code = '600475'  # 华光环能
    strategy_instance = StockMA_Strategy(stock_code)
    strategy_result = strategy_instance.evaluate_strategy()
    print(f"股票代码 {stock_code} 符合均线策略要求: {strategy_result}")
