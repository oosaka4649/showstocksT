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

    def generate_signals(self, metrics_dict):
        p_z = metrics_dict["Price_Z"]
        v_z = metrics_dict["Volume_Z"]
        vpki = metrics_dict["VPKI"]
        cos_theta = metrics_dict["Cosine_Similarity"]
        quadrant = metrics_dict["Quadrant"]
        
        # 提取用于空间定位的原始数据和均线防线
        raw_p = metrics_dict["Raw_Price"]
        ma_short = metrics_dict["MA_Short"]
        ma_long = metrics_dict["MA_Long"]
        
        n = len(p_z)

        combined_signals = np.zeros(n, dtype=int)
        signal_labels = np.full(n, "观望", dtype=object)

       # 市场象限分类： quadrant
        # 1: 价格和成交量同时走强 (主升共振)
        # 2: 价格下跌但成交量放大 (左侧建仓)
        # 3: 价格和成交量同时走弱 (弱势下跌)
        # 4: 价格上涨但成交量萎缩 (高位诱多)

        # 信号 1：左侧爆量抄底 (保持硬核统计过滤)
        #   场景：价格下跌、成交量放大，属于震荡反转的潜在买点。        
        buy_left_mask = (quadrant == 2) & (p_z <= self.v_bottom_threshold) & (v_z >= self.v_volume_threshold)
        combined_signals[buy_left_mask] = 1
        signal_labels[buy_left_mask] = "BUY_左侧爆量抄底 old"

        buy_left_mask_all = (quadrant == 3) & ((p_z < self.v_bottom_threshold) | (v_z < self.v_volume_threshold))
        combined_signals[buy_left_mask_all] = 1
        signal_labels[buy_left_mask_all] = "BUY_左侧爆量抄底 new 1"        

        # 数学结合：只有在『基础逆转成立』+『放量或能量耗尽』的同时，价格还【跌破了短线生命线或长线均线】，才执行真出局
       # 🚀 核心增加：过滤阀 3（空间生命线双重死守防线）
        # 如果均线数据还没算出来(NaN)，默认不保护；一旦均线算出来，必须【跌破生命线】才允许被洗出局
        below_short_ma = np.where(np.isnan(ma_short), True, raw_p < ma_short)
        below_long_ma = np.where(np.isnan(ma_long), True, raw_p < ma_long)        
        sell_right_mask = below_short_ma | below_long_ma

        combined_signals[sell_right_mask & (combined_signals == 0)] = -1
        signal_labels[sell_right_mask & (signal_labels == "观望")] = "SELL_抄底完了，卖出"

        #   场景：价格上升但成交量萎缩，属于高位诱多的潜在卖点。
        sell_left_mask = (quadrant == 4) & (p_z >= 1.5) & (v_z <= self.divergence_volume)
        combined_signals[sell_left_mask] = -1
        signal_labels[sell_left_mask] = "SELL_高位缩量诱多"        

        '''
        # 信号 2：右侧顺势加仓
        #   场景：价格和成交量同时向好，方向一致且动能保持正向。        
        buy_right_mask = (quadrant == 1) & (cos_theta >= self.momentum_cosine) & (vpki > 0)
        combined_signals[buy_right_mask & (combined_signals == 0)] = 1
        signal_labels[buy_right_mask & (signal_labels == "观望")] = "BUY_右侧顺势加仓"

        # 信号 3：高位缩量诱多减仓
        #   场景：价格上升但成交量萎缩，属于高位诱多的潜在卖点。
        sell_left_mask = (quadrant == 4) & (p_z >= 1.5) & (v_z <= self.divergence_volume)
        combined_signals[sell_left_mask] = -1
        signal_labels[sell_left_mask] = "SELL_高位缩量诱多"

        # ----------------------------------------------------------------------
        # 🔥 终极进化：信号 4 【动能逆转突变出局】—— 融入空间生命线防线
        # ----------------------------------------------------------------------
        # 基础条件：夹角余弦极度为负，方向发生钝化掉头        
        base_reverse = (cos_theta <= -0.7) & (quadrant != 2)

        # 过滤阀 1：量价行为确认（放量下跌才走）
        # 过滤阀 1：放量下跌才是真见顶 (V_Z > 0 代表今天成交量高于20日均量，排除缩量洗盘)        
        volume_confirm = (v_z > 0.0)
        
        # 过滤阀 2：惯性高能区保护
        energy_depleted = np.full(n, True, dtype=bool)
        for i in range(1, n):
            if not np.isnan(vpki[i-1]) and abs(vpki[i-1]) > 2.5: 
                energy_depleted[i] = False
                
        # 🚀 核心增加：过滤阀 3（空间生命线双重死守防线）
        # 如果均线数据还没算出来(NaN)，默认不保护；一旦均线算出来，必须【跌破生命线】才允许被洗出局
        below_short_ma = np.where(np.isnan(ma_short), True, raw_p < ma_short)
        below_long_ma = np.where(np.isnan(ma_long), True, raw_p < ma_long)
        
        # 数学结合：只有在『基础逆转成立』+『放量或能量耗尽』的同时，价格还【跌破了短线生命线或长线均线】，才执行真出局
        sell_right_mask = base_reverse & (volume_confirm | energy_depleted) & (below_short_ma | below_long_ma)

        combined_signals[sell_right_mask & (combined_signals == 0)] = -1
        signal_labels[sell_right_mask & (signal_labels == "观望")] = "SELL_动能逆转真出局"
        
        # 记录被成功拦截的“假摔/恶意洗盘”节点
        fake_reverse_mask = base_reverse & ~sell_right_mask
        signal_labels[fake_reverse_mask & (signal_labels == "观望")] = "🔍拦截：生命线上缩量洗盘(坚定持股)"
        '''
        return {"Signals": combined_signals, "Labels": signal_labels}


