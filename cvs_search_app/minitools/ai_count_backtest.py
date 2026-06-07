import os
import numpy as np
from tdxcomm import TDXData as tdx
from typing import List, Union
import user_config as ucfg
import sys
try:
    from minitools.ai_backtest_base import BaseModel, VP_BacktestEngine
except Exception:
    from ai_backtest_base import BaseModel, VP_BacktestEngine

# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
# 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)
show_templates_html_path = os.path.join(parent_dir, 'templates', ucfg.my_stocks_html_folder_name)
show_templates_comm_html_path = os.path.join(parent_dir, 'templates', ucfg.common_html_folder_name)

# ==============================================================================
# 1. 核心数学计算引擎 (Model)  https://share.google/aimode/n9SjEjk4ckJDR88qJ
#
#该模型的核心作用是把原始价格和成交量数据，转换为一组可直接用于交易信号判定的量化特征。
# 它的输出主要用于后续 VP_SignalGenerator / VP_SignalGenerator_pulse 中的买卖逻辑判断。
# ==============================================================================
class Advanced_VP_KineticModel(BaseModel):
    """量价动态引力场模型（纯向量化高速版）

    该类基于价格与成交量的 Z-score 特征，构建量价动能指数 (VPKI)、
    向量余弦相似度 (Cosine_Similarity) 和市场象限分类 (Quadrant)。
    这是后续信号生成器的核心输入。
    """

    def __init__(self, p_window=20, v_window=20):
        # p_window: 价格移动平均与偏离度计算窗口
        # v_window: 成交量 Z-score 和中位数窗口
        self.p_window = p_window
        self.v_window = v_window


    def analyze(self, prices, volumes):
        """计算价格与成交量相关特征。

        返回值包含：
        - Price_Z: 价格偏离度的 Z-score
        - Volume_Z: 成交量的 Z-score
        - VPKI: 量价动能强弱指数
        - Cosine_Similarity: 量价动能方向变化的余弦相似度
        - Quadrant: 市场象限分类 (1~4)
        """
        p = np.array(prices, dtype=float)
        v = np.array(volumes, dtype=float)
        n = len(p)

        # 如果数据长度不足以形成滚动窗口，提前返回全 NaN/空的结果，避免 as_strided 产生负维度
        if n < max(self.p_window, self.v_window):
            price_z = np.full(n, np.nan)
            volume_z = np.full(n, np.nan)
            vpki = np.full(n, np.nan)
            cos_theta = np.full(n, np.nan)
            market_quadrant = np.zeros(n, dtype=int)
            return {
                "Price_Z": price_z,
                "Volume_Z": volume_z,
                "VPKI": vpki,
                "Cosine_Similarity": cos_theta,
                "Quadrant": market_quadrant,
            }

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

        # 记录成交量中位数，用于判断当期成交量是高于还是低于历史中位数
        full_v_median = np.full(n, np.nan)
        full_v_median[v_valid_slice] = v_medians

        # 3. 交叉特征生成
        #    VPKI 代表量价动能指数：价格偏离度 * 成交量强度 * 量比方向
        #    如果当前成交量大于中位数，则 vol_sign 为 +1，否则为 -1。
        vpki = np.full(n, np.nan)
        cos_theta = np.full(n, np.nan)
        market_quadrant = np.zeros(n, dtype=int)

        start_idx = self.p_window * 2 - 2
        if n <= start_idx:
            return {"Price_Z": price_z, "Volume_Z": volume_z, "VPKI": vpki, "Cosine_Similarity": cos_theta, "Quadrant": market_quadrant}

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
        }

# ==============================================================================
# 2. 策略信号生成器 (Generator) pyqt5 版本升级，增加了真假动能逆转甄别引擎，优化了信号标签细分，让你在日志里一眼看清每个信号的核心触发原因
# 
# 太棒了，经过多次尝试后，结果有个小问题，特别在上涨途中加仓后，第二天或第三天，就因为动能逆转就出局了，导致错过了后面上涨行情，
# 能否既能很好的判断主力是真假动能逆转的逻辑上改善一下
# 
# 这是一个非常高级且普遍存在的“趋势跟踪痛点”。

