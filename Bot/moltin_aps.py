import logging

import moltin_requests


moltin_logger = logging.getLogger('moltin_loger')


def get_all_products():
    method = 'products'
    products = moltin_requests.make_get_request(method)
    moltin_logger.debug('Got all products')
    return products


def get_product_info(product_id):
    method = f'products/{product_id}'
    product_info = moltin_requests.make_get_request(method)
    moltin_logger.debug(f'Got product «{product_id}» info')
    return product_info


def get_file_info(file_id):
    method = f'files/{file_id}'
    file_info = moltin_requests.make_get_request(method)
    moltin_logger.debug(f'Got file «{file_id}» info')
    return file_info


def create_customer(customer_info):
    payload = {'data': {'type': 'customer'}}
    payload['data'].update(customer_info)
    method = 'customers'
    response = moltin_requests.make_post_request(method, payload)
    moltin_logger.debug('Customer created')
    return response


def update_customer_info(customer_id, customer_info):
    payload = {'data': {'type': 'customer'}}
    payload['data'].update(customer_info)
    method = f'customers/{customer_id}'
    response = moltin_requests.make_put_request(method, payload)
    moltin_logger.debug('Customer info updated')
    return response


def get_cart(cart_name):
    method = f'carts/{cart_name}'
    cart = moltin_requests.make_get_request(method)
    moltin_logger.debug(f'Got «{cart_name}» cart')
    return cart


def get_cart_items(cart_name):
    method = f'carts/{cart_name}/items'
    cart_items = moltin_requests.make_get_request(method)
    moltin_logger.debug(f'Got cart «{cart_name}» items')
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
    moltin_requests.make_post_request(method, payload)
    moltin_logger.debug(f'Product was added to «{cart_name}» cart')


def remove_item_from_cart(cart_name, item_id):
    method = f'carts/{cart_name}/items/{item_id}'
    response = moltin_requests.make_delete_request(method).json()
    moltin_logger.debug(f'Item {item_id} was deleted from cart')
    return response


def delete_cart(cart_name):
    method = f'carts/{cart_name}'
    response = moltin_requests.make_delete_request(method)
    moltin_logger.debug(f'Cart «{cart_name}» was deleted. Response code is: {response.status_code}')
    return response.status_code == 204
