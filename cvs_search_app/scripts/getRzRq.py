import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# 发送HTTP请求获取网页内容
#url = 'https://example.com'
url = 'https://www.sse.com.cn/market/othersdata/margin/sum/'

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
element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'text-nowrap')))

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
titles = soup.findChild('table')
in_test = "text-center"
for title in titles:
    for sube in title:
        subtr = sube.findAll('td')
        #print(subtr)
        tm_txt = ''
        for subetd in subtr:
            if in_test not in str(subetd):
                tm_txt = tm_txt + '-' + subetd.text.replace(',', "")
        print(tm_txt)