# 在量化交易中，这被称为“洗盘陷阱（Whipsaw Trap）”。
# 出现这个问题的原因在于：当你在“第一象限（主升共振）”追涨或加仓后，股价在主升浪中不可能每天都垂直上涨，它必定会出现1-3天的正常技术性回踩（即洗盘）。
# 因为价格突然减速或微跌，二维量价向量在空间中就会形成一个急刹车并向左下弯头的动作。
# 这就导致原有的 Cosine_Similarity <= -0.7 的条件被误触发，从而被主力洗盘出局，错失了后面的大波段。
# 为了精准识别主力是“真动能逆转（出货变盘）”还是“假动能逆转（回踩洗盘）”，
# 我们需要对核心数学模型进行两大维度的逻辑升级：💡 核心改进思路（真假动能判别法）引入“成交量非对称校验”——主力的狐狸尾巴假逆转
# （洗盘）：股价短期回踩减速，但成交量极度萎缩。这说明主力筹码锁死，根本没有出货，只是散户在跟风抛售（即典型的“缩量回调”）。
# 真逆转（出货）：股价滞涨或大跌，同时成交量异常放大或维持高位。
# 这说明多空分歧巨大，主力在边拉边派发（即典型的“放量砸盘”）。
# 数学修正：只有当动能方向调头（余弦为负），且成交量 Z-score 依然处于高位（\(V_z > 0\)）时，才判定为真逆转出局。
# 引入“引力场能量消耗度（VPKI 绝对值）”——物理惯性原理物理学中，一辆全速前进的卡车，即使踩了刹车，由于巨大的动量，它也不可能瞬间倒车。
# 如果前几天的量价动能指数（\(VPKI\)）处于极高的高能状态（例如连续大于 2.0），说明多头能量极其充沛。即使今天余弦夹角变负（转弯），
# 这大概率也只是高能状态下的局部扰动（洗盘）。数学修正：只有当系统的整体绝对动能已经衰减到低能区（\(VPKI < 0.5\)）时，
# 余弦夹角的反转信号才算真正有效。
# ==============================================================================
class VP_SignalGenerator_pulse:
    """升级版：具备『真假动能逆转甄别引擎』的信号生成器。

    该类在传统多因子信号基础上，额外引入成交量确认与动能耗散判断，
    用于区分“真逆转出局”与“假逆转洗盘持股”。
    """

    def __init__(self, v_bottom_threshold=-2.0, v_volume_threshold=2.5, momentum_cosine=0.8, divergence_volume=-1.0):
        self.v_bottom_threshold = v_bottom_threshold
        self.v_volume_threshold = v_volume_threshold
        self.momentum_cosine = momentum_cosine
        self.divergence_volume = divergence_volume

    def generate_signals(self, metrics_dict):
        """根据模型特征生成交易信号和标签。

        metrics_dict 必须含有 Advanced_VP_KineticModel.analyze() 输出的字段。
        返回信号数组与标签数组，供后续回测逻辑使用。
        """
        p_z = metrics_dict["Price_Z"]
        v_z = metrics_dict["Volume_Z"]
        vpki = metrics_dict["VPKI"]
        cos_theta = metrics_dict["Cosine_Similarity"]
        quadrant = metrics_dict["Quadrant"]
        n = len(p_z)

        combined_signals = np.zeros(n, dtype=int)
        signal_labels = np.full(n, "观望", dtype=object)

        # 信号 1：左侧爆量抄底
        #   场景：价格下跌、成交量放大，属于震荡反转的潜在买点。
        buy_left_mask = (quadrant == 2) & (p_z <= self.v_bottom_threshold) & (v_z >= self.v_volume_threshold)
        combined_signals[buy_left_mask] = 1
        signal_labels[buy_left_mask] = "BUY_左侧爆量抄底"

        # 信号 2：右侧顺势加仓
        #   场景：价格和成交量同时向好，方向一致且动能保持正向。
        buy_right_mask = (quadrant == 1) & (cos_theta >= self.momentum_cosine) & (vpki > 0)
        combined_signals[buy_right_mask & (combined_signals == 0)] = 1
        signal_labels[buy_right_mask & (signal_labels == "观望")] = "BUY_右侧顺势加仓"

        # 信号 3：高位缩量诱多减仓
        #   场景：股价继续上涨但成交量萎缩，高位诱多风险升高。
        sell_left_mask = (quadrant == 4) & (p_z >= 1.5) & (v_z <= self.divergence_volume)
        combined_signals[sell_left_mask] = -1
        signal_labels[sell_left_mask] = "SELL_高位缩量诱多"

        # ----------------------------------------------------------------------
        # 核心进化：信号 4 【动能逆转突变出局】—— 融入真假辨别逻辑
        # ----------------------------------------------------------------------
        # 基础条件：夹角余弦极度为负，方向发生钝化掉头
        base_reverse = (cos_theta <= -0.7) & (quadrant != 2)
        
        # 过滤阀 1：放量下跌才是真见顶 (V_Z > 0 代表今天成交量高于20日均量，排除缩量洗盘)
        volume_confirm = (v_z > 0.0)
        
        # 过滤阀 2：动能真正耗尽 (VPKI绝对值降到低能区，排除主升浪途中的强力震荡)
        # 如果前一天的动能指标绝对值很大，说明主力控盘极深，不允许轻易判定出局
        energy_depleted = np.full(n, True, dtype=bool)
        for i in range(1, n):
            if not np.isnan(vpki[i-1]) and abs(vpki[i-1]) > 2.5: 
                energy_depleted[i] = False # 高能惯性保护，判定为洗盘，不离场
        
        # 三者共振，才是真正的趋势崩塌（真逆转）
        sell_right_mask = base_reverse & (volume_confirm | energy_depleted)
        
        combined_signals[sell_right_mask & (combined_signals == 0)] = -1
        
        # 为了方便调试，我们细分标签，让你在日志里一眼看清真逆转出局。
        signal_labels[sell_right_mask & (signal_labels == "观望")] = "SELL_动能逆转真出局"
        
        # 识别假逆转：满足方向掉头但不满足放量/能量耗尽条件，判断为洗盘而非出局。
        fake_reverse_mask = base_reverse & ~sell_right_mask
        signal_labels[fake_reverse_mask & (signal_labels == "观望")] = "🔍识别：主力缩量洗盘持股"

        return {"Signals": combined_signals, "Labels": signal_labels}
    

