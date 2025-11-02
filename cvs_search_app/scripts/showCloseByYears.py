import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import matplotlib as mpl

# 设置中文字体支持
def set_chinese_font():
    """
    设置matplotlib支持中文显示
    """
    try:
        # 尝试使用系统中已有的中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号
        print("中文字体设置成功")
    except:
        print("警告: 中文字体设置失败，图表中的中文可能显示为方块")
        # 如果上述字体不存在，尝试使用系统默认字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

# 在程序开始时调用字体设置
set_chinese_font()

def calculate_annual_growth_by_years(csv_file, start_date, price_column='Close'):
    """
    读取股票数据并按自然年计算价格涨幅
    
    参数:
    csv_file: 股票数据文件路径
    start_date: 起始日期 (YYYY-MM-DD格式)
    price_column: 价格列名，默认为'Close'
    """
    
    # 读取数据
    try:
        df = pd.read_csv(csv_file, parse_dates=['Date'], dayfirst=False)
        df.sort_values('Date', inplace=True)
        df.set_index('Date', inplace=True)
    except Exception as e:
        print(f"读取文件错误: {e}")
        return None
    
    # 检查价格列是否存在
    if price_column not in df.columns:
        print(f"错误: 数据中不存在'{price_column}'列")
        print(f"可用列: {list(df.columns)}")
        return None
    
    # 转换为指定的起始日期
    start_date = pd.to_datetime(start_date)
    df = df[df.index >= start_date]
    
    if len(df) == 0:
        print(f"错误: 起始日期 {start_date.date()} 之后没有数据")
        return None
    # 创建分组
    periods = []
    current_start = start_date
    
    # 按365天为周期创建分组
    while current_start <= df.index.max():
        period_end = current_start + timedelta(days=365)
        
        # 获取当前周期的数据
        period_data = df[(df.index >= current_start) & (df.index < period_end)]
        
        if len(period_data) > 0:
            # 获取当前周期的起始价格
            period_start_price = period_data.iloc[0][price_column]
            
            # 计算相对于当前周期起始价格的涨幅百分比
            period_data = period_data.copy()
            period_data['Growth_Rate'] = (period_data[price_column] / period_start_price - 1) * 100
            
            # 添加周期信息
            period_data['Period_Start'] = current_start
            period_data['Period_End'] = period_end
            
            periods.append(period_data)
        
        # 移动到下一个周期
        current_start = period_end
    
    return periods, df

def plot_annual_growth_curves(periods, start_date):
    """
    绘制年度涨幅曲线图
    """
    plt.figure(figsize=(14, 8))
    
    # 为每个周期设置不同的颜色
    colors = plt.cm.Set1(np.linspace(0, 1, len(periods)))
    
    for i, period_data in enumerate(periods):
        if len(period_data) > 0:
            # 获取周期信息
            period_start = period_data['Period_Start'].iloc[0]
            period_end = period_data['Period_End'].iloc[0]
            period_start_price = period_data.iloc[0]['Close']
            
            # 创建相对日期（周期内的天数）
            days_from_start = (period_data.index - period_start).days
            
            # 绘制曲线
            plt.plot(days_from_start, period_data['Growth_Rate'], 
                    label=f'{period_start.date()} 至 {period_end.date()}', 
                    color=colors[i], linewidth=2)
    
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    plt.title(f'股票价格年度涨幅分析\n按365天周期分组，以每个周期起始价格为基准', 
              fontsize=14, fontweight='bold')
    plt.xlabel('周期内天数', fontsize=12)
    plt.ylabel('相对于周期起始价格的涨幅 (%)', fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.show()

def display_period_statistics(periods):
    """
    显示周期统计信息
    """
    print("=" * 80)
    print(f"{'周期涨幅统计汇总'}")
    print("=" * 80)
    
    for i, period_data in enumerate(periods):
        if len(period_data) > 0:
            period_start = period_data['Period_Start'].iloc[0]
            period_end = period_data['Period_End'].iloc[0]
            period_start_price = period_data.iloc[0]['Close']
            period_end_price = period_data.iloc[-1]['Close']
            period_growth = period_data['Growth_Rate'].iloc[-1]
            period_max_growth = period_data['Growth_Rate'].max()
            period_min_growth = period_data['Growth_Rate'].min()
            trading_days = len(period_data)
            
            print(f"周期 {i+1}: {period_start.date()} 至 {period_end.date()}")
            print(f"  起始价格: {period_start_price:.2f} | 结束价格: {period_end_price:.2f}")
            print(f"  期末涨幅: {period_growth:7.2f}% | 最高涨幅: {period_max_growth:7.2f}% | "
                  f"最低涨幅: {period_min_growth:7.2f}% | 交易天数: {trading_days:3d}")
            print("-" * 80)

def analyze_stock_growth_by_years(csv_file, start_date):
    """
    主分析函数 - 按自然年分析
    """
    # 计算涨幅
    result = calculate_annual_growth_by_years(csv_file, start_date)
    if result is None:
        return
    
    years, df = result
    
    if len(years) == 0:
        print("错误: 没有找到有效的年份数据")
        return
    
    # 显示统计信息
    #display_period_statistics(start_date)
    
    # 绘制曲线
    plot_annual_growth_curves(years, start_date)
    
    # 合并所有年份数据并返回
    combined_df = pd.concat(years)
    return combined_df

# 使用示例
if __name__ == "__main__":
    # 示例用法
    csv_file = "D:\python\showstocksT\cvs_search_app\stockscsv\sz002941.csv"  # 替换为您的CSV文件路径
    start_date = "2018-01-01"    # 替换为您想要的起始日期
    
    # 执行分析
    result_df = analyze_stock_growth_by_years(csv_file, start_date)
    '''
    # 如果需要保存处理后的数据
    if result_df is not None:
        result_df.to_csv("processed_stock_growth_by_years.csv")
        print("\n处理后的数据已保存为 'processed_stock_growth_by_years.csv'")
        
        '''