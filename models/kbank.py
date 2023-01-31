import os
import requests
import base64
import uuid
import datetime as dt

# pratomrerk
# update 2023-01-31
# ref https://apiportal.kasikornbank.com/product/public/Information/Slip Verification/Try API/OAuth 2.0

class kbank:

    def __init__(self, USER_AGENT):
        self.KBANK_CONSUMER_ID = os.environ.get('KBANK_CONSUMER_ID', 'a2FzaWtvcm5iYW5rdXNlcg==')
        self.KBANK_CONSUMER_SECRET = os.environ.get('KBANK_CONSUMER_SECRET', 'a2FzaWtvcm5iYW5rcGFzc3dvcmQ=')
        self.KBANK_AUTHORIZATION = base64.b64encode(f'{self.KBANK_CONSUMER_ID}:{self.KBANK_CONSUMER_SECRET}'.encode()).decode()
        self.KBANK_TEST_MODE = os.environ.get('KBANK_TEST_MODE', '0')
        self.KBANK_ACCESS_TOKEN = None
        self.USER_AGENT = USER_AGENT
        self.BASE_URL = 'https://openapi-sandbox.kasikornbank.com'

    def oauth(self):
        url = f'{self.BASE_URL}/v2/oauth/token'
        headers = {
            'Authorization': 'Basic ' + self.KBANK_AUTHORIZATION,
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': self.USER_AGENT,
        }
        if self.KBANK_TEST_MODE == '1':
            headers['x-test-mode'] = 'true'
            headers['env-id'] = 'OAUTH2'
        data = {
            'grant_type': 'client_credentials'
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            print('Error: kbank_oauth')
            print(response.text)
            return None

        
    def verify(self, user, slip):
        url = f'{self.BASE_URL}/v1/verslip/kbank/verify'
        headers = {
            'Authorization': 'Bearer ' + user['access_token'],
            'Content-Type': 'application/json',
            'User-Agent': self.USER_AGENT,
        }
        if self.KBANK_TEST_MODE == '1':
            headers['x-test-mode'] = 'true'
        print(headers)
        rqUID = str(uuid.uuid1())
        # ISO 8601 format
        rqDt = dt.datetime.now().isoformat() + '+07:00'
        data = {
            'rqUID': rqUID,
            'rqDt': rqDt,
            'data': {
                'sendingBank' : slip['sending_bank_id'],
                'transRef' : slip['trans_ref'],
            },
        }
        print(data)
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            print('Error: kbank_verify')
            print(response.text)
            return None

    def verifier(self, sending_bank_id, trans_ref):

        timestamp = dt.datetime.timestamp(dt.datetime.now())

        # check expire
        if self.KBANK_ACCESS_TOKEN is not None:
            user = self.KBANK_ACCESS_TOKEN
            if timestamp >= user['expires']:
                self.KBANK_ACCESS_TOKEN = None

        if self.KBANK_ACCESS_TOKEN is None:
            user = self.oauth()
            if user is None:
                return None
            user['expires'] = timestamp + int(user['expires_in'])
            self.KBANK_ACCESS_TOKEN = user
        
        user = self.KBANK_ACCESS_TOKEN
        #print(user)
        return self.verify(user, {
            'sending_bank_id': sending_bank_id,
            'trans_ref': trans_ref
        })