# ==============================================================================
# 2. 策略信号生成器 (Generator)
# ==============================================================================
class VP_SignalGenerator:
    """基于引力场多维统计阈值生成交易信号。

    这是基础版本的信号生成器，仅使用象限、余弦和 VPKI 来判定买入/卖出。
    """

    def __init__(self, v_bottom_threshold=-2.0, v_volume_threshold=2.5, momentum_cosine=0.8, divergence_volume=-1.0):
        self.v_bottom_threshold = v_bottom_threshold
        self.v_volume_threshold = v_volume_threshold
        self.momentum_cosine = momentum_cosine
        self.divergence_volume = divergence_volume

    def generate_signals(self, metrics_dict):
        """从模型特征生成基础交易信号和标签。"""
        p_z = metrics_dict["Price_Z"]
        v_z = metrics_dict["Volume_Z"]
        vpki = metrics_dict["VPKI"]
        cos_theta = metrics_dict["Cosine_Similarity"]
        quadrant = metrics_dict["Quadrant"]
        n = len(p_z)

        combined_signals = np.zeros(n, dtype=int)
        signal_labels = np.full(n, "观望", dtype=object)

        # 信号 1：左侧爆量抄底
        buy_left_mask = (quadrant == 2) & (p_z <= self.v_bottom_threshold) & (v_z >= self.v_volume_threshold)
        combined_signals[buy_left_mask] = 1
        signal_labels[buy_left_mask] = "BUY_左侧爆量抄底"

        # 信号 2：右侧顺势加仓
        buy_right_mask = (quadrant == 1) & (cos_theta >= self.momentum_cosine) & (vpki > 0)
        combined_signals[buy_right_mask & (combined_signals == 0)] = 1
        signal_labels[buy_right_mask & (signal_labels == "观望")] = "BUY_右侧顺势加仓"

        # 信号 3：高位缩量诱多减仓
        sell_left_mask = (quadrant == 4) & (p_z >= 1.5) & (v_z <= self.divergence_volume)
        combined_signals[sell_left_mask] = -1
        signal_labels[sell_left_mask] = "SELL_高位缩量诱多"

        # 信号 4：动能逆转突变出局
        sell_right_mask = (cos_theta <= -0.7) & (quadrant != 2)
        combined_signals[sell_right_mask & (combined_signals == 0)] = -1
        signal_labels[sell_right_mask & (signal_labels == "观望")] = "SELL_动能逆转出局"

        return {"Signals": combined_signals, "Labels": signal_labels}


