import pytest
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.fixture(scope="module")
def driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

BASE_URL = "http://localhost:5173"

def take_screenshot(driver, name):
    os.makedirs("evidencias", exist_ok=True)
    driver.save_screenshot(f"evidencias/{name}.png")

def test_01_cadastro_novo_usuario(driver):
    driver.get(f"{BASE_URL}/")
    time.sleep(2)
    driver.find_element(By.XPATH, "//span[contains(text(), 'Primeiro cadastro')]").click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "nome")))
    driver.find_element(By.NAME, "nome").send_keys("Usuário Teste")
    driver.find_element(By.NAME, "email").send_keys(f"teste_{int(time.time())}@vendas.com")
    driver.find_element(By.NAME, "senha").send_keys("senha123")
    take_screenshot(driver, "01_cadastro_preenchido")
    driver.find_element(By.XPATH, "//button[text()='Cadastrar']").click()
    time.sleep(2)
    take_screenshot(driver, "01_cadastro_sucesso")
    assert "login" in driver.current_url or driver.current_url == f"{BASE_URL}/"

def test_02_cadastro_duplicado(driver):
    driver.get(f"{BASE_URL}/")
    time.sleep(1)
    driver.find_element(By.XPATH, "//span[contains(text(), 'Primeiro cadastro')]").click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "nome")))
    driver.find_element(By.NAME, "nome").send_keys("Admin")
    driver.find_element(By.NAME, "email").send_keys("admin@vendas.com")
    driver.find_element(By.NAME, "senha").send_keys("admin123")
    driver.find_element(By.XPATH, "//button[text()='Cadastrar']").click()
    time.sleep(2)
    take_screenshot(driver, "02_cadastro_erro_duplicado")
    assert "/cadastro" in driver.current_url

def test_03_login_fluxo_feliz(driver):
    driver.get(f"{BASE_URL}/")
    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys("admin@vendas.com")
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys("admin123")
    take_screenshot(driver, "03_login_preenchido")
    driver.find_element(By.XPATH, "//button[text()='Entrar']").click()
    WebDriverWait(driver, 10).until(EC.url_contains("/dashboard"))
    take_screenshot(driver, "03_login_sucesso_dashboard")
    assert "/dashboard" in driver.current_url

def test_04_login_senha_errada(driver):
    driver.get(f"{BASE_URL}/")
    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys("admin@vendas.com")
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys("errada123")
    driver.find_element(By.XPATH, "//button[text()='Entrar']").click()
    time.sleep(2)
    take_screenshot(driver, "04_login_erro_senha")
    assert "/dashboard" not in driver.current_url

def test_05_login_email_inexistente(driver):
    driver.get(f"{BASE_URL}/")
    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys("naoexiste@vendas.com")
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys("123456")
    driver.find_element(By.XPATH, "//button[text()='Entrar']").click()
    time.sleep(2)
    take_screenshot(driver, "05_login_erro_email")
    assert "/dashboard" not in driver.current_url

def test_06_cadastro_cliente_fluxo_feliz(driver):
    # Re-logar para garantir acesso
    test_03_login_fluxo_feliz(driver)
    driver.find_element(By.XPATH, "//li[contains(text(), 'Clientes')]").click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Novo Cliente')]")))
    driver.find_element(By.XPATH, "//button[contains(text(), 'Novo Cliente')]").click()
    
    driver.find_element(By.NAME, "nome").send_keys("Cliente Automação S.A.")
    driver.find_element(By.NAME, "cpf_cnpj").send_keys("12.345.678/0001-00")
    driver.find_element(By.NAME, "contato").send_keys("Carlos Teste")
    driver.find_element(By.NAME, "telefone").send_keys("(11) 98888-7777")
    driver.find_element(By.NAME, "email").send_keys("carlos@cliente.com")
    driver.find_element(By.NAME, "endereco").send_keys("Av. das Automações, 500")
    
    take_screenshot(driver, "06_cliente_preenchido")
    driver.find_element(By.XPATH, "//button[text()='Salvar']").click()
    time.sleep(2)
    take_screenshot(driver, "06_cliente_lista_sucesso")
    assert "Cliente Automação S.A." in driver.page_source

def test_07_cadastro_cliente_erro_validacao(driver):
    driver.get(f"{BASE_URL}/clientes")
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Novo Cliente')]")))
    driver.find_element(By.XPATH, "//button[contains(text(), 'Novo Cliente')]").click()
    # Tenta salvar vazio
    driver.find_element(By.XPATH, "//button[text()='Salvar']").click()
    time.sleep(1)
    take_screenshot(driver, "07_cliente_erro_vazio")
    assert driver.find_elements(By.XPATH, "//button[text()='Salvar']")

def test_08_edicao_cliente(driver):
    driver.get(f"{BASE_URL}/clientes")
    time.sleep(2)
    # Tenta achar o botão de editar (pode ser um ícone)
    edit_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='edit']")
    if not edit_buttons:
        edit_buttons = driver.find_elements(By.XPATH, "//*[contains(@class, 'MuiIconButton-root')]")
    
    edit_buttons[0].click()
    time.sleep(1)
    nome_field = driver.find_element(By.NAME, "nome")
    nome_field.clear()
    nome_field.send_keys("Cliente Alterado via Script")
    take_screenshot(driver, "08_cliente_edicao_pre")
    driver.find_element(By.XPATH, "//button[text()='Salvar']").click()
    time.sleep(2)
    take_screenshot(driver, "08_cliente_edicao_pos")
    assert "Alterado via Script" in driver.page_source

def test_09_navegacao_dashboard(driver):
    driver.find_element(By.XPATH, "//li[contains(text(), 'Dashboard')]").click()
    time.sleep(2)
    take_screenshot(driver, "09_dashboard_view")
    assert "Dashboard" in driver.page_source

def test_10_logout(driver):
    driver.find_element(By.XPATH, "//button[contains(text(), 'Sair')]").click()
    time.sleep(2)
    take_screenshot(driver, "10_logout_sucesso")
    assert driver.current_url == f"{BASE_URL}/"
