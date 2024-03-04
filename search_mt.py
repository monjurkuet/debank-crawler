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
        self.num_workers = 2  # You can adjust the number of worker threads as needed
        self.page_view_limit = 2
        # Initialize workers
        for _ in range(self.num_workers):
            worker = threading.Thread(target=self.worker_loop)
            worker.daemon = True
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
    def fetch_data(self, driver, address):
        base_search_url = 'https://debank.com/profile/{}/history'
        driver.get(base_search_url.format(address))
        # Implement scraping logic here
        # For simplicity, let's assume we're just returning a dummy response
        return {'address': address, 'data': 'dummy data'}
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
for address in addresses[:4]:
    debank.add_task(address)
# You can add more tasks here
# debank.add_task('another_address')

# Close the DebankHistoryFetcher
debank.close()