# ==============================================================================
# 3. 回测统计内核 (Engine)
# ==============================================================================


# ==============================================================================
# 4. 🎛️ 新增：量化总调度大脑 (Facade 门面类) —— 负责整合与完善使用流程
# ==============================================================================
class VP_QuantRunner:
    """引力场系统的大脑。将数据准备、特征提取、信号生成和回测串成一个闭环。"""

    def __init__(self, p_window=15, v_window=20, v_bottom=-2.0, v_volume=2.5, momentum_cos=0.8, divergence_vol=-1.0):
        """统一管理模型参数并建立与信号生成器的关联。"""
        self.model = Advanced_VP_KineticModel(p_window=p_window, v_window=v_window)
        ''' 
        self.generator = VP_SignalGenerator(
            v_bottom_threshold=v_bottom,
            v_volume_threshold=v_volume,
            momentum_cosine=momentum_cos,
            divergence_volume=divergence_vol
        )
        '''
        self.generator = VP_SignalGenerator_pulse(
            v_bottom_threshold=v_bottom,
            v_volume_threshold=v_volume,
            momentum_cosine=momentum_cos,
            divergence_volume=divergence_vol
        )

    def split_data(self, data, start_date=None):
        """从原始 K 线数据中提取日期、收盘价和成交量。

        该函数兼容 TDX 数据结构，返回用于后续分析的字典。
        """
        category_data = []
        values = []
        volumes = []
        closes = []

        volumes_macd = [] # 这个是为了计算 macd 用的，输入为量值，看看能不能生成一个和 macd 类似的曲线，观察成交量和 macd 的关系


        '''
            date         开        收        最低       最高       量
        ["2004-01-02", 10452.74, 10409.85, 10367.41, 10554.96, 168890000],
        data 结构
        
        '''

        for i, tick in enumerate(data):
            date_str = tick[0]
            if start_date and date_str < start_date:
                continue
            category_data.append(tick[0]) # 日期
            values.append(tick) # 全部内容
            closes.append(tick[2]) # 收盘价
            # 元代码 是 tick 4 错了，应该是 tick 5 因为 4是 最高价，5才是量
            volumes_macd.append(tick[5]) # 这个是为了计算 macd 用的，输入为量值，看看能不能生成一个和 macd 类似的曲线，观察成交量和 macd 的关系

            volumes.append([i, tick[5], 1 if tick[1] > tick[2] else -1])  # i 是序号 从 0 开始，如果 开始大于收盘 1 ，反之 -1 估计是标 量线颜色用 红 绿
        return {"categoryData": category_data, "values": values, "volumes": volumes, "closes": closes, "volumes_macd": volumes_macd}        

    def load_stock_data(self, stock_data):
        """读取拆分后的股票数据，返回日期、收盘价和成交量序列。"""
        dates, prices, volumes = stock_data["categoryData"], stock_data["closes"], stock_data["volumes_macd"]  # 注意这里我们用的是 volumes_macd 来观察成交量和 macd 的关系
        return dates, prices, volumes

    def run_pipeline(self, stock_data):
        """运行模型、生成信号并回测，最终输出报告。"""
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
        """输出标准量化研究格式的 Markdown 看板。"""
        print("\n" + "="*60)
        print(f"   {tdx_datas.stock_name}      量价动态引力场策略 终极绩效看板          ")
        print("="*60)
        markdown_output = f"""
核心绩效指标 (Performance Metrics)
绩效评估维度  策略表现数值                       基准对比 (买入持有)                  阿尔法超额收益
总收益率      {report['total_return']:.2f}%    {report['benchmark_return']:.2f}%   {report['total_return'] - report['benchmark_return']:.2f}%
历史最大回撤  {report['max_drawdown']:.2f}%       --                                     --
综合交易胜率  {report['win_rate']:.2f}%           --                                     --
总计开仓次数  {report['total_trades']} 次         --                                     --
单笔极端极端极大盈利: +{report['max_win']:.2f}%   极大亏损: {report['max_loss']:.2f}%    --        
动作序列 | 交易日期 | 执行价格 | 核心触发触发原因 | 本笔损益表现 || :--- | :--- | :--- | :--- | :--- |"""
        print(markdown_output)
        for idx, log in enumerate(report["trade_logs"]):
            color_prefix = "+" if log['return'] > 0 else ""
            ret_str = f"{color_prefix}{log['return']:.2f}%" if log['type'] != 'BUY' else "--"
            print(f"| {idx+1} | {log['date']} | {log['price']:.2f} | {log['reason']} | {ret_str} |")
        print("\n" + "="*60)



    '''
    要为一只特定的股票进行“个性化阈值定制”，我们需要知道它在真实历史上的波动规律。
    有些大盘股（如工商银行）价格 Z-score 很难超过 \(\pm 1.5\)，而有些妖股或科创板股票（如部分题材股）在暴涨暴跌时 Price_Z 可以飙到 \(\pm 5\)。
    我们需要通过统计学分位数（Quantiles）来查看这只股票的 Price_Z 和 Volume_Z 在历史上的概率分布，进而精准找出那 5% 的“极端异常点”作为我们的买卖阈值。

     如何看懂输出结果并微调？当你运行上述闭环流程后，
     屏幕上会先喷出一张概率分布特征表：如果发现 5% 概率位的 Price_Z 是 -1.2：说明这只股票极其温和（如大型蓝筹股），历史上面对再大的利空也很难跌破 2 个标准差。
     如果死守老参数 -2.0，你这辈子都等不到它的抄底信号。
     现在系统会自动帮你把门槛放宽到 -1.2，做到因股制宜。
     如果发现 95% 概率位的 Volume_Z 是 4.5：说明这是一只股性极度活跃的“妖股”，平时一旦放量就是惊天巨量。
     如果用老参数 2.5，系统会频繁误判其为“爆量”从而发出错误的买入信号。
     系统会自动帮你把门槛提高到 4.5，只有真正惊天动地的巨量出现时才准许开仓。
    '''

    def customize_thresholds(self, metrics_dict):
        """
        分析股票的历史标准差分布，并自动计算出个性化的最优阈值
        :param metrics_dict: Advanced_VP_KineticModel.analyze() 返回的字典
        :return: dict 建议的个性化阈值
        """
        # 剔除未暖机完成的 NaN 缺失值
        p_z = metrics_dict["Price_Z"][~np.isnan(metrics_dict["Price_Z"])]
        v_z = metrics_dict["Volume_Z"][~np.isnan(metrics_dict["Volume_Z"])]

        if len(p_z) == 0 or len(v_z) == 0:
            print("错误：有效数据量不足，无法进行标准差分布统计。")
            return None

        print("\n" + "="*60)
        print("      股票历史标准差概率分布特征表 (Quantiles)       ")
        print("="*60)
        print(f"{'分位数级别':<12}{'价格偏离 Z-score':<18}{'成交量 Z-score':<15}")
        print("-"*60)
        
        # 计算关键概率触点
        percentiles = [1, 5, 25, 50, 75, 95, 99]
        p_pct = np.percentile(p_z, percentiles)
        v_pct = np.percentile(v_z, percentiles)
        
        for i, pctl in enumerate(percentiles):
            print(f"{pctl}% 概率位{':':<4}{p_pct[i]:<20.2f}{v_pct[i]:<15.2f}")
            
        print("-"*60)
        print(" 【数学含义解读】:")
        print(f" 1. 该股历史上只有 5% 的极端超跌时刻，Price_Z 会低于 {p_pct[1]:.2f}")
        print(f" 2. 该股历史上只有 5% 的极端放量时刻，Volume_Z 会高于 {v_pct[5]:.2f}")
        print("="*60)

        # 自动定制个性化阈值（采用历史真实的前 5% 和 95% 作为极端边界）
        suggested_v_bottom = p_pct[1]       # 对应 5% 的极度超跌位
        suggested_v_volume = v_pct[5]       # 对应 95% 的极度爆量位
        suggested_divergence = v_pct[1]     # 对应 5% 的极端缩量位（高位诱多用）

        print("\n[ 智能推荐] 基于此股历史波动率，为您定制的『引力场个性化阈值』如下：")
        print(f" -> 抄底价格阈值 (v_bottom_threshold):  {suggested_v_bottom:.2f}  (老参数: -2.00)")
        print(f" -> 抄底爆量阈值 (v_volume_threshold):  {suggested_v_volume:.2f}  (老参数: 2.50)")
        print(f" -> 诱多缩量阈值 (divergence_volume):   {suggested_divergence:.2f}  (老参数: -1.00)")
        
        return {
            "v_bottom": suggested_v_bottom,
            "v_volume": suggested_v_volume,
            "divergence_vol": suggested_divergence
        }
