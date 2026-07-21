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

import ai_quant_backtest_test43 as a1

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
        tdx_http_api.TDX_Tools.info2file(quant_result_file=result_file_path, quant_result_info = "\n"*2)
        out_info = '='*20 + f' 并列输出：{time_str} {stock_code}  {tdx_datas.stock_name}' + '='*20 + '数据量: ' + str(data_len)   + '   数据长度不够，不分析，直接退出' + '='*10
        tdx_http_api.TDX_Tools.info2file(quant_result_file=result_file_path, quant_result_info = out_info)
        return False, tdx_datas.stock_name, None
    
    tdx_http_api.TDX_Tools.info2file(quant_result_file=result_file_path, quant_result_info = "\n"*1)
    out_info = '='*20 + f' 并列输出：{time_str} {stock_code}  {tdx_datas.stock_name}' + '='*20 + '数据量: ' + str(data_len)   + '='*10
    tdx_http_api.TDX_Tools.info2file(quant_result_file=result_file_path, quant_result_info = out_info)

    # 捕获两侧输出
    out1, rep1 = capture_stdout(r1.run, chart_data)

    order_info, is_order, last_trade_log = tdx_http_api.TDX_Tools.print_folder_trades_log(rep1)
    #if len(last_trade_log) > 0:  由于是全市信息，量非常大，缩短输出的长度，不打印收益信息
    #    tdx_http_api.TDX_Tools.info2file(quant_result_file=result_file_path, quant_result_info=order_info)
    return is_order, tdx_datas.stock_name, last_trade_log


def generate_multi_stock_report(stock_data_dict: dict, output_filename: str = "multi_stock_report.html"):
    """
    Python 架构师多组股票定制版：
    1. 保持无统计看板的精简风格
    2. 支持传入任意多组股票数据，每只股票独立分块
    3. 核心布局依然是买入与卖出/平仓横向成对合一
    4. 100% 纯静态内联 CSS，零联网、零 JS、断网双击秒开
    """
    if not stock_data_dict:
        print("⚠️ 警告：传入的股票数据字典为空，未生成报告。")
        return

    # 全局块结构拼接
    all_stocks_sections_html = ""

    # 遍历每只股票的数据
    for stock_info, trade_list in stock_data_dict.items():
        
        # 1. 架构级内部数据重组：将当前股票零散的明细智能匹配成完整的交易对
        paired_trades = []
        current_buy = None

        for trade in trade_list:
            t_type = str(trade.get("type", "")).upper()
            if "BUY" in t_type:
                if current_buy:
                    paired_trades.append({"buy": current_buy, "close": None})
                current_buy = trade
            elif "CLOSE" in t_type or "SELL" in t_type:
                if current_buy:
                    paired_trades.append({"buy": current_buy, "close": trade})
                    current_buy = None
                else:
                    paired_trades.append({"buy": None, "close": trade})
                    
        if current_buy:
            paired_trades.append({"buy": current_buy, "close": None})

        # 2. 循环拼接当前股票内部的成对表格行
        table_rows_html = ""
        for idx, pair in enumerate(paired_trades, 1):
            buy_data = pair["buy"]
            close_data = pair["close"]

            # 格式化买入侧数据
            if buy_data:
                b_date = str(buy_data.get("date", "-"))
                b_price = f"{float(buy_data.get('price', 0.0)):.2f}"
                b_reason = str(buy_data.get("reason", "-"))
            else:
                b_date = b_price = b_reason = '<span style="color:#cbd5e1;">-</span>'

            # 格式化平仓侧数据
            if close_data:
                c_type = str(close_data.get("type", ""))
                c_label = "平仓 (CLOSE)" if "CLOSE" in c_type else "卖出 (SELL)"
                c_date = str(close_data.get("date", "-"))
                c_price = f"{float(close_data.get('price', 0.0)):.2f}"
                c_return_val = float(close_data.get("return", 0.0))
                c_reason = str(close_data.get("reason", "-"))

                if c_return_val > 0:
                    return_badge = f'<span style="color: #10b981; font-weight: bold; font-family: monospace;">+{c_return_val:.2f}%</span>'
                elif c_return_val < 0:
                    return_badge = f'<span style="color: #ef4444; font-weight: bold; font-family: monospace;">{c_return_val:.2f}%</span>'
                else:
                    return_badge = '<span style="color: #94a3b8; font-family: monospace;">0.00%</span>'
            else:
                c_label = c_date = c_price = return_badge = c_reason = '<span style="color:#cbd5e1;">-</span>'

            # 组装单行
            table_rows_html += f"""
            <tr style="border-bottom: 2px solid #f1f5f9;">
                <td style="padding: 16px 12px; text-align: center; font-weight: bold; color: #94a3b8; font-family: monospace;">#{idx}</td>
                
                <!-- 买入侧 -->
                <td style="padding: 16px 16px; background-color: #fbfdfc; border-right: 1px dashed #e2e8f0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="background-color: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px;">买入 (BUY)</span>
                        <div style="font-size: 13px;">{b_reason}</div>
                    </div>
                    <div style="font-family: monospace; font-size: 12px; color: #64748b; margin-top: 6px;">日期: {b_date}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="font-family: monospace; font-size: 14px; font-weight: bold;color: #0f172a;">价格: ¥{b_price}</span></div>
                </td>
                
                <!-- 平仓/卖出侧 -->
                <td style="padding: 16px 16px; background-color: #fcfcfd;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        {"".join([f'<span style="background-color: #fffbeb; color: #b45309; border: 1px solid #fde68a; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px;">{c_label}</span>' if close_data else ''])}
                        <div style="font-size: 13px;">{c_reason}</div>
                        <div style="font-size: 13px;">实现收益: {return_badge}</div>
                    </div>
                    <div style="font-family: monospace; font-size: 12px; color: #64748b; margin-top: 6px;">日期: {c_date}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="font-family: monospace; font-size: 14px; font-weight: bold;color: #0f172a;">价格: ¥{c_price}</span></div>
                </td>
            </tr>
            """

        # 3. 将当前股票包装为一个独立的高颜值表格区块
        all_stocks_sections_html += f"""
        <!-- 股票小区块 -->
        <div style="margin-bottom: 40px;">
            <!-- 股票标签头 -->
            <div style="background-color: #1e293b; color: #ffffff; padding: 12px 20px; border-radius: 8px 8px 0 0; font-size: 15px; font-weight: bold; display: flex; justify-content: space-between; align-items: center;">
                <span>📈 标的资产：{stock_info}</span>
                <span style="font-size: 11px; background-color: rgba(255,255,255,0.15); padding: 2px 8px; border-radius: 4px; font-weight: normal; font-family: monospace;">波段流水 count: {len(paired_trades)}</span>
            </div>
            
            <!-- 成对明细表格 -->
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <table style="width: 100%; border-collapse: collapse; text-align: left; table-layout: fixed;">
                    <thead style="background-color: #f8fafc; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 12px; font-weight: 600; text-transform: uppercase;">
                        <tr>
                            <th style="padding: 12px; text-align: center; width: 60px;">波段</th>
                            <th style="padding: 12px 16px; width: 47%;">🟢 开仓入场明细 (BUY SIDE)</th>
                            <th style="padding: 12px 16px; width: 47%;">🔴 出场平仓明细 (EXIT SIDE)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows_html}
                    </tbody>
                </table>
            </div>
        </div>
        """

    # 4. 基础全内联纯静态网页整体骨架
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>多标的量化交易对明细报告</title>
</head>
<body style="background-color: #f8fafc; color: #334155; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 30px 15px;">
    
    <div style="max-w: 1100px; margin: 0 auto; width: 100%;">
        
        <!-- 精简主标题 -->
        <header style="border-bottom: 1px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 32px;">
            <h1 style="color: #0f172a; margin: 0; font-size: 22px; font-weight: 800;">📊 策略交易对开平仓轨迹明细 (多组别)</h1>
            <p style="color: #94a3b8; font-size: 12px; margin: 4px 0 0 0;">多标的横向对齐账单 · 100% 纯本地离线完美兼容</p>
        </header>

        <!-- 注入所有股票的分块数据 -->
        {all_stocks_sections_html}

        <!-- 精简页脚 -->
        <footer style="margin-top: 40px; text-align: center; font-size: 11px; color: #cbd5e1;">
            🔒 Multi-Asset Data Pipeline Output · End of Report
        </footer>
    </div>
