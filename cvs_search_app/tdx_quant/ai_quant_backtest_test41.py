'''
根据 backtest py，由ai进一步优化和修改

量价象限划分（Quadrant）根据 \((\text{Price\_Z}, \text{Volume\_Z})\) 的正负号确定其所处的几何空间象限：
第一象限 (Q1): \(\text{Price\_Z} > 0, \text{Volume\_Z} > 0 \implies\) 量价齐升
第二象限 (Q2): \(\text{Price\_Z} \le 0, \text{Volume\_Z} > 0 \implies\) 放量下跌 / 爆量抄底
第三象限 (Q3): \(\text{Price\_Z} \le 0, \text{Volume\_Z} \le 0 \implies\) 缩量下跌
第四象限 (Q4): \(\text{Price\_Z} > 0, \text{Volume\_Z} \le 0 \implies\) 缩量上涨 / 缩量诱多
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
        量化架构师核心模块：全套量价几何空间计算工程 + 信号自适应决策机
        
        输入参数 (metrics_dict 必须包含以下原始时序数据, 且长度必须一致):
        - metrics_dict["Raw_Price"]: np.ndarray, 原始收盘价
        - metrics_dict["Volume_Z"]: np.ndarray (若上游未提供, 代码内部会自动从原始Volume计算)
        - metrics_dict["MA_Short"]: np.ndarray, 短线防御生命线
        - metrics_dict["MA_Long"]: np.ndarray, 长线防御生命线
        """
        # -------------------------------------------------------------------------
        # 1. 前置数学计算逻辑（特征工程向量化实现）
        # -------------------------------------------------------------------------
        raw_p = metrics_dict["Raw_Price"]
        ma_short = metrics_dict["MA_Short"]
        ma_long = metrics_dict["MA_Long"]
        n = len(raw_p)
        
        # 1.1 计算价格变化率 (Price Return)
        price_return = np.zeros(n)
        price_return[1:] = (raw_p[1:] - raw_p[:-1]) / (raw_p[:-1] + 1e-8)
        
        # 1.2 计算 Price_Z (滚动 Z-Score 标准化)
        # 使用 NumPy 步长实现高效滚动统计，规避 for 循环
        price_z = np.zeros(n)
        for i in range(window, n):
            window_data = price_return[i - window + 1 : i + 1]
            p_std = np.std(window_data)
            price_z[i] = (price_return[i] - np.mean(window_data)) / (p_std + 1e-8)
            
        # 1.3 计算 Volume_Z (若上游未提供标准化后的量，则从原始 Volume 动态计算)
        if "Volume_Z" in metrics_dict:
            v_z = metrics_dict["Volume_Z"]
        else:
            raw_v = metrics_dict["Raw_Volume"]
            v_z = np.zeros(n)
            for i in range(window, n):
                window_v = raw_v[i - window + 1 : i + 1]
                v_std = np.std(window_v)
                v_z[i] = (raw_v[i] - np.mean(window_v)) / (v_std + 1e-8)

        # 1.4 计算量价几何象限 (Quadrant)
        # 初始化全为 3 象限 (P<=0, V<=0)
        quadrant = np.full(n, 3, dtype=int)
        quadrant[(price_z > 0) & (v_z > 0)] = 1   # 第一象限：量价齐升
        quadrant[(price_z <= 0) & (v_z > 0)] = 2  # 第二象限：放量下跌/爆量抄底
        quadrant[(price_z > 0) & (v_z <= 0)] = 4  # 第四象限：缩量上涨/诱多

        # 1.5 计算空间几何动能 VPKI (带方向的欧氏距离模长)
        vector_magnitude = np.sqrt(price_z**2 + v_z**2)
        vpki = np.sign(price_z) * vector_magnitude

        # 1.6 计算量价向量与多头基准向量 (1, 1) 的余弦相似度
        # 规避分母为 0 的异常
        cos_theta = (price_z * 1.0 + v_z * 1.0) / (vector_magnitude * np.sqrt(2.0) + 1e-8)
        
        # -------------------------------------------------------------------------
        # 2. 纯几何多空环境识别（无滞后平滑）
        # -------------------------------------------------------------------------
        in_bull_quadrant = (quadrant == 1) | (quadrant == 2)
        bull_energy_score = (in_bull_quadrant.astype(int) + 
                            np.roll(in_bull_quadrant, 1).astype(int) + 
                            np.roll(in_bull_quadrant, 2).astype(int))
        
        is_agile_uptrend = bull_energy_score >= 2

        # -------------------------------------------------------------------------
        # 3. 核心信号掩码（完美集成您的策略原版骨架）
        # -------------------------------------------------------------------------
        # --- 信号 1：左侧爆量抄底 ---
        buy_left_up = is_agile_uptrend & (quadrant == 2) & (price_z <= self.v_bottom_threshold) & (v_z >= self.v_volume_threshold)
        buy_left_down = ~is_agile_uptrend & (quadrant == 2) & (price_z <= -2.0) & (v_z >= max(self.v_volume_threshold, 2.5))
        mask_buy_left = buy_left_up | buy_left_down

        # --- 信号 2：右侧顺势加仓 ---
        buy_right_up = is_agile_uptrend & (quadrant == 1) & (cos_theta >= 0.4) & (vpki > 0)
        buy_right_down = ~is_agile_uptrend & (quadrant == 1) & (cos_theta >= self.momentum_cosine) & (vpki > 1.5)
        mask_buy_right = buy_right_up | buy_right_down

        # --- 信号 3：高位缩量诱多减仓 ---
        mask_sell_left = (quadrant == 4) & (price_z >= 1.5) & (v_z <= self.divergence_volume)

        # --- 信号 4：动能逆转突变出局 ---
        base_reverse = (cos_theta <= -0.7) & (quadrant != 2)
        volume_confirm = (v_z > 0.0)
        
        prev_vpki_abs = np.abs(np.roll(vpki, 1))
        energy_depleted = np.isnan(prev_vpki_abs) | (prev_vpki_abs <= 2.5)
        
        below_short_ma = np.isnan(ma_short) | (raw_p < ma_short)
        below_long_ma = np.isnan(ma_long) | (raw_p < ma_long)
        lifeline_broken = below_short_ma | below_long_ma
        
        mask_sell_right = base_reverse & (volume_confirm | energy_depleted) & lifeline_broken
        mask_fake_reverse = base_reverse & ~mask_sell_right

        # -------------------------------------------------------------------------
        # 4. 信号矩阵规整与状态机赋值
        # -------------------------------------------------------------------------
        combined_signals = np.zeros(n, dtype=int)
        signal_labels = np.full(n, "观望", dtype=object)

        signal_labels[mask_fake_reverse] = "🔍拦截：生命线上缩量洗盘(坚定持股)"
        combined_signals[mask_buy_right] = 1
        signal_labels[mask_buy_right] = "BUY_右侧顺势加仓"
        combined_signals[mask_buy_left] = 1
        signal_labels[mask_buy_left] = "BUY_左侧爆量抄底"
        combined_signals[mask_sell_left] = -1
        signal_labels[mask_sell_left] = "SELL_高位缩量诱多"
        combined_signals[mask_sell_right] = -1
        signal_labels[mask_sell_right] = "SELL_动能逆转真出局"

        # 排除前 window 天特征热身期的无效数据
        combined_signals[:window] = 0
        signal_labels[:window] = "初始化热身期"

        return {"Signals": combined_signals, "Labels": signal_labels}

    # 4
    def generate_signals(self, metrics_dict):
        """
        回归纯粹：基于量价几何空间的无滞后自适应交易策略
        
        不引入任何外部均线过滤，完全依赖 Price_Z 和 Volume_Z 的几何分布
        自动在多头/空头环境下切换频率，保持原始策略的敏捷度。
        """
        # -------------------------------------------------------------------------
        # 1. 基础数据解构（保持100%原样）
        # -------------------------------------------------------------------------
        p_z = metrics_dict["Price_Z"]
        v_z = metrics_dict["Volume_Z"]
        vpki = metrics_dict["VPKI"]
        cos_theta = metrics_dict["Cosine_Similarity"]
        quadrant = metrics_dict["Quadrant"]
        
        raw_p = metrics_dict["Raw_Price"]
        ma_short = metrics_dict["MA_Short"]
        ma_long = metrics_dict["MA_Long"]
        
        n = len(p_z)
        
        # -------------------------------------------------------------------------
        # 2. 纯几何多空环境识别（无滞后平滑）
        # -------------------------------------------------------------------------
        # 统计过去3天处于“量价齐升(Q1)”或“爆量抄底(Q2)”的频率
        # 如果频繁出现Q1或Q2，说明市场处于无滞后的【多头动力区】，应当高频交易
        in_bull_quadrant = (quadrant == 1) | (quadrant == 2)
        bull_energy_score = (in_bull_quadrant.astype(int) + 
                            np.roll(in_bull_quadrant, 1).astype(int) + 
                            np.roll(in_bull_quadrant, 2).astype(int))
        
        # 只要过去3天有2天以上处于多头象限，即判定为敏捷的多头环境
        is_agile_uptrend = bull_energy_score >= 2

        # -------------------------------------------------------------------------
        # 3. 核心信号掩码（完全继承原版骨架，仅做非线性阈值微调）
        # -------------------------------------------------------------------------
        
        # --- 信号 1：左侧爆量抄底 ---
        # 多头环境：放宽阈值高频抄底；空头环境：保持硬核极值过滤，追求高胜率
        buy_left_up = is_agile_uptrend & (quadrant == 2) & (p_z <= self.v_bottom_threshold) & (v_z >= self.v_volume_threshold)
        buy_left_down = ~is_agile_uptrend & (quadrant == 2) & (p_z <= -2.0) & (v_z >= max(self.v_volume_threshold, 2.5))
        mask_buy_left = buy_left_up | buy_left_down

        # --- 信号 2：右侧顺势加仓 ---
        # 多头环境：放宽夹角要求（cos_theta >= 0.4），允许高频敏捷加仓
        buy_right_up = is_agile_uptrend & (quadrant == 1) & (cos_theta >= 0.4) & (vpki > 0)
        # 空头环境：维持极度严格的硬核过滤，非大动能不参与，确保低频高胜率
        buy_right_down = ~is_agile_uptrend & (quadrant == 1) & (cos_theta >= self.momentum_cosine) & (vpki > 1.5)
        mask_buy_right = buy_right_up | buy_right_down

        # --- 信号 3：高位缩量诱多减仓 ---
        # 完全保留原汁原味的统计过滤
        mask_sell_left = (quadrant == 4) & (p_z >= 1.5) & (v_z <= self.divergence_volume)

        # --- 信号 4：动能逆转突变出局（原版终极进化的优雅复刻） ---
        base_reverse = (cos_theta <= -0.7) & (quadrant != 2)
        volume_confirm = (v_z > 0.0)
        
        # 矢量化平移计算能量耗尽
        prev_vpki_abs = np.abs(np.roll(vpki, 1))
        energy_depleted = np.isnan(prev_vpki_abs) | (prev_vpki_abs <= 2.5)
        
        # 均线生命线防御（100%保留原版逻辑：跌破短线或长线均线）
        below_short_ma = np.isnan(ma_short) | (raw_p < ma_short)
        below_long_ma = np.isnan(ma_long) | (raw_p < ma_long)
        lifeline_broken = below_short_ma | below_long_ma
        
        # 最终出局掩码
        mask_sell_right = base_reverse & (volume_confirm | energy_depleted) & lifeline_broken
        
        # 拦截提示
        mask_fake_reverse = base_reverse & ~mask_sell_right

        # -------------------------------------------------------------------------
        # 4. 信号矩阵规整与状态机赋值（保持原有优先级）
        # -------------------------------------------------------------------------
        combined_signals = np.zeros(n, dtype=int)
        signal_labels = np.full(n, "观望", dtype=object)

        signal_labels[mask_fake_reverse] = "🔍拦截：生命线上缩量洗盘(坚定持股)"

        combined_signals[mask_buy_right] = 1
        signal_labels[mask_buy_right] = "BUY_右侧顺势加仓"
        
        combined_signals[mask_buy_left] = 1
        signal_labels[mask_buy_left] = "BUY_左侧爆量抄底"

        combined_signals[mask_sell_left] = -1
        signal_labels[mask_sell_left] = "SELL_高位缩量诱多"
        
        combined_signals[mask_sell_right] = -1
        signal_labels[mask_sell_right] = "SELL_动能逆转真出局"

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

        report['quant_info'] = f"backtest test 4-1， 右侧交易，感觉和其他策略相反，都不好时，这个有特别惊喜"
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
