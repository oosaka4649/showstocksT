'''
新策略的数学建模核心我们如何用纯数学和向量化语言来严格定义“低位、长期盘整、突然放量上涨”？

长期盘整（Volatility Squeeze）：使用滚动窗口内价格的标准差与布林带带宽（Bandwidth）。

如果过去较长一段时间内（如 30 天）波动率持续收敛，说明主力在暗中吸筹或市场交投极度死寂。

股价低位（Low Relative Price）：使用长周期的相对价格分位数（PPO），确保盘整发生在一个相对的历史低位区间（如过去 60 天的 30% 分位数以下）。

突然放量上涨（Volume & Price Spike）：在死寂的盘整中，突然出现一根K线，其 Price_Z > 1.5（强烈上涨）且 Volume_Z > 2.0（成交量数倍放大）。
量价瞬间冲入第一象限（Q1，量价齐升），这就是量子坍缩打破死寂的“破局点”。
'''

import os
import numpy as np
from typing import List, Union
import sys

# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
# 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minitools import tdxcomm as tdx
from minitools import user_config as ucfg


show_templates_html_path = os.path.join(parent_dir, 'templates', ucfg.my_stocks_html_folder_name)
show_templates_comm_html_path = os.path.join(parent_dir, 'templates', ucfg.common_html_folder_name)
from ai_backtest_base import BaseModel, VP_BacktestEngine, VP_QuantRunner_BaseModel

