import requests
from bs4 import BeautifulSoup
import re
import os
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

'''

sh999999.day 上综指
sz399001.day 深成指
response = requests.get(url)
web_content = response.text
#print(web_content)
# 使用BeautifulSoup解析网页内容
soup = BeautifulSoup(web_content, 'html.parser')

# 提取指定内容，例如所有的标题
#titles = soup.find_all('h1')
titles = soup.find_all('td')
for title in titles:
    print(title.text)
'''
    
# 设置ChromeDriver路径
current_dir = os.path.dirname(os.path.abspath(__file__))
chrome_driver_path = os.path.join(current_dir, 'chromedriver.exe')

# 发送HTTP请求获取网页内容
url = 'https://data.10jqka.com.cn/market/rzrq/'
# 上一级目录（父目录）
parent_dir = os.path.dirname(current_dir)
rzrq_csv_path = os.path.join(parent_dir, 'data', 'rzrq.csv')

# 设置ChromeDriver路径
service = Service(chrome_driver_path)
# 初始化WebDriver
driver = webdriver.Chrome(service=service)

data_lines = []

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
<table class="m-table J-ajax-table">
<thead>
     <tr>
        <th rowspan="2" class="th-col" width="100">交易日期</th>
        <th colspan="4" class="th-col" width="100">本日融资余额(亿元)</th>
        <th colspan="4" class="th-col" width="100">本日融资买入额(亿元)</th>
        <th colspan="4" class="th-col" width="400">本日融券余量余额(亿元)</th>
        <th colspan="4" class="th-col">本日融资融券余额(亿元)</th>
    </tr>
    <tr class="row2">
        <th class="th-col" width="70">上海</th>
        <th class="th-col" width="70">深圳</th>
        <th class="th-col" width="70">北京</th>
        <th class="th-col" width="70">合计</th>
        <th class="th-col" width="70">上海</th>
        <th class="th-col" width="70">深圳</th>
        <th class="th-col" width="70">北京</th>
        <th class="th-col" width="70">合计</th>
        <th class="th-col" width="70">上海</th>
        <th class="th-col" width="70">深圳</th>
        <th class="th-col" width="70">北京</th>
        <th class="th-col" width="70">合计</th>
        <th class="th-col" width="70">上海</th>
        <th class="th-col" width="70">深圳</th>
        <th class="th-col" width="70">北京</th>
        <th class="th-col" width="70">合计</th>
    </tr>
</thead>
<tbody>
<tr class="">
		<td class="">2026-02-27</td>
		<td class="">13408.73</td>
		<td class="tc">-</td>
		<td class="tc">-</td>
		<td class="tc">13408.73</td>
		
		<td class="">1133.74</td>
		<td class="tc">-</td>
		<td class="tc">-</td>
		<td class="tc">1133.74</td>
		
		<td class="">116.82</td>
		<td class="tc">-</td>
		<td class="tc">-</td>
		<td class="tc">116.82</td>
		
		<td class="">13525.55</td>
		<td class="tc">-</td>
		<td class="tc">-</td>
		<td class="tc">13525.55</td>
</tr>
</tbody>
</table>
'''

def read_web_page():
    return_line_num = 0

    # 打开网页
    driver.get(url)
    # 等待JavaScript加载完成
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'm-table')))

    # 获取页面内容
    page_content = driver.page_source

    # 使用BeautifulSoup解析网页内容
    soup = BeautifulSoup(page_content, 'html.parser')

    # 提取指定内容，例如所有的标题
    titles = soup.findChild('tbody')
    tm_txt = ''
    for title in titles:
        if title != '\n': 
            subtb = title
            #print(subtb)
            subtr = subtb.findAll('td')
            if subtr is None or len(subtr) < 9: break
            #print(subtr)  只取 本日融资余额(亿元) 和 本日融券余额(亿元) 的合计列， 和作为数据不全时判断栏位是否为'-' 的深圳和北交，如果是则不处理
            
            # 检查深圳和北交是否为 '-'，如果是则跳过该行
            if str(subtr[2]) == '<td class="tc">-</td>' or str(subtr[3]) == '<td class="tc">-</td>':
                continue
            #日期 subtr[0] ，融资合计 subtr[4]，融券合计 subtr[12]，融资融券合计 subtr[16]
            tm_txt = str(subtr[0]) + ',' + str(subtr[4]) + ','+ str(subtr[12]) + ','+ str(subtr[16])
            substrings_to_remove = ["<td class>", "<td class=\"tc\">","<td class=\"tl\">","</td>","<td>","\n"] # 使用正则表达式删除特定子字符串 
            pattern = "|".join(substrings_to_remove)

            modified_string = re.sub(pattern, "", tm_txt)
            #print(modified_string)
            detail_txt = modified_string + '\n'
            if not search_string_in_csv_memory(modified_string):
                return_line_num += 1  
    
    return return_line_num


"""
    读取CSV文件到内存列表，检查字符串是否存在，不存在则添加。
    
    参数:
        search_string (str): 要查找/添加的字符串
    
    返回:
        list: 更新后的内存数据列表
"""  
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

def get_main():
    # 读取已有CSV文件内容到内存
    csv_file_path = rzrq_csv_path
    add_string_to_csv_memory(csv_file_path)
    if read_web_page() == 0:
        print('没有新数据，结束')
    save_to_csv(csv_file_path, data_lines)    # 再写入数据行

# 使用示例
if __name__ == "__main__":
    get_main()
