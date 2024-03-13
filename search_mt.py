import threading
import queue
import threading
import queue
import undetected_chromedriver as uc
import json
import time
import os
import dotenv
import traceback

dotenv.load_dotenv()
PROXY_SERVER = os.getenv('PROXY_SERVER')
IS_HEADLESS = os.getenv('IS_HEADLESS')

class DebankHistoryFetcher:
    def __init__(self, callback, num_workers, page_view_limit, is_exit_on_complete=False):
        self.callback = callback
        self.task_queue = queue.Queue()
        self.workers = []
        self.num_workers = num_workers              # Worker threads
        self.page_view_limit = page_view_limit      # Number of page views before refreshing the driver
        self.is_exit_on_complete = is_exit_on_complete  # Whether workers should quit if queue is empty
        # Initialize workers
        for _ in range(self.num_workers):
            worker = threading.Thread(target=self.worker_loop)
            worker.daemon = False
            worker.start()
            self.workers.append(worker)
            time.sleep(3)                       # Add a delay to avoid problems with spinning up chrome instances

    def add_task(self, task: tuple):
        """
        We add addresses to task queue and workers take them and scrape and send results to callback
        :param task: (monitor_id, address)
        :return:
        """
        self.task_queue.put(task)

    def worker_loop(self):
        """
        Each worker runs in its own thread and processes from common queue
        :return:
        """
        page_view_count = 0
        driver = self.get_new_driver()
        while True:
            try:
                data = None
                next_task = self.task_queue.get(timeout=1)  # Adjust timeout as needed
                if next_task is None:
                    # If queue is empty, exit if is_exit_on_complete is True else check again
                    if self.is_exit_on_complete:
                        break
                    else:
                        continue
                monitor_id, address = next_task
                page_view_count += 1
                if page_view_count > self.page_view_limit:
                    page_view_count = 1
                    driver.quit()
                    driver = self.get_new_driver()
                retry = 5
                while retry > 0:
                    retry -= 1
                    data = self.fetch_data(driver, address)
                    if data['data']==None:
                        print('Retry with new driver')
                        driver.quit()
                        time.sleep(1)
                        driver = self.get_new_driver()
                    else:
                        break
                self.callback( (monitor_id, address, data) )
            except queue.Empty:
                continue
            except Exception as e:
                print("".join(traceback.TracebackException.from_exception(e).format()))
        driver.quit()

    def get_new_driver(self):
        """
        Instantiate a new chrome driver with headless/proxy options
        :return:
        """
        options = uc.ChromeOptions()
        caps = options.to_capabilities()
        caps['goog:loggingPrefs'] = {'performance': 'ALL'}
        if IS_HEADLESS:
            options.add_argument(f'--headless')
        if PROXY_SERVER:
            options.add_argument(f'--proxy-server={PROXY_SERVER}')
        return uc.Chrome(options=options, desired_capabilities=caps)
    
    def parse_logs(self, driver, target_url):
        # keep checking for 10 secs until api request is intercepted
        check_time = 5
        wait_time_each_iter = 2
        response_json = None
        while check_time > 0:
            check_time -= 1
            time.sleep(wait_time_each_iter)
            logs_raw = driver.get_log("performance")
            logs = [json.loads(lr["message"])["message"] for lr in logs_raw]
            for log in logs:
                try:
                    resp_url = log["params"]["response"]["url"]
                    if target_url in resp_url:
                        request_id = log["params"]["requestId"]
                        response_body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                        response_json = json.loads(response_body['body'])
                        return response_json
                except Exception as e:
                    response_json = None
                    #print(e)
            if response_json:
                break
            else:
                print('Checking network logs.....')
        return response_json

    def parse_tx(self,history_list):
        final_data=[]
        if history_list:
            for each_tx in history_list:
                tx_timestamp=each_tx['time_at']
                chain=each_tx['chain']
                tx_hash=each_tx['id']
                function_=each_tx['tx']['name']
                protocol=each_tx['project_id']
                protocol_address=each_tx['other_addr']
                tr_in=each_tx['receives']
                tr_out=each_tx['sends']
                data={'tx_timestamp':tx_timestamp,'chain':chain,'tx_hash':tx_hash,'function_':function_,'protocol':protocol,'protocol_address':protocol_address,'tr_in':tr_in,'tr_out':tr_out}
                final_data.append(data)
        else:
            pass
        return final_data

    def clean_history(self, response_json):
        try:
            history_list = response_json['data']['history_list']
            history_list = [each_row for each_row in history_list if each_row['is_scam'] != True]
        except Exception as e:
            print(e)
            history_list=None
        if history_list:
           history_list= self.parse_tx(history_list)
        return history_list
    
    def extract_additional_tx_data(self,driver,history_list):
        # extract tx-data from webpage
        html_history=driver.find_elements('xpath','//div[@class="dbChangeTokenList"]//div[@data-token-chain]')
        full_data=[]
        for i in html_history:
            try:
                token_name=i.get_attribute('data-name')
            except:
                token_name=None
            try:
                token_id=i.get_attribute('data-id')
            except:
                token_id=None
            try:
                protocol_image_url=i.find_element('xpath','./div/img').get_attribute('src')
            except:
                protocol_image_url=None
            data={'token_name':token_name,'token_id':token_id,'protocol_image_url':protocol_image_url}  
            full_data.append(data)
        # extract tx hash url,protocol name, protocol image url from webpage
        html_protocol=driver.find_elements('xpath','//div[contains(@class, "History_tableLine")]')
        additional_data=[]
        for i in html_protocol:
            try:
                tx_hash_url=i.find_element('xpath','.//div[contains(@class, "History_txStatus")]//a').get_attribute('href')
            except:
                tx_hash_url=None
            try:
                protocol_clean=i.find_element('xpath','.//span[contains(@class, "TransactionAction_projectName")]').text
            except:
                protocol_clean=None
            try:
                protocol_image_url=i.find_element('xpath','.//div[contains(@class, "TransactionAction_transactionAction")]//img').get_attribute('src')
            except:
                protocol_image_url=None
            data={'tx_hash_url':tx_hash_url,'protocol_clean':protocol_clean,'protocol_image_url':protocol_image_url}  
            additional_data.append(data)
        # Match data from api with data from html
        history_list_final=[]
        for each_history in history_list:
            tx_hash=each_history['tx_hash']
            tr_in=each_history['tr_in']
            tr_out=each_history['tr_out']
            tr_in_final=[]
            if tr_in:
                for each_tr in tr_in:
                    try:
                        each_tr['total_usd'] = each_tr['price']*each_tr['amount']
                    except:
                        each_tr['total_usd']=None
                    token_id=each_tr['token_id']
                    each_tr['token_name']=next((token['token_name'] for token in full_data if token['token_id'] == token_id), None)
                    tr_in_final.append(each_tr)
            tr_out_final=[]
            if tr_out:
                for each_tr in tr_out:
                    try:
                        each_tr['total_usd'] = each_tr['price']*each_tr['amount']
                    except:
                        each_tr['total_usd']=None
                    token_id=each_tr['token_id']
                    each_tr['token_name']=next((token['token_name'] for token in full_data if token['token_id'] == token_id), None)
                    tr_out_final.append(each_tr)
            each_history['tr_in']=tr_in_final
            each_history['tr_out']=tr_out_final
            each_history['tx_hash_url']=next((tx['tx_hash_url'] for tx in additional_data if tx_hash in tx['tx_hash_url']), None)
            each_history['protocol_clean']=next((tx['protocol_clean'] for tx in additional_data if tx_hash in tx['tx_hash_url']), None)
            each_history['protocol_image_url']=next((tx['protocol_image_url'] for tx in additional_data if tx_hash in tx['tx_hash_url']), None)
            history_list_final.append(each_history)
        return history_list_final

    def fetch_data(self, driver, address):
        base_search_url = 'https://debank.com/profile/{}/history'
        driver.get(base_search_url.format(address))
        print('Checking : ', address)
        if "It looks like you're checking an incorrect address" in driver.page_source:
            history_list = 'incorrect_address'
        else:
            # Implemented scraping logic here
            SEARCH_API = 'https://api.debank.com/history/list'
            response_json = self.parse_logs(driver,SEARCH_API)
            if response_json:
                history_list = self.clean_history(response_json) # filter history
                history_list = self.extract_additional_tx_data(driver,history_list)
            else:
                history_list=None
        return {'address': address, 'data': history_list}

    def close(self):
        # Stop workers
        for _ in range(self.num_workers):
            self.task_queue.put(None)
        for worker in self.workers:
            worker.join()




