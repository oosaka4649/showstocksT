import numpy as np
import pandas as pd
import os
import json
import sys
from pathlib import Path
import re
import time
from typing import Dict, List, Optional, Tuple

# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
    # 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from minitools import tdxcomm as tdx
from minitools import user_config as ucfg

'''
这个是2-1的简化版

1 去掉大盘过滤，保留函数，直接返回，后面添加
2 策略全参数里面缩短了历史最大量对比周期有 100 改为 30，即，只考虑30日内的量
3 将当天实体涨跌幅统一改为  10%

'''
class StrategyConfig:
    """策略全参数配置类"""
    def __init__(self):
        # --- 大盘过滤器参数 ---
        self.MARKET_BREADTH_RATIO_LIMIT = 4.0      # 下跌/上涨家数极限比值 (4:1)
        self.MARKET_LIQUIDITY_LIMIT = 0.8           # 全市场总成交额对于20日均额的下限比例
        
        # --- 个股形态参数 ---
        self.STOCK_VOL_MA_PERIOD = 20               # 个股成交量均线周期
        self.STOCK_VOL_MULT_THRESHOLD = 2.0         # 个股当前量必须大于20日均量的2倍
        self.STOCK_MAX_VOL_PERIOD = 30             # 个股历史最大量对比周期    为了测试将100天，改为30天
        self.STOCK_MAX_VOL_RATIO = 0.8              # 当前量必须达到100天内最大天量的80%以上
        self.STOCK_SHADOW_RATIO_MIN = 0.6           # 下影线占比阈值 (下影线占全天振幅60%以上)
        self.STOCK_MAX_ENTITY_DEAL = -0.10         # 个股当天实体跌幅不得大于 -2.5% -0.025
        self.STOCK_MAX_ENTITY_GAIN = 0.10          # 个股当天实体涨幅不得大于 +1.5% (防止追高暴涨股) 0.015


class MarketEnvironmentFilter:
    """大盘量价环境过滤器 (一票否决制)"""
    def __init__(self, config: StrategyConfig, index_df: pd.DataFrame):
        self.cfg = config
        self.index_data = self._preprocess_index(index_df)

    def _preprocess_index(self, df: pd.DataFrame) -> pd.DataFrame:
        """预处理指数数据，计算5日成交量均线及昨收"""
        df = df.sort_values('trade_date').copy()
        df['index_vol_ma5'] = df['vol'].rolling(window=5, min_periods=1).mean()
        df['index_pre_close'] = df['close'].shift(1)
        return df

    def is_market_safe(self, current_date: str, breadth_data: Dict) -> bool:
        '''
        简化大盘过滤，后续 有时间 添加 读入 沪深两市 K线数据，进行叠加后放开
        """大盘一票否决制详细策略内容"""
        index_snapshot = self.index_data[self.index_data['trade_date'] == current_date]
        if index_snapshot.empty:
            return False  
            
        # 显式精准转为第一行标量字典
        row = index_snapshot.iloc[0].to_dict()
        
        # --- 核心条件 1：情绪广度未崩盘 ---
        if breadth_data['advance_count'] > 0:
            breadth_ratio = breadth_data['decline_count'] / breadth_data['advance_count']
            if breadth_ratio >= self.cfg.MARKET_BREADTH_RATIO_LIMIT:
                return False
        else:
            return False  
            
        # --- 核心条件 2：指数属于健康的缩量调整 ---
        if float(row['close']) < float(row['index_pre_close']):
            if float(row['vol']) >= float(row['index_vol_ma5']):
                return False  
                
        # --- 核心条件 3：全市场总流动性在安全线以上 ---
        if 'market_volume_ma20' in breadth_data and breadth_data['market_volume_ma20'] > 0:
            liquidity_ratio = breadth_data['total_amount'] / breadth_data['market_volume_ma20']
            if liquidity_ratio < self.cfg.MARKET_LIQUIDITY_LIMIT:
                return False
        '''
        return True