# ==============================================================================
# 1. 核心数学计算引擎 (Model) —— 已加入多周期移动平均线
# ==============================================================================
class Advanced_VP_KineticModel(BaseModel):
    """量价动态引力场模型（纯向量化高速版 - 融合生命线防线）"""

    def __init__(self, p_window=15, v_window=20, ma_short=20, ma_long=60):
        self.p_window = p_window
        self.v_window = v_window
        self.ma_short = ma_short
        self.ma_long = ma_long

    def analyze(self, prices, volumes):
        """返回值包含：
        - Price_Z: 价格偏离度的 Z-score
        - Volume_Z: 成交量的 Z-score
        - VPKI: 量价动能强弱指数
        - Cosine_Similarity: 量价动能方向变化的余弦相似度
        - Quadrant: 市场象限分类 (1~4)
        """        
        p = np.array(prices, dtype=float)
        v = np.array(volumes, dtype=float)
        n = len(p)

        # ----------------------------------------------------------------------
        # 新增核心：向量化计算 20日与60日趋势生命线
        # ----------------------------------------------------------------------
        ma_s_arr = np.full(n, np.nan)
        ma_l_arr = np.full(n, np.nan)
        
        if n >= self.ma_short:
            ma_s_arr[self.ma_short - 1:] = np.mean(self._rolling_window(p, self.ma_short), axis=1)
        if n >= self.ma_long:
            ma_l_arr[self.ma_long - 1:] = np.mean(self._rolling_window(p, self.ma_long), axis=1)

        # 1. 向量化计算成交量的 Z-score 和中位数
        #    每个时刻用过去 v_window 个成交量计算均值、标准差和中位数。        
        v_windows = self._rolling_window(v, self.v_window)
        v_means = np.mean(v_windows, axis=1)
        v_stds = np.std(v_windows, axis=1, ddof=0)
        v_medians = np.median(v_windows, axis=1)

        volume_z = np.full(n, np.nan)
        v_valid_slice = slice(self.v_window - 1, n)
        # 防止标准差为 0 导致除零异常
        v_stds_safe = np.where(v_stds == 0, 1.0, v_stds)
        volume_z[v_valid_slice] = (v[v_valid_slice] - v_means) / v_stds_safe

        # 2. 向量化计算股价偏离度 (Deviation) 的 Z-score
        #    先计算价格的移动平均，再求当前价格相对于该均值的偏离比例。        
        p_ma_windows = self._rolling_window(p, self.p_window)
        p_mas = np.mean(p_ma_windows, axis=1)
        p_valid_slice = slice(self.p_window - 1, n)
        # 防止标准差为 0 导致除零异常
        p_mas_safe = np.where(p_mas == 0, 1.0, p_mas)

        price_deviation = np.full(n, 0.0)
        price_deviation[p_valid_slice] = (p[p_valid_slice] - p_mas) / p_mas_safe
        # 再对偏离度本身做滚动标准化，得到更加稳定的 price_z
        dev_windows = self._rolling_window(price_deviation, self.p_window)
        dev_means = np.mean(dev_windows, axis=1)
        dev_stds = np.std(dev_windows, axis=1, ddof=0)

        price_z = np.full(n, np.nan)
        dev_valid_slice = slice(self.p_window * 2 - 2, n)
        dev_stds_safe = np.where(dev_stds == 0, 1.0, dev_stds)

        price_z[dev_valid_slice] = (
            price_deviation[dev_valid_slice] - dev_means[self.p_window - 1 :]
        ) / dev_stds_safe[self.p_window - 1 :]


        full_v_median = np.full(n, np.nan)
        full_v_median[v_valid_slice] = v_medians

        # 3. 交叉特征生成
        vpki = np.full(n, np.nan)
        cos_theta = np.full(n, np.nan)
        market_quadrant = np.zeros(n, dtype=int)

        start_idx = self.p_window * 2 - 2
        if n <= start_idx:
            return {"Price_Z": price_z, "Volume_Z": volume_z, "VPKI": vpki, "Cosine_Similarity": cos_theta, "Quadrant": market_quadrant, "MA_Short": ma_s_arr, "MA_Long": ma_l_arr, "Raw_Price": p}

        # 3. 交叉特征生成
        #    VPKI 代表量价动能指数：价格偏离度 * 成交量强度 * 量比方向
        #    如果当前成交量大于中位数，则 vol_sign 为 +1，否则为 -1。
        vol_sign = np.where(v >= full_v_median, 1.0, -1.0)
        vpki[start_idx:] = (
            price_z[start_idx:]
            * np.log(1.0 + np.abs(volume_z[start_idx:]))
            * vol_sign[start_idx:]
        )

        # 市场象限分类：
        # 1: 价格和成交量同时走强 (主升共振)
        # 2: 价格下跌但成交量放大 (左侧建仓)
        # 3: 价格和成交量同时走弱 (弱势下跌)
        # 4: 价格上涨但成交量萎缩 (高位诱多)
        q1 = (price_z >= 0) & (volume_z >= 0)
        q2 = (price_z < 0) & (volume_z >= 0)
        q3 = (price_z < 0) & (volume_z < 0)
        q4 = (price_z >= 0) & (volume_z < 0)

        market_quadrant[q1] = 1
        market_quadrant[q2] = 2
        market_quadrant[q3] = 3
        market_quadrant[q4] = 4
        market_quadrant[:start_idx] = 0
        # 计算余弦相似度：表示量价动能变化方向是否平稳
        # 若余弦接近 1，则方向一致；若接近 -1，则发生钝转。
        p_prev, p_curr = price_z[start_idx:-1], price_z[start_idx + 1 :]
        v_prev, v_curr = volume_z[start_idx:-1], volume_z[start_idx + 1 :]

        dp = p_curr - p_prev
        dv = v_curr - v_prev

        dot_product = p_prev * dp + v_prev * dv
        norm_s_prev = np.sqrt(p_prev**2 + v_prev**2)
        norm_delta_s = np.sqrt(dp**2 + dv**2)

        denominator = norm_s_prev * norm_delta_s
        safe_mask = denominator > 0

        cos_results = np.full(len(p_curr), np.nan)
        cos_results[safe_mask] = dot_product[safe_mask] / denominator[safe_mask]
        cos_theta[start_idx + 1 :] = cos_results

        return {
            "Price_Z": price_z,
            "Volume_Z": volume_z,
            "VPKI": vpki,
            "Cosine_Similarity": cos_theta,
            "Quadrant": market_quadrant,
            "MA_Short": ma_s_arr,
            "MA_Long": ma_l_arr,
            "Raw_Price": p
        }


