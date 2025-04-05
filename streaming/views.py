from selenium.webdriver import Chrome
from selenium import webdriver
from django.http import JsonResponse
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By  
from selenium.webdriver.support import expected_conditions as EC  
from selenium.webdriver.support.ui import WebDriverWait as Wait  
import time

def disney(request):
    driver = webdriver.Chrome()

    driver.get("https://www.disneyplus.com/es-419/identity/login/enter-email")
    time.sleep(4)
    email = driver.find_element(By.ID, 'email')
    email.send_keys('gregoriantoni201100@gmail.com')
    time.sleep(2)
    button = driver.find_element(By.TAG_NAME, 'button')
    button.click()
    time.sleep(5)
    password = driver.find_element(By.ID, 'password')
    password.send_keys('gregorio56130')
    time.sleep(4)
    button = driver.find_element(By.XPATH, '//button[.//span[contains(text(), "Iniciar sesión")]]')   
    if button.is_displayed() and button.is_enabled():
        print("El botón está visible y habilitado")
    else:
        print("El botón no está visible o habilitado")
    button.click()
    time.sleep(5)
    driver.quit()
        
    return JsonResponse({
        'status': 'success',
        'message': 'Página cargada (ver screenshot)'
    })