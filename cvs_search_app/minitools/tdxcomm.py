'''
这要做成一个取得tdx数据，并转换成各种格式输出
'''

import os
from struct import unpack

current_dir = os.path.dirname(os.path.abspath(__file__))
# 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)

# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
aijinggu_csv_path = os.path.join(current_dir, 'data', 'aijinggu.csv')
scripts_path = os.path.join(current_dir, 'scripts', 'getaijinggu_byall.py')
stocks_csv_dir = os.path.join(current_dir, 'stockscsv')
tdx_day_file_path = 'C:\\zd_zsone\\vipdoc\\'  # tdx路径

class TDXData:

    STOCK_CODE_NUM = {'6':'sh','3':'sz','0':'sz','4':'bj','8':'bj','9':'bj'}  # 股票代码前缀
    CSV_HEADER_INFO = ['Date','Open','High','Low','Close','Amount','Volume']

    def __init__(self, stock_code = None):
        self.day_file_path = '' 
        self.stock_code = stock_code
        self.day_datas = []

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
      'Date','Open','High','Low','Close','Amount','Volume'
    '''
    # 将通达信的日线文件转换成list[list]格式
    def creatstocKDataList(self):
        if self.day_file_path is not None and len(self.day_file_path) > 1:
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
                # input 'Date','Open','High','Low','Close','Amount','Volume'
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
                # output 'Date','Open','Close','Low','High','Volume','Volume'
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


    def getTDXStockKDatas(self):
        return self.day_datas
    '''
    utile end
    '''

if __name__ == "__main__":
    data = TDXData()
    