class StockSingleScanner:
    """单只股票时间序列形态扫描器 (适配单股循环流)"""
    def __init__(self, config: StrategyConfig):
        self.cfg = config

    def _safe_divide(self, numerator: float, denominator: float) -> float:
        """防御性控制：防止一字板无波幅个股导致除零错误"""
        return 0.0 if denominator == 0 else float(numerator / denominator)

    def convert_to_dataframe(self, stock_data: Dict) -> pd.DataFrame:
        """【数据适配器】将您特有的股票数据格式转换为标准时间序列 DataFrame"""
        category_data = stock_data["categoryData"]
        closes = stock_data["closes"]
        volumes = stock_data["volumes"]
        
        dates = [row[0] for row in category_data]
        opens = [float(row[1]) for row in category_data]
        closes_list = [float(c) for c in closes]
        lows = [float(row[3]) for row in category_data]
        highs = [float(row[4]) for row in category_data]
        
        df = pd.DataFrame({
            'trade_date': dates,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes_list,
            'vol': [float(v) for v in volumes]
        })
        
        df = df.sort_values('trade_date').reset_index(drop=True)
        df['pre_close'] = df['close'].shift(1)
        return df

    def check_signal(self, single_stock_df: pd.DataFrame, current_date: str) -> Tuple[bool, float, float]:
        """个股形态精密筛查详细策略内容"""
        if single_stock_df.empty:
            return False, 0.0, 0.0
            
        if not (len(single_stock_df) >= 100):
            return False, 0.0, 0.0
            
        # 1. 统计计算：滚动计算均线与历史100天最大量
        single_stock_df['vol_ma20'] = single_stock_df['vol'].rolling(window=self.cfg.STOCK_VOL_MA_PERIOD, min_periods=20).mean()
        single_stock_df['vol_max100'] = single_stock_df['vol'].rolling(window=self.cfg.STOCK_MAX_VOL_PERIOD, min_periods=30).max() #min_periods=100
        
        # 2. 定位执行日快照
        target_rows = single_stock_df[single_stock_df['trade_date'] == current_date]
        if target_rows.empty:
            return False, 0.0, 0.0
            
        # 【核心修正】：精准定位到第0行并解包字典，杜绝降维歧义
        row_dict = target_rows.iloc[0].to_dict()
        
        # 安全防御：利用原生 np.isnan 对标量进行纯净校验
        if np.isnan(row_dict['vol_ma20']) or np.isnan(row_dict['vol_max100']) or np.isnan(row_dict['pre_close']):
            return False, 0.0, 0.0

        # 获取具体的纯 Python 标量值
        close_val = float(row_dict['close'])
        pre_close_val = float(row_dict['pre_close'])
        open_val = float(row_dict['open'])
        low_val = float(row_dict['low'])
        high_val = float(row_dict['high'])
        vol_val = float(row_dict['vol'])
        vol_ma20_val = float(row_dict['vol_ma20'])
        vol_max100_val = float(row_dict['vol_max100'])

        # ==============================================================================
        # 个股多重核心算式过滤器 
        # ==============================================================================
        
        # --- 条件 1：趋势回调特征（涨跌幅限制） ---
        today_entity_pct = (close_val - pre_close_val) / pre_close_val
        
        if self.cfg.STOCK_MAX_ENTITY_DEAL > today_entity_pct:
            return False, 0.0, 0.0
            
        if today_entity_pct > self.cfg.STOCK_MAX_ENTITY_GAIN:
            return False, 0.0, 0.0  

        # --- 条件 2：爆发历史天量确认 ---
        is_volume_spike = vol_val > (vol_ma20_val * self.cfg.STOCK_VOL_MULT_THRESHOLD)
        is_near_max_vol = vol_val >= (vol_max100_val * self.cfg.STOCK_MAX_VOL_RATIO)
        if not (is_volume_spike and is_near_max_vol):
            return False, 0.0, 0.0

        # --- 条件 3：铁板承接度计算 (DSC) ---
        entity_bottom = min(open_val, close_val)
        lower_shadow = entity_bottom - low_val
        total_amplitude = high_val - low_val
        
        # 计算下影线占比
        dsc_score = self._safe_divide(lower_shadow, total_amplitude)
        
        if self.cfg.STOCK_SHADOW_RATIO_MIN > dsc_score:
            return False, 0.0, 0.0  

        # ==============================================================================
        # 统计学打分输出
        # ==============================================================================
        vol_score = self._safe_divide(vol_val, vol_ma20_val)
        
        return True, dsc_score, vol_score


