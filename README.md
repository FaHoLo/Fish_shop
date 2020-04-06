# Fish store bot

The project was created for sales via telegram bot with CMS [Moltin](https://www.moltin.com/).

### Bot in work

![Tg example](Examples/tg_example.gif)

### Installation

1. Python3 should already be installed.

2. Use `pip` (or `pip3`, there is a conflict with Python2) to install the dependencies:
```
pip install -r requirements.txt
```
3. It is recommended to use [virtualenv/venv](https://docs.python.org/3/library/venv.html) to isolate the project.

4. Register store on [Moltin](https://www.moltin.com/), get `store id`, `client id`, `client secret` and add them to file `.env` under the names `MOLT_STORE_ID`, `MOLT_CLIENT_ID`, `MOLT_CLIENT_SECRET`. Warn: they will interview you before registering.

5. To work with Telegram you need:
    * Enable `VPN` if the messenger is blocked in your country;
    * Get `bot token` and put it in `.env` under the name `TG_BOT_TOKEN`, more about that [here](https://core.telegram.org/bots#6-botfather);
    * Get `bot token` for the bot logger required to track bot errors. Put it in `.env` under the name `TG_LOG_BOT_TOKEN`.
    * Get your `id` from `@userinfobot` and put in `.env` as `TG_CHAT_ID`

6. Get a free database on [redislabs.com](https://redislabs.com/), get the host, port and password from the database and put them in `.env` under the names `DB_HOST`, `DB_PORT` and `DB_PASSWORD`.

7. Run the file `tg_bot.py`.

### Project goals

This code is written for educational purposes on the online course for web developers [dvmn.org](https://dvmn.org/).
