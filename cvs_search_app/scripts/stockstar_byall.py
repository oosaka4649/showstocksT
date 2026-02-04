import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
import re
import csv
import os
import time
from datetime import datetime

'''
当机器上安装的Chrome浏览器自动升级时，使用Selenium会报错，原因是ChromeDriver版本与Chrome浏览器版本不匹配。
解决方法是下载与当前Chrome浏览器版本匹配的ChromeDriver，并替换掉原有的ChromeDriver。exe文件。

https://googlechromelabs.github.io/chrome-for-testing/#stable

ChromeバージョンアップによるSeleniumエラーのトラブルシューティング
https://zenn.dev/ykesamaru/articles/a1a4fd5eae8563


'''

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# 发送HTTP请求获取网页内容  获取证券之星 网站上的龙虎榜数据 并分析其进场出场及买卖行为
# https://quote.stockstar.com/BillBoard/sz_2026-01-22.html 
# 
# 页面特点  数据特点
#    1  页面分 沪市，深市 ，北交所 三个部分
#    2  每个部分有一个页面 按日期显示数据
#    3  每个部分的数据格式相同
#    4  https://quote.stockstar.com/BillBoard/sz_2026-01-22.html
#                                                2026-01-22  日期部分
#                               sh_ 沪市 sz_ 深市部分 bjs_ 北交所部分
'''
<div class="lhb_listtop">
							<div class="lhb_le">2</div>
							<div class="lhb_cen">有价格涨跌幅限制的日收盘价格涨幅达到20%的证券</div>
							<div class="lhb_les">
								<div class="lub_look">
									<img src="//i.ssimg.cn/images/DataCenter/resource/lub_zk.png">
									<p>检查明细</p>
								</div>
							</div>
						</div>

<div class="lub_none" style="display: block;">
							<div class="lub_lere">
								<div class="wite_le"></div>
								<div class="lub_listbot">
										<table width="100%" class="table1">
											<tbody><tr class="lhb_first">
												<td width="7.5%">名称</td>
												<td width="7.5%">股票代码</td>
												<td width="28.33%">成交金额（万元）</td>
												<td width="28.33%">净买入（万元）</td>
												<td width="28.33%">成交数量（万股）</td>

											</tr>
											<tr>
												<td width="7.5%"><a href="//stock.quote.stockstar.com/920368.shtml">连城数控</a></td>
												<td width="7.5%"><a href="//stock.quote.stockstar.com/920368.shtml">920368</a></td>
												<td width="28.33%">126115.49</td>
												<td width="28.33%">5772.91</td>
												<td width="28.33%">2825.45</td>
											</tr>
										</tbody></table>
										<table width="100%" class="table2">
											<tbody><tr>
												<td colspan="4">买入金额最大的前五名</td>
											</tr>
											<tr class="table2_wite">
												<td width="7.5%">
													序号
												</td>
												<td width="40.8%">
													营业厅名称
												</td>
												<td width="25.8%">
													买入金额（万元）
												</td>
												<td width="25.8%">
													交易时间
												</td>
											</tr>
												<tr>
													<td>
														1
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_f1ce2b4371101b8a_1_1_1.html">华鑫证券有限责任公司上海宛平南路营业部</a>
													</td>
													<td class="table_red">
														4515.96
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														2
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_jgmmtj_1_1_1.html">机构专用</a>
													</td>
													<td class="table_red">
														4507.09
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														3
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_df87a914bee9d83_1_1_1.html">中信建投证券股份有限公司福州东街证券营业部</a>
													</td>
													<td class="table_red">
														2904.89
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														4
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_aa7de8d1948067fc_1_1_1.html">中信建投证券股份有限公司福清福和路证券营业部</a>
													</td>
													<td class="table_red">
														2673.12
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														5
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_42444502b6fa87c8_1_1_1.html">华创证券有限责任公司北京西直门证券营业部</a>
													</td>
													<td class="table_red">
														2451.58
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
										</tbody></table>
										<table width="100%" class="table2">
											<tbody><tr>
												<td colspan="4">卖出金额最大的前五名</td>
											</tr>
											<tr class="table2_wite">
												<td width="7.5%">
													序号
												</td>
												<td width="40.8%">
													营业厅名称
												</td>
												<td width="25.8%">
													卖出金额（万元）
												</td>
												<td width="25.8%">
													交易时间
												</td>
											</tr>
												<tr>
													<td>
														1
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_eafe8971cbd89e0f_1_1_1.html">申万宏源西部证券有限公司霍尔果斯亚欧路证券营业部</a>
													</td>
													<td class="table_green">
														4929.08
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														2
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_7fa065e8c6cff046_1_1_1.html">国信证券股份有限公司深圳互联网分公司</a>
													</td>
													<td class="table_green">
														3451.67
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														3
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_b916d33a2393f5ee_1_1_1.html">国泰海通证券股份有限公司陕西西安唐延路营业部</a>
													</td>
													<td class="table_green">
														1819.37
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														4
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_fa9a6bd74b4d5fc3_1_1_1.html">中信建投证券股份有限公司厦门杏东路证券营业部</a>
													</td>
													<td class="table_green">
														1556.51
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														5
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_jgmmtj_1_1_1.html">机构专用</a>
													</td>
													<td class="table_green">
														1301.84
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
										</tbody></table>
										<table width="100%" class="table1">
											<tbody><tr class="lhb_first">
												<td width="7.5%">名称</td>
												<td width="7.5%">股票代码</td>
												<td width="28.33%">成交金额（万元）</td>
												<td width="28.33%">净买入（万元）</td>
												<td width="28.33%">成交数量（万股）</td>

											</tr>
											<tr>
												<td width="7.5%"><a href="//stock.quote.stockstar.com/920414.shtml">欧普泰</a></td>
												<td width="7.5%"><a href="//stock.quote.stockstar.com/920414.shtml">920414</a></td>
												<td width="28.33%">17420.09</td>
												<td width="28.33%">585.36</td>
												<td width="28.33%">1043.54</td>
											</tr>
										</tbody></table>
										<table width="100%" class="table2">
											<tbody><tr>
												<td colspan="4">买入金额最大的前五名</td>
											</tr>
											<tr class="table2_wite">
												<td width="7.5%">
													序号
												</td>
												<td width="40.8%">
													营业厅名称
												</td>
												<td width="25.8%">
													买入金额（万元）
												</td>
												<td width="25.8%">
													交易时间
												</td>
											</tr>
												<tr>
													<td>
														1
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_2e0d92a4707a448b_1_1_1.html">东莞证券股份有限公司常熟东南大道证券营业部</a>
													</td>
													<td class="table_red">
														1032.6
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														2
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_a495d0de78431a34_1_1_1.html">国泰海通证券股份有限公司上海江苏路营业部</a>
													</td>
													<td class="table_red">
														860.5
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														3
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_9d6ab634ccd04a9_1_1_1.html">财通证券股份有限公司杭州环城北路证券营业部</a>
													</td>
													<td class="table_red">
														568.87
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														4
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_4a9522459508850a_1_1_1.html">国金证券股份有限公司乌鲁木齐南湖路证券营业部</a>
													</td>
													<td class="table_red">
														524.09
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														5
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_e5790d6461bec2a3_1_1_1.html">中国银河证券股份有限公司北京陶然桥证券营业部</a>
													</td>
													<td class="table_red">
														430.25
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
										</tbody></table>
										<table width="100%" class="table2">
											<tbody><tr>
												<td colspan="4">卖出金额最大的前五名</td>
											</tr>
											<tr class="table2_wite">
												<td width="7.5%">
													序号
												</td>
												<td width="40.8%">
													营业厅名称
												</td>
												<td width="25.8%">
													卖出金额（万元）
												</td>
												<td width="25.8%">
													交易时间
												</td>
											</tr>
												<tr>
													<td>
														1
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_f335e9a7df3ded79_1_1_1.html">招商证券股份有限公司北京车公庄西路证券营业部</a>
													</td>
													<td class="table_green">
														1486.22
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														2
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_a9d5bdc58908de45_1_1_1.html">中国银河证券股份有限公司北京珠市口大街证券营业部</a>
													</td>
													<td class="table_green">
														592.75
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														3
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_f710b4e218295cf_1_1_1.html">华泰证券股份有限公司漳州水仙大街证券营业部</a>
													</td>
													<td class="table_green">
														356
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														4
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_7fa065e8c6cff046_1_1_1.html">国信证券股份有限公司深圳互联网分公司</a>
													</td>
													<td class="table_green">
														301.25
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
												<tr>
													<td>
														5
													</td>
													<td>
														<a href="//quote.stockstar.com/BillBoard/department_f1ddac7322921205_1_1_1.html">东北证券股份有限公司四川第二分公司</a>
													</td>
													<td class="table_green">
														261.87
													</td>
													<td>
														2026-01-23
													</td>
												</tr>
										</tbody></table>

								</div>
							</div>
						</div>
'''
url = 'https://quote.stockstar.com/BillBoard/' # https://quote.stockstar.com/BillBoard/bjs_2026-01-23.html
url_2 = '.html'

