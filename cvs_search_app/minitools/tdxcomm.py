'''
这要做成一个取得tdx数据，并转换成各种格式输出
'''

import os
import pandas as pd
from struct import unpack
import user_config as ucfg

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

if __name__ == "__main__":
    data = TDXData()
    