import unittest
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

class AuthenticationTests(unittest.TestCase):
    
    def setUp(self):
        os.environ["PATH"] += os.pathsep + '/Users/tariqhamdan/Downloads/chrome-mac-arm-64/'
        from webdriver_manager.chrome import ChromeDriverManager
        self.driver = webdriver.Chrome()

        self.driver.maximize_window()

    def tearDown(self):
        self.driver.quit()

    def test_user_login(self):
        driver = self.driver

        # Open the login page
        driver.get('http://bargetrader-staging-env.eba-urbgv66v.us-west-2.elasticbeanstalk.com/login')

        username_input = driver.find_element(By.NAME, 'username')
        password_input = driver.find_element(By.NAME, 'password')

        username_input.send_keys('vin')
        password_input.send_keys('diesel')

        login_button = driver.find_element(By.XPATH, '//input[@type="submit"]')
        login_button.click()

        # Use explicit wait to ensure the welcome message is present after login
        welcome_message_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="player-info"]/h2'))
        )

        welcome_message = welcome_message_element.text
        self.assertIn('vin', welcome_message)

    def test_user_logout(self):
        pass # Placeholder for now

    def test_user_registration(self):
        pass # Placeholder for now
