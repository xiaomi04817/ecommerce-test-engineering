
# 用 Selenium 写一个 Python 脚本，完成电商端到端下单流程：
# 1. 打开 http://localhost:3000
# 2. 登录（账号 testuser1 / Test@123456）
# 3. 搜索"手机"
# 4. 点击第一个商品进入详情
# 5. 点击"加入购物车"
# 6. 进入购物车，去结算
# 7. 提交订单
# 8. 断言：提示"下单成功"或页面跳转到订单页

from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# 手动指定 ChromeDriver 路径（国内环境自动下载失败）
service = Service(executable_path=r"d:/driver/chromedriver.exe")
driver = webdriver.Chrome(service=service)
driver.maximize_window()
BASE = "http://localhost:3000"

# 显示等待：最长等10秒，元素出现就立刻继续
wait = WebDriverWait(driver, 10)

driver.get(f'{BASE}/login')

# 等输入框出来再填
user_input = wait.until(
    EC.presence_of_element_located((By.XPATH, '//input[@placeholder="请输入用户名"]'))
)
user_input.send_keys("testuser1")

pwd_input = wait.until(
    EC.presence_of_element_located((By.XPATH, '//input[@placeholder="请输入密码"]'))
)
pwd_input.send_keys("Test@123456")

# 点击登录按钮
login_btn = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.submit-btn'))
)
login_btn.click()
sleep(3)

# 搜索"手机"
prd_input = wait.until(
    EC.presence_of_element_located((By.XPATH, '//input[@placeholder="搜索商品名称（至少2个字符）"]'))
)
prd_input.send_keys("手机")
prd_input.send_keys(Keys.ENTER)
sleep(3)

# 在详情页点"加入购物车"
add_cart_btn = wait.until(
    EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"加入购物车")]'))
)
add_cart_btn.click()

# 点击购物车
cart_button = wait.until(
    EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"购物车")]'))
)
cart_button.click()

# 点击去结算
buy_button = wait.until(
    EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"去结算")]'))
)
buy_button.click()

# 点击添加地址
add_address_info= wait.until(
    EC.element_to_be_clickable((By.XPATH,'//button[contains(.,"添加地址")]'))
)
add_address_info.click()

add_address_new_info= wait.until(
    EC.element_to_be_clickable((By.XPATH,'//button[contains(.,"添加新地址")]'))
)
add_address_new_info.click()

# 添加收货信息
add_name = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[placeholder="请输入收件人姓名"]'))
)
add_name.send_keys("西西米")

add_phone = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR,'input[placeholder="请输入手机号"]'))
)
add_phone.send_keys("15587510539")

add_province = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR,'input[placeholder="请输入省份"]'))
)
add_province.send_keys("浙江省")

add_city = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR,'input[placeholder="请输入城市"]'))
)
add_city.send_keys("台州市")

add_address = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR,'input[placeholder="请输入区/县"]'))
)
add_address.send_keys("玉环市")

add_detail = wait.until(
    EC.element_to_be_clickable((By.CLASS_NAME,"el-textarea__inner"))
)
add_detail.send_keys("芦浦镇芦浦药店")

add_info = wait.until(
    EC.element_to_be_clickable((By.XPATH, '//footer//button[contains(.,"添加")]'))
)
add_info.click()

back_btn = wait.until(
    EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"返回商品列表")]'))
)
back_btn.click()

cart_button = wait.until(
    EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"购物车")]'))
)
cart_button.click()

buy_button = wait.until(
    EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"去结算")]'))
)
buy_button.click()

submit_order = wait.until(
    EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"提交订单")]'))
)
submit_order.click()
sleep(3)

current_url = driver.current_url
assert f"{BASE}/order" in current_url , f"跳转失败: {current_url}"

driver.quit()

