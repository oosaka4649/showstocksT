import json
import re
from datetime import datetime
import csv

'''
这程序是，将页面copy下来的数据，提取出其中的JSON数据部分，解析后打印出来。

https://data.eastmoney.com/rzrq/total.html


交易日期	收盘-沪深300	涨跌幅(%)-沪深300	   融资	                                                                融券	                                                    融资融券余额(元)	融资融券余额差值(元)
                                                余额(元)	余额占流通市值比	买入额(元)	偿还额(元)	净买入(元)	    余额(元)	余量(股)	卖出量(股)	偿还量(股)	净卖出(股)
2026-03-19	4583.25	        -1.61	            26323亿	    2.60%	            1919亿	    1962亿	    -42.86亿	178.8亿	     30.59亿	1.13亿	    8623万	    2673万	        26501亿	            26144亿


数据格式如下：

{'DIM_DATE': '2026-03-19 00:00:00',    交易日期
                         'NEW': 4583.2511,  收盘-沪深300
                         'ZDF': -1.611763,  涨跌幅(%)-沪深300
                         'LTSZ': 101164456680522.31,  流通市值(元)
                         'ZDF3D': -1.890333,  3日涨跌幅(%)
                         'ZDF5D': -2.22523,   5日涨跌幅(%)
                         'ZDF10D': -1.386516, 10日涨跌幅(%)
                         
                         'RZYE': 2632250785435,  融资余额(元)
                         'RZYEZB': 2.601952,  融资余额占流通市值比
                         'RZMRE': 191869202239,  融资买入额(元)
                         'RZMRE3D': 583796435466,  融资买入额(元) 3日
                         'RZMRE5D': 1025630480804,  融资买入额(元) 5日
                         'RZMRE10D': 2176418846598,  融资买入额(元) 10日
                         
                         'RZCHE': 196155174502,  融资偿还额(元)
                         'RZCHE3D': 594546487337,   融资偿还额(元) 3日
                         'RZCHE5D': 1039325860215,  融资偿还额(元) 5日
                         'RZCHE10D': 2177997484342,  融资偿还额(元) 10日
                         
                         'RZJME': -4285972264,  融资净买入(元)
                         'RZJME3D': -10750051904,  融资净买入(元) 3日
                         'RZJME5D': -13695379479,  融资净买入(元) 5日
                         'RZJME10D': -1578637836,  融资净买入(元) 10日
                         
                         'RQYE': 17877039501,  融券余额(元)
                         'RQYL': 3058749357,  融券余量(股)

                         'RQCHL': 86230304,  融券偿还量(股)
                         'RQCHL3D': 325011183,  融券偿还量(股) 3日
                         'RQCHL5D': 512806908,  融券偿还量(股) 5日
                         'RQCHL10D': 1039534305,  融券偿还量(股) 10日
                         
                         'RQMCL': 112956334,  融券卖出量(股)
                         'RQMCL3D': 287935002,  融券卖出量(股) 3日
                         'RQMCL5D': 438266521,  融券卖出量(股) 5日
                         'RQMCL10D': 1049903497,  融券卖出量(股) 10日
                         
                         'RQJMG': 26726030,  融券净卖出(股)
                         'RQJMG3D': -37076181,  融券净卖出(股) 3日
                         'RQJMG5D': -74540387,  融券净卖出(股) 5日
                         'RQJMG10D': 10369192,  融券净卖出(股) 10日
                         
                         'RZRQYE': 2650127824936,  融资融券余额(元)
                         'RZRQYECZ': 2614373745934}  融资融券余额差值(元)


目前只提取了几个字段，后续可以根据需要提取更多字段。
交易日期  融资余额(元) 融券余额(元)  融资融券余额(元)
'''

file_path = 'e:\\mygithub\\showstocksT\\scripts\\rzrq_data_all_2026_03_22\\rzrq_data.csv'
data_lines = []  # 内存中的数据行列表

for file_num in range(1, 70):  # 假设有多个文件，循环处理 由于早期融资金额较小不足亿元，就忽略了前几个文件
    # 读取文件
    with open(f'e:\\mygithub\\showstocksT\\scripts\\rzrq_data_all_2026_03_22\\get{file_num}', 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取JSON部分（去掉 datatable2860332( 和最后的 }); ）
    json_start = content.find('(') + 1
    json_end = content.rfind(')')
    json_str = content[json_start:json_end]

    # 解析JSON
    data = json.loads(json_str)

    # 提取data部分
    data_list = data['result']['data']

    # 打印前几个数据项作为示例
    for item in data_list:
        #print(item['DIM_DATE'], item['RZYE'], item['RQYE'], item['RZRQYE'])
        data_lines.append(f"{str(item['DIM_DATE'])[:10]},{round(float(item['RZYE']) / 100000000, 2)},{round(float(item['RQYE']) / 100000000, 2)},{round(float(item['RZRQYE']) / 100000000, 2)}")


"""
将内存数据列表写回CSV文件，按第一列日期排序

参数:
    file_path (str): CSV文件路径
    data_lines (list): 内存中的数据行列表
"""

# 将字符串行分割为列表，并尝试解析日期
parsed_data = []
for line in data_lines:
    # 将每行字符串分割为字段列表
    fields = line.split(',')
    
    # 尝试将第一个字段解析为日期
    date_str = fields[0] if fields else ""
    try:
        # 尝试多种日期格式
        date_obj = None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y.%m.%d', '%Y/%m/%d'):
            try:
                date_obj = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        # 如果无法解析，则使用原始字符串
        if date_obj is None:
            date_key = date_str
        else:
            date_key = date_obj
            
        parsed_data.append((date_key, fields))
    except:
        # 如果解析出错，使用原始字符串作为键
        parsed_data.append((date_str, fields))

# 按日期排序
try:
    # 尝试按日期对象排序
    parsed_data.sort(key=lambda x: x[0], reverse=True)
except:
    # 如果日期对象排序失败，尝试按字符串排序
    parsed_data.sort(key=lambda x: str(x[0]), reverse=True)

# 提取排序后的字段列表
sorted_data = [fields for _, fields in parsed_data]

# 写入CSV文件
with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
    csv_writer = csv.writer(csvfile)
    # 写入标题行
    #csv_writer.writerow(header.split(','))
    # 写入排序后的数据行
    csv_writer.writerows(sorted_data)

print(f"数据已按日期排序并保存到 {file_path}")