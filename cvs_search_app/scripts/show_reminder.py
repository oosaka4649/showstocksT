import time
import tkinter as tk
from tkinter import font
from tkinter import messagebox
import calendar
from datetime import datetime, timedelta
import re

def show_reminder(getout_day):
    root = tk.Tk()
    root.geometry("800x600")  # 设置窗口大小为400x300像素
    root.withdraw()  # 隐藏主窗口
    root.attributes("-topmost", True)  # 设置窗口总在最前
    messagebox.showinfo("提醒", getout_day + "\n 快起来运动 时间到了！\n 市场中钱是赚不完的，但钱是可以亏完的！")
    root.destroy()

def set_timer(hour, minute):
    while True:
        current_time = time.localtime()
        if current_time.tm_hour == hour and current_time.tm_min == minute:
            show_reminder()
            break
        time.sleep(30)  # 每30秒检查一次时间
        
def set_hourly_reminder():
    getout_day = get_out_day()  # 先调用一次显示结果
    while True:
        show_reminder(getout_day)
        time.sleep(1800)  # 每3600秒（1小时）弹出一次
        
############################################################################################################################

def calculate_monthly_weekday(input_str, year=None, month=None):
    """
    计算每月第几周的星期几是几号
    输入格式固定为【每个月第几周的星期几】，其中"几"可以是中文数字或阿拉伯数字
    
    Args:
        input_str: 输入字符串，格式为"每个月第几周的星期几"
        year: 年份，如果为None则使用当前年份
        month: 月份，如果为None则使用当前月份
    
    Returns:
        dict: 包含详细信息的字典
    """
    # 周数映射（中文到数字）
    week_mapping = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, 
        '1': 1, '2': 2, '3': 3, '4': 4, '5': 5
    }
    
    # 星期映射
    weekday_mapping = {
        '一': 0, '二': 1, '三': 2, '四': 3, '五': 4, '六': 5, '日': 6, '天': 6
    }
    
    # 简化的正则表达式，只匹配固定格式
    pattern = r'每个月第([一二三四五12345])周的星期([一二三四五六日天])'
    match = re.search(pattern, input_str)
    
    if not match:
        raise ValueError("输入格式不正确，请使用【每个月第几周的星期几】的格式，例如：每个月第三周的星期五")
    
    week_num_str = match.group(1)
    weekday_str = match.group(2)
    
    # 转换周数和星期
    week_num = week_mapping.get(week_num_str)
    weekday = weekday_mapping.get(weekday_str)
    
    if week_num is None:
        raise ValueError(f"无法识别的周数: {week_num_str}")
    if weekday is None:
        raise ValueError(f"无法识别的星期: {weekday_str}")
    
    # 获取当前年月（如果未指定）
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    
    # 计算当月第一天是星期几（0=周一, 6=周日）
    first_day_weekday, month_days = calendar.monthrange(year, month)
    
    # 计算第一个指定的星期几是几号
    # 注意：Python的calendar中周一=0，周日=6
    first_target_weekday = (weekday - first_day_weekday) % 7
    if first_target_weekday < 0:
        first_target_weekday += 7
    
    # 第n个星期几的日期 = 1 + (第一个目标星期几的偏移) + 7*(n-1)
    target_date = 1 + first_target_weekday + 7 * (week_num - 1)
    
    # 检查日期是否有效
    if target_date > month_days:
        return {
            'success': False,
            'message': f'{year}年{month}月没有第{week_num}个星期{weekday_str}',
            'year': year,
            'month': month,
            'target_week': week_num,
            'target_weekday': weekday_str,
            'input_pattern': input_str
        }
    
    # 创建日期对象
    result_date = datetime(year, month, target_date)
    
    # 星期几的中文全称
    weekday_full = {
        0: '星期一', 1: '星期二', 2: '星期三', 
        3: '星期四', 4: '星期五', 5: '星期六', 6: '星期日'
    }[weekday]
    
    return {
        'success': True,
        'date': result_date,
        'date_str': result_date.strftime('%Y-%m-%d'),
        'chinese_date': f'{year}年{month}月{target_date}日',
        'weekday': weekday_full,
        'week_number': week_num,
        'year': year,
        'month': month,
        'day': target_date,
        'input_pattern': input_str
    }
    
def get_out_day():
    """计算每个月的期权到期日（每个月的第三个星期五）"""
    #print("=== 日期计算函数测试 ===\n")
    
    # 测试用例
    test_cases = [
        "每个月第三周的星期五",  # 股指期货交割日
        "每个月第四周的星期三",  # 股指期权最后交易日
    ]
    result_info = "-" * 50
    result_info += "\n A50指数期货交割日 每个月倒数第二个工作日， 遇节假日顺延\n 股指期权交易日\n"
    for test_case in test_cases:
        #print(f"输入: {test_case}")
        
        # 计算当前月份
        try:
            current_result = calculate_monthly_weekday(test_case)
            if current_result['success']:
                #print(f"结果: {current_result['chinese_date']} ({current_result['date_str']})")
                result_info += f"\n {test_case}: ({current_result['date_str']})\n"
            else:
                print(f"结果: {current_result['message']}")
        except Exception as e:
            print(f"错误: {e}")
        
    result_info += "-" * 50
    return result_info        
############################################################################################################################

# 开始每小时提醒
set_hourly_reminder()
'''
要让这个程序在开机时自动启动，你可以将其添加到系统的启动项中。以下是如何在Windows系统上实现这一点的步骤：

创建一个批处理文件：
打开记事本，输入以下内容：
@echo off
python "C:\path\to\your\script.py"

将文件保存为start_reminder.bat，确保将C:\path\to\your\script.py替换为你的Python脚本的实际路径。
将批处理文件添加到启动文件夹：
按下Win + R键，输入shell:startup，然后按回车。这将打开启动文件夹。
将start_reminder.bat文件复制到这个文件夹中。
这样，每次开机时，Windows都会自动运行这个批处理文件，从而启动你的Python提醒程序。
# 设置提醒时间，例如每天的14:30
set_timer(11, 37)
'''