# ==============================================================================
# 2. 策略信号生成器 (Generator) —— 已注入空间价格防御过滤网
# ==============================================================================
class VP_SignalGenerator:
    """具备『空间均线双重防御系统』与『真假动能甄别』的终极信号生成器"""

    def __init__(self, v_bottom_threshold=-2.0, v_volume_threshold=2.5, momentum_cosine=0.8, divergence_volume=-1.0):
        self.v_bottom_threshold = v_bottom_threshold
        self.v_volume_threshold = v_volume_threshold
        self.momentum_cosine = momentum_cosine
        self.divergence_volume = divergence_volume


    def generate_signals_with_geometry(self, metrics_dict: dict, window: int = 20) -> dict:
        """
        蓄势右侧突破策略：低位长期盘整 + 突然放量上涨破局
        
        摒弃左侧接飞刀，转为绝对的右侧狙击。
        """
        # -------------------------------------------------------------------------
        # 1. 基础量价几何空间计算工程
        # -------------------------------------------------------------------------
        raw_p = metrics_dict["Raw_Price"]
        ma_short = metrics_dict["MA_Short"]
        ma_long = metrics_dict["MA_Long"]
        n = len(raw_p)
        
        price_return = np.zeros(n)
        price_return[1:] = (raw_p[1:] - raw_p[:-1]) / (raw_p[:-1] + 1e-8)
        
        price_z = np.zeros(n)
        for i in range(window, n):
            window_data = price_return[i - window + 1 : i + 1]
            price_z[i] = (price_return[i] - np.mean(window_data)) / (np.std(window_data) + 1e-8)
            
        if "Volume_Z" in metrics_dict:
            v_z = metrics_dict["Volume_Z"]
        else:
            raw_v = metrics_dict["Raw_Volume"]
            v_z = np.zeros(n)
            for i in range(window, n):
                window_v = raw_v[i - window + 1 : i + 1]
                v_z[i] = (raw_v[i] - np.mean(window_v)) / (np.std(window_v) + 1e-8)

        # 象限路由 (1:量价齐升, 2:爆量下跌, 4:缩量上涨)
        quadrant = np.full(n, 3, dtype=int)
        quadrant[(price_z > 0) & (v_z > 0)] = 1   
        quadrant[(price_z <= 0) & (v_z > 0)] = 2  
        quadrant[(price_z > 0) & (v_z <= 0)] = 4  

        # -------------------------------------------------------------------------
        # 2. 右侧核心：长期盘整与低位特征提取
        # -------------------------------------------------------------------------
        combined_signals = np.zeros(n, dtype=int)
        signal_labels = np.full(n, "观望", dtype=object)
        
        # 设定长期观察窗口（如 30 天盘整，60 天低位）
        consolidation_window = min(30, window * 2)
        low_zone_window = min(60, window * 3)

        for i in range(low_zone_window, n):
            # 2.1 统计学定义【低位】：当前价格处于过去长周期最高最低价的 35% 以下
            hist_max = np.max(raw_p[i - low_zone_window : i])
            hist_min = np.min(raw_p[i - low_zone_window : i])
            price_location = (raw_p[i] - hist_min) / (hist_max - hist_min + 1e-8)
            is_at_low_zone = price_location <= 0.35

            # 2.2 统计学定义【长期盘整】：过去 30 天的价格波动率（标准差）处于极低状态
            # 我们用过去 30 天的最高价与最低价的差幅来衡量，差幅小于 8% 代表横盘死寂
            recent_prices = raw_p[i - consolidation_window : i]
            price_range_pct = (np.max(recent_prices) - np.min(recent_prices)) / (np.min(recent_prices) + 1e-8)
            is_consolidating = price_range_pct <= 0.08  # 波动幅度在 8% 以内横盘

            # 均线防御过滤器
            below_short_ma = np.isnan(ma_short[i]) or (raw_p[i] < ma_short[i])
            below_long_ma = np.isnan(ma_long[i]) or (raw_p[i] < ma_long[i])
            lifeline_broken = below_short_ma or below_long_ma

            # ──【右侧核心决策引擎：低位蓄势突破】──
            # 条件：长期在低位盘整 (is_at_low_zone & is_consolidating) 
            # 突变：今天突然放量暴动，冲入第1象限量价齐升，且价格Z分数学异常强烈 (price_z > 1.5)，成交量大幅异动 (v_z > 1.8)
            if is_at_low_zone and is_consolidating:
                if quadrant[i] == 1 and price_z[i] > 1.5 and v_z[i] > 1.8:
                    combined_signals[i] = 1
                    signal_labels[i] = f"🚀🚀突破：低位蓄势横盘 {consolidation_window} 天后，今日放量破局入场"
                    continue

            # ──【右侧出局引擎：高位滞涨或跌破生命线】──
            # 右侧买入后，如果跌破短线或长线均线（生命线断裂），或者高位缩量诱多(Q4)，果断清仓
            if lifeline_broken and quadrant[i] == 3 and v_z[i] > 1.0:
                combined_signals[i] = -1
                signal_labels[i] = "🚨出局：破局失败，跌破趋势生命线（右侧硬核止损）"
            elif quadrant[i] == 4 and price_z[i] > 2.0 and v_z[i] < -1.0:
                combined_signals[i] = -1
                signal_labels[i] = "🛑🛑减仓：高位缩量滞涨诱多，防范假突破"

        # 初始化热身期锁死
        combined_signals[:low_zone_window] = 0
        signal_labels[:low_zone_window] = "初始化热身期"

        return {"Signals": combined_signals, "Labels": signal_labels}



