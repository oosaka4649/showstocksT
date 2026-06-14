#!/usr/bin/env python3
"""并行运行并列打印 ai_quant_backtest.py 和 ai_quant_backtest_tmp.py 的输出"""
import sys
import io
import contextlib
import os
import time

import ai_quant_backtest as a1
import ai_quant_backtest_tmp as a2
import ai_tdx_get_data as tdx_http_api


# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
# 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minitools.tdxcomm import TDXData as tdx
from minitools import user_config as ucfg

STOCK_CODE_NUM = {'6':'.SH','3':'.SZ','0':'.SZ','4':'.BJ','8':'.BJ','9':'.BJ'}  # 股票代码前缀
#特殊代码
STOCK_CODE_ZS = {'999999':'.SH','399001':'.SZ'}  # 股票代码前缀，sh999999 是上证指数，sz399001 是深成指

def get_stock_prefix(stock_code):
    """根据股票代码获取前缀 第一位数字 6=sh 0,3=sz 9=bj"""
    prefix = STOCK_CODE_NUM.get(stock_code[0], 'unknown')
    #对特殊代码进行处理，比如 000001 是上证指数，000002 是万科A，这些都是深圳交易所的股票，但代码以0开头，所以需要特殊处理
    if stock_code in STOCK_CODE_ZS:
        prefix = STOCK_CODE_ZS[stock_code]
    return prefix

def capture_stdout(func, *args, **kwargs):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = func(*args, **kwargs)
    return buf.getvalue(), res


def side_by_side_print(left_text, right_text, left_width=None, sep=' | '):
    left_lines = left_text.splitlines()
    right_lines = right_text.splitlines()
    n = max(len(left_lines), len(right_lines))
    if left_width is None:
        left_width = max((len(l) for l in left_lines), default=0) + 2
        left_width = min(left_width, 120)
    for i in range(n):
        L = left_lines[i] if i < len(left_lines) else ''
        R = right_lines[i] if i < len(right_lines) else ''
        print(L.ljust(left_width) + sep + R)


def main(stock_code="300215", start_date="2025-01-01"):
    time_str = time.strftime('%Y-%m-%d %H:%M:%S')
    code_ex = get_stock_prefix(stock_code)  # 获取股票代码前缀

    #if len(sys.argv) < 2:
    #    print('Usage: python run_parallel_backtests.py STOCK_CODE [START_DATE]')
    #    sys.exit(1)

    #stock_code = sys.argv[1]
    #start_date = sys.argv[2] if len(sys.argv) > 2 else '2025-01-01'
    # 准备数据（与原脚本流程一致）
    tdx_datas = tdx(stock_code)
    tdx_datas.getStockDayFile()
    tdx_datas.creatstocKDataList()

    # 构造两个 runner
    r1 = a1.VP_QuantRunner()  # 传入 tdx_datas 用于报告显示
    r2 = a2.VP_QuantRunner()  # 传入 tdx_datas 用于报告显示
    api_model = tdx_http_api.TDX_HTTP_API_BaseModel(start_date=start_date)
    _snapshot_data = api_model._tdx_get_market_snapshot(stock_code + code_ex)  # 获取市场快照数据
    chart_data = r1._split_data_add_snapshot_data(tdx_datas.getTDXStockKDatas(), _snapshot_data, start_date=start_date)
    data_len = len(chart_data["categoryData"])
    r1.info2file(quant_result_info='='*20 + f' 并列输出：{time_str} {stock_code}  {tdx_datas.stock_name}' + '='*20 + '数据量: ' + str(data_len) + '='*10)
    r1.info2file(quant_result_info= stock_code + ',' + str(chart_data['categoryData'][(data_len -4):]) + ',' + str(chart_data['closes'][(data_len -4):]) + ',' + str(chart_data['volumes'][(data_len -4):]))
    # 捕获两侧输出
    out1, rep1 = capture_stdout(r1.run, chart_data)
    out2, rep2 = capture_stdout(r2.run, chart_data)
    r1.side_by_side_print_result(out1, out2)
    #side_by_side_print(out1, out2)



'''
先在通达信选股公式选股
  选项  数据导出  ，或 直接 34 弹出到出框
  打开导出数据的excel文件，复制第一列的股票代码，打开 notepad，粘贴，进入列编辑模式，添加单引号和逗号，变成 '300215', 形式，
  将结果考入到下面 list里面，直接执行

'''
if __name__ == '__main__':
    stock_code = "300215"
    start_date = "2025-01-01"
    '''可以在这里修改 stock_code 和 start_date 来测试不同的股票和起始日期
    for stock_code in ucfg.my_stocks_min_max_list:
        main(stock_code, start_date)
    '''
    stock_code_list = [
'000048',
'001359',
'002119',
'002378',
'002409',
'002617',
'002654',
'002842',
'002965',
'002971',
'300054',
'300131',
'300263',
'300666',
'300706',
'300894',
'301161',
'301500',
'600500',
'603120',
'603175',
'603283',
'603324',
'603916',
'605589',
'688010',
'688167',
'688233',
'688530',
'688662',
'688729',
'920015',
]
    for stock_code in stock_code_list:
        main(stock_code, start_date)
