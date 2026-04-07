import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

home = 'https://www.magazineluiza.com.br/'
query = 'cola bastao'
profile = os.path.abspath(os.path.join('var','browser_profiles','magalu_selenium'))
os.makedirs(profile, exist_ok=True)
opts = Options()
opts.add_argument('--headless=new')
opts.add_argument('--window-size=1400,900')
opts.add_argument(f'--user-data-dir={profile}')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-blink-features=AutomationControlled')
opts.add_argument('--lang=pt-BR')
opts.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
opts.add_experimental_option('excludeSwitches', ['enable-automation'])
opts.add_experimental_option('useAutomationExtension', False)
opts.add_experimental_option('prefs', {
    'intl.accept_languages': 'pt-BR,pt,en-US,en',
    'credentials_enable_service': False,
    'profile.password_manager_enabled': False,
    'profile.default_content_setting_values.notifications': 2,
})

driver = webdriver.Chrome(options=opts)
driver.set_page_load_timeout(45)
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
"""})

driver.get(home)
search = WebDriverWait(driver, 12).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="header-search-input"]')))
search.clear()
search.send_keys(query)
search.send_keys(Keys.ENTER)

try:
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Fazer login']"))).click()
except Exception:
    pass

try:
    WebDriverWait(driver, 10).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, '[data-testid="product-title"], [data-testid="product-card-container"], [data-testid="product-card"]')) > 0)
except Exception:
    pass

time.sleep(2)
html = driver.page_source or ''
print('url=', driver.current_url)
print('title=', driver.title)
print('product_titles=', len(driver.find_elements(By.CSS_SELECTOR, '[data-testid="product-title"]')))
print('product_cards=', len(driver.find_elements(By.CSS_SELECTOR, '[data-testid="product-card-container"], [data-testid="product-card"]')))
print('price_values=', len(driver.find_elements(By.CSS_SELECTOR, '[data-testid="price-value"]')))
print('login_buttons=', len(driver.find_elements(By.XPATH, "//span[normalize-space()='Fazer login']")))
low = html.lower()
for token in ['validate.perfdrive.com','radware bot manager captcha','window.ssjsinternal','shieldsquare','data-testid="product-title"','data-testid="price-value"']:
    print(token, token in low or token in driver.current_url.lower())
print('snippet=', low[:600])
driver.quit()
