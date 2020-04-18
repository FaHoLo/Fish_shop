import os
import logging
import requests


moltin_logger = logging.getLogger('moltin_loger')


def get_cart(cart_name):
    method = f'carts/{cart_name}'
    return make_get_request(method)

def get_cart_items(cart_name):
    cart_items = make_get_request(f'carts/{cart_name}/items')
    moltin_logger.debug(f'Got cart {cart_name} items')
    return cart_items

def add_product_to_cart(cart_name, product_id, quantity):
    method = f'carts/{cart_name}/items'
    payload = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': quantity,

        }
    }
    make_post_request(method, payload)
    moltin_logger.debug(f'Product was added to {cart_name} cart')

def make_get_request(method, payload=None):
    headers = collect_authorization_header()
    response = requests.get(f'https://api.moltin.com/v2/{method}', params=payload, headers=headers)
    response.raise_for_status()
    # TODO Paginaton
    moltin_logger.debug(f'GET request with method {method} was sent to moltin. Response is:\n{response.json()}')
    return response.json()['data']

def collect_authorization_header():
    access_token = get_access_token()
    header = {
        'Authorization': f'Bearer {access_token}',
    }
    return header

def get_access_token():
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
    return response.json()['access_token']

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

def remove_item_from_cart(cart_name, item_id):
    method = f'carts/{cart_name}/items/{item_id}'
    response = make_delete_request(method).json()
    moltin_logger.debug(f'Item {item_id} was deleted from cart {method}. Response is:\n{response}')
    return response

def make_delete_request(method):
    headers = collect_authorization_header()
    response = requests.delete(f'https://api.moltin.com/v2/{method}', headers=headers)
    response.raise_for_status()
    moltin_logger.debug(f'DELETE request with method {method} was sent to moltin. Response is:\n{response.content}')
    return response

def delete_cart(cart_name):
    method = f'carts/{cart_name}'
    response = make_delete_request(method)
    moltin_logger.debug(f'Cart {cart_name} was deleted. Response code is:{response.status_code}')
    return response.status_code == 204
