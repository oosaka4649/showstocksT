import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime

'''
当机器上安装的Chrome浏览器自动升级时，使用Selenium会报错，原因是ChromeDriver版本与Chrome浏览器版本不匹配。
解决方法是下载与当前Chrome浏览器版本匹配的ChromeDriver，并替换掉原有的ChromeDriver。exe文件。

ChromeバージョンアップによるSeleniumエラーのトラブルシューティング
https://zenn.dev/ykesamaru/articles/a1a4fd5eae8563


'''

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# 发送HTTP请求获取网页内容  爱金股网站上的T王数据，  按人名
# T王简介 此席位每天做T，其乐无穷 游资T王龙虎榜上榜统计 
# 获取T王的当日数据，或多日数据，长期 监控他参与的个股，并分析其进场出场及买卖行为
# 适当参与
url = 'https://www.aijingu.com/youzi/'
url_2 = '.html?page='

t_name = {'13':'T王','6':'苏南帮','56':'N周二','52':'竞价抢筹','23':'孙哥','21':'炒股养家','72':'南京帮','74':'屠文斌','31':'宁波桑田路'}
  
# 设置ChromeDriver路径
driver_path = 'c:\\tmp\\chromedriver\\chromedriver.exe'


service = Service(driver_path)


# 初始化WebDriver
driver = webdriver.Chrome(service=service)
'''
苏南帮
席位多为江苏本地席位联动操作，3/4板多为强顶一字板。
https://www.aijingu.com/youzi/6.html

T王
此席位每天做T，其乐无穷。
https://www.aijingu.com/youzi/13.html

炒股养家
目前资金量极大，对市场和个股都有很独到的理解力，通道优势较强，
常常利用通道使个股一字涨停，隔日高位逐步离场。善于挖掘题材龙头，
近期开始有波段锁仓操作，较有名的就是在雄安龙头青龙管业上的底部介入锁仓，被他挖掘的个股值得关注

南京帮简介
游资短庄，多与江苏本地的席位进行联合操作，选股也偏短线，连续拉板提升辨识度，在通过制造大波动吸引目光利用资金优势对倒拉升。

屠文斌简介
屠文斌是叱咤风云的老牌游资，偏好大流通可观察其出手来判断板块地位。

宁波桑田路简介
宁波知名的游资，资金量超过10亿，操作风格彪悍凌厉，是众多知名游资里面溢价比较高的席位，交易风格多为打板为主，不拘泥于是高位板，还是低位板，可以锁仓做T很久，也可以跑的飞快，基本市场每一个妖股背后都有它的身影
'''

tailal_txt = '上榜日期,证券号码,证券简称,上榜涨幅,买入额（万）,卖出额（万）,净买入（万）,所属营业部,游资名称'

data_lines = []

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
    
def read_web_page(i, j):
    return_line_num = 0
    print('第',i,'页')
    # 打开网页
    driver.get(url + str(j) + url_2 + str(i))    
    
    # 等待JavaScript加载完成
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'tc')))

    # 获取页面内容
    page_content = driver.page_source

    # 使用BeautifulSoup解析网页内容
    soup = BeautifulSoup(page_content, 'html.parser')

    # 提取指定内容，例如所有的标题
    #titles = soup.find_all('h1')
    titles = soup.findChild('tbody')
    tm_txt = ''
    for title in titles:
        if title != '\n': 
            subtb = title
            #print(subtb)
            subtr = subtb.findAll('td')
            if subtr is None or len(subtr) < 9: break
            #print(subtr)
            tm_txt = str(subtr[0]) + ',' + str(subtr[1]) + ','+ str(subtr[2]) + ','+ str(subtr[3]) + ','+ str(subtr[5]) + ','+ str(subtr[6]) + ','+ str(subtr[7]) + ','+ str(subtr[8]) + ','+ str(t_name[j])
            #print(tm_txt)
            substrings_to_remove = ["<td class=\"tc nowrap\">", "<td class=\"tc\">","<td class=\"tl\">","</td>","<font color=\"#ff0000\">","<font color=\"#5EBC35\">","<font color=\"#D9383E\">","</font>", '<a href=\"[^"]+\" target=\"_blank\">',"</a>","\n"] # 使用正则表达式删除特定子字符串 
            pattern = "|".join(substrings_to_remove)

            modified_string = re.sub(pattern, "", tm_txt)
            #print(modified_string)
            detail_txt = modified_string + '\n'
            if not search_string_in_csv_memory(modified_string):
                return_line_num += 1  
    
    return return_line_num

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
    csv_file_path = 'D:\\python\\showstocksT\\cvs_search_app\\aijinggu_all.csv'
    add_string_to_csv_memory(csv_file_path)
    for j in t_name.keys():
        for i in range(1,25):
            if read_web_page(i, j) == 0:
                print('没有新数据，结束')
                break
    save_to_csv(csv_file_path, data_lines)    # 再写入数据行

# 使用示例
if __name__ == "__main__":
    get_main()

