import os
import redis
import logging
import log_config
import moltin_aps as molt
from textwrap import dedent
from dotenv import load_dotenv
from requests.exceptions import HTTPError

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


_database = None
tg_logger = logging.getLogger('tg_logger')

load_dotenv()
bot = Bot(token=os.environ['TG_BOT_TOKEN'])
dp = Dispatcher(bot)

CART_BUTTON = InlineKeyboardButton('Cart', callback_data='cart')
MENU_BUTTON = InlineKeyboardButton('Back to menu', callback_data='menu')
CONTACTING_MESSAGE = '''\
We will contact you shortly.
If you want to change email, send «change email»
If you want to cancel order, send «/cancel»
'''


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level='ERROR',
        handlers=[log_config.SendToTelegramHandler()]
    )
    executor.start_polling(dp)

@dp.callback_query_handler(lambda callback_query: True)
async def handle_callback_query(callback_query: types.CallbackQuery):
    await handle_user_reply(callback_query)

@dp.message_handler()
async def handle_message(message: types.Message):
    await handle_user_reply(message)

async def handle_user_reply(update):
    db = await get_database_connection()
    chat_id, user_reply = await handle_update(update)
    user_state = await get_user_state(chat_id, user_reply, db)
    states_functions = {
        'START': handle_start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': handle_email,
        'CONTACTING': handle_contacting
    }

    state_handler = states_functions[user_state]
    next_state = await state_handler(update)
    db.set(chat_id, next_state)
    tg_logger.debug(f'User «{chat_id}» state changed to {next_state}')

async def get_database_connection():
    global _database
    if _database is None:
        database_password = os.getenv('DB_PASSWORD')
        database_host = os.getenv('DB_HOST')
        database_port = os.getenv('DB_PORT')
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
        tg_logger.debug('Got new db connection')
    return _database

async def handle_update(update):
    if type(update) == types.Message:
        chat_id = f'tg-{update.chat.id}'
        user_reply = update.text
    elif type(update) == types.CallbackQuery:
        chat_id = f'tg-{update.message.chat.id}'
        user_reply = update.data
    return chat_id, user_reply

async def get_user_state(chat_id, user_reply, db):
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode('utf-8')
    return user_state

async def handle_start(message: types.Message):
    await send_menu(message)
    return 'HANDLE_MENU'

async def send_menu(message: types.Message):
    keyboard = await collect_menu_keyboard()
    await message.answer('Choose goods:', reply_markup=keyboard)
    tg_logger.debug(f'Menu was sent to {message.chat.id}')

async def collect_menu_keyboard():
    products = molt.get_all_products()
    keyboard = InlineKeyboardMarkup(row_width=2)
    for product in products:
        keyboard.insert(InlineKeyboardButton(product['name'], callback_data=product['id']))
    keyboard.add(CART_BUTTON)
    tg_logger.debug(f'Menu keyboard was collected')
    return keyboard

async def handle_menu(callback_query: types.CallbackQuery):
    if callback_query.data == 'cart':
        await send_cart(callback_query)
        await delete_bot_message(callback_query)
        return 'HANDLE_CART'

    product_info = molt.get_product_info(callback_query.data)
    image_id = product_info['relationships']['main_image']['data']['id']
    image_url = molt.get_file_info(image_id)['link']['href']
    text = dedent(f'''\
    {product_info['name']}\n
    {product_info['meta']['display_price']['with_tax']['formatted']} per kg
    {product_info['meta']['stock']['level']}kg on stock\n
    {product_info['description']}
    ''')
    keyboard = await collect_product_description_keyboard(callback_query.data)

    await callback_query.answer(text=product_info['name'])
    await bot.send_photo(callback_query.message.chat.id, image_url, caption=text, reply_markup=keyboard)
    await delete_bot_message(callback_query)
    return 'HANDLE_DESCRIPTION'
    tg_logger.debug(f'{product_info['name']} description was sent')

async def send_cart(callback_query):
    keyboard = InlineKeyboardMarkup(row_width=2).add(MENU_BUTTON)
    cart_name = f'tg-{callback_query.message.chat.id}'
    chat_id = callback_query.message.chat.id
    cart_items = molt.get_cart_items(cart_name)
    if not cart_items:
        text = 'You don\'t have any items in your cart.'
        tg_logger.debug(f'Got empty cart for {chat_id}')
    else:
        keyboard.insert(InlineKeyboardButton('Pay', callback_data='pay'))
        text, keyboard = await collect_full_cart(cart_items, cart_name, keyboard)
    await callback_query.answer('Cart')
    await bot.send_message(chat_id, text, reply_markup=keyboard)
    tg_logger.debug(f'Cart was sent to {chat_id}')

