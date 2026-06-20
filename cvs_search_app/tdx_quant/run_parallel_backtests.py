#!/usr/bin/env python3
"""并行运行并列打印 ai_quant_backtest.py 和 ai_quant_backtest_tmp.py 的输出"""
import sys
import io
import contextlib
import unicodedata
import os
import time

# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
    # 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from minitools import tdxcomm as tdx
from minitools import user_config as ucfg





import ai_quant_backtest as a1
import ai_quant_backtest_tmp as a2
import ai_quant_backtest_test as a3
import ai_quant_backtest_test2 as a4

import ai_tdx_get_data as tdx_http_api

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


def _display_width(text):
    """计算文本在等宽终端中的显示宽度，中文、全角字符视为 2 个宽度。"""
    width = 0
    for ch in text:
        if unicodedata.east_asian_width(ch) in ('F', 'W'):
            width += 2
        else:
            width += 1
    return width


def _pad_text(text, width):
    """按显示宽度补齐文本。"""
    padding = width - _display_width(text)
    return text + ' ' * padding if padding > 0 else text


def side_by_side_print(left_text, right_text, left_width=None, sep=' | '):
    left_lines = left_text.splitlines()
    right_lines = right_text.splitlines()
    n = max(len(left_lines), len(right_lines))
    if left_width is None:
        left_width = max((_display_width(l) for l in left_lines), default=0) + 2
        left_width = min(left_width, 120)
    for i in range(n):
        L = left_lines[i] if i < len(left_lines) else ''
        R = right_lines[i] if i < len(right_lines) else ''
        print(_pad_text(L, left_width) + sep + R)


def multi_column_print(*texts, col_widths=None, sep=' | '):
    """
    将多段多行文本并排打印到控制台（支持 3 列及以上任意多列）
    
    :param texts: 变长参数，传入多个多行字符串
    :param col_widths: 列表或元组，手动指定每列的宽度。默认 None 则自动计算
    :param sep: 列与列之间的分隔符
    """
    if not texts:
        return

    # 1. 将每段文本按行拆分，形成二维列表：columns_lines[列号][行号]
    columns_lines = [text.splitlines() for text in texts]
    num_columns = len(columns_lines)
    
    # 2. 计算最大行数，决定循环打印多少轮
    max_lines = max(len(lines) for lines in columns_lines)
    
    # 3. 动态计算或解析每一列的对齐宽度
    if col_widths is None:
        col_widths = []
        for lines in columns_lines:
            # 自动计算当前列的最长行宽，+2 作为安全间距，最高限制 120
            w = max((_display_width(l) for l in lines), default=0) + 2
            w = min(w, 120)
            col_widths.append(w)
    elif len(col_widths) < num_columns:
        # 如果用户提供的宽度列表长度不足，用默认逻辑补齐
        col_widths = list(col_widths) + [120] * (num_columns - len(col_widths))

    # 4. 逐行拼接并打印
    for i in range(max_lines):
        row_cells = []
        for col_idx in range(num_columns):
            lines = columns_lines[col_idx]
            width = col_widths[col_idx]
            
            # 安全取行，超出文本范围则视为空字符串
            cell_text = lines[i] if i < len(lines) else ''
            
            # 最后一列通常不需要 padding 补白，避免右侧有无意义的空格
            if col_idx == num_columns - 1:
                row_cells.append(cell_text)
            else:
                row_cells.append(_pad_text(cell_text, width))
                
        # 用分隔符拼接当前行的所有列并打印
        print(sep.join(row_cells))



def main(stock_code="300215", start_date="2025-01-01", add_flg=False):
    time_str = time.strftime('%Y-%m-%d %H:%M:%S')
    code_ex = get_stock_prefix(stock_code)  # 获取股票代码前缀

    #if len(sys.argv) < 2:
    #    print('Usage: python run_parallel_backtests.py STOCK_CODE [START_DATE]')
    #    sys.exit(1)

    #stock_code = sys.argv[1]
    #start_date = sys.argv[2] if len(sys.argv) > 2 else '2025-01-01'
    # 准备数据（与原脚本流程一致）
    tdx_datas = tdx.TDXData(stock_code)
    tdx_datas.getStockDayFile()
    tdx_datas.creatstocKDataList()

    # 构造两个 runner
    r1 = a1.VP_QuantRunner()  # 传入 tdx_datas 用于报告显示
    r2 = a2.VP_QuantRunner()  # 传入 tdx_datas 用于报告显示
    r3 = a3.VP_QuantRunner()
    r4 = a4.VP_QuantRunner()
    _snapshot_data = None
    if add_flg:
        api_model = tdx_http_api.TDX_HTTP_API_BaseModel(start_date=start_date)
        _snapshot_data = api_model._tdx_get_market_snapshot(stock_code + code_ex)  # 获取市场快照数据
    chart_data = r1._split_data_add_snapshot_data(tdx_datas.getTDXStockKDatas(), _snapshot_data, start_date=start_date)
    data_len = len(chart_data["categoryData"])
    r1.info2file(quant_result_info='='*20 + f' 并列输出：{time_str} {stock_code}  {tdx_datas.stock_name}' + '='*20 + '数据量: ' + str(data_len) + '='*10)
    #r1.info2file(quant_result_info= stock_code + ',' + str(chart_data['categoryData'][(data_len -4):]) + ',' + str(chart_data['closes'][(data_len -4):]) + ',' + str(chart_data['volumes_macd'][(data_len -4):]))
    # 捕获两侧输出
    out1, rep1 = capture_stdout(r1.run, chart_data)
    out2, rep2 = capture_stdout(r2.run, chart_data)
    out3, rep3 = capture_stdout(r3.run, chart_data)
    out4, rep3 = capture_stdout(r4.run, chart_data)
    r1.multi_column_print(out1, out3, out4, out2)
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
    add_flg = False
    '''可以在这里修改 stock_code 和 start_date 来测试不同的股票和起始日期
    for stock_code in ucfg.my_stocks_min_max_list:
        main(stock_code, start_date)
    '''
    stock_code_list = [
'601006',
]
    for stock_code in stock_code_list:
        main(stock_code, start_date, add_flg)
