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
# 加载股票数据
def load_stock_data(file_path):
    """加载股票数据并返回收盘价序列"""
    try:
        # 尝试作为 vectorbt 格式加载
        return vbt.Data.load(file_path).get('close')
    except:
        try:
            # 尝试作为 CSV 加载
            df = pd.read_csv(file_path)
            # 保留必要列
            required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df = df[[col for col in required_cols if col in df.columns]]
            df.set_index('Date', inplace=True)
            #return vbt.Data.from_data(df).get('Close')
            return df.get('Close')
        except Exception as e:
            print(f"加载数据失败: {e}")
            return None


def simple_backtest(file_path):
    """
    简单的均线交叉策略回测示例
    """
    return_info = ''
    # 加载数据
    close = load_stock_data(file_path)

    if close is not None:
        return_info += f"成功加载数据: {len(close)} 个交易日\n"
        print(f"成功加载数据: {len(close)} 个交易日")
        
        # 简单分析
        fast_ma = vbt.MA.run(close, 5)
        slow_ma = vbt.MA.run(close, 10)
        slow_ma_60 = vbt.MA.run(close, 60)
        
        # 计算RSI
        rsi = vbt.RSI.run(close)
        
        # 绘制图表
        fig = close.vbt.plot()
        fast_ma.ma.vbt.plot(fig=fig, trace_kwargs=dict(name='5日均线'))
        slow_ma.ma.vbt.plot(fig=fig, trace_kwargs=dict(name='10日均线'))
        #fig.show()
        
        # 打印最新指标值
        print(f"最新收盘价: {close.iloc[-1]}")
        return_info += f"最新收盘价: {close.iloc[-1]}\n"
        try:
            entries = fast_ma.ma_crossed_above(slow_ma_60)
            exits = fast_ma.ma_crossed_below(slow_ma)
            pf = vbt.Portfolio.from_signals(close, entries, exits, init_cash=100000)
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

