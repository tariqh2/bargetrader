import unittest
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import random
import string

class AuthenticationTests(unittest.TestCase):
    
    def setUp(self):
        os.environ["PATH"] += os.pathsep + '/Users/tariqhamdan/Downloads/chrome-mac-arm-64/'
        from webdriver_manager.chrome import ChromeDriverManager
        self.driver = webdriver.Chrome()

        self.driver.maximize_window()

    def tearDown(self):
        self.driver.quit()
    
    def login_user(self): # Asbtracting the user login into a seperate method to be reused
        driver = self.driver
        # Open the login page
        driver.get('http://bargetrader-staging-env.eba-urbgv66v.us-west-2.elasticbeanstalk.com/login')

        username_input = driver.find_element(By.NAME, 'username')
        password_input = driver.find_element(By.NAME, 'password')

        username_input.send_keys('vin')
        password_input.send_keys('diesel')

        login_button = driver.find_element(By.XPATH, '//input[@type="submit"]')
        login_button.click()
    
    def register_user(self, username, password):
        driver = self.driver
        # Open the registration page
        driver.get('http://bargetrader-staging-env.eba-urbgv66v.us-west-2.elasticbeanstalk.com/register')

        # Define a maximum wait time (e.g., 10 seconds)
        wait = WebDriverWait(driver, 10)

        # Fill in the registration form
        username_input = wait.until(EC.presence_of_element_located((By.NAME, 'username')))
        password_input = driver.find_element(By.NAME, 'password')
        confirm_password_input = driver.find_element(By.NAME, 'confirmation')

        username_input.send_keys(username)
        password_input.send_keys(password)
        confirm_password_input.send_keys(password)

        # Submit the registration form
        submit_register_button = driver.find_element(By.XPATH, '//input[@type="submit"][@value="Register"]')
        submit_register_button.click()

    def test_user_login(self):
        self.login_user() # Use the new method here

        # Use explicit wait to ensure the welcome message is present after login
        welcome_message_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="player-info"]/h2'))
        )

        welcome_message = welcome_message_element.text
        self.assertIn('vin', welcome_message)

    def test_user_logout(self):
        # Login to the application
        self.login_user()

        # Find and click the logout button
        logout_button = self.driver.find_element(By.XPATH, '//footer/a[@class="btn btn-danger"]')
        logout_button.click()

        # Validate logout was successful by checking that you're on the index page.
        # This assumes that there's a unique header or element on the index.html page that you can verify.

        index_page_header = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//h1'))
        ).text
        self.assertEqual(index_page_header, "Welcome to Contango!") # Use the correct header text

    def test_user_registration(self):
        # Generate a random username for testing
        random_username = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
        password = 'testpassword123'  

        # Use the register_user method
        self.register_user(random_username, password)

        # Check if registration was successful
        # After registration, validate that the registration was successful by checking the welcome message
        welcome_message_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="player-info"]/h2'))
        )
        welcome_message = welcome_message_element.text
        self.assertIn(random_username, welcome_message)