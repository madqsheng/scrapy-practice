from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import os
import requests

url = "https://courses.d2l.ai/zh-v2/"
root_dir=r'C:/Users/admin/Desktop/动手学习深度学习'

# 创建 Firefox 浏览器选项
firefox_options = Options()
firefox_options.headless = True  # 开启无头模式
# 创建 Firefox 浏览器实例，并传入选项
driver = webdriver.Firefox(options=firefox_options)
# 打开网页
driver.get(url)

#一级目录
h2_list=[]
h2s = driver.find_elements_by_xpath("//h2[@class='fs-4']")
for h2 in h2s:
    h2_list.append(h2.text)

# 使用 XPath 定位所有 class 为 "module" 的 div 元素
module_divs = driver.find_elements_by_xpath("//div[@class='module']")

# 打印所有匹配的 div 元素的文本内容
for i,div in enumerate(module_divs):
    folder_path = os.path.join(root_dir,h2_list[0])
    # 如果不存在，创建文件夹
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    dd_elements=div.find_elements_by_xpath("./dl/dd")
    for dd_element in dd_elements:
        dt=dd_element.find_elements_by_xpath("./dl/dt")
        if len(dt)==0:#休课是空的
            continue
        else:
            title = dt[0].text
        
        #找pdf链接
        dd=dd_element.find_elements_by_xpath("./dl/dd")[1]
        a_element = dd.find_elements_by_xpath("./a")
        if a_element:
            # 如果包含 <a> 标签，提取其 href 属性值
            href_value = a_element[0].get_attribute("href")

            #下载文件
            file_response = requests.get(href_value)

            # 检查请求是否成功
            if file_response.status_code == 200:
                file_name = os.path.join(folder_path,f"{title}.pdf")

                # 保存PDF文件
                with open(file_name, 'wb') as pdf_file:
                    pdf_file.write(file_response.content)
                print(f"PDF文件已成功下载并保存为 {file_name}")
            else:
                print("请求失败，状态码:", file_response.status_code)

# 关闭浏览器
driver.quit()