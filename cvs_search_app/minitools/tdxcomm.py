'''
这要做成一个取得tdx数据，并转换成各种格式输出
'''

import os
import sys
import pandas as pd
from struct import unpack
import talib
import numpy as np

# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
import user_config as ucfg
# 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)

# 脚本常量
aijinggu_csv_path = os.path.join(parent_dir, 'data', 'aijinggu.csv')
scripts_path = os.path.join(parent_dir, 'scripts', 'getaijinggu_byall.py')
stocks_csv_dir = os.path.join(parent_dir, 'stockscsv')
tdx_day_file_path = 'C:\\zd_zsone\\vipdoc\\'  # tdx路径

class TDXData:

    STOCK_CODE_NUM = {'6':'sh','3':'sz','0':'sz','4':'bj','8':'bj','9':'bj'}  # 股票代码前缀
    CSV_HEADER_INFO = ['Date','Open','Close','Low','High','Volume','Amount']

    #特殊代码
    STOCK_CODE_ZS = {'999999':'sh','399001':'sz'}  # 股票代码前缀，sh999999 是上证指数，sz399001 是深成指

    def __init__(self, stock_code = None):
        self.day_file_path = '' 
        self.stock_code = stock_code
        self.day_datas = []
        self.stock_code_list = {}
        self.stock_name = ''

    '''
     通过股票代码，获取 TDX 中该股票的 day文件路径
    '''
    def getStockDayFile(self):
        try:
            if self.stock_code is not None and len(self.stock_code) == 6 and self.stock_code.isdigit():
                stock_prefix = self.get_stock_prefix()
                self.day_file_path = self.get_stock_day_file_full_path(stock_prefix)
                if not os.path.exists(self.day_file_path):
                    self.day_file_path = None
        except Exception as e:
            self.day_file_path = None  

    '''
    utile star
    '''
    '''
      由于 py echart绘图需要输入数据是 list[list],暂时写这一个函数，后续需要其他格式再添加
      'Date','Open','Close','Low','High','Volume','Amount'

      20260119 添加一个日期，用于对近期的数据进行回测，避免远古数据对回测结果的影响
          比如 东北证券，在2007年复牌时，股票爆涨，这对目前2026年没有意义
    '''
    # 将通达信的日线文件转换成list[list]格式
    def creatstocKDataList(self, startDay=None):
        if self.day_file_path is not None and len(self.day_file_path) > 1:
            self.stock_name = self.get_stock_names()
            # 以二进制方式打开源文件
            source_file = open(self.day_file_path, 'rb')
            buf = source_file.read()
            source_file.close()
            buf_size = len(buf)
            rec_count = int(buf_size / 32)
            begin = 0
            end = 32
            # 解析 startDay（如果提供），支持可被 pandas 解析的任何日期格式
            start_dt = pd.to_datetime(startDay) if startDay is not None else None
            for i in range(rec_count):
                day_line = []
                # 将字节流转换成Python数据格式
                # I: unsigned int
                # f: float
                # input 'Date','Open','High','Low','Close','Volume','Amount'
                a = unpack('IIIIIfII', buf[begin:end])
                # 处理date数据
                year = a[0] // 10000
                month = (a[0] % 10000) // 100
                day = (a[0] % 10000) % 100
                date = '{}-{:02d}-{:02d}'.format(year, month, day)
                tmp_open = str(a[1] / 100.0)
                tmp_high = str(a[2] / 100.0)
                tmp_low = str(a[3] / 100.0)
                tmp_close = str(a[4] / 100.0)
                tmp_amount = str(a[5] / 100.0)
                tmp_volume = str(a[6] / 100.0)
                # output 'Date','Open','Close','Low','High','Volume','Amount'
                day_line = [date, tmp_open, tmp_close, tmp_low, tmp_high, tmp_volume, tmp_amount]
                # 如果未提供 startDay，全部加入；否则只加入日期大于等于 startDay 的数据
                if start_dt is None or pd.to_datetime(date) >= start_dt:
                    self.day_datas.append(day_line)
                begin += 32
                end += 32            


    def get_stock_prefix(self):
        """根据股票代码获取前缀 第一位数字 6=sh 0,3=sz 9=bj"""
        prefix = self.STOCK_CODE_NUM.get(self.stock_code[0], 'unknown')
        #对特殊代码进行处理，比如 000001 是上证指数，000002 是万科A，这些都是深圳交易所的股票，但代码以0开头，所以需要特殊处理
        if self.stock_code in self.STOCK_CODE_ZS:
            prefix = self.STOCK_CODE_ZS[self.stock_code]
        return prefix

    def get_stock_day_file_full_path(self, stock_prefix):
        return f"{tdx_day_file_path}\\{stock_prefix}\\lday\\{stock_prefix}{self.stock_code}.day"  # 示例路径，{0}为市场前缀，{1}为股票代码 'C:\\zd_zsone\\vipdoc\\sh\\lday\\sh600475.day'


    #获取日线数据的list格式
    def getTDXStockKDatas(self):
        return self.day_datas
    
    #获取日线数据的DataFrame格式
    def getTDXStockKDataFrame(self):
        data = pd.DataFrame(self.day_datas, columns=self.CSV_HEADER_INFO)
        data["Date"] = pd.to_datetime(data["Date"])
        data = data.set_index(["Date"])
        return data
    
    #获取日线 list，周线 list数据，月线 list数据
    def getTDXStockDWMDatas(self):
        w_datas = self.tdx_weekly_data()
        dwdatas = w_datas.reset_index().values.tolist()

        m_datas = self.tdx_monthly_data()
        m_datas = m_datas.reset_index().values.tolist() 
        return {"Day_Data": self.day_datas, "Week_Data": dwdatas, "Month_Data": m_datas}

    #将日线数据转换成周线数据的DataFrame格式
    def tdx_weekly_data(self) -> pd.DataFrame :
            weekly_df = self.getTDXStockKDataFrame().resample('W').apply({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            })
            return weekly_df

    #将日线数据转换成月线数据的DataFrame格式
    def tdx_monthly_data(self) -> pd.DataFrame :
            monthly_df = self.getTDXStockKDataFrame().resample('ME').apply({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last'
            })
            return monthly_df

    def read_stock_names(self) -> dict:
        stock_list = {}
        # 读取通达信正常交易状态的股票列表。infoharbor_spec.cfg退市文件不齐全，放弃使用
        tdx_stocks = pd.read_csv(ucfg.tdx['tdx_path'] + '/T0002/hq_cache/infoharbor_ex.code',
                                sep='|', header=None, index_col=None, encoding='gbk', dtype={0: str})
        '''
                        0      1                  2
            0     000001   平安银行       平安保险,谢永林,冀光恒
            1     000002  万  科Ａ          VANKE,黄力平
        '''
        # 只取 代码 和 名称 两列
        df1 = pd.DataFrame(tdx_stocks, columns = [0, 1])
        self.stock_code_list = pd.Series(df1[1].values,index=df1[0]).to_dict()
        return self.stock_code_list
    
    def sanitize_stock_name(self, name: str) -> str:
        if not isinstance(name, str):
            return name
        invalid_chars = '<>:"/\\|?*'
        return ''.join('x' if ch in invalid_chars else ch for ch in name)

    def get_stock_names(self):
        stock_name = self.read_stock_names().get(self.stock_code, 'xx')
        return self.sanitize_stock_name(stock_name)
    '''
    utile end
    '''

