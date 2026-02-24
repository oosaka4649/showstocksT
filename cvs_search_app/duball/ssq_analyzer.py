
import pandas as pd
import json
import re
import matplotlib.pyplot as plt
#import seaborn as sns
from collections import Counter
import numpy as np

def load_data():
    # 示例数据结构，实际使用时替换为真实API调用或CSV读取
    data = {
        'date': ['2026-02-12', '2026-02-10', '2026-02-08'],
        'red1': [7, 11, 1],
        'red2': [8, 15, 3],
        'red3': [16, 17, 5],
        'red4': [17, 22, 18],
        'red5': [18, 25, 29],
        'red6': [30, 30, 32],
        'blue': [1, 7, 4]
    }
    return pd.DataFrame(data)


def load_data_from_json():
        # 读取现有的JSON
    with open('E:\mygithub\showstocksT\cvs_search_app\duball\/all_lottery_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    date_list = []
    red1_list = []
    red2_list = []
    red3_list = []
    red4_list = []  
    red5_list = []
    red6_list = []
    blue_list = []
    for entry in data:
        date_list.append(entry['开奖日期'])
        red1_list.append(int(entry['开奖号码']['红球'][0]))
        red2_list.append(int(entry['开奖号码']['红球'][1]))
        red3_list.append(int(entry['开奖号码']['红球'][2]))
        red4_list.append(int(entry['开奖号码']['红球'][3]))
        red5_list.append(int(entry['开奖号码']['红球'][4]))
        red6_list.append(int(entry['开奖号码']['红球'][5]))
        blue_list.append(int(entry['开奖号码']['蓝球']))
    df = pd.DataFrame({
        'date': date_list,
        'red1': red1_list,
        'red2': red2_list,
        'red3': red3_list,
        'red4': red4_list,
        'red5': red5_list,
        'red6': red6_list,
        'blue': blue_list
    })
    return df

def analyze_odd_even(df):
    """奇偶分析"""
    odd_count = []
    even_count = []
    
    for i in range(len(df)):
        reds = df.iloc[i][['red1','red2','red3','red4','red5','red6']].values
        odds = sum(1 for x in reds if x % 2 == 1)
        evens = 6 - odds
        odd_count.append(odds)
        even_count.append(evens)
        
    counter = Counter(zip(odd_count, even_count))
    print("奇偶分布统计:")
    for k,v in sorted(counter.items()):
        print(f"奇数{k[0]}个,偶数{k[1]}个: {v}次")
    return counter

def analyze_zones(df):
    """区间分析 (01-11, 12-22, 23-33)"""
    zone_counts = []
    
    for i in range(len(df)):
        reds = df.iloc[i][['red1','red2','red3','red4','red5','red6']].values
        z1 = sum(1 for x in reds if 1 <= x <= 11)
        z2 = sum(1 for x in reds if 12 <= x <= 22)
        z3 = sum(1 for x in reds if 23 <= x <= 33)
        zone_counts.append((z1,z2,z3))
        
    counter = Counter(zone_counts)
    print("\n区间分布统计:")
    for k,v in sorted(counter.items()):
        print(f"{k[0]}:{k[1]}:{k[2]} = {v}次")
    return counter

def analyze_sum_range(df):
    """和值范围分析"""
    sums = []
    
    for i in range(len(df)):
        reds = df.iloc[i][['red1','red2','red3','red4','red5','red6']].sum()
        sums.append(reds)
        
    ranges = [(x,x+10) for x in range(20,200,10)]
    range_counter = {}
    
    for r in ranges:
        count = sum(1 for s in sums if r[0] <= s < r[1])
        range_counter[r] = count
        
    print("\n和值范围统计:")
    for k,v in sorted(range_counter.items()):
        print(f"[{k[0]}, {k[1]}) : {v}次")
    return range_counter,sums

def visualize_analysis(counters_dict):
    """可视化分析结果"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('双色球历史数据分析')
    
    # 奇偶分布饼图
    oe_labels = [f'{k[0]}奇{k[1]}偶' for k in counters_dict['odd_even'].keys()]
    oe_sizes = list(counters_dict['odd_even'].values())
    axes[0,0].pie(oe_sizes, labels=oe_labels, autopct='%1.1f%%')
    axes[0,0].set_title('奇偶分布')
    
    # 区间分布柱状图
    zones = list(counters_dict['zones'].keys())
    counts = list(counters_dict['zones'].values())
    zone_strs = [f'{z[0]}:{z[1]}:{z[2]}' for z in zones]
    axes[0,1].bar(range(len(zones)), counts)
    axes[0,1].set_xticks(range(len(zones)))
    axes[0,1].set_xticklabels(zone_strs, rotation=45)
    axes[0,1].set_title('区间分布')
    
    # 和值直方图
    axes[1,0].hist(counters_dict['sums'], bins=20, edgecolor='black')
    axes[1,0].set_xlabel('和值')
    axes[1,0].set_ylabel('频次')
    axes[1,0].set_title('和值分布')
    
    # 蓝球分布
    blue_counter = Counter(counters_dict['blues'])
    blues = list(blue_counter.keys())
    bcounts = list(blue_counter.values())
    axes[1,1].bar(blues, bcounts)
    axes[1,1].set_xlabel('蓝球号码')
    axes[1,1].set_ylabel('出现次数')
    axes[1,1].set_title('蓝球分布')
    
    plt.tight_layout()
    plt.show()

def main():
    #df = load_data()
    df = load_data_from_json()
    print("开始分析双色球历史数据...")
    
    # 各种统计分析
    odd_even_result = analyze_odd_even(df)
    zone_result = analyze_zones(df)
    sum_ranges, all_sums = analyze_sum_range(df)
    
    # 收集蓝球数据用于图表展示
    blues = df['blue'].tolist()
    
    # 准备绘图数据
    counters_for_plot = {
        'odd_even': odd_even_result,
        'zones': zone_result,
        'sums': all_sums,
        'blues': blues
    }
    
    # 数据可视化
    visualize_analysis(counters_for_plot)
    
if __name__ == "__main__":
    main()