t_name = {'sh_':'上海','sz_':'深圳','bjs_':'北交所'}

current_dir = os.path.dirname(os.path.abspath(__file__))
chrome_driver_path = os.path.join(current_dir, 'chromedriver.exe')
# 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)
stockstar_csv_path = os.path.join(parent_dir, 'data', 'stockstar.csv')
  
# 设置ChromeDriver路径
service = Service(chrome_driver_path)


# 初始化WebDriver
driver = webdriver.Chrome(service=service)

tailal_txt = '上榜日期,证券号码,证券简称,上榜涨幅,买入额（万）,卖出额（万）,净买入（万）,所属营业部,游资名称'

data_lines = []

"""
    读取CSV文件到内存列表，检查字符串是否存在，不存在则添加。
    
    参数:
        search_string (str): 要查找/添加的字符串
    
    返回:
        list: 更新后的内存数据列表
"""  
def replace_comma_in_string(text, replacement_char='|'):
    """
    将字符串中的逗号替换为指定字符
    
    参数:
        text (str): 输入字符串
        replacement_char (str): 替换的目标字符，默认为 '|'
    
    返回:
        str: 替换后的字符串
    
    示例:
        >>> replace_comma_in_string('日换手率达20%的证券,龙虎榜', '|')
        '日换手率达20%的证券|龙虎榜'
        
        >>> replace_comma_in_string('有价格涨跌幅限制,日收盘价格涨幅达到20%', '-')
        '有价格涨跌幅限制-日收盘价格涨幅达到20%'
    """
    return str(text).replace(',', replacement_char)