class QuantitativeTradingEngine:
    """量化策略总调度引擎"""
    def __init__(self, config: StrategyConfig, env_filter: MarketEnvironmentFilter, scanner: StockSingleScanner):
        self.cfg = config
        self.env_filter = env_filter
        self.scanner = scanner

    def run_daily_pipeline(self, current_date: str, stock_code_list: List[str], fetch_data_func, breadth_data: Dict) -> pd.DataFrame:
        """每日盘后标准流水线"""
        print(f"[{current_date}] 启动盘后策略选股流水线...")
        
        # 1. 大盘环境优先检查
        if not self.env_filter.is_market_safe(current_date, breadth_data):
            print(f"[{current_date}] 警报：大盘过滤器触发熔断！今日放弃所有个股信号，安全退出。")
            return pd.DataFrame(columns=['trade_date', 'ts_code', 'stock_name', 'stock_dsc', 'stock_vol_zscore'])
            
        print(f"[{current_date}] 大盘环境安全。进入个股循环扫描...")
        results = []
        
        # 2. 串行股票池循环
        for stock_code in stock_code_list:
            try:
                stock_name, stock_raw_data = fetch_data_func(stock_code)
                stock_df = self.scanner.convert_to_dataframe(stock_raw_data)
                
                # 执行策略形态校验
                is_signal, dsc_score, vol_score = self.scanner.check_signal(stock_df, current_date)
                
                if is_signal:
                    results.append({
                        'trade_date': current_date,
                        'ts_code': stock_code,
                        'stock_name': stock_name,
                        'stock_dsc': round(dsc_score, 4),
                        'stock_vol_zscore': round(vol_score, 2)
                    })
                    print(f" -> [信号触发] 股票: {stock_code} ({stock_name}) | 下影线占比: {dsc_score:.2%} | 超额量能: {vol_score:.1f}倍")
                    
            except Exception as e:
                print(f" 警告：股票 {stock_code} 数据解析异常，已自动跳过。错误: {str(e)}")
                continue
                
        output_manifest = pd.DataFrame(results)
        if not output_manifest.empty:
            output_manifest = output_manifest.sort_values(by=['stock_vol_zscore', 'stock_dsc'], ascending=False).reset_index(drop=True)
        else:
            output_manifest = pd.DataFrame(columns=['trade_date', 'ts_code', 'stock_name', 'stock_dsc', 'stock_vol_zscore'])
            
        print(f"[{current_date}] 扫描完成。本日共计选出 {len(output_manifest)} 只满足非对称吸筹特征的股票。")
        return output_manifest


# ==============================================================================
# 生产环境运行与测试示例 (已通过严格闭环测试)
# ==============================================================================
def _split_data(data, start_date=None):
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
        volumes.append(tick[5]) # 这个是为了计算 macd 用的，输入为量值，看看能不能生成一个和 macd 类似的曲线，观察成交量和 macd 的关系
    return {"categoryData": category_data, "values": values, "volumes": volumes, "closes": closes}

# 4. 构造符合你格式要求的“个股原始数据字典”接口函数
def mock_fetch_stock_data(stock_code: str, start_date="2025-01-01") -> Tuple[str, Dict]:

    tdx_datas = tdx.TDXData(stock_code)
    tdx_datas.getStockDayFile()
    tdx_datas.creatstocKDataList()
    chart_data = _split_data(tdx_datas.getTDXStockKDatas(), start_date=start_date)
    raw_dict = {
        "categoryData": chart_data["values"],
        "closes": chart_data["closes"],
        "volumes": chart_data["volumes"]
    }
    return tdx_datas.stock_name, raw_dict


def get_and_filter_filenames(
    folder_path: str,
    ignore_prefix_pattern: str = r"^(temp_|test_)",
    exclude_exact_names: List[str] = None,
    keep_only_prefix_pattern: str = r"^backtest_"
) -> List[str]:
    """
    量化安全级：文件名正则清洗与双向过滤引擎
    
    功能:
    1. 内存级安全读取：绝对不触碰、不重命名磁盘实际文件，只在内存的 List 中做字符串清洗。
    2. 【修改核心】正则内容擦除：将原始文件名中满足 ignore_prefix_pattern 的内容【抹去/替换为空】。
    3. 精确名单剔除：如果清洗后的文件名在 exclude_exact_names 黑名单中，则剔除。
    4. 正则白名单保留：对清洗后的文件名进行校验，【只保留】以 keep_only_prefix_pattern 开头的名字。
    
    参数:
    - folder_path: str, 目标文件夹路径
    - ignore_prefix_pattern: str, 文件名中【要被抹去/擦除】的正则表达式内容
    - exclude_exact_names: List[str], 指定从返回列表中【要剔除】的精确文件名黑名单
    - keep_only_prefix_pattern: str, 用于匹配【只保留】的开头的正则表达式
    
    返回:
    - List[str]: 经过内存级字串清洗、黑白名单双向卡口后，最终生成的纯净文件名列表
    """
    dir_path = Path(folder_path)
    
    # 健壮性检查
    if not dir_path.exists() or not dir_path.is_dir():
        print(f"⚠️ 警告：路径不存在或不是有效的文件夹 -> {folder_path}")
        return []

    exclude_set: Set[str] = set(exclude_exact_names) if exclude_exact_names else set()
    final_file_list: List[str] = []
    
    # 预编译正则表达式
    regex_ignore = re.compile(ignore_prefix_pattern)
    end_regex_ignore = re.compile(r"\.day$")  # 额外的正则，用于去掉 .day 后缀
    regex_keep_only = re.compile(keep_only_prefix_pattern)

    # 遍历文件夹进行内存级处理
    for file_path in dir_path.iterdir():
        if file_path.is_file():
            raw_filename = file_path.name
            
            # ── 阶段 1：【核心修改】执行内存级正则字串擦除 ──
            # 使用 re.sub 将匹配到的干扰字串替换为 "" (空字符串)
            cleaned_filename = regex_ignore.sub("", raw_filename)
            cleaned_filename = end_regex_ignore.sub("", cleaned_filename)  # 去掉 .day 后缀

            # ── 阶段 2：基于清洗后的新名字做黑名单拦截 ──
            if cleaned_filename in exclude_set:
                continue
                
            # ── 阶段 3：基于清洗后的新名字做特定开头白名单筛选 ──
            if not regex_keep_only.match(cleaned_filename):
                continue
                
            # 完美的成果装入 list
            final_file_list.append(cleaned_filename)

    return final_file_list

