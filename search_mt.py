import threading
import queue
import undetected_chromedriver as uc
import json
import time

class DebankHistoryFetcher:
    def __init__(self, callback):
        self.callback = callback
        self.task_queue = queue.Queue()
        self.workers = []
        self.num_workers = 4  # You can adjust the number of worker threads as needed
        self.page_view_limit = 3
        # Initialize workers
        for _ in range(self.num_workers):
            worker = threading.Thread(target=self.worker_loop)
            worker.daemon = False
            worker.start()
            self.workers.append(worker)
            time.sleep(3)
    def add_task(self, address):
        self.task_queue.put(address)
    def worker_loop(self):
        page_view_count = 0
        driver = self.get_new_driver()
        while True:
            try:
                address = self.task_queue.get(timeout=1)  # Adjust timeout as needed
                if address is None:
                    break
                page_view_count += 1
                if page_view_count > self.page_view_limit:
                    page_view_count = 1
                    driver.quit()
                    driver = self.get_new_driver()
                data = self.fetch_data(driver, address)
                self.callback(address, data)
            except queue.Empty:
                continue
        driver.quit()
    def get_new_driver(self):
        options = uc.ChromeOptions()
        caps = options.to_capabilities()
        caps['goog:loggingPrefs'] = {'performance': 'ALL'}
        proxy_server = "127.0.0.1:16379"
        options.add_argument(f'--proxy-server={proxy_server}')
        return uc.Chrome(options=options, desired_capabilities=caps)
    
    def parse_logs(self, driver,logs, target_url):
        for log in logs:
            try:
                resp_url = log["params"]["response"]["url"]
                if target_url in resp_url:
                    request_id = log["params"]["requestId"]
                    response_body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                    response_json = json.loads(response_body['body'])
                    return response_json
            except Exception as e:
                pass
        return None
    def clean_history(self, response_json):
        history_list = response_json['data']['history_list']
        history_list = [each_row for each_row in history_list if each_row['is_scam'] != True]
        return history_list
    def fetch_data(self, driver, address):
        base_search_url = 'https://debank.com/profile/{}/history'
        driver.get(base_search_url.format(address))
        print('navigated')
        time.sleep(20)
        # Implement scraping logic here
        logs_raw = driver.get_log("performance")
        logs = [json.loads(lr["message"])["message"] for lr in logs_raw]
        SEARCH_API = 'https://api.debank.com/history/list'
        response_json = self.parse_logs(driver,logs, SEARCH_API)
        if response_json:
            history_list = self.clean_history(response_json)
            return {'address': address, 'data': history_list}
    def close(self):
        # Stop workers
        for _ in range(self.num_workers):
            self.task_queue.put(None)
        for worker in self.workers:
            worker.join()


addresses=['0x9d17bb55b57b31329cf01aa7017948e398b277bc','0x786694b02f1d331be540e727f1f2a697c45b57e4','0x0edefa91e99da1eddd1372c1743a63b1595fc413',
 '0x05bb279648e4e4cbcdecf2d4d6ec310999d444e7','0x65c76a684dbfd773bab8a7463e7498686bafd833','0x2fe9811e6b3cceb5c14cca6523f10ffdf4288af6',
 '0x7e4be95f871504778094060b5a12f43698cc7241','0xc8093288d89e494d1d0b41d2e598e58fe1e0eaf1','0x9d17bb55b57b31329cf01aa7017948e398b277bc']

# Example usage:
def my_callback(address, data):
    print(f"Data for address {address}: {data}")

debank = DebankHistoryFetcher(my_callback)
for address in addresses:
    debank.add_task(address)
# You can add more tasks here
# debank.add_task('another_address')

# Close the DebankHistoryFetcher
debank.close()