def search_string_in_csv_memory(search_string):
    has_is_exist = False
    # 检查字符串是否存在
    found = any(search_string == line for line in data_lines)
    
    # 若不存在则添加到内存列表
    if not found:
        data_lines.append(search_string)
        print(f"字符串 '{search_string}' 已添加到内存")
    else:
        print(f"字符串 '{search_string}' 已存在，未添加")
        has_is_exist = True
    
    return has_is_exist

def add_string_to_csv_memory(csv_file_path):
    """
    读取CSV文件到内存列表，检查字符串是否存在，不存在则添加。
    
    参数:
        csv_file_path (str): CSV文件路径
   
    返回:
        list: 更新后的内存数据列表
    """  
    # 读取CSV文件内容到内存
    try:
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                # 将每行转换为字符串（保留原始格式）
                line_str = ','.join(row)
                data_lines.append(line_str)
    except FileNotFoundError:
        print(f"文件 {csv_file_path} 不存在，将创建新列表")

'''
  sc_name 证券市场名称  sh sz bjs
  date_str 日期字符串  2026-01-23
'''
def read_web_page(sc_name, date_str):
    return_line_num = 0
    print('第',sc_name,'页')
    # 打开网页
    driver.get(url + str(sc_name) + str(date_str) + url_2 )
    
    # 等待JavaScript加载完成
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'lhb_onelist')))  #等待指定元素加载完成

    # 获取页面内容
    page_content = driver.page_source

    # 使用BeautifulSoup解析网页内容
    soup = BeautifulSoup(page_content, 'html.parser')

    # 提取指定内容，例如所有的标题
    #titles = soup.find_all('h1')
    titles = soup.findChild('ul')
    uls = soup.find('ul', {'class': 'lhb_onelist'})
    tm_txt = ''

    #print(uls)  #debug
    """
    解析例子子说明：
     假设我们有以下HTML内容，我们想要提取表格中的数据：
        # 1. 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # 2. 按class名或结构查找表格
        table = soup.find('table', {'class': 'table1'})

        # 3. 提取所有行和单元格
        rows = table.find_all('tr')
        cells = row.find_all('td')

        # 4. 获取文本内容（去除标签）
        text = cells[0].get_text(strip=True)
    """
    # 3. 提取所有行和单元格  
    # li 一组就是一个li ， 每个 li 就是 一个 龙虎榜 日换手率达20%的证券 理由等
    #  一个 li 里面 有两个 div， 第一个div是  理由 
    # 第二个 div 里面 有多个 table  每个股票有三个 table， 
    #        第一个 table 是 股票总结信息  一行tr 多个td   {'class': 'table1'}
    #        第二个 table 是 买入金额最大的前五名  多行tr 多个td  买入金额最大的前五名  {'class': 'table2'}
    #        第三个 table 是 卖出金额最大的前五名  多行tr 多个td  卖出金额最大的前五名  {'class': 'table2'}
    #  tables = soup.find_all('table', {'class': 'table1'})
    li_rows = uls.find_all('li')
    li_num = 0
    title_only_flg = True
    for li_stocks in li_rows:
        if li_num == 0:
            li_num += 1
            continue  #跳过第一个li ，因为它不是数据部分 title部分
        divs_reason = li_stocks.find_all('div', {'class': 'lhb_cen'})  # 第一个div是  理由
        if len(divs_reason) > 1:
            continue
        reason_info = divs_reason[0].get_text(strip=True)  # 理由部分
        reason_info = replace_comma_in_string(reason_info, '!')  # 将逗号替换为 ! 避免CSV格式错误
        #print (reason_info)  #debug
        # 第二个 div 里面 有多个 table  每个股票有三个 table，
        tables = li_stocks.find_all('table', {'class': 'table1'}) # 第一个 table 是 股票总结信息  一个  {'class': 'table1'} 就代码一个股票
        if len(tables) < 1:   # 股票个数
            continue
        title_only_flg = False
        for stock_info in tables:
            stock_rows = stock_info.find_all('tr')[1:]  # 跳过标题和表头行
            #<tr class="lhb_first">
            #<td width="7.5%">名称</td>
            #<td width="7.5%">股票代码</td>
            #<td width="28.33%">成交金额（万元）</td>
            #<td width="28.33%">净买入（万元）</td>
            #<td width="28.33%">成交数量（万股）</td>
            #</tr>
            summary_cells = stock_rows[0].find_all('td')
            if len(summary_cells) < 5:
                continue
            stock_code = summary_cells[1].get_text(strip=True)
            stock_name = summary_cells[0].get_text(strip=True)
            # tailal_txt = '上榜日期,证券号码,证券简称,上榜涨幅 - ,买入额（万） - ,卖出额（万） - ,净买入（万）,所属营业部 reason_info ,游资名称 证券之星'
            tm_txt = str(date_str) + ',' + str(stock_code) + ',' + str(stock_name) + ',-,' + '-' + ',-' + ',' + summary_cells[3].get_text(strip=True) + ',' + reason_info + ',证券之星'
            #print(tm_txt)
            if not search_string_in_csv_memory(tm_txt):
                return_line_num += 1            
        #print(f"股票代码: {stock_code}, 股票名称: {stock_name}")  #debug
        # 解析 买入金额最大的前五名 表格 todo
    return return_line_num, title_only_flg


