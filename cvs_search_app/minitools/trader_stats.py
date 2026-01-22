"""
游资月度净买入统计模块
用于生成按游资名称和月份统计的净买入金额直方图
"""
import pandas as pd
import re
from pyecharts.charts import Bar
from pyecharts import options as opts


def clean_numeric_string(value):
    """
    清洗包含汉字的数值字符串，转换为浮点数，保留负号
    
    参数:
    value (str): 可能包含汉字的数值字符串
    
    返回:
    float: 转换后的数值
    """
    match = re.search(r'-?\d+\.?\d*', str(value))
    if match:
        return float(match.group())
    return 0.0


def statistics_by_month_and_trader(csv_file_path, months_ago=24, separate_traders=False):
    """
    按游资名称和月份统计净买入金额，并生成柱状图
    
    参数:
    csv_file_path (str): CSV文件路径，需包含'上榜日期'、'游资名称'、'净买入（万）'列
    months_ago (int): 显示最近N个月的数据，默认24个月（两年）
    separate_traders (bool): 是否将游资分开显示（当前仅支持分开显示）
    
    返回:
    list: Bar对象列表（每行显示3个图）
    """
    try:
        # 读取CSV文件
        df = pd.read_csv(csv_file_path, dtype=str)
        
        # 清洗数据
        df['净买入（万）'] = df['净买入（万）'].apply(clean_numeric_string)
        
        # 将上榜日期转换为日期类型
        df['上榜日期'] = pd.to_datetime(df['上榜日期'])
        
        # 提取年月
        df['年月'] = df['上榜日期'].dt.to_period('M')
        
        # 按游资名称和年月分组，对净买入金额求和
        group_data = df.groupby(['游资名称', '年月'])['净买入（万）'].sum().reset_index()
        
        # 获取最近N个月的数据
        all_months = sorted(group_data['年月'].unique(), key=str)
        if len(all_months) > months_ago:
            recent_months = all_months[-months_ago:]
        else:
            recent_months = all_months
        
        # 过滤数据
        group_data = group_data[group_data['年月'].isin(recent_months)]
        
        # 按年月排序
        group_data = group_data.sort_values('年月')
        
        # 获取唯一的游资名称
        traders = sorted(group_data['游资名称'].unique())
        
        # 获取所有年月的唯一值
        months = sorted(group_data['年月'].unique(), key=str)
        months_str = [str(m) for m in months]
        
        if separate_traders:
            # 为每个游资创建单独的柱状图
            bars = []
            for trader in traders:
                trader_data = group_data[group_data['游资名称'] == trader]
                
                # 创建完整的月份数据，缺失的月份用0填充
                values = []
                for month in months:
                    month_value = trader_data[trader_data['年月'] == month]['净买入（万）'].sum()
                    values.append(month_value if month_value > 0 else 0)
                
                # 跳过所有月份都为0的游资
                if sum(values) == 0:
                    continue
                
                bar = Bar(init_opts=opts.InitOpts(width="40%", height="400px"))
                bar.add_xaxis(months_str)
                bar.add_yaxis(
                    trader,
                    [round(v, 2) for v in values]
                )
                
                # 配置图表选项
                bar.set_global_opts(
                    title_opts=opts.TitleOpts(
                        title=f"游资月度净买入统计 - {trader}",
                        subtitle=f"最近{months_ago}个月的数据"
                    ),
                    xaxis_opts=opts.AxisOpts(
                        name="年月",
                        type_="category",
                        axislabel_opts=opts.LabelOpts(rotate=45)
                    ),
                    yaxis_opts=opts.AxisOpts(
                        name="净买入（万元）",
                        type_="value"
                    ),
                    tooltip_opts=opts.TooltipOpts(
                        trigger="axis"
                    )
                )
                bars.append(bar)
            
            return bars
        
    except Exception as e:
        print(f"生成直方图失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def statistics_by_trader_monthly(csv_file_path, months_ago=12):
    """
    按月份统计，每月显示所有游资的净买入金额对比
    
    参数:
    csv_file_path (str): CSV文件路径，需包含'上榜日期'、'游资名称'、'净买入（万）'列
    months_ago (int): 显示最近N个月的数据，默认12个月（一年）
    
    返回:
    list: Bar对象列表，每个月一个图，显示该月所有游资的净买入对比
    """
    try:
        # 读取CSV文件
        df = pd.read_csv(csv_file_path, dtype=str)
        
        # 清洗数据
        df['净买入（万）'] = df['净买入（万）'].apply(clean_numeric_string)
        
        # 将上榜日期转换为日期类型
        df['上榜日期'] = pd.to_datetime(df['上榜日期'])
        
        # 提取年月
        df['年月'] = df['上榜日期'].dt.to_period('M')
        
        # 按游资名称和年月分组，对净买入金额求和
        group_data = df.groupby(['游资名称', '年月'])['净买入（万）'].sum().reset_index()
        
        # 获取最近N个月的数据
        all_months = sorted(group_data['年月'].unique(), key=str)
        if len(all_months) > months_ago:
            recent_months = all_months[-months_ago:]
        else:
            recent_months = all_months
        
        # 过滤数据
        group_data = group_data[group_data['年月'].isin(recent_months)]
        
        # 按年月排序
        group_data = group_data.sort_values('年月')
        
        # 获取所有唯一的月份
        months = sorted(group_data['年月'].unique(), key=str)
        
        # 为每个月创建柱状图
        bars = []
        for month in months:
            month_data = group_data[group_data['年月'] == month]
            
            # 按游资名称排序
            month_data = month_data.sort_values('游资名称')
            
            # 跳过数据为空的月份
            if len(month_data) == 0:
                continue
            
            # 获取该月的游资名称和净买入金额
            traders_list = month_data['游资名称'].tolist()
            values = [round(v, 2) for v in month_data['净买入（万）'].tolist()]
            
            # 创建柱状图
            bar = Bar(init_opts=opts.InitOpts(width="40%", height="400px"))
            bar.add_xaxis(traders_list)
            bar.add_yaxis(
                str(month),
                values
            )
            
            # 配置图表选项
            bar.set_global_opts(
                title_opts=opts.TitleOpts(
                    title=f"游资月度净买入对比 - {month}",
                    subtitle="该月份各游资的净买入金额统计"
                ),
                xaxis_opts=opts.AxisOpts(
                    name="游资名称",
                    type_="category",
                    axislabel_opts=opts.LabelOpts(rotate=45)
                ),
                yaxis_opts=opts.AxisOpts(
                    name="净买入（万元）",
                    type_="value"
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis"
                )
            )
            bars.append(bar)
        
        return bars
        
    except Exception as e:
        print(f"生成直方图失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
