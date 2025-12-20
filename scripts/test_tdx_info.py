import pandas as pd
import user_config as ucfg

'''
读取通达信正常交易状态的股票列表。
https://gitee.com/amengng/stock-analysis/blob/master/readTDX_lday.py
'''
def read_stock_names() -> dict:
    stock_list = {}
    # 读取通达信正常交易状态的股票列表。infoharbor_spec.cfg退市文件不齐全，放弃使用
    tdx_stocks = pd.read_csv(ucfg.tdx['tdx_path'] + '/T0002/hq_cache/infoharbor_ex.code',
                             sep='|', header=None, index_col=None, encoding='gbk', dtype={0: str})
    '''
                    0      1                  2
        0     000001   平安银行       平安保险,谢永林,冀光恒
        1     000002  万  科Ａ          VANKE,黄力平
    '''
    # 将
    df1 = pd.DataFrame(tdx_stocks, columns = [0, 1])
    stock_list = pd.Series(df1[1].values,index=df1[0]).to_dict()
    return stock_list

def get_stock_names():
    stocks = read_stock_names()
    return stocks.get('600312')

if __name__ == "__main__":
    print(get_stock_names())