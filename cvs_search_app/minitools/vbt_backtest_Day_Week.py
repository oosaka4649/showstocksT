import vectorbt as vbt
import pandas as pd
import os
import sys
# 获取当前脚本的绝对路径，并找到其父目录（即 project 目录）
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
parent_dir = os.path.dirname(current_dir)
# 将父目录加入 sys.path
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from tdxcomm import TDXData as tdx
from typing import List, Union
import user_config as ucfg
from strategy_ma import StockMA_Strategy
from scripts.RootInfo import MainUtile as utile
'''
https://github.com/polakowo/vectorbt/tree/master/apps/candlestick-patterns

https://www.marketcalls.in/python/mastering-vectorbt-backtesting-and-optimization-part-1-python-tutorial.html

https://blog.csdn.net/zhangyunchou2015/article/details/147185207

'''


class VectorbtBacktest_DayWeek(StockMA_Strategy):
    def __init__(self, stock_code: str):
        super().__init__(stock_code)
        
    # 加载股票数据
    def load_stock_data(self):
        """加载股票数据并返回收盘价序列"""
        try:
            # 尝试作为 vectorbt 格式加载
            return self.chart_data
        except Exception as e:
            print(f"加载数据失败: {e}")
            return None


    def simple_backtest(self):
        """
        简单的均线交叉策略回测示例
        """
        return_info = ''

        chart_data_all = self.load_stock_data()
        # 加载数据
        close = chart_data_all['closes']
        float_close_list = [float(s) for s in close]

        st_day = chart_data_all['categoryData']
        # 2. 合并成 DataFrame
        vbt_df = pd.DataFrame({
            'Time': st_day,
            'Price': float_close_list
        })

        # 3. 转换时间格式并设定为 Index
        vbt_df['Time'] = pd.to_datetime(vbt_df['Time']) # 转换为时间对象
        vbt_df.set_index('Time', inplace=True)     # 设定为索引

        if float_close_list is not None:
            return_info += f"成功加载数据: {len(float_close_list)} 个交易日\n"
            print(f"成功加载数据: {len(float_close_list)} 个交易日")
            
            # 简单分析
            fast_ma = vbt.MA.run(vbt_df['Price'], 5)
            slow_ma = vbt.MA.run(vbt_df['Price'], 10)
            slow_ma_60 = vbt.MA.run(vbt_df['Price'], 60)
            
            # 计算RSI
            rsi = vbt.RSI.run(vbt_df)

            try:
                entries = fast_ma.ma_crossed_above(slow_ma_60)
                exits = fast_ma.ma_crossed_below(slow_ma)
                pf = vbt.Portfolio.from_signals(vbt_df['Price'], entries, exits, init_cash=100000)
                return_info = utile.generate_report(utile.BACK_TEST_1, pf.total_return(), pf.total_profit(), pf.stats(), return_info)
                return return_info, pf
            except Exception as e:
                print(f"加载数据失败: {e}")
                return_info = f"加载数据失败: {e}"
                return return_info
        else:
            print("无法加载数据，请检查文件路径和格式")
            return_info = "无法加载数据，请检查文件路径和格式"
            return return_info

if __name__ == "__main__":
    stock_code = '600475'  # 华光环能
    strategy_instance = VectorbtBacktest_DayWeek(stock_code)
    strategy_result = strategy_instance.simple_backtest()
    print(f"股票代码 {stock_code} 符合均线策略要求: {strategy_instance.stock_name}")
