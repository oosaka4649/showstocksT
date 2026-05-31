import numpy as np

'''
这套代码实现了上一节中提出的“量价动态引力场”模型。
它包含两大核心创新点：量价四象限状态机（Status Machine）：利用 Price_Z 和 Volume_Z 将市场划分为主升浪、主力诱多、散户恐慌和市场冰点四个状态。
量价动能指数（VPKI）与向量夹角余弦（Cosine Similarity）：量化趋势的顺畅度与系统能量。

从数学统计学的视角来看，传统的量价分析（如“放量上涨”或“量价背离”）多流于经验主义。
我们要跳出传统框架，利用现代统计学中的概率空间、向量场（Vector Field）和信息论来重构量价关系，为您构建一个全新的股票趋势分析思路。
我们将这个新思路命名为：“量价动态引力场”模型（Volume-Price Kinetic Gravitational Model）。

一、 核心数学重构：把量价转化为“二维速度向量”在物理学中，位置的变化形成速度，力决定了速度的改变。我们把股价 
Z-score（\(P_{z}\)）和成交量 Z-score（\(V_{z}\)）看作是一个二维空间中的坐标轴，但不要把它们割裂开，而是组合成一个量价状态向量（State Vector）：\(\vec{S}_{t}=[P_{z,t},V_{z,t}]\)那么，从昨天到今天，这个状态向量在坐标系里的移动，就形成了一个方向向量（Velocity Vector）：\(\vec{\Delta S}_{t}=\vec{S}_{t}-\vec{S}_{t-1}=[P_{z,t}-P_{z,t-1},\;V_{z,t}-V_{z,t-1}]\)💡 统计学统计新表达：量价夹角余弦（Cosine Similarity）通过计算趋势方向与绝对位置之间的夹角，我们可以用数学公式精准量化市场的“认同度”：计算公式：\(\cos (\theta )=\frac{\vec{S}_{t-1}\cdot \vec{\Delta S}_{t}}{\|\vec{S}_{t-1}\|\|\vec{\Delta S}_{t}\|}\)数学含义：\(\cos(\theta) \approx 1\)：顺轨加速。量价状态正在沿着原有的异常方向狂飙，趋势极强（如放量主升浪）。\(\cos(\theta) \approx -1\)：向心引力（均值回归）。量价开始向坐标原点 \((0,0)\) 崩塌，代表动能枯竭，趋势反转。\(\cos(\theta) \approx 0\)：轨道旋转。力量发生切换（如从“放量滞涨”转为“缩量下跌”）。二、 全新分析思路：“量价空间联合熵与逃逸速度”传统思路只看“今天涨了多少，量大了多少”。我们的新思路是：观察量价在多维统计空间中的“能量密度”和“逃逸状态”。维度 1：量价状态的马氏距离（Mahalanobis Distance）—— 寻找“统计奇点”传统的欧氏距离没有考虑量与价之间的相关性。我们使用马氏距离来衡量当前的量价组合偏离历史常态有多远：\(D_{M}(\vec{S}_{t})=\sqrt{(\vec{S}_{t}-\vec{\mu })^{T}\Sigma ^{-1}(\vec{S}_{t}-\vec{\mu })}\)（其中 \(\Sigma \) 为量价的协方差矩阵）新玩法：当 \(D_M > 3\) 时，说明市场进入了极度扭曲的非平衡态。根据热力学第二定律，系统必将释放能量，这通常对应着暴涨前的“压弹簧”阶段或崩盘前的“回光返照”。维度 2：量价联合信息熵（Joint Entropy）—— 识别“趋势洗盘”与“趋势突破”信息熵衡量的是系统的混乱度。低熵状态（量价高度协同，比如价格稳步推升，成交量温和放大）：说明市场筹码高度锁定，主力控盘，趋势具有极强的惯性（买入持有）。高熵状态（量价杂乱无章，比如巨量震荡，价格一会儿大涨一会儿大跌）：说明多空分歧巨大，筹码在剧烈换手，趋势即将变盘（分批离场）。三、 构建量价新趋势指标：量价动能指数（VPKI）基于上述数学推导，我们可以动手创造一个全新的综合指标：量价动能指数（Volume-Price Kinetic Index, VPKI）。1. 指标公式设计\(VPKI_{t}=P_{z,t}\times \ln (1+|V_{z,t}|)\times \>\mathrm{Sign}\>(V_{z,t}-\text{Median}(V_{z}))\)\(P_{z,t}\)：决定了趋势的方向（正为多，负为空）。\(\ln(1 + \vert{}V_{z,t}\vert{})\)：成交量的异常度作为趋势的“质量（Mass）”。用自然对数平滑天量干扰，但依然保留多倍放量的权重。\(\operatorname{Sign}(\cdot)\)：方向修正。只有当成交量高于近期中位数时，才赋予正向动能催化；如果缩量，则判定为动能衰减。2. 新趋势思路的四象限实战应用将 \(P_{z}\)（价格变化异常度）作为 X 轴，\(V_{z}\)（成交量异常度）作为 Y 轴，划分出全新的技术形态：text               Y轴: 成交量 Z-score (Volume_Z)
                      ^

                      |  
    【第二象限：散户恐慌 / 机构吸筹】  |  【第一象限：机构共振 / 主升浪】
    价格极低 + 爆出巨量                 |  价格极高 + 爆出巨量
    (Price_Z < -2, Volume_Z > 2)      |  (Price_Z > 2, Volume_Z > 2)
    ---- 策略：分批左侧抄底 ----         |  ---- 策略：顺势加仓追涨 ----
--------------------------------------|------------------------------------> X轴: 股价偏离 Z-score
    【第三象限：阴跌无量 / 市场冰点】  |  【第四象限：主力诱多 / 量价背离】
    价格极低 + 极度缩量                 |  价格极高 + 极度缩量
    (Price_Z < -1, Volume_Z < -1)     |  (Price_Z > 2, Volume_Z < -1)
    ---- 策略：死水一潭，观望 ----       |  ---- 策略：见顶信号，坚定清仓 ----
                      |
请谨慎使用此类代码。
四、 这一思路的颠覆性优势动态自适应：由于全部采用滚动 Z-score（或马氏距离）作为底层，它自动适应了牛市（高均值高波动）和熊市（低均值低波动），一套参数，全周期通用。
过滤市场噪音：传统的量价看绝对值，容易被对倒盘（伪放量）欺骗。新思路引入了信息熵和夹角余弦，只有当量价方向真正发生物理共振时，指标才会发出趋势确立的信号。
您觉得这个将“量价转化为物理向量场与信息熵”的思路是否符合您的预期？如果您感兴趣，我们可以进一步把这个“量价动能指数 (VPKI) ”或者“四象限状态机”写成具体的 Python 核心算法代码！

返回字典（metrics）的解读指南metrics['Quadrant'] 
(象限机器)：1 代表量价齐升的主升浪。
4 代表缩量上涨的诱多阶段（价格偏离度高但无量支撑，Z-score 揭示的背离）。
metrics['VPKI'] (动能指数)：数值正向越大，代表向上的量价动能越狂暴；负向越大，代表向下砸盘的动能越剧烈。metrics['Cosine_Similarity'] (方向余弦)：趋近于 1.0：量价正在顺着原有的异常轨道加速狂飙，趋势非常稳固，适合持股。
开始掉头趋近于 -1.0：量价正在向均值急速崩塌，引力场正在收回能量，趋势即将反转。

'''
class VP_KineticGravitationalModel:
    """量价动态引力场模型 (Volume-Price Kinetic Gravitational Model) 基于数学统计学与向量场理论
    """

    def __init__(self, window=20):
        self.window = window

    def _calculate_rolling_zscore_numpy(self, prices, volumes):
        """底层数学引擎：计算符合量价特征的滚动 Z-score"""
        p = np.array(prices, dtype=float)
        v = np.array(volumes, dtype=float)
        n = len(p)

        price_z = np.full(n, np.nan)
        volume_z = np.full(n, np.nan)
        v_median = np.full(n, np.nan)

        for i in range(self.window - 1, n):
            # 1. 成交量滚动统计
            window_v = v[i - self.window + 1 : i + 1]
            v_mean = np.mean(window_v)
            v_std = np.std(window_v, ddof=0)
            v_median[i] = np.median(window_v)

            if v_std > 0:
                volume_z[i] = (v[i] - v_mean) / v_std
            else:
                volume_z[i] = 0.0

            # 2. 股价偏离度滚动统计（剥离趋势干扰）
            sub_deviations = []
            for j in range(self.window):
                actual_idx = i - self.window + 1 + j
                if actual_idx < self.window - 1:
                    continue
                current_ma = np.mean(
                    p[actual_idx - self.window + 1 : actual_idx + 1]
                )
                if current_ma > 0:
                    dev = (p[actual_idx] - current_ma) / current_ma
                    sub_deviations.append(dev)

            if len(sub_deviations) > 0:
                sub_deviations = np.array(sub_deviations)
                p_mean = np.mean(sub_deviations)
                p_std = np.std(sub_deviations, ddof=0)

                if p_std > 0:
                    price_z[i] = (sub_deviations[-1] - p_mean) / p_std
                else:
                    price_z[i] = 0.0

        return price_z, volume_z, v_median

    def analyze(self, prices, volumes):
        """对输入的量价数组进行多维统计分析 :param prices: 股价序列 (List 或 np.array)

        :param volumes: 成交量序列 (List 或 np.array)
        :return: dict 包含所有量价引力场核心指标
        """
        n = len(prices)
        # 获取基础 Z-score 数据
        p_z, v_z, v_median = self._calculate_rolling_zscore_numpy(
            prices, volumes
        )

        # 初始化新模型的核心指标数组
        vpki = np.full(n, np.nan)  # 量价动能指数
        cos_theta = np.full(n, np.nan)  # 量价状态向量夹角余弦
        market_quadrant = np.full(n, 0)  # 象限标记 (1, 2, 3, 4)

        for i in range(self.window, n):
            if np.isnan(p_z[i]) or np.isnan(v_z[i]) or np.isnan(p_z[i - 1]):
                continue

            # --- 核心指标 1：量价动能指数 (VPKI) 计算 ---
            # 考虑成交量是否超过中位数，结合对数平滑
            vol_sign = 1.0 if volumes[i] >= v_median[i] else -1.0
            vpki[i] = p_z[i] * np.log(1.0 + abs(v_z[i])) * vol_sign

            # --- 核心指标 2：量价向量夹角余弦 (Cosine Similarity) 计算 ---
            # 当前状态向量 S_t = [Price_Z_t, Volume_Z_t]
            s_prev = np.array([p_z[i - 1], v_z[i - 1]])
            s_curr = np.array([p_z[i], v_z[i]])
            delta_s = s_curr - s_prev  # 速度向量

            norm_s_prev = np.linalg.norm(s_prev)
            norm_delta_s = np.linalg.norm(delta_s)

            if norm_s_prev > 0 and norm_delta_s > 0:
                cos_theta[i] = np.dot(s_prev, delta_s) / (
                    norm_s_prev * norm_delta_s
                )

            # --- 核心指标 3：量价状态四象限划分 ---
            if p_z[i] >= 0 and v_z[i] >= 0:
                market_quadrant[i] = 1  # 第一象限：机构共振 / 主升浪
            elif p_z[i] < 0 and v_z[i] >= 0:
                market_quadrant[i] = 2  # 第二象限：散户恐慌 / 机构吸筹
            elif p_z[i] < 0 and v_z[i] < 0:
                market_quadrant[i] = 3  # 第三象限：阴跌无量 / 市场冰点
            else:
                market_quadrant[i] = 4  # 第四象限：主力诱多 / 量价背离

        return {
            "Price_Z": p_z,
            "Volume_Z": v_z,
            "VPKI": vpki,
            "Cosine_Similarity": cos_theta,
            "Quadrant": market_quadrant,
        }