async def collect_full_cart(cart_items, cart_name, keyboard):
    text = 'In your cart:\n\n'
    for item in cart_items:
        total_price = molt.get_cart(cart_name)['meta']['display_price']['with_tax']['formatted']
        product_name = item['name']
        item_id = item['id']
        text += dedent(f'''\
            {product_name}
            {item['description']}
            {item['meta']['display_price']['with_tax']['unit']['formatted']} per kg
            {item['quantity']}kg in cart for {item['meta']['display_price']['with_tax']['value']['formatted']}\n
        ''')
        keyboard.add(InlineKeyboardButton(f'Remove {product_name}', callback_data=item_id))
    text += f'Total: {total_price}'
    tg_logger.debug(f'Cart was collected')
    return text, keyboard

async def delete_bot_message(update):
    if type(update) == types.Message:
        await bot.delete_message(update.chat.id, update.message_id)
    elif type(update) == types.CallbackQuery:
        await bot.delete_message(update.message.chat.id, update.message.message_id)
    tg_logger.debug('Previous bot message was deleted')

async def collect_product_description_keyboard(product_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton('1 kg', callback_data=f'{product_id},1'),
        InlineKeyboardButton('5 kg', callback_data=f'{product_id},5'),
        InlineKeyboardButton('10 kg', callback_data=f'{product_id},10'),
    )
    keyboard.add(MENU_BUTTON)
    keyboard.add(CART_BUTTON)
    tg_logger.debug(f'Description keyboard was collected')
    return keyboard

async def handle_description(callback_query: types.CallbackQuery):
    if callback_query.data == 'menu':
        await send_menu(callback_query.message)
        await delete_bot_message(callback_query)
        return 'HANDLE_MENU'
    elif callback_query.data == 'cart':
        await send_cart(callback_query)
        await delete_bot_message(callback_query)
        return 'HANDLE_CART'
    else:
        product_id, number_of_kilos = callback_query.data.split(',')
        molt.add_product_to_cart(f'tg-{callback_query.message.chat.id}', product_id, int(number_of_kilos))
        await callback_query.answer(f'{number_of_kilos} kg added to cart')
        return 'HANDLE_DESCRIPTION'

async def handle_cart(callback_query: types.CallbackQuery):
    if callback_query.data == 'menu':
        await send_menu(callback_query.message)
        await delete_bot_message(callback_query)
        return 'HANDLE_MENU'
    elif callback_query.data == 'pay':
        text = 'Send your email, please'
        await callback_query.answer(text)
        await bot.send_message(callback_query.message.chat.id, text)
        tg_logger.debug(f'Start payment conversation')
        return 'WAITING_EMAIL'
    else:
        molt.remove_item_from_cart(f'tg-{callback_query.message.chat.id}', callback_query.data)
        await send_cart(callback_query)
        await delete_bot_message(callback_query)
    return 'HANDLE_CART'

async def handle_email(message: types.Message):
    customer_email = message.text
    customer_id = f'tg-{message.from_user.id}'
    customer_key = f'customer_id-{customer_id}'
    customer_info = {
        'name': customer_id,
        'email': customer_email,
    }
    if await get_moltin_customer_id_from_db(customer_key):
        await update_customer_info(customer_key, customer_info)
    else:
        await create_customer(customer_key, customer_info)
    await message.answer(CONTACTING_MESSAGE)
    return 'CONTACTING'

async def get_moltin_customer_id_from_db(customer_key):
    db = await get_database_connection()
    customer_id = db.get(customer_key)
    if customer_id:
        customer_id = customer_id.decode('utf-8')
    tg_logger.debug(f'Got moltin customer id «{customer_id}» from db')
    return customer_id

async def update_customer_info(customer_key, customer_info):
    db = await get_database_connection()
    customer_id = db.get(customer_key).decode('utf-8')
    molt.update_customer_info(customer_id, customer_info)
    tg_logger.debug(f'Customer «{customer_id}» info was updated')

async def create_customer(customer_key, customer_info):
    db = await get_database_connection()
    customer_id = molt.create_customer(customer_info)['data']['id']
    db.set(customer_key, customer_id)
    tg_logger.debug(f'New customer «{customer_key}» was created')

async def handle_contacting(update):
    if type(update) == types.Message:
        state, answer = await handle_message_while_contacting(update)
        await bot.send_message(update.chat.id, answer)
        return state
    elif type(update) == types.CallbackQuery:
        await update.answer('We will contact you shortly')
        await bot.send_message(update.message.chat.id, CONTACTING_MESSAGE)
        return 'CONTACTING'

async def handle_message_while_contacting(message):
    if message.text.lower() == 'change email':
        tg_logger.debug(f'Got request for email change')
        return 'WAITING_EMAIL', 'Send your email, please'
    elif message.text == '/cancel':
        molt.delete_cart(f'tg-{message.chat.id}')
        return 'START', 'Order cancelled. Send /start to choose goods'
    else:
        tg_logger.warning(f'While conatcing got message: {message.text}')
        return 'CONTACTING', CONTACTING_MESSAGE


if __name__ == '__main__':
    main()