# ==============================================================================
# 3. 回测统计内核 (Engine) —— 维持原样保持严谨
# ==============================================================================

    
#==============================================================================
#4. 量化总调度大脑 (Facade 门面类) —— 已接入自适应优化流
# ==============================================================================
class VP_QuantRunner(VP_QuantRunner_BaseModel):
    def __init__(self, p_window=15, v_window=15, v_bottom=-2.0, v_volume=2.5, momentum_cos=0.8, divergence_vol=-1.0, ma_short=20, ma_long=60):
        self.model = Advanced_VP_KineticModel(p_window=p_window, v_window=v_window, ma_short=ma_short, ma_long=ma_long)
        self.generator = VP_SignalGenerator(v_bottom_threshold=v_bottom, v_volume_threshold=v_volume, momentum_cosine=momentum_cos, divergence_volume=divergence_vol)

    def run_pipeline(self, stock_data):
        """一键运行整个量化回测流水线，并自动输出高级 Markdown 报表"""
        # Step 1: 加载数据
        dates, prices, volumes = self.load_stock_data(stock_data)
        # Step 2: 提取统计特征
        metrics = self.model.analyze(prices, volumes)
        # Step 3: 生成交易信号
        trade_signals = self.generator.generate_signals_with_geometry(metrics)
        # Step 4: 回测绩效评估
        report = VP_BacktestEngine.evaluate(prices, dates, trade_signals["Signals"], trade_signals["Labels"])

        report['quant_info'] = f"backtest test 4-2， 蓄势右侧突破策略：低位长期盘整 + 突然放量上涨破局"
        report["quant_notes"] = "该策略专注于识别低位长期盘整后的突然放量上涨突破信号，以捕捉潜在的上涨机会。成交回数极低，成功概率特别高，适合市场极度低迷时使用，也没有出场信号。"
        # Step 5: 打印格式化的 Markdown 绩效看板
        self._print_markdown_report(report)
        return report

    def _print_markdown_report(self, report):
        print("\n" + "="*80)
        print(f"ai quant backtest 4-1     量价引力场 + 趋势生命线防线 终极绩效看板")
        print("="*80)
        markdown_output = f"""
核心绩效指标 (Performance Metrics)
绩效评估维度    策略表现数值    基准对比 (买入持有) 阿尔法超额收益
总收益率      {report['total_return']:.2f}%    {report['benchmark_return']:.2f}%   {report['total_return'] - report['benchmark_return']:.2f}%
历史最大回撤  {report['max_drawdown']:.2f}%       --    --
综合交易胜率  {report['win_rate']:.2f}%           --    --
总计开仓次数  {report['total_trades']} 次         --    --
单笔极端极端极大盈利: +{report['max_win']:.2f}%   极大亏损: {report['max_loss']:.2f}%   --

策略历史开平仓动作明细 (Trade Logs)        
| 动作序列 | 交易日期 | 执行价格 | 核心触发原因 | 本笔损益表现 |
| :--- | :--- | :--- | :--- | :--- |"""
        print(markdown_output)
        for idx, log in enumerate(report["trade_logs"]):
            color_prefix = "+" if log['return'] > 0 else ""
            ret_str = f"{color_prefix}{log['return']:.2f}%" if log['type'] != 'BUY' else "--"
            print(f"| {idx+1} | {log['date']} | {log['price']:.2f} | {log['reason']} | {ret_str} |")
        print("\n" + "="*60)

    def customize_thresholds(self, metrics_dict):
        """自适应分析近期标准差分布特征"""
        p_z = metrics_dict["Price_Z"][~np.isnan(metrics_dict["Price_Z"])]
        v_z = metrics_dict["Volume_Z"][~np.isnan(metrics_dict["Volume_Z"])]
        if len(p_z) == 0 or len(v_z) == 0:
            return None
        p_pct = np.percentile(p_z, [5, 95])
        v_pct = np.percentile(v_z, [5, 95])
        return {"v_bottom": p_pct[0], "v_volume": v_pct[1], "divergence_vol": v_pct[0]}
    

    def run(self, chart_data):
        # Step 1: 加载数据
        dates, prices, volumes = self.load_stock_data(chart_data)
        initial_metrics = self.model.analyze(prices, volumes)
        # 第二阶段：提取这一年历史数据的个性化阈值，注入空间防护并开启精准回测
        custom_params = self.customize_thresholds(initial_metrics)
        result = None 
        if custom_params:
            print(f"\n[安全中心] 成功提取自适应标准差！空间短线生命线设为：20日均线。")
            optimized_runner = VP_QuantRunner(p_window=15, v_window=15, ma_short=5, ma_long=20, # 注入双生命线
                                            v_bottom=custom_params["v_bottom"],
                                            v_volume=custom_params["v_volume"],
                                            divergence_vol=custom_params["divergence_vol"],
                                            momentum_cos=0.80 # 保持追涨的高协同要求
                                            )
            # 一键输出彻底消灭洗盘假信号后的终极绩效
            result = optimized_runner.run_pipeline(chart_data)
        return result         
#==============================================================================
# 5. 使用流程主入口 (黄金窗口数据量建议：250 - 500 天)
# ==============================================================================
if __name__ == "__main__":
    # ---- 🚀 执行标准的两阶段定制化回测工作流 ----
    # 第一阶段：用默认配置获取股票基础特征
        # 指定你的实际股票数据
    stock_code = "300162"  # 替换为你想分析的股票代码
    #stock_code = sys.argv[1]
    start_date = "2025-01-01" #日线级别最佳数据量：250 天 到 500 天（即 1 到 2 年的历史数据）。
    tdx_datas = tdx.TDXData(stock_code)
    tdx_datas.getStockDayFile()
    tdx_datas.creatstocKDataList()
    all_data = tdx_datas.getTDXStockDWMDatas()

    runner = VP_QuantRunner(p_window=15, v_window=15, ma_short=20, ma_long=60)
    chart_data = runner.split_data(tdx_datas.getTDXStockKDatas(), start_date=start_date)
    runner.run(chart_data)
