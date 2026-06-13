#!/usr/bin/env python3
"""并行运行并列打印 ai_quant_backtest.py 和 ai_quant_backtest_tmp.py 的输出"""
import sys
import io
import contextlib
from tdxcomm import TDXData as tdx

import ai_quant_backtest as a1
import ai_quant_backtest_tmp as a2


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
    stock_code = "300215"
    start_date = "2025-01-01"

    # 准备数据（与原脚本流程一致）
    tdx_datas = tdx(stock_code)
    tdx_datas.getStockDayFile()
    tdx_datas.creatstocKDataList()
    # 保留模块级变量，供两个模块的 _print_markdown_report 使用
    a1.tdx_datas = tdx_datas
    a2.tdx_datas = tdx_datas

    # 构造两个 runner
    r1 = a1.VP_QuantRunner()
    r2 = a2.VP_QuantRunner()

    chart_data = r1.split_data(tdx_datas.getTDXStockKDatas(), start_date=start_date)

    # 捕获两侧输出
    out1, rep1 = capture_stdout(r1.run_pipeline, chart_data)
    out2, rep2 = capture_stdout(r2.run_pipeline, chart_data)

    print('\n' + '='*20 + f' 并列输出：{stock_code} ' + '='*20 + '\n')
    side_by_side_print(out1, out2)


if __name__ == '__main__':
    main()
