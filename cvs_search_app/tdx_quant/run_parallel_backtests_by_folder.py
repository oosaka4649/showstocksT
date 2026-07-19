#!/usr/bin/env python3
"""
读取文件夹中的股票代码，批量执行本脚本，并将结果输出到 HTML 文件中。

和基本参照 run_parallel_backtests.py 的区别：
不使用通达信读取实时行情
也不需要判断股票趋势
也不需要并列打印

每次只读取一个文件夹，并，删除指定的特殊代码名
每次只使用一个策略执行，显示是否具有交易机会
   使用极限策略，主要是长期低迷，或市场长期单边下跌时

在结果集中，只显示具有交易机会的股票代码和名称，以及交易日志，不显示全部
"""
import sys
import io
import contextlib
import unicodedata
import os
import json
import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import List, Set

# 脚本常量
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
    # 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from minitools import tdxcomm as tdx
from minitools import user_config as ucfg

import ai_quant_backtest_test42 as a1

import ai_tdx_get_data as tdx_http_api

STOCK_CODE_NUM = {'6':'.SH','3':'.SZ','0':'.SZ','4':'.BJ','8':'.BJ','9':'.BJ'}  # 股票代码前缀
#特殊代码
STOCK_CODE_ZS = {'999999':'.SH','399001':'.SZ'}  # 股票代码前缀，sh999999 是上证指数，sz399001 是深成指
result_file_path = 'folder_backtest_results.txt'  # 输出结果的 HTML 文件路径
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




def main(stock_code="300215", start_date="2025-01-01"):
    out_info = ''
    time_str = tdx_http_api.TDX_Tools.get_Today_Str()
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

    _snapshot_data = None
    chart_data = r1._split_data_add_snapshot_data(tdx_datas.getTDXStockKDatas(), _snapshot_data, start_date=start_date)
    data_len = len(chart_data["categoryData"])

    #数据量不够，直接退出
    if data_len < 100:
        tdx_http_api.TDX_Tools.info2file(quant_result_file=result_file_path, quant_result_info = "\n"*3)
        out_info = '='*20 + f' 并列输出：{time_str} {stock_code}  {tdx_datas.stock_name}' + '='*20 + '数据量: ' + str(data_len)   + '   数据长度不够，不分析，直接退出' + '='*10
        tdx_http_api.TDX_Tools.info2file(quant_result_file=result_file_path, quant_result_info = out_info)
        return False, tdx_datas.stock_name, None
    
    tdx_http_api.TDX_Tools.info2file(quant_result_file=result_file_path, quant_result_info = "\n"*3)
    out_info = '='*20 + f' 并列输出：{time_str} {stock_code}  {tdx_datas.stock_name}' + '='*20 + '数据量: ' + str(data_len)   + '='*10
    tdx_http_api.TDX_Tools.info2file(quant_result_file=result_file_path, quant_result_info = out_info)

    # 捕获两侧输出
    out1, rep1 = capture_stdout(r1.run, chart_data)

    order_info, is_order, last_trade_log = tdx_http_api.TDX_Tools.print_folder_trades_log(rep1)
    if len(last_trade_log) > 0:
        tdx_http_api.TDX_Tools.info2file(quant_result_file=result_file_path, quant_result_info=order_info)
    return is_order, tdx_datas.stock_name, last_trade_log


if __name__ == '__main__':
    # 策略开始日期
    start_date = "2026-01-01"

    TARGET_DIR_SH = "C:\\zd_zsone\\vipdoc\\sh\\lday"
    
    # 过滤规则配置
    PREFIX_REGEX_SH = r"^(sh)"          # 清洗：【抹去】开头的 temp_ 或 test_
    BLACK_LIST_SH = [
        "600200",
        "603388",
        ]    # 内存剔除名单，保留这个，后续可以删除一些不需要的
    KEEP_ONLY_REGEX_SH = r"^(68|60)"  # 只保留以 68 或 60 开头的文件名  588开头是基金 881开头是板块
    
    # 执行过滤
    result_list = get_and_filter_filenames(
        folder_path=TARGET_DIR_SH,
        ignore_prefix_pattern=PREFIX_REGEX_SH,    # 清洗：【抹去】开头的 temp_ 或 test_
        exclude_exact_names=BLACK_LIST_SH, # 减法：精确去掉黑名单
        keep_only_prefix_pattern=KEEP_ONLY_REGEX_SH       # 加法：【只保留】以 backtest_ 开头的文件
    )
    
    print("📋 内存中安全生成的最终文件名列表:")
    print(result_list[:5])  # 仅打印前10个文件名，避免输出过长
    print(f"总计: {len(result_list)} 个文件名符合条件。")

    stock_code_list = [
'605339',

]
    
    stock_code_list = result_list
        
    tdx_http_api.TDX_Tools.info2file(quant_result_file=result_file_path, quant_result_info = "\n"*10)
    is_order_info = []
    for stock_code in stock_code_list:
        is_order, stock_name, last_trade_log = main(stock_code, start_date)
        if is_order:
            is_order_info.append('命中: ' + stock_code + f'  {stock_name}' + "\n" + json.dumps(last_trade_log, ensure_ascii=False) + ' \n' )
    tdx_http_api.TDX_Tools.info2file(quant_result_file=result_file_path, quant_result_info = "\n"*3)
    tdx_http_api.TDX_Tools.info2file(quant_result_file=result_file_path, quant_result_info = "当前命中名单 test：\n" + '\n '.join(is_order_info))

