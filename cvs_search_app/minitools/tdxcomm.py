'''
这要做成一个取得tdx数据，并转换成各种格式输出
'''

import os
import pandas as pd
from struct import unpack
import user_config as ucfg
import talib
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
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
    '''
    # 将通达信的日线文件转换成list[list]格式
    def creatstocKDataList(self):
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
                self.day_datas.append(day_line)
                begin += 32
                end += 32            


    def get_stock_prefix(self):
        """根据股票代码获取前缀 第一位数字 6=sh 0,3=sz 9=bj"""
        prefix = self.STOCK_CODE_NUM.get(self.stock_code[0], 'unknown')
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
    
    def get_stock_names(self):
        return self.read_stock_names().get(self.stock_code, 'xx')
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

  

if __name__ == "__main__":
    data = TDXData()
    