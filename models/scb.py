import os
import requests
import base64
import uuid
import datetime as dt

# pratomrerk
# update 2023-01-31
# ref https://developer.scb/#/documents/api-reference-index/authentication/post-oauth-token.html

class scb:

    def __init__(self, USER_AGENT):
        self.SCB_API_KEY = os.environ.get('SCB_API_KEY', '1')
        self.SCB_API_SECRET = os.environ.get('SCB_API_SECRET', '1')
        self.SCB_ACCESS_TOKEN = None
        self.USER_AGENT = USER_AGENT
        self.BASE_URL = 'https://api-sandbox.partners.scb/partners/sandbox'

    def oauth(self):
        url = f'{self.BASE_URL}/v1/oauth/token'
        self.requestUId = str(uuid.uuid1())
        headers = {
            'requestUId': self.requestUId,
            'resourceOwnerID': self.SCB_API_KEY,
            'Content-Type': 'application/json',
            'User-Agent': self.USER_AGENT,
        }
        data = {
            'applicationKey': self.SCB_API_KEY,
            'applicationSecret': self.SCB_API_SECRET,
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            print('Error: scb_oauth')
            print(response.text)
            return None

        
    def verify(self, user, slip):
        sending_bank_id = slip['sending_bank_id']
        trans_ref = slip['trans_ref']
        url = f'{self.BASE_URL}/v1/payment/billpayment/transactions/{trans_ref}?sendingBank={sending_bank_id}'
        headers = {
            'Authorization': 'Bearer ' + user['data']['accessToken'],
            'requestUId': self.requestUId,
            'resourceOwnerID': self.SCB_API_KEY,
            'Content-Type': 'application/json',
            'User-Agent': self.USER_AGENT,
        }
        print(headers)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print('Error: scb_verify')
            print(response.text)
            return None

    def verifier(self, sending_bank_id, trans_ref):
        timestamp = dt.datetime.timestamp(dt.datetime.now())

        # check expire
        if self.SCB_ACCESS_TOKEN is not None:
            user = self.SCB_ACCESS_TOKEN
            if timestamp >= user['expires']:
                self.SCB_ACCESS_TOKEN = None

        if self.SCB_ACCESS_TOKEN is None:
            user = self.oauth()
            print(user)
            if user is None:
                return None
            user['expires'] = timestamp + int(user['data']['expiresIn'])
            self.SCB_ACCESS_TOKEN = user
        
        user = self.SCB_ACCESS_TOKEN
        #print(user)
        return self.verify(user, {
            'sending_bank_id': sending_bank_id,
            'trans_ref': trans_ref
        })