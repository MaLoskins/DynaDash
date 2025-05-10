# tests/integration/test_e2e_selenium.py

import unittest
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class E2ETestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Point at local app and spin up Chrome via webdriver_manager
        cls.base_url = "http://127.0.0.1:5000"
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument("--headless")  # uncomment to run headless

        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service, options=chrome_options)
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_full_user_flow(self):
        driver = self.driver
        base = self.base_url

        # 1. Log in (submit is <input type="submit">)
        driver.get(f"{base}/auth/login")
        driver.find_element(By.ID, "email").send_keys("newgentle2014@icloud.com")
        driver.find_element(By.ID, "password").send_keys("liu0369liu")
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        WebDriverWait(driver, 10).until(EC.url_contains("/visual/index"))

        # 2. Upload dataset (submit is <input type="submit">)
        driver.get(f"{base}/data/upload")
        dataset_path = os.path.join(os.getcwd(), "test_dataset.csv")
        assert os.path.exists(dataset_path), f"Test dataset not found at {dataset_path}"
        driver.find_element(By.ID, "file").send_keys(dataset_path)
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        WebDriverWait(driver, 10).until(EC.url_matches(r".*/data/view/\d+"))
        dataset_id = driver.current_url.rstrip("/").split("/")[-1]

        # 3. Generate visualization (submit is <input type="submit">)
        driver.get(f"{base}/visual/generate/{dataset_id}")
        driver.find_element(By.ID, "title").send_keys("Test Viz")
        driver.find_element(By.ID, "description").send_keys("End-to-end test with provided dataset")
        Select(driver.find_element(By.ID, "chart_type")).select_by_index(1)
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        WebDriverWait(driver, 20).until(EC.url_contains("/visual/view/"))

        # 4. Assert title appears
        header = driver.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Test Viz", header, "Expected visualization title not found")
