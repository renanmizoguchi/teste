#!/usr/bin/env python3
# pip install selenium webdriver-manager

import os
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager

BASE_URL = 'https://approcket.cmsw.com/'
CNPJ    = '07714104000107'
USUARIO = 'renan.mizoguchi'
SENHA   = 'renan.mizoguchi'

def set_date_via_js(driver, element, value):
    driver.execute_script("""
        const el = arguments[0], val = arguments[1];
        const nativeSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
        ).set;
        nativeSetter.call(el, val);
        el.dispatchEvent(new Event('input',  { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.blur();
    """, element, value)

def run_once():
    # cálculo de período: 1 dias antes até o dia atual
    hoje      = datetime.today()
    data_inicio = (hoje - timedelta(days=1)).strftime('%d/%m/%Y')
    data_fim    = hoje.strftime('%d/%m/%Y')

    # setup do Edge
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.set_capability('acceptInsecureCerts', True)
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    service = Service(EdgeChromiumDriverManager().install(), log_path=os.devnull)
    driver = webdriver.Edge(service=service, options=options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 30)

    try:
        # 1. Acessa login
        driver.get(BASE_URL)
        time.sleep(2)

        # 2. Preenche e envia credenciais
        wait.until(EC.presence_of_element_located((By.ID, 'cnpj'))).send_keys(CNPJ)
        driver.find_element(By.NAME, 'login.usuario').send_keys(USUARIO)
        driver.find_element(By.NAME, 'login.senha').send_keys(SENHA)
        driver.find_element(By.CSS_SELECTOR, 'input.login_button').click()
        time.sleep(2)

        # 3. Aguarda redirecionamento
        wait.until(lambda d: d.current_url != BASE_URL)
        time.sleep(2)

        # 4. Navega em “Report View New”
        report_view = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//a[contains(normalize-space(.), 'Report View New')]"
        )))
        report_view.click()
        time.sleep(2)

        # 5. Alterna para aba de relatório
        original = driver.current_window_handle
        for h in driver.window_handles:
            if h != original:
                driver.switch_to.window(h)
                break
        time.sleep(2)

        # 6. Seleciona aba “Report on Demand”
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, 'MuiBackdrop-root')))
        demand_tab = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[@role='tab' and .//span[text()='Report on Demand']]"
        )))
        demand_tab.click()
        time.sleep(2)

        # 7. Espera grid carregar
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[@col-id='id_report']")))
        time.sleep(2)

        # 8. Rola e clica na linha ID=5879
        row = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//div[@role='row' and .//div[@col-id='id_report' and normalize-space(text())='5879']]"
        )))
        driver.execute_script("arguments[0].scrollIntoView(true);", row)
        row.click()
        time.sleep(2)

        # 9. Preenche datas via JS
        inputs = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//input[@placeholder='Select date']")))
        # data início
        start = inputs[0]
        driver.execute_script("arguments[0].scrollIntoView(true);", start)
        start.click(); time.sleep(1)
        set_date_via_js(driver, start, data_inicio)
        time.sleep(2)
        # data fim
        end = inputs[1]
        driver.execute_script("arguments[0].scrollIntoView(true);", end)
        end.click(); time.sleep(1)
        set_date_via_js(driver, end, data_fim)
        time.sleep(2)

        # 10. Executa e fecha
        exec_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[.//span[text()='Executar e Fechar']]"
        )))
        exec_btn.click()
        time.sleep(2)
    finally:
        driver.quit()

if __name__ == '__main__':
    MAX_ATTEMPTS = 3
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(f"Tentativa {attempt} de {MAX_ATTEMPTS}...")
            run_once()
            print("Concluído com sucesso.")
            break
        except Exception as e:
            print(f"Erro na tentativa {attempt}: {e}")
            if attempt < MAX_ATTEMPTS:
                print("Aguardando 2s antes da próxima tentativa...")
                time.sleep(2)
            else:
                print("Limite de tentativas atingido. Abortando.")
                raise
