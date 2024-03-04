import undetected_chromedriver as uc

options = uc.ChromeOptions()
caps = options.to_capabilities()
caps['goog:loggingPrefs'] = {'performance': 'ALL'}
proxy_server = "127.0.0.1:16379"
options.add_argument(f'--proxy-server={proxy_server}')
driver = uc.Chrome(
            headless=False,
            options=options,
            desired_capabilities=caps
        )

driver.get('https://debank.com/profile/0x171c53d55b1bcb725f660677d9e8bad7fd084282/history')



driver.quit()