################################# common utile ##############################

    '''
        # 分割数据，返回绘图需要的格式
        # input data 结构
            date         开        收        最低       最高       量  价

        # output 格式
        {   "categoryData": category_data,  #全部日期
            "values": values,               #全部日线数据 时间，开 收，低，高， 量，金额
            "volumes": volumes,            #成交量数据
            "closes": closes              #收盘价数据
        }

    '''
    def split_data(self, data):
        category_data = []
        values = []
        volumes = []
        closes = []

        '''
            date         开        收        最低       最高       量
        ["2004-01-02", 10452.74, 10409.85, 10367.41, 10554.96, 168890000],
        data 结构
        
        '''

        for i, tick in enumerate(data):
            category_data.append(tick[0]) # 日期
            values.append(tick) # 全部内容
            closes.append(tick[2]) # 收盘价
            # 元代码 是 tick 4 错了，应该是 tick 5 因为 4是 最高价，5才是量
            volumes.append([i, tick[5], 1 if tick[1] > tick[2] else -1])  # i 是序号 从 0 开始，如果 开始大于收盘 1 ，反之 -1 估计是标 量线颜色用 红 绿
        return {"categoryData": category_data, "values": values, "volumes": volumes, "closes": closes}
    
    '''
    计算周线均线数据,返回 list 格式
    w_data 周线数据  一周只有一个（默认是 周日的日期）
    chart_all_data['categoryData'] 用于对齐日期
    先用 talib 计算均线，然后对齐日期（将一周一个数据的list，补齐全日期，非周末填np.nan空值

    input:
        day_count: 5, 10, 20 ...
        w_data = [
            [date, open, close, low, high, volume],  # 一周只有一个数据 当周的开，收，低，高，量
            ...
        ]
        #{"categoryData": category_data, "values": values, "volumes": volumes, "closes": closes}
        chart_all_data = {'categoryData': [... all dates ...], ...}
    output:
        week_ma_dataes = [ma1, ma2, ma3, ...]
    '''
    def calculate_W_ma_list(self, day_count: int, w_data, chart_all_data):
        '''
        ta lib 使用 np.array 作为输入，但 pyecharts 需要 list 作为输出，所以这里做了转换，而且 数据类型为 double
        '''
        temp_closes = [row[4] for row in w_data if row[4] is not None]
        #将周线日期调整为周五日期（如果使用周线日期，则和日线的日期不对齐，导致均线画不出来，因为日线没有周末数据，划线都以日线的日期为准）
        temp_date = self.change_Wday_to_workday(w_data)
        #先用 talib 计算均线
        temp_w_ma = talib.SMA(np.array(temp_closes, dtype='double'), timeperiod=day_count)
        #对齐日期，补齐非周末日期为 np.nan
        week_ma_dataes = self.add_workday_to_Wday(chart_all_data, temp_date, temp_w_ma)
        return week_ma_dataes


    # 将周线日期调整为周五日期,因为日线没有周末数据，划线都以日线的日期为准
    def change_Wday_to_workday(self, w_data):
        temp_date = [(row[0] - + pd.Timedelta(days=2)).strftime("%Y-%m-%d") for row in w_data if row[4] is not None]
        return temp_date
    
    # 对齐日期，将只有周数据的list，填充np.nan，补全非周末日期为 np.nan，使其长度和日线数据长度一致
    def add_workday_to_Wday(self, chart_all_data, temp_date, temp_w_ma):
        week_ma_dataes = []
        count = 0
        for dt in chart_all_data['categoryData']:
            count += 1
            if dt in temp_date:
                idx = temp_date.index(dt)
                if not np.isnan(temp_w_ma[idx]):
                    week_ma_dataes.append(temp_w_ma[idx])
                else:
                    week_ma_dataes.append(np.float64(np.nan))
            else:
                if count >= len(chart_all_data['categoryData']):
                    week_ma_dataes.append(temp_w_ma[-1]) # 最后一个值 为了不是周末，导致没有值，线没有画到最后
                else :
                    week_ma_dataes.append(np.float64(np.nan))
        return week_ma_dataes


    '''
    计算月线均线数据,返回 list 格式
    m_data 月线数据  一月只有一个（默认是 月末的日期）
    chart_all_data['categoryData'] 用于对齐日期
    先用 talib 计算均线，然后对齐日期（将一月一个数据的list，补齐全日期，非月末填np.nan空值
    input:
        day_count: 5, 10, 20 ...
        m_data = [
            [date, open, close, low, high, volume],  # 一月只有一个数据 当月的开，收，低，高，量
            ...
        ]
        #{"categoryData": category_data, "values": values, "volumes": volumes, "closes": closes}
        chart_all_data = {'categoryData': [... all dates ...], ...}
    '''
    def calculate_M_ma_list(self,day_count: int, m_data, chart_all_data):
        '''
        ta lib 使用 np.array 作为输入，但 pyecharts 需要 list 作为输出，所以这里做了转换，而且 数据类型为 double
        '''
        temp_closes = [row[4] for row in m_data if row[4] is not None]
        #将月线日期调整为每月的最后一个交易日（如果使用月线日期，则有可能月末是周末或节假日，因为日线没有这些日期的数据，划线都以日线的日期为准）
        temp_date = self.change_Mday_to_workday(m_data)
        temp_month_ma = talib.SMA(np.array(temp_closes, dtype='double'), timeperiod=day_count)
        month_ma_dataes = self.add_workday_to_Mday(chart_all_data, temp_date, temp_month_ma)
        return month_ma_dataes 
    
    # 将月线日期调整为每月的最后一个交易日
    def change_Mday_to_workday(self, m_data):
        temp_date = []
        for row in m_data:
            if row[4] is not None :
                if row[0].weekday() <= 4:  # 只取每月的最后一个交易日（假设为周五）
                    temp_date.append(row[0].strftime("%Y-%m-%d"))
                elif row[0].weekday() == 5:  # 如果是周六，取前一天（周五）
                    temp_date.append((row[0] - pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
                elif row[0].weekday() == 6:  # 如果是周日，取前两天（周五）
                    temp_date.append((row[0] - pd.Timedelta(days=2)).strftime("%Y-%m-%d"))
        return temp_date 
    
    # 对齐日期，将只有月数据的list，填充np.nan，补全非月末日期为 np.nan，使其长度和日线数据长度一致
    def add_workday_to_Mday(self, chart_all_data, temp_date, temp_month_ma):
        month_ma_dataes = []
        count = 0
        for dt in chart_all_data['categoryData']:
            count += 1
            if dt in temp_date:
                idx = temp_date.index(dt)
                if not np.isnan(temp_month_ma[idx]):
                    month_ma_dataes.append(temp_month_ma[idx])
                else:
                    month_ma_dataes.append(np.float64(np.nan))
            else:
                if count >= len(chart_all_data['categoryData']):
                    month_ma_dataes.append(temp_month_ma[-1]) # 最后一个值 为了不是月末，导致没有值，线没有画到最后
                else :
                    month_ma_dataes.append(np.float64(np.nan))
        return month_ma_dataes

    #由于下面的函数，如果输入数据中有 np.nan，计算结果会全是 np.nan，所以在计算前先对数据进行标准化或归一化处理，处理后再计算 macd，这样就不会因为输入数据中有 np.nan 导致计算结果全是 np.nan
    def standardize_macd( arr):
        arr = np.asarray(arr, dtype=float)
        mask = np.isnan(arr)

        if mask.all():
            return arr

        mean = np.nanmean(arr)
        std = np.nanstd(arr)

        if std == 0:
            result = np.zeros_like(arr)
            result[mask] = np.nan
            return result

        result = (arr - mean) / std
        result[mask] = np.nan
        return result



    '''
    Z-score 标准化Z-score 标准化基于原始数据的均值（Mean）和标准差（Standard Deviation）进行转换。
    它将数据转化为均值为 (0)、方差为 (1) 的正态分布（或标准分布）。
    数学公式：(Z=frac{x-mu }{sigma })其中 (x) 为原始数据，(mu) 为全体数据的均值，(sigma ) 为全体数据的标准差。
    数据范围：没有固定的理论上下限，转换后的数据通常集中在 ([-3, 3]) 之间。
    '''
    def standardize(arr):
        """
        Z-score 标准化：将数组转换为均值为 0、标准差为 1 的分布。
        
        参数:
            arr (array-like): 输入数组（一维或多维，但按整体计算）
        
        返回:
            np.ndarray: 标准化后的数组，形状与输入相同
        
        处理特殊情况：
            - 如果标准差为零（所有元素相等），返回全零数组（均值即为自身）。
        """
        arr = np.asarray(arr, dtype=float)
        mean = np.mean(arr)
        std = np.std(arr)
        
        if std == 0:
            # 所有值相同，标准化后均为 0
            return np.zeros_like(arr)
        
        return (arr - mean) / std


    def normalize_macd(arr, feature_range=(0, 1)):
        """
        相较于没有macd的函数，这个函数只是，对输入数据进行归一化处理时，就不会因为输入数据中有 np.nan 导致计算结果全是 np.nan
        Min-Max 归一化：将数组缩放到指定的特征范围（默认 [0, 1]）。
        
        参数:
            arr (array-like): 输入数组
            feature_range (tuple): 目标范围，默认为 (0, 1)
        
        返回:
            np.ndarray: 归一化后的数组，形状与输入相同
        
        处理特殊情况：
            - 如果最大值等于最小值，返回全 0 数组（或全为 feature_range[0]）。
            - 如果输入中包含 nan，则保留 nan 位点，并忽略它们的影响。
        """
        arr = np.asarray(arr, dtype=float)
        mask = np.isnan(arr)

        if mask.all():
            return arr

        min_val = np.nanmin(arr)
        max_val = np.nanmax(arr)
        a, b = feature_range

        if max_val == min_val:
            result = np.full_like(arr, a)
            result[mask] = np.nan
            return result

        scaled = (arr - min_val) / (max_val - min_val)
        result = scaled * (b - a) + a
        result[mask] = np.nan
        return result
    

    '''
    Min-Max 归一化Min-Max 归一化（线性归一化）基于原始数据的最大值（Max）和最小值（Min）进行缩放。它将原始数据线性映射到指定的区间内。
    数据范围：严格限定在固定的区间，通常为 ([0, 1]) 或 ([-1, 1])
    
    '''

    def normalize(arr, feature_range=(0, 1)):
        """
        Min-Max 归一化：将数组缩放到指定的特征范围（默认 [0, 1]）。
        
        参数:
            arr (array-like): 输入数组
            feature_range (tuple): 目标范围，默认为 (0, 1)
        
        返回:
            np.ndarray: 归一化后的数组，形状与输入相同
        
        处理特殊情况：
            - 如果最大值等于最小值，返回全 0 数组（或全为 feature_range[0]）。
        """
        arr = np.asarray(arr, dtype=float)
        min_val = np.min(arr)
        max_val = np.max(arr)
        a, b = feature_range
        
        if max_val == min_val:
            # 所有值相同，无法缩放，返回全为下限值
            return np.full_like(arr, a)
        
        # 线性缩放公式
        scaled = (arr - min_val) / (max_val - min_val)  # 先缩放到 [0, 1]
        return scaled * (b - a) + a    



    '''
    成交量为什么不使用和股价一样的处理细节？
    因为由于突发事件，成交量也会比平时多出数倍您的直觉非常敏锐！
    这正是量化金融中一个非常经典且深刻的数据特征问题。
    
    结论先行：成交量不使用股价那套“偏离度”处理，恰恰就是因为成交量的“突发放大数倍”是脉冲式的、会自我修正的；
    而股价的上涨是累积式的、不会轻易回头。
    以下从数学结构和金融逻辑两个维度，为您拆解为什么成交量可以直接做 Z-score，
    而股价必须拐个弯：1. 数据的数学结构不同（随机游走 vs. 均值回归）股价是“非平稳的”（随机游走）：股价具有时间累积效应。
                       如果一只股票从 10 元涨到 100 元，它会产生一个新的价格平台，永远都不会再回到 10 元。
                       如果您直接对绝对股价做 20 日滚动 Z-score，在持续暴涨的牛市里，每天的价格都会踩着前期的价格往上爬，导致连续几周的 Price_Z 都卡死在 +2 或 +3 的上限，指标出现严重钝化，失去灵敏度。
                       因此，我们必须用“偏离度”把这个长期趋势剥离掉。
                成交量是“天生均值回归的”（脉冲式）：成交量无论因为突发事件放大到多少倍（比如平时 1 万手，今天突发利好爆量到 50 万手），它绝对不可能长期维持在 50 万手。
                过几天热度散去，成交量一定会重新掉落回 1 万手或 2 万手附近。也就是说，成交量虽然有突发的高峰，但它的中枢（均值）在短期内是相对稳定的。
                这种天生会“吐故纳新、回到原点”的数据，直接做 Z-score 就能完美捕捉到那次突发的脉冲。
                    2. 我们对两者的“分析目的”完全不同对成交量：我们需要捕捉“绝对的异常”突发事件导致成交量放大数倍，这正是我们梦寐以求想要捕捉的信号！
                    如果直接对成交量做 Z-score，今天爆量，Volume_Z 就会立刻飙升到 +4 甚至 +6。这个高额的数值会像一个明亮的警报灯一样告诉程序：“注意，这地方出大事了！”这正是我们需要的反馈。
                    对股价：我们需要剔除“绝对幅度的干扰”股价由于基数不同，绝对涨幅的威力不同。比如股票 A 从 10 元涨到 11 元（涨 10%），股票 B 从 100 元涨到 101 元（涨 1%）。
                    如果我们不用“偏离度（百分比）”消除基数影响，直接对股价绝对值做 Z-score，高价股和小幅波动就会产生严重的数学扭曲。
    
    '''
    def calculate_rolling_zscore(prices, volumes, window=20):
        """使用 NumPy 数组计算股价和成交量的滚动 Z-score。

        :param prices: 股价数组 (List 或 NumPy Array)
        :param volumes: 成交量数组 (List 或 NumPy Array)
        :param window: 滚动窗口大小（默认20天）
        :return: (price_z, volume_z) 两个与其等长的 NumPy 数组，前 window-1
        个元素为 np.nan
        """
        # 转换为 numpy 浮点数数组，方便处理缺失值
        p = np.array(prices, dtype=float)
        v = np.array(volumes, dtype=float)
        n = len(p)

        # 初始化结果数组，默认填充为 nan
        price_z = np.full(n, np.nan)
        volume_z = np.full(n, np.nan)

        if n < window:
            return price_z, volume_z

        # 1. 计算成交量的滚动 Z-score
        # 2. 计算股价偏离度 (Price Deviation) 的滚动 Z-score
        for i in range(window - 1, n):
            # 截取当前窗口内的数据
            window_v = v[i - window + 1 : i + 1]
            window_p = p[i - window + 1 : i + 1]

            # --- 成交量计算 (直接 Z-score) ---
            v_mean = np.mean(window_v)
            v_std = np.std(window_v, ddof=0)  # ddof=0 为总体标准差
            if v_std > 0:
                volume_z[i] = (v[i] - v_mean) / v_std
            else:
                volume_z[i] = 0.0  # 若标准差为0（数据完全一样），Z-score 设为 0

            # --- 股价计算 (基于滑动窗口内的偏离度再做 Z-score) ---
            # 计算窗口内每天的股价，偏离【各自过去20天均线】的比例
            # 为了严格保证不引入未来数据，这里动态计算该窗口内部的偏离度序列
            sub_deviations = []
            for j in range(window):
                # 找到当前考察点 j 在原数组中的实际索引
                actual_idx = i - window + 1 + j
                if actual_idx < window - 1:
                    continue
                # 计算这一天的移动平均线
                current_ma = np.mean(p[actual_idx - window + 1 : actual_idx + 1])
                if current_ma > 0:
                    dev = (p[actual_idx] - current_ma) / current_ma
                    sub_deviations.append(dev)

            # 对当前的偏离度序列计算 Z-score
            if len(sub_deviations) > 0:
                sub_deviations = np.array(sub_deviations)
                p_mean = np.mean(sub_deviations)
                p_std = np.std(sub_deviations, ddof=0)

                if p_std > 0:
                    price_z[i] = (sub_deviations[-1] - p_mean) / p_std
                else:
                    price_z[i] = 0.0

        return price_z, volume_z





if __name__ == "__main__":
    data = TDXData()
    