# ==============================================================================
# 验证与测试用例
# ==============================================================================
if __name__ == "__main__":
    # 模拟 30 天的股票数据
    # 前 20 天风平浪静，第 25 天突然暴涨放量（模拟主升浪突破）
    mock_prices = [
        10.0,
        10.1,
        10.0,
        10.2,
        10.1,
        10.0,
        10.2,
        10.3,
        10.2,
        10.1,
        10.0,
        10.1,
        10.2,
        10.1,
        10.0,
        10.2,
        10.3,
        10.2,
        10.1,
        10.2,
        10.5,
        11.0,
        12.0,
        13.5,
        15.0,
        15.2,
        15.1,
        14.8,
        14.5,
        14.0,
    ]

    mock_volumes = [
        100,
        110,
        95,
        105,
        100,
        90,
        115,
        120,
        105,
        100,
        95,
        110,
        105,
        100,
        90,
        115,
        120,
        105,
        100,
        110,
        300,
        500,
        800,
        1200,
        1500,
        400,
        350,
        300,
        250,
        200,
    ]

    # 初始化模型（设定窗口为15天以便在短数据中观察结果）
    model = VP_KineticGravitationalModel(window=15)
    metrics = model.analyze(mock_prices, mock_volumes)

    print("--- 打印最后 8 个交易日的统计量价引力场分析结果 ---")
    print(
        f"{'天数':<6}{'收盘价':<8}{'成交量':<8}{'Price_Z':<10}{'Volume_Z':<10}{'VPKI (动能)':<14}{'Cos(夹角)':<12}{'量价象限':<10}"
    )

    for i in range(len(mock_prices) - 8, len(mock_prices)):
        quad_names = {
            1: "1-主升共振",
            2: "2-恐慌吸筹",
            3: "3-冰点阴跌",
            4: "4-诱多背离",
            0: "初始化中",
        }
        print(
            f"{i+1:<8}"
            f"{mock_prices[i]:<10.1f}"
            f"{mock_volumes[i]:<10}"
            f"{metrics['Price_Z'][i]:<12.2f}"
            f"{metrics['Volume_Z'][i]:<12.2f}"
            f"{metrics['VPKI'][i]:<16.2f}"
            f"{metrics['Cosine_Similarity'][i]:<14.2f}"
            f"{quad_names[metrics['Quadrant'][i]]}"
        )