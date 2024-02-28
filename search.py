import undetected_chromedriver as uc
import json
import time

class DebankHistoryFetcher:
    def __init__(self, address):
        self.address = address
        self.base_search_url = 'https://debank.com/profile/{}/history'
        self.driver = self.get_driver()

    def get_driver(self):
        options = uc.ChromeOptions()
        caps = options.to_capabilities()
        caps['goog:loggingPrefs'] = {'performance': 'ALL'}
        driver = uc.Chrome(
            headless=True,
            options=options,
            desired_capabilities=caps
        )
        return driver

    def parse_logs(self, logs, target_url):
        for log in logs:
            try:
                resp_url = log["params"]["response"]["url"]
                if target_url in resp_url:
                    request_id = log["params"]["requestId"]
                    response_body = self.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                    response_json = json.loads(response_body['body'])
                    return response_json
            except Exception as e:
                pass
        return None

    def clean_history(self, response_json):
        history_list = response_json['data']['history_list']
        history_list = [each_row for each_row in history_list if each_row['is_scam'] != True]
        return history_list

    def fetch_history_list(self):
        self.driver.get(self.base_search_url.format(self.address))
        time.sleep(9)
        logs_raw = self.driver.get_log("performance")
        logs = [json.loads(lr["message"])["message"] for lr in logs_raw]
        SEARCH_API = 'https://api.debank.com/history/list'
        response_json = self.parse_logs(logs, SEARCH_API)
        if response_json:
            history_list = self.clean_history(response_json)
            return history_list
        else:
            return None

    def close_driver(self):
        if self.driver:
            self.driver.quit()


# Example usage:
address = '0xbe676a680343de114f7e71df9397bdeabe77551e'
debank_fetcher = DebankHistoryFetcher(address)
history_list = debank_fetcher.fetch_history_list()

if history_list:
    print(history_list)
else:
    print("No history list found.")

# Close the WebDriver
debank_fetcher.close_driver()