import unittest
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

class AuthenticationTests(unittest.TestCase):
    
    def setUp(self):
        self.driver = webdriver.Chrome(ChromeDriverManager().install())

    def tearDown(self):
        self.driver.quit()

    def test_user_registration(self):
        pass # Placeholder for now

    def test_user_login(self):
        pass # Placeholder for now
