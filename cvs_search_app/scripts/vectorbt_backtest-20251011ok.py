import vectorbt as vbt
import pandas as pd
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
    # 文件路径
    #file_path = 'D:\\python\\showstocksT\\cvs_search_app\\stockscsv\\sh600475.csv'

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
        print(f"最新RSI值: {rsi.rsi.iloc[-1]:.2f}")
        return_info += f"最新RSI值: {rsi.rsi.iloc[-1]:.2f}\n"
        print(f"5日均线: {fast_ma.ma.iloc[-1]:.2f}")
        return_info += f"5日均线: {fast_ma.ma.iloc[-1]:.2f}\n"
        print(f"10日均线: {slow_ma.ma.iloc[-1]:.2f}")
        return_info += f"10日均线: {slow_ma.ma.iloc[-1]:.2f}\n"
        try:
            entries = fast_ma.ma_crossed_above(slow_ma_60)
            exits = fast_ma.ma_crossed_below(slow_ma)
            pf = vbt.Portfolio.from_signals(close, entries, exits, init_cash=100000)

            '''
            #        打印回测结果
                    print('1---输出总收益')
                    print(pf.total_profit())
                    print('2---输出总收益率')
                    print(pf.total_return())
                    #pf.stats().to_csv('D:\\python\\showstocksT\\cvs_search_app\\stockscsv\\backtest_results.csv')
                    # Accessing trade details
                    trades = pf.trades.records_readable
                    #print("\n交易详细清单:")
                    trades.to_csv('D:\\python\\showstocksT\\cvs_search_app\\stockscsv\\trade_details.csv')
                    pf.plot().show()
            '''
            return return_info, pf
        except Exception as e:
            print(f"加载数据失败: {e}")
            return_info = f"加载数据失败: {e}"
            return return_info
    else:
        print("无法加载数据，请检查文件路径和格式")
        return_info = "无法加载数据，请检查文件路径和格式"
        return return_info

