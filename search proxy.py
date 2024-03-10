import undetected_chromedriver as uc
import json

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

logs_raw = driver.get_log("performance")
logs = [json.loads(lr["message"])["message"] for lr in logs_raw]

for log in logs:
            try:
                resp_url = log["params"]["response"]["url"]
                if 'https://api.debank.com/history/list' in resp_url:
                    request_id = log["params"]["requestId"]
                    response_body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                    response_json = json.loads(response_body['body'])
                    response_json
            except Exception as e:
                pass

"It looks like you're checking an incorrect address" in driver.page_source

driver.quit()