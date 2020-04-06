import os
import logging
from telegram import Bot


class SendToTelegramHandler(logging.Handler):

    def emit(self, record):
        log_entry = self.format(record)   
        self.send_error_log_to_telegram(log_entry)

    def send_error_log_to_telegram(self, text):
        tg_bot_token = os.environ['TG_LOG_BOT_TOKEN']
        chat_id = os.environ['TG_CHAT_ID']
        bot = Bot(token=tg_bot_token)
        message_max_length = 4096

        if len(text) <= message_max_length:
            return bot.send_message(chat_id, text)

        parts = split_text_on_parts(text, message_max_length)
        for part in parts:
            bot.send_message(chat_id, part)


def split_text_on_parts(text, message_max_length):
    parts = []
    while text:
        if len(text) <= message_max_length:
            parts.append(text)
            break    
        part = text[:message_max_length]
        first_lnbr = part.rfind('\n')
        if first_lnbr != -1:
            parts.append(part[:first_lnbr])
            text = text[first_lnbr+1:]
        else:
            parts.append(part)
            text = text[message_max_length:]
    return parts