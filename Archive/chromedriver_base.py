import undetected_chromedriver as uc
import json

SEARCH_API = 'https://api.debank.com/history/list'

options = uc.ChromeOptions()
caps = options.to_capabilities()
caps['goog:loggingPrefs'] = {'performance': 'ALL'}
driver = uc.Chrome(
    headless=False,
    options=options,
    desired_capabilities=caps
)

def parse_logs(logs, target_url):
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

def parse_tx(history_list):
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

def clean_history(response_json):
    try:
        history_list = response_json['data']['history_list']
        history_list = [each_row for each_row in history_list if each_row['is_scam'] != True]
    except Exception as e:
        print(e)
        history_list=None
    if history_list:
        history_list= parse_tx(history_list)
    return history_list

def fetch_history_list():
    logs_raw = driver.get_log("performance")
    logs = [json.loads(lr["message"])["message"] for lr in logs_raw]
    SEARCH_API = 'https://api.debank.com/history/list'
    response_json = parse_logs(logs, SEARCH_API)
    if response_json:
        history_list = clean_history(response_json)
        return history_list
    else:
        return None


def extract_additional_tx_data(driver,history_list):
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


driver.get('https://debank.com/profile/0x41bc7d0687e6cea57fa26da78379dfdc5627c56d/history')
history_list = fetch_history_list()    
history_list_final=extract_additional_tx_data(driver,history_list)
                    