if __name__ == "__main__":
    # 指定你的实际股票数据
    stock_code = "300769"  # 替换为你想分析的股票代码
    stock_code = sys.argv[1]
    start_date = "2025-01-01" #日线级别最佳数据量：250 天 到 500 天（即 1 到 2 年的历史数据）。
    tdx_datas = tdx(stock_code)
    tdx_datas.getStockDayFile()
    tdx_datas.creatstocKDataList()
    all_data = tdx_datas.getTDXStockDWMDatas()
    
# --------------------------------------------------------------------------
# # 💎 优化后的标准使用流程 💎# --------------------------------------------------------------------------
# 1. 声明大脑，一处调参。# 价格窗口设为 15 天，成交量设为 20 天，余弦追涨阈值拉高到 0.85 保证严苛
    runner = VP_QuantRunner(p_window=15,v_window=20,momentum_cos=0.85)
    chart_data = runner.split_data(tdx_datas.getTDXStockKDatas(), start_date=start_date)

    # 2. 读取数据并生成第一版指标 metrics
        # Step 1: 加载数据
    dates, prices, volumes = runner.load_stock_data(chart_data)
    # Step 2: 提取统计特征
    metrics = runner.model.analyze(prices, volumes)
    
    # 3. 🔥 调用分析函数，打印标准差分布，获取定制化参数
    custom_params = runner.customize_thresholds(metrics)
    
    # 4. 重新注入个性化参数，开启精准二次回测
    if custom_params:
        print("\n 正在将定制阈值注入大脑，启动二次精准回测...")
        print(tdx_datas.stock_name)
        optimized_runner = VP_QuantRunner(
            p_window=15,
            v_window=20,
            v_bottom=custom_params["v_bottom"],
            v_volume=custom_params["v_volume"],
            divergence_vol=custom_params["divergence_vol"],
            momentum_cos=0.85 # 右侧共振维持严苛过滤
        )
        
        # 5. 输出优化后的终极绩效看板
    # 2. 一键注入 CSV 运行完整流水线print(f"正在启动引力场调度系统，正在分析数据源: {TARGET_CSV}...")
        final_report = runner.run_pipeline(chart_data)