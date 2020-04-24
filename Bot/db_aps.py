import os
import redis
import logging
import moltin_aps


_database = None

db_logger = logging.getLogger('db_logger')


async def get_database_connection():
    global _database
    if _database is None:
        database_password = os.getenv('DB_PASSWORD')
        database_host = os.getenv('DB_HOST')
        database_port = os.getenv('DB_PORT')
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
        db_logger.debug('Got new db connection')
    return _database

async def get_moltin_customer_id(customer_key):
    db = await get_database_connection()
    customer_id = db.get(customer_key)
    if customer_id:
        customer_id = customer_id.decode('utf-8')
    db_logger.debug(f'Got moltin customer id «{customer_id}» from db')
    return customer_id

async def update_customer_info(customer_key, customer_info):
    db = await get_database_connection()
    customer_id = db.get(customer_key).decode('utf-8')
    moltin_aps.update_customer_info(customer_id, customer_info)
    db_logger.debug(f'Customer «{customer_id}» info was updated')

async def create_customer(customer_key, customer_info):
    db = await get_database_connection()
    customer_id = moltin_aps.create_customer(customer_info)['data']['id']
    db.set(customer_key, customer_id)
    db_logger.debug(f'New customer «{customer_key}» was created')
