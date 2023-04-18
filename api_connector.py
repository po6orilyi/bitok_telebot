import json
import time

import requests

from config import api_username, api_password, request_timeout_seconds


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class ApiConnector:
    api_url = 'https://api.bitok.pp.ua'

    def __init__(self):
        self.bearer_token_receiving_time = 0
        self.bearer_token = None

        self._update_bearer_token()

        if not self.bearer_token:
            raise ValueError('Bearer token wasn\'t received')
        print()
        print(self.bearer_token)
        print()

    def _set_bearer_token_receiving_time(self, ts: float) -> None:
        self.bearer_token_receiving_time = ts

    def _set_bearer_token(self, token: str) -> None:
        self.bearer_token = token

    def _update_bearer_token(self):
        url = self.api_url + "/token"
        payload = {'username': api_username, 'password': api_password}
        response = requests.post(url, data=payload, timeout=request_timeout_seconds)
        try:
            token = json.loads(response.text).get('token')
            self._set_bearer_token_receiving_time(time.time())
            self._set_bearer_token(token)
        except json.decoder.JSONDecodeError:
            print(response.text)
            raise

    def get_bearer_token(self) -> str:
        current_ts = time.time()
        if self.bearer_token_receiving_time + 55*60 < current_ts:
            self._update_bearer_token()
        print()
        print('GET BEARER TOKEN FUNCTION:')
        print(self.bearer_token)
        print()
        return self.bearer_token

    def get_transaction_info(self, transaction_id: int) -> dict:
        url = self.api_url + '/transaction'
        payload = {'Id': transaction_id}
        response = requests.get(url, params=payload, auth=BearerAuth(self.get_bearer_token()),
                                timeout=request_timeout_seconds)
        try:
            print(response.text)
            return json.loads(response.text)
        except json.decoder.JSONDecodeError:
            raise

    def search_transaction(self, account_id: str, date_start: str) -> dict:
        url = self.api_url + '/transaction/search'
        payload = {'AccountId': account_id, 'DateStart': date_start}
        response = requests.get(url, params=payload, auth=BearerAuth(self.get_bearer_token()),
                                timeout=request_timeout_seconds)
        try:
            return json.loads(response.text)
        except json.decoder.JSONDecodeError:
            raise

    def add_new_transaction(self, account_id: str, card_number: str, bank_name: str, transaction_sum: float,
                            currency: str) -> dict:
        '''
        RESPONSE:
        {
            "Id": 70,
            "AccountId": "aaa",
            "Card": "5555-888-444",
            "Bank": "bank1",
            "Summ": 33.44,
            "Currency": "USD",
            "Status": "waiting",
            "User": "",
            "DateCreate": "2023-04-07 15:57:39",
            "DateUpdate": "2023-04-07 15:57:39"
        }
        '''
        url = self.api_url + "/transaction"
        data={
            'AccountID': account_id,
            'Card': card_number,
            'Bank': bank_name,
            'Summ': transaction_sum,
            'Currency': currency
        }
        response = requests.post(url, data=json.dumps(data), auth=BearerAuth(self.get_bearer_token()),
                                 timeout=request_timeout_seconds)
        try:
            return json.loads(response.text)
        except json.decoder.JSONDecodeError:
            raise

    def update_transaction_info(self, transaction_id: int, **kwargs) -> bool:
        url = self.api_url + "/transaction"
        data={
            'Id': transaction_id
        }
        if kwargs:
            data.update(kwargs)
        response = requests.put(url, data=json.dumps(data), auth=BearerAuth(self.get_bearer_token()),
                                 timeout=request_timeout_seconds)
        if response.status_code == 200:
            return True
        return False

    def delete_transaction(self, transaction_id: int) -> bool:
        url = self.api_url + "/transaction"
        data={
            'Id': transaction_id
        }
        response = requests.delete(url, data=json.dumps(data), auth=BearerAuth(self.get_bearer_token()),
                                 timeout=request_timeout_seconds)
        if response.status_code == 200:
            return True
        return False

    def save_transactions_info_to_xlsx_file(self, account_id: str, date_from: str, date_to: str):
        url = self.api_url + "/transaction/xlsx"
        payload={
            'AccountId': account_id,
            'DateFrom': date_from,
            'DateTo': date_to
        }
        response = requests.get(url, params=payload, auth=BearerAuth(self.get_bearer_token()),
                                 timeout=request_timeout_seconds)

        filename = f'{account_id}_{date_from.replace(" ", "_")}_{date_to.replace(" ", "_")}.xlsx'
        return self._write_data_to_xlsx(filename=filename, data=response.content)

    def _write_data_to_xlsx(self, filename:str, data: bytes) -> bool:
        with open(filename, 'wb') as f:
            f.write(data)
            return True
