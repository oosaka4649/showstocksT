import vectorbt as vbt
import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.RootInfo import MainUtile as utile
'''
https://github.com/polakowo/vectorbt/tree/master/apps/candlestick-patterns

https://www.marketcalls.in/python/mastering-vectorbt-backtesting-and-optimization-part-1-python-tutorial.html

https://blog.csdn.net/zhangyunchou2015/article/details/147185207

'''

class vectorbt_back_test:
    def __init__(self, file_path=None, test_type=1):
        self.csv_file_path = file_path
        self.test_type = test_type
        
    # 加载股票数据
    def load_stock_data(self):
        """加载股票数据并返回收盘价序列"""
        try:
            # 尝试作为 vectorbt 格式加载
            return vbt.Data.load(self.csv_file_path).get('close')
        except:
            try:
                # 尝试作为 CSV 加载
                df = pd.read_csv(self.csv_file_path)
                # 保留必要列
                required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                df = df[[col for col in required_cols if col in df.columns]]
                df.set_index('Date', inplace=True)
                return df.get('Close')
            except Exception as e:
                print(f"加载数据失败: {e}")
                return None


    def simple_backtest(self):
        """
        简单的均线交叉策略回测示例
        """
        return_info = ''
        # 加载数据
        close = self.load_stock_data()

        if close is not None:
            return_info += f"成功加载数据: {len(close)} 个交易日\n"
            print(f"成功加载数据: {len(close)} 个交易日")

            # 计算RSI
            rsi = vbt.RSI.run(close)
            
            # 打印最新指标值
            print(f"最新收盘价: {close.iloc[-1]}")
            return_info += f"最新收盘价: {close.iloc[-1]}\n"
            try:
                entries, exits = get_ma_line_backtest_entry_exit(self.test_type, close)
                pf = vbt.Portfolio.from_signals(close, entries, exits, init_cash=100000)
                return_info = utile.generate_report(utile.get_backtest_info(self.test_type), pf.total_return(), pf.total_profit(), pf.stats(), return_info)
                return return_info, pf
            except Exception as e:
                print(f"加载数据失败: {e}")
                return_info = f"加载数据失败: {e}"
                return return_info
        else:
            print("无法加载数据，请检查文件路径和格式")
            return_info = "无法加载数据，请检查文件路径和格式"
            return return_info
        
def get_backtest_type_name(back_type):
    if back_type == 1:
        return "均线策略一"
    elif back_type == 2:
        return "均线策略二"
    elif back_type == 3:
        return "均线策略三"
    else:
        return "未知策略"
    
def get_ma_line_backtest_entry_exit(back_type, close):
        # 简单分析
    fast_ma = vbt.MA.run(close, 5)
    slow_ma = vbt.MA.run(close, 10)
    if back_type == 1:
        entries = fast_ma.ma_crossed_above(slow_ma)
        exits = fast_ma.ma_crossed_below(slow_ma)
    elif back_type == 2:
        entries = fast_ma.ma_crossed_above(slow_ma) & (close > slow_ma.ma)
        exits = fast_ma.ma_crossed_below(slow_ma) | (close < slow_ma.ma)
    elif back_type == 3:
        entries = fast_ma.ma_crossed_above(slow_ma) & (close > slow_ma.ma)
        exits = fast_ma.ma_crossed_below(slow_ma) | (close < slow_ma.ma)
    else:
        entries = pd.Series([False] * len(close), index=close.index)
        exits = pd.Series([False] * len(close), index=close.index)
    return entries, exits