def my_callback(_tuple: tuple):
    monitor_id, address, data = _tuple
    print(f"Data for address {address}: {data}")

if __name__ == '__main__':

    addresses=['0x41bc7d0687e6cea57fa26da78379dfdc5627c56d','0x9d17bb55b57b31329cf01aa7017948e398b277bc','0x786694b02f1d331be540e727f1f2a697c45b57e4','0x0edefa91e99da1eddd1372c1743a63b1595fc413',
     '0x05bb279648e4e4cbcdecf2d4d6ec310999d444e7','0x65c76a684dbfd773bab8a7463e7498686bafd833','0x2fe9811e6b3cceb5c14cca6523f10ffdf4288af6',
     '0x7e4be95f871504778094060b5a12f43698cc7241','0xc8093288d89e494d1d0b41d2e598e58fe1e0eaf1','0x9d17bb55b57b31329cf01aa7017948e398b277bc']


    #addresses = ['0x4e5a83140d2a69ee421f9b00b92df9ee27d7dffa']
    #addresses=['0x41bc7d0687e6cea57fa26da78379dfdc5627c56d']

# Example usage:
    NUM_WORKERS = 1
    PAGE_VIEW_LIMIT = 10
    IS_EXIT_ON_COMPLETE = True

    debank = DebankHistoryFetcher(my_callback, NUM_WORKERS, PAGE_VIEW_LIMIT, IS_EXIT_ON_COMPLETE)
    for address in addresses:
        debank.add_task((0, address))

    # Close the DebankHistoryFetcher
    debank.close()