</body>
</html>"""

    # 5. 文件安全写出
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(html_template)
        
    print(f"✅ [多组股票成对对齐版] 报表已无依赖成功生成: {os.path.abspath(output_filename)}")

        
if __name__ == '__main__':
    # 策略开始日期
    start_date = "2026-01-01"

    TARGET_DIR_SH = "C:\\zd_zsone\\vipdoc\\sh\\lday"
    TARGET_DIR_SZ = "C:\\zd_zsone\\vipdoc\\sz\\lday"
    TARGET_DIR = TARGET_DIR_SH
    # 过滤规则配置
    PREFIX_REGEX_SH = r"^(sh|sz)"          # 清洗：【抹去】开头的 temp_ 或 test_
    BLACK_LIST_SH = [
        "600200",
        "603388",
        ]    # 内存剔除名单，保留这个，后续可以删除一些不需要的
    KEEP_ONLY_REGEX_SH = r"^(68|60|00|30)"  # 只保留以 68 或 60 开头的文件名  588开头是基金 881开头是板块 399是指数
    
    # 执行过滤
    result_list = get_and_filter_filenames(
        folder_path=TARGET_DIR,
        ignore_prefix_pattern=PREFIX_REGEX_SH,    # 清洗：【抹去】开头的 temp_ 或 test_
        exclude_exact_names=BLACK_LIST_SH, # 减法：精确去掉黑名单
        keep_only_prefix_pattern=KEEP_ONLY_REGEX_SH       # 加法：【只保留】以 backtest_ 开头的文件
    )
    
    print("📋 内存中安全生成的最终文件名列表:")
    print(result_list[:5])  # 仅打印前10个文件名，避免输出过长
    print(f"总计: {len(result_list)} 个文件名符合条件。")

    stock_code_list = [
'600007',

'600059',
'600050',
]
    
    #stock_code_list = result_list
        
    tdx_http_api.TDX_Tools.info2file(quant_result_file=result_file_path, quant_result_info = "\n"*10)
    is_order_info = {} #[]
    for stock_code in stock_code_list:
        is_order, stock_name, last_trade_log = main(stock_code, start_date)
        if is_order:
            key_info = f'{stock_code}-{stock_name}'
            is_order_info[key_info] = last_trade_log
    generate_multi_stock_report(is_order_info)

