import requests

headers = {
    'content-type': 'application/json',
    'source': 'app',
    'x-debank-version': '1.3.59',
    'account': '{"random_at":1709143741,"random_id":"66d0d739bdc64beaab6dda5689260919","session_id":"b8e8803fa9b04986bb83625ab9d03c13","user_addr":"0x2e9c60b5007e49e80daccba8401375c9eafae8e8","wallet_type":"qrcode","is_verified":true}',
    'x-api-ts': '1709144376',
    'x-api-nonce': 'n_q4D7O6DIKpA5xdaRCRRKVZQ4ci8pd2baXm3qdDvF',
    'x-api-ver': 'v2',
    'x-api-sign': 'b109a0d5960e48e675f4488d70a8d75117fb8ce9d3e92fc39d52aea4e1712d67',
    'user-agent': 'okhttp/4.9.2',
}

params = {
    'user_addr': '0x41bc7d0687e6cea57fa26da78379dfdc5627c56d',
    'start_time': '1709107760',
    'page_count': '20',
}

response = requests.get('https://app-api.debank.com/history/list', params=params, headers=headers)