def save_to_csv(file_path, data_lines):
    """
    将内存数据列表写回CSV文件，按第一列日期排序
    
    参数:
        file_path (str): CSV文件路径
        data_lines (list): 内存中的数据行列表
    """
    
    if not data_lines:
        print("无数据可保存")
        return
    
    # 分离标题行和数据行
    header = data_lines[0] if data_lines else ""
    data_rows = data_lines[1:] if len(data_lines) > 1 else []
    
    # 如果没有数据行，只写入标题行
    if not data_rows:
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(header.split(','))
        print(f"只有标题行，已保存到 {file_path}")
        return
    
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
    
def get_workdays(days=5):
    """
    生成包含当日在内的指定天数的有效工作日列表  第一次生成时使用，只使用一次
    
    参数:
        days (int): 要生成的工作日天数，默认5
    
    返回:
        list: 包含指定天数工作日的列表，按时间从新到旧排列（最近的工作日在前）
    
    示例:
        >>> get_workdays(3)
        ['2026-01-24', '2026-01-23', '2026-01-22']  # 如果今天是周六
    """
    workdays = []
    current_date = datetime.now().date()  # 获取今天的日期
    
    while len(workdays) < days:
        # weekday(): 0=周一, 1=周二, ..., 4=周五, 5=周六, 6=周日
        if current_date.weekday() < 5:  # 是工作日（周一到周五）
            weekday_name = ['周一','周二','周三','周四','周五','周六','周日'][current_date.weekday()]
            date_str = current_date.strftime('%Y-%m-%d')
            workdays.append(date_str)
            print(f"添加工作日: {date_str} ({weekday_name})")
        else:
            weekday_name = ['周一','周二','周三','周四','周五','周六','周日'][current_date.weekday()]
            print(f"跳过非工作日: {current_date.strftime('%Y-%m-%d')} ({weekday_name})")
        
        # 继续向前遍历
        current_date -= pd.Timedelta(days=1)
    
    return workdays

