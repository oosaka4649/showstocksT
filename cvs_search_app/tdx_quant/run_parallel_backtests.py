#!/usr/bin/env python3
"""并行运行并列打印 ai_quant_backtest.py 和 ai_quant_backtest_tmp.py 的输出"""
import sys
import io
import contextlib
import os

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


def main():
    #if len(sys.argv) < 2:
    #    print('Usage: python run_parallel_backtests.py STOCK_CODE [START_DATE]')
    #    sys.exit(1)

    #stock_code = sys.argv[1]
    #start_date = sys.argv[2] if len(sys.argv) > 2 else '2025-01-01'
    code_ex = '.SH'  # 默认后缀，适用于上海证券交易所的股票代码
    code_ex = '.SZ'  # 如果你分析的是深圳证券交易所的股票，改成这个后缀
    stock_code = "300215"
    start_date = "2025-01-01"

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

    # 捕获两侧输出
    out1, rep1 = capture_stdout(r1.run, chart_data)
    out2, rep2 = capture_stdout(r2.run, chart_data)

    print('\n' + '='*20 + f' 并列输出：{stock_code}  {tdx_datas.stock_name}' + '='*20 + '\n')
    side_by_side_print(out1, out2)


if __name__ == '__main__':
    main()
