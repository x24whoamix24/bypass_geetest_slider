from selenium import webdriver
from captcha_solver.nocaptcha import CapatchaSolver
GEETEST_DEMO_PAGE = "https://www.geetest.com/en/demo"




def main():
    driver = webdriver.Chrome()
    driver.maximize_window()
    captcha_solver = CapatchaSolver(driver)
    # Goto demo page
    driver.get(GEETEST_DEMO_PAGE)
    # Scroll down to the end of the page
    # Find the slider test button and click it
    button = driver.find_element_by_xpath('//*[@id="gt-show-mobile"]/div/section[1]/div/div/div[2]')
    button.click()
    # Now that we have reached the slider test part, we can call our captcha sovler
    # class to solve the captcha for us
    captcha_solver.solve_captcha()

if __name__ == "__main__":
    main()