def get_main():
    # 读取已有CSV文件内容到内存
    csv_file_path = stockstar_csv_path
    add_string_to_csv_memory(csv_file_path)
    # 获取当前日期，判断是否工作日（周一到周五），如果不是则向前推一天
    tmp_date = datetime.now()
    # weekday(): 0=周一, 1=周二, ..., 4=周五, 5=周六, 6=周日
    while tmp_date.weekday() >= 5:  # 5=周六, 6=周日
        tmp_date -= pd.Timedelta(days=1)
        print(f"非工作日，推至上一天: {tmp_date.strftime('%Y-%m-%d')} ({['周一','周二','周三','周四','周五','周六','周日'][tmp_date.weekday()]})")

    # 读取网页数据并更新内存列表
    all_line_num = -1
    time.sleep(2)  # 避免请求过快被封IP
    while all_line_num < 0:
        title_only_flg = True
        tmp_today_str = tmp_date.strftime('%Y-%m-%d')
        print(f"最终使用日期: {tmp_today_str} ({['周一','周二','周三','周四','周五','周六','周日'][tmp_date.weekday()]})")
        all_line_num = 0
        for j in t_name.keys():
            line_num, title_only_flg = read_web_page(j, tmp_today_str)
            all_line_num += line_num
        if all_line_num == 0 and title_only_flg is False:
            print('没有新数据，结束')
            all_line_num = 0  # 退出循环
            break
        elif all_line_num == 0 and title_only_flg:
            all_line_num = -1  # 继续循环读取前一天数据
            tmp_date -= pd.Timedelta(days=1)
        else:
            all_line_num = -1  # 继续循环读取前一天数据
            tmp_date -= pd.Timedelta(days=1)
            
    save_to_csv(csv_file_path, data_lines)    # 再写入数据行



def fast_add_data():
    # 读取已有CSV文件内容到内存
    csv_file_path = stockstar_csv_path
    add_string_to_csv_memory(csv_file_path)
    # 生成 获取数据的日期 列表
    workdays = get_workdays(500)
    for wday in workdays:
    # 读取网页数据并更新内存列表
        time.sleep(2)  # 避免请求过快被封IP
        for j in t_name.keys():
            if read_web_page(j, wday) == 0:
                print('没有新数据，结束')
                break
    # 保存回CSV文件
    save_to_csv(csv_file_path, data_lines)
# 使用示例
if __name__ == "__main__":
    #https://quote.stockstar.com/BillBoard/bjs_2026-01-23.html
    get_main()
    #fast_add_data()