# ==============================================================================
# 3. 回测统计内核 (Engine) —— 维持原样保持严谨
# ==============================================================================

    
#==============================================================================
#4. 量化总调度大脑 (Facade 门面类) —— 已接入自适应优化流
# ==============================================================================
class VP_QuantRunner(VP_QuantRunner_BaseModel):
    def __init__(self, p_window=15, v_window=20, v_bottom=-2.0, v_volume=2.5, momentum_cos=0.8, divergence_vol=-1.0, ma_short=20, ma_long=60, lookback_window=250):
        self.model = Advanced_VP_KineticModel(p_window=p_window, v_window=v_window, ma_short=ma_short, ma_long=ma_long)
        self.generator = VP_SignalGenerator(v_bottom_threshold=v_bottom, v_volume_threshold=v_volume, momentum_cosine=momentum_cos, divergence_volume=divergence_vol)
        self.lookback = lookback_window

    def run_pipeline(self, stock_data):
        """一键运行整个量化回测流水线，并自动输出高级 Markdown 报表"""
        # Step 1: 加载数据
        dates, prices, volumes = self.load_stock_data(stock_data)
        # Step 2: 提取统计特征
        metrics = self.model.analyze(prices, volumes)
        # Step 3: 生成交易信号
        trade_signals = self.generator.generate_signals(metrics)
        # Step 4: 回测绩效评估
        report = VP_BacktestEngine.evaluate(prices, dates, trade_signals["Signals"], trade_signals["Labels"])
        # Step 5: 打印格式化的 Markdown 绩效看板
        self._print_markdown_report(report)
        return report

    def _print_markdown_report(self, report):
        print("\n" + "="*80)
        print(f"ai quant backtest test    左侧抄底 + 趋势生命线防线 终极绩效看板")
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


    '''
    
    def customize_thresholds(self, metrics_dict):
        """自适应分析近期标准差分布特征"""
        p_z = metrics_dict["Price_Z"][~np.isnan(metrics_dict["Price_Z"])]
        v_z = metrics_dict["Volume_Z"][~np.isnan(metrics_dict["Volume_Z"])]
        if len(p_z) == 0 or len(v_z) == 0:
            return None
        p_pct = np.percentile(p_z, [5, 95])
        v_pct = np.percentile(v_z, [5, 95])
        return {"v_bottom": p_pct[0], "v_volume": v_pct[1], "divergence_vol": v_pct[0]}

        '''
    '''
返回自适应阈值：
v_bottom: 价格近期极度下跌的边界（跌破这个值意味着超跌，可能是抄底信号）。
v_volume: 价格近期极度上涨的边界（突破这个值意味着超买，可能是追涨或止盈信号）。
divergence_vol: 成交量极度萎缩的边界（缩量到这个地步，可能意味着变盘在即）。     

应用：结合返回的 v_volume 和 divergence_vol，系统可以捕捉“量价背离”。
例如，当价格跌破 v_bottom（极度超跌），但成交量却萎缩到了 divergence_vol（无量空跌），这在技术分析中是极强的地量见地价、企稳反弹的信号。
   
 '''
    
    def customize_thresholds(self, metrics_dict):
        p_z_raw = metrics_dict.get("Price_Z", np.array([]))
        v_z_raw = metrics_dict.get("Volume_Z", np.array([]))
        p_z = p_z_raw[~np.isnan(p_z_raw)][-self.lookback:]
        v_z = v_z_raw[~np.isnan(v_z_raw)][-self.lookback:]
        
        if len(p_z) < 120 or len(v_z) < 120: return None

        # 核心逻辑：利用价格Z值乘以成交量权重，寻找“极低价格下成交量却极小”的负向极端真空区
        # 这种情况通常代表散户割肉殆尽，机构拒绝抛售
        volume_weight_p = p_z * (1.0 / (np.abs(v_z) + 0.1))
        
        """
        策略三：基于成交量加权分离度与流动性真空雷达
        优势：专抓主力控盘股的洗盘末端，反弹爆发力最强
        """        
        # 【调优】极度严格的左尾控制：寻找一年内最惨烈的 2.5% 价格恐慌点
        #价格恐慌底 (price_panic_bottom)：过去一年中最低的 2% 的价格区间。这是极度恐慌才会砸出来的绝对死区。
        price_panic_bottom = np.percentile(p_z, 2.5),
        # 地量控制：寻找流动性极度枯竭的前 7% 缩量点
        #地量极限 (volume_dry_limit)：过去一年中最低的 10% 的成交量水平。代表市场交投极其冷清
        volume_dry_limit = np.percentile(v_z, 7.0),  # 地量卡得更死（前7%）
        vacuum_threshold = np.percentile(volume_weight_p, 5.0)

        return {"v_bottom": price_panic_bottom, "v_volume": volume_dry_limit, "divergence_vol": vacuum_threshold}


    def run(self, chart_data):
        # Step 1: 加载数据
        dates, prices, volumes = self.load_stock_data(chart_data)
        initial_metrics = self.model.analyze(prices, volumes)
        # 第二阶段：提取这一年历史数据的个性化阈值，注入空间防护并开启精准回测
        custom_params = self.customize_thresholds(initial_metrics)
        result = None  
        if custom_params:
            print(f"\n[安全中心] 成功提取自适应标准差！空间短线生命线设为：20日均线。")
            optimized_runner = VP_QuantRunner(p_window=15, v_window=20, ma_short=5, ma_long=20, # 注入双生命线
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
    stock_code = "688249"  # 替换为你想分析的股票代码
    #stock_code = sys.argv[1]
    start_date = "2025-01-01" #日线级别最佳数据量：250 天 到 500 天（即 1 到 2 年的历史数据）。
    tdx_datas = tdx.TDXData(stock_code)
    tdx_datas.getStockDayFile()
    tdx_datas.creatstocKDataList()
    all_data = tdx_datas.getTDXStockDWMDatas()

    runner = VP_QuantRunner(p_window=15, v_window=20, ma_short=20, ma_long=60)
    chart_data = runner.split_data(tdx_datas.getTDXStockKDatas(), start_date=start_date)
    runner.run(chart_data)
