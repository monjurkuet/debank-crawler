import undetected_chromedriver as uc
import json
import time
from concurrent.futures import ThreadPoolExecutor

class DebankHistoryFetcher:
    def __init__(self, addresses, num_threads=5, addresses_per_thread=4):
        self.addresses = addresses
        self.base_search_url = 'https://debank.com/profile/{}/history'
        self.num_threads = num_threads
        self.addresses_per_thread = addresses_per_thread
        self.drivers = self.get_drivers()

    def get_drivers(self):
        # Create a Chrome driver for each thread
        drivers = []
        for _ in range(self.num_threads):
            options = uc.ChromeOptions()
            caps = options.to_capabilities()
            caps['goog:loggingPrefs'] = {'performance': 'ALL'}
            driver = uc.Chrome(
                headless=False,
                options=options,
                desired_capabilities=caps
            )
            drivers.append(driver)
        return drivers

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

    def fetch_history_for_addresses(self, addresses_chunk, driver):
        history_lists = []
        for address in addresses_chunk:
            driver.get(self.base_search_url.format(address))
            time.sleep(9)
            logs_raw = driver.get_log("performance")
            logs = [json.loads(lr["message"])["message"] for lr in logs_raw]
            SEARCH_API = 'https://api.debank.com/history/list'
            response_json = self.parse_logs(logs, SEARCH_API)
            if response_json:
                history_list = self.clean_history(response_json)
                history_lists.append(history_list)
            else:
                history_lists.append(None)
        return history_lists

    def fetch_history_list(self):
        history_lists = []

        # Split addresses into chunks for each thread
        address_chunks = [self.addresses[i:i + self.addresses_per_thread] for i in range(0, len(self.addresses), self.addresses_per_thread)]

        # Use ThreadPoolExecutor for concurrent fetching
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [
                executor.submit(self.fetch_history_for_addresses, chunk, driver)
                for chunk, driver in zip(address_chunks, self.drivers)
            ]

            for future in futures:
                history_lists.extend(future.result())

        return history_lists

    def close_drivers(self):
        for driver in self.drivers:
            if driver:
                driver.quit()


# Example usage with a list of addresses:
addresses = ['0xbe676a680343de114f7e71df9397bdeabe77551e', '0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e','0xbe676a680343de114f7e71df9397bdeabe77551e']  # Add more addresses
num_threads = 2
addresses_per_thread = 4
debank_fetcher = DebankHistoryFetcher(addresses, num_threads=num_threads, addresses_per_thread=addresses_per_thread)
history_lists = debank_fetcher.fetch_history_list()

for history_list in history_lists:
    if history_list:
        print(history_list)
    else:
        print("No history list found.")

# Close the WebDriver instances
debank_fetcher.close_drivers()
