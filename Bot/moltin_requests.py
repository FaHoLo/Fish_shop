import os
import logging
import requests
from datetime import datetime


moltin_logger = logging.getLogger('moltin_loger')

_access_token_info = None


def make_get_request(method, payload=None):
    headers = collect_authorization_header()
    response = requests.get(f'https://api.moltin.com/v2/{method}', params=payload, headers=headers)
    response.raise_for_status()
    # TODO Paginaton
    moltin_logger.debug(f'GET request with method {method} was sent to moltin. Response is:\n{response.json()}')
    return response.json()['data']

def collect_authorization_header():
    global _access_token_info
    if not _access_token_info or check_for_token_expired(_access_token_info['expires']):
        _access_token_info = get_access_token_info()
        
    access_token = _access_token_info['access_token']
    header = {
        'Authorization': f'Bearer {access_token}',
    }
    return header

def get_access_token_info():
    client_id = os.environ['MOLT_CLIENT_ID']
    client_secret = os.environ['MOLT_CLIENT_SECRET']
    payload = {
    'client_id': f'{client_id}',
    'client_secret': f'{client_secret}',
    'grant_type': 'client_credentials'
    }
    response = requests.post('https://api.moltin.com/oauth/access_token', data=payload)
    response.raise_for_status()
    moltin_logger.debug(f'Got moltin access token')
    return response.json()

def check_for_token_expired(token_expires):
    now_time = int(datetime.now().timestamp())
    if now_time >= token_expires:
        return True

def make_post_request(method, payload=None):
    headers = collect_authorization_header()
    headers['Content-Type'] = 'application/json'
    response = requests.post(f'https://api.moltin.com/v2/{method}', headers=headers, json=payload)
    response.raise_for_status()
    moltin_logger.debug(f'POST request with method {method} was sent to moltin. Response is:\n{response.json()}')
    return response.json()

def make_put_request(method, payload=None):
    headers = collect_authorization_header()
    headers['Content-Type'] = 'application/json'
    response = requests.put(f'https://api.moltin.com/v2/{method}', headers=headers, json=payload)
    response.raise_for_status()
    moltin_logger.debug(f'PUT request with method {method} was sent to moltin. Response is:\n{response.json()}')
    return response.json()

def make_delete_request(method):
    headers = collect_authorization_header()
    response = requests.delete(f'https://api.moltin.com/v2/{method}', headers=headers)
    response.raise_for_status()
    moltin_logger.debug(f'DELETE request with method {method} was sent to moltin. Response is:\n{response.content}')
    return response