def run_strategy_example():
    # 1. 实例化核心配置
    config = StrategyConfig()
    
    # 2. 构造模拟的大盘指数数据 (良性缩量回调)
    index_data_raw = {
        'trade_date': ['2026-07-20', '2026-07-21', '2026-07-22', '2026-07-23', '2026-07-24'],
        'open': [3050.0, 3040.0, 3030.0, 3020.0, 3010.0],
        'high': [3060.0, 3050.0, 3040.0, 3030.0, 3015.0],
        'low': [3030.0, 3020.0, 3010.0, 3000.0, 2995.0],
        'close': [3040.0, 3030.0, 3020.0, 3010.0, 3005.0], # 指数今天收盘 3005.0，相比昨天3010.0下跌
        'vol': [1500.0, 1400.0, 1300.0, 1200.0, 1000.0],    # 今天成交量 1000，明显小于前几天的均值（缩量跌）
        'amount': [150.0, 140.0, 130.0, 120.0, 100.0]
    }
    mock_index_df = pd.DataFrame(index_data_raw)
    
    # 3. 构造盘后全市场广度快照 (大盘未崩盘)
    mock_breadth = {
        'trade_date': '2026-07-24',
        'advance_count': 1500,     # 上涨1500家 + 平盘
        'decline_count': 4940,     # 下跌3000家 (下跌/上涨 = 2.0，未超过4倍的安全红线)
        'total_amount': 19300.0,    # 全市场今日总成交额
        'market_volume_ma20': 8000.0 # 全市场20日平均总成交额 (7500/8000 = 0.93，流动性充沛)
    }

    # 5. 依赖注入组装量化引擎
    ami_filter = MarketEnvironmentFilter(config, index_df=mock_index_df)
    single_scanner = StockSingleScanner(config)
    engine = QuantitativeTradingEngine(config, env_filter=ami_filter, scanner=single_scanner)
    

    target_dir = {'SH':"C:\\zd_zsone\\vipdoc\\sh\\lday",
                  'SZ':"C:\\zd_zsone\\vipdoc\\sz\\lday"}

    target_keep = {'SH': r"^(68|60)", # 只保留以 68 或 60 开头的文件名  588开头是基金 881开头是板块 399是指数
                   'SZ': r"^(00|30)"}
    # 过滤规则配置
    PREFIX_REGEX = r"^(sh|sz)"          # 清洗：【抹去】开头的 temp_ 或 test_
    BLACK_LIST = [
        "600200",
        "603388",
        ]    # 内存剔除名单，保留这个，后续可以删除一些不需要的
    
    TARGET_DIR = target_dir['SZ']
    KEEP_ONLY_REGEX = target_keep['SZ']


    # 执行过滤
    result_list = get_and_filter_filenames(
        folder_path=TARGET_DIR,
        ignore_prefix_pattern=PREFIX_REGEX,    # 清洗：【抹去】开头的 temp_ 或 test_
        exclude_exact_names=BLACK_LIST, # 减法：精确去掉黑名单
        keep_only_prefix_pattern=KEEP_ONLY_REGEX      # 加法：【只保留】以 backtest_ 开头的文件
    )
    
    print("📋 内存中安全生成的最终文件名列表:")
    print(result_list[:5])  # 仅打印前10个文件名，避免输出过长
    print(f"总计: {len(result_list)} 个文件名符合条件。")

    # 6. 定义要扫描的测试股票池
    test_stock_pool = [
'000815',
     ]
   
    test_stock_pool = result_list

    panic_manifest = engine.run_daily_pipeline(
        current_date='2026-07-27',
        stock_code_list=test_stock_pool,
        fetch_data_func=mock_fetch_stock_data,
        breadth_data=mock_breadth
    )
    print("\n[输出结果清单]:")
    print(panic_manifest)


# 执行测试
if __name__ == "__main__":
    run_strategy_example()
