import requests
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
import re


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
#url = 'https://example.com'
url = 'https://www.aijingu.com/youzi/13.html?page=1'

'''
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
driver_path = 'c:\\tmp\\chromedriver\\chromedriver.exe'


service = Service(driver_path)


# 初始化WebDriver
driver = webdriver.Chrome(service=service)
'''
# 初始化WebDriver
driver = webdriver.Chrome(executable_path=driver_path)
'''
# 打开网页
#url = 'https://example.com'
driver.get(url)

# 等待JavaScript加载完成
wait = WebDriverWait(driver, 10)
element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'tc')))

# 获取页面内容
page_content = driver.page_source

# 关闭浏览器
driver.quit()

# 处理页面内容
#print(page_content)


# 使用BeautifulSoup解析网页内容
soup = BeautifulSoup(page_content, 'html.parser')

# 提取指定内容，例如所有的标题
#titles = soup.find_all('h1')
titles = soup.findChild('tbody')
tm_txt = ''
detail_txt = ''
tailal_txt = '上榜日期,证券号码,证券简称,今日涨幅,买入额（万）,卖出额（万）,净买入（万）, 所属营业部'
for title in titles:
    if title != '\n': 
        subtb = title
        #print(subtb)
        subtr = subtb.findAll('td')
        #print(subtr)
        tm_txt = str(subtr[0]) + ',' + str(subtr[1]) + ','+ str(subtr[2]) + ','+ str(subtr[4]) + ','+ str(subtr[5]) + ','+ str(subtr[6]) + ','+ str(subtr[7]) + ','+ str(subtr[8])
        #print(tm_txt)
        substrings_to_remove = ["<td class=\"tc nowrap\">", "<td class=\"tc\">","<td class=\"tl\">","</td>","<font color=\"#ff0000\">","<font color=\"#5EBC35\">","<font color=\"#D9383E\">","</font>", '<a href=\"[^"]+\" target=\"_blank\">',"</a>","\n"] # 使用正则表达式删除特定子字符串 
        pattern = "|".join(substrings_to_remove) 
        modified_string = re.sub(pattern, "", tm_txt)
        #print(modified_string)
        detail_txt = detail_txt + modified_string + '\n'
'''        
上榜日期
证券号码
证券简称
今日涨幅
买入额（万）
卖出额（万）
净买入（万）

格式化显示 csv格式 串

import pandas as pd
from io import StringIO

csv_str = "代码,名称,最新价\n603155,新亚强,26.76\n600519,贵州茅台,1688.00"
df = pd.read_csv(StringIO(csv_str))
print(df)

'''
all_txt = tailal_txt + '\n' + detail_txt
df = pd.read_csv(StringIO(all_txt))
#print(df)
df.to_csv('D:\\python\\showstocksT\\cvs_search_app\\aijinggu_Twang.csv', index=False, encoding='utf-8-sig')




