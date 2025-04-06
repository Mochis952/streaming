from selenium import webdriver
from selenium.webdriver.common.by import By
from django.http import JsonResponse
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from django.http import JsonResponse
import json
import logging
import time
def delete_disney(request):
    logging.info("Este es un mensaje informativo")
    logging.info(request)
    # ejemplo para acceder a un elemento nombre = request.get('hola', None)
    try:
        request = json.loads(request.body)
        driver = login_disney(request)
        
        time.sleep(2)

        # Buscar el perfil 'prueba' y hacer clic en él
        profile = request.get('profile', None)
        element = driver.find_element(By.XPATH, f"//h3[text()='{profile}']")

        element.click()

        time.sleep(4)  # Espera fija para esperar la carga de la siguiente página

        # Enviar PIN
        digits = request.get('pin', None)
        for i, digit in enumerate(digits):
            digit_field = driver.find_element(By.ID, f'digit-{i}')
            digit_field.send_keys(digit)

        time.sleep(4)  # Espera fija antes de eliminar

        # Hacer clic en 'Eliminar perfil'
        button = driver.find_element(By.XPATH, "//button[text()='Eliminar perfil']")
        button.click()

        time.sleep(2)

        # Confirmar eliminación
        button = driver.find_element(By.XPATH, "//button[text()='ELIMINAR']")
        button.click()

        time.sleep(2)

        driver.quit()
            
        return JsonResponse({
            'status': 'success',
            'message': 'Perfil eliminado correctamente'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def create_disney(request):
    try:
        request = json.loads(request.body)
        driver = login_disney(request)
        
        time.sleep(2)

        element = driver.find_element(By.XPATH, "//h3[text()='Crear perfil']")
        element.click()

        time.sleep(2)

        password = driver.find_element(By.ID, 'password')
        password.send_keys(request.get('password', None))
        time.sleep(4)
        continue_button = driver.find_element(By.ID, 'password-continue-login')
        continue_button.click()
        time.sleep(2)
        button = driver.find_element(By.XPATH, "//button[text()='SALTAR']")
        button.click()
        time.sleep(2)
        addProfile = driver.find_element(By.ID, 'addProfile')
        addProfile.send_keys(request.get('profile', None))
        time.sleep(1)
        element = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="gender-picker-dropdown-control"]')
        element.click()
        time.sleep(1)
        element = driver.find_element(By.ID, 'react-select-gender-picker-dropdown-option-0-1')
        element.click()
        time.sleep(1)
        dob_input = driver.find_element(By.ID, 'dob-input')
        dob_input.send_keys('20101999')
        time.sleep(4)
        button = driver.find_element(By.XPATH, "//button[text()='GUARDAR']")
        button.click()
        time.sleep(3)
        digits = request.get('pin', None)
        for i, digit in enumerate(digits):
            digit_field = driver.find_element(By.ID, f'digit-{i}')
            digit_field.send_keys(digit)
        time.sleep(2)
        button = driver.find_element(By.XPATH, "//button[text()='CONFIGURAR PIN DE PERFIL']")
        button.click()
        time.sleep(2)

        driver.quit()
            
        return JsonResponse({
            'status': 'success',
            'message': 'Perfil creado correctamente'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def login_disney(request):
    driver = webdriver.Chrome()

    driver.get("https://www.disneyplus.com/es-419/identity/login/enter-email")
    time.sleep(3)
    
    # Ingresar email
    email = driver.find_element(By.ID, 'email')
    email.send_keys(request.get('email', None))
    time.sleep(4)

    # Hacer clic en el botón de continuar
    button = driver.find_element(By.TAG_NAME, 'button')
    button.click()
    time.sleep(2)

    # Ingresar contraseña
    password = driver.find_element(By.ID, 'password')
    password.send_keys(request.get('password', None))
    time.sleep(4)

    # Hacer clic en "Iniciar sesión"
    button = driver.find_element(By.XPATH, '//button[.//span[contains(text(), "Iniciar sesión")]]')
    button.click()
    time.sleep(4)

    # Hacer clic en "Modificar perfiles"
    button = driver.find_element(By.XPATH, '//button[@aria-label="Modificar perfiles"]')
    button.click()

    return driver
