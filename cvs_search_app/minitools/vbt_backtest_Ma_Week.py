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

#from tdxcomm import TDXData as tdx
from typing import List, Union
import user_config as ucfg
from strategy_ma import StockMA_Strategy
from scripts.RootInfo import MainUtile as utile
'''
根据 VectorbtBacktest_DayWeek  改编
原因是，VectorbtBacktest_DayWeek 感觉有点怪，一般指标都是短期上穿长期，是交易点，但 VectorbtBacktest_DayWeek 是 周穿日均线
   虽然，目前看，在大多数股票中表现不错，大部是30%以上收益，但原因不知道
   每次都是把余额全部买入，也就是满仓操作，但看来效果也不错
   但这个策略观察看来，每个股票全年也就交易7-9次，10次算多的

这次，对 VectorbtBacktest_DayWeek 进行修改，就是用短期上穿长期，看看效果怎么样
   策略是  买入时机是 5日均线上穿 周均线，卖出不变，就是股价跌穿5日均线

    结果是不好 000686 使用 策略1 712%收益，改这个只有 400%左右
            600158 使用 策略1 463%收益，改这个只有 -62%


这函数的意义，是搞清楚了，
                entries = fast_ma.ma_crossed_above(slow_ma_w) # 5日上穿周 买
                exits = close_indicator_obj.close_crossed_below(fast_ma.ma) #股价下穿5日均线卖

close_indicator_obj.close_crossed_below  收盘价，下穿 均线  close_indicator_obj 收盘价对象， close crossed below 收盘价下穿
fast_ma.ma_crossed_above  均线对象 上穿  fast_ma 均线对象  fast_ma.ma_crossed_above 均线对象的均线 上穿

'''


class VectorbtBacktest_MaWeek(StockMA_Strategy):
    def __init__(self, stock_code: str):
        super().__init__(stock_code)

    def simple_backtest(self):
        """
        简单的均线交叉策略回测示例
        """
        return_info = ''
        # 加载股票数据
        chart_data_all = self.chart_data
        # 加载close 数据
        close = chart_data_all['closes']
        float_close_list = [float(s) for s in close]

        #加载周线数据
        w_data_df = self.all_data['Week_Data']
        w_data = self.tdx_data.calculate_W_ma_list(5,w_data_df, self.chart_data)
        #填充None
        w_data_list = utile.fill_all_missing(w_data)
    
        m_data_df = self.all_data['Month_Data']
        m_data = self.tdx_data.calculate_M_ma_list(5, m_data_df, self.chart_data)
        m_data_list = utile.fill_all_missing(m_data)

        st_day = chart_data_all['categoryData']
        # 2. 合并成 DataFrame
        vbt_df = pd.DataFrame({
            'Time': st_day,
            'Price': float_close_list,
            'wPrice': w_data_list,
            'mPrice': m_data_list
        })

        # 3. 转换时间格式并设定为 Index
        vbt_df['Time'] = pd.to_datetime(vbt_df['Time']) # 转换为时间对象
        vbt_df.set_index('Time', inplace=True)     # 设定为索引

        if float_close_list is not None:
            return_info += f"成功加载数据: {len(float_close_list)} 个交易日\n"
            print(f"成功加载数据: {len(float_close_list)} 个交易日")
            
            
            # 1. 定义一个简单的计算函数（直接返回原数据）
            def get_raw_price(close):
                return close

            # 2. 创建一个指标工厂
            RawIndicator = vbt.IndicatorFactory(
                class_name="RawPrice",
                short_name="raw",
                input_names=["close"],
                output_names=["value"]
            ).from_apply_func(get_raw_price)

            # 3. 运行并转换 df['close']
            close_indicator_obj = RawIndicator.run(vbt_df['Price']) 
            
            
            # 简单分析
            fast_ma = vbt.MA.run(vbt_df['Price'], 5)
            fast_ma_10 = vbt.MA.run(vbt_df['Price'], 10)
            slow_ma_w = vbt.MA.run(vbt_df['wPrice'], 5)
            slow_ma_m = vbt.MA.run(vbt_df['mPrice'], 5)
            
            # 计算RSI
            rsi = vbt.RSI.run(vbt_df)

            try:
                '''
                    # 1. 计算 5 日均线指标对象
                    # vbt.MA.run 返回的对象自带交叉判断方法
                    ma = vbt.MA.run(price_series, window=window)
                    
                    # 2. 生成信号
                    # close_crossed_above: 当价格从下方穿过均线时返回 True
                    entries = ma.close_crossed_above(ma.ma)
                    
                    # close_crossed_below: 当价格从上方跌破均线时返回 True
                    exits = ma.close_crossed_below(ma.ma)
                '''
                #entries = slow_ma_w.close_crossed_above(fast_ma.ma)   # 周上穿股价  买ma_crossed_above
                #exits = fast_ma.ma_crossed_below(fast_ma_10)          # 5日下穿10日 卖

                entries = fast_ma.ma_crossed_above(slow_ma_w) # 5日上穿周 买
                #exits = fast_ma.close_crossed_above(fast_ma.ma)
                exits = close_indicator_obj.close_crossed_below(fast_ma.ma) #股价下穿5日均线卖

                pf = vbt.Portfolio.from_signals(vbt_df['Price'], entries, exits, init_cash=100000)
                return_info = utile.generate_report(utile.BACK_TEST_Ma_Week, pf.total_return(), pf.total_profit(), pf.stats(), return_info)
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
    strategy_instance = VectorbtBacktest_MaWeek(stock_code)
    strategy_result = strategy_instance.simple_backtest()
    print(f"股票代码 {stock_code} 符合均线策略要求: {strategy_instance.stock_name}")
