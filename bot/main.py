import json
import os, asyncio, logging

from aiogram import Dispatcher, Bot
from aiogram.types import BotCommand, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from modules.DataBase import DataBase

from modules.parsers.barona import Barona
from modules.parsers.eezy import Eezy
from modules.parsers.oikotie import Oikotie

from dotenv import load_dotenv



load_dotenv()

db = DataBase('data/database.db')
bot_main = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

CUR_DICT_LANG = {}
with open("data/langs.json", "r", encoding='utf-8') as file:
    CUR_DICT_LANG: dict = json.load(fp=file)

from modules.telegram import start


async def main_bot():
    dp = Dispatcher()

    dp.include_routers(
        start.router,
    )

    await bot_main.delete_my_commands()

    commands = [
        BotCommand(command='/start', description='Menu'),
        BotCommand(command='/help', description='Help'),
        BotCommand(command='/info', description='Info'),
        BotCommand(command='/settings', description='Settings'),
        BotCommand(command='/about', description='About'),
    ]

    await bot_main.set_my_commands(commands=commands)

    await dp.start_polling(bot_main, skip_updates=True)


async def parse_oikotie(keyword: list = '', location: str = ''):
    oikotie = Oikotie()
    await oikotie.parse_by_selenium(keyword=keyword, location=location)


async def parse_eezy(keyword='', location=''):
    eezy = Eezy()
    await eezy.parse_by_bs4(keyword=keyword, location=location)


async def parse_barona(keyword=None, location=None):
    barona_parser = Barona()
    await barona_parser.parse(keyword=keyword, location=location)


async def parsers():
    while True:
        await parse_barona()
        await parse_eezy()
        await parse_oikotie()

        users = await db.get_all_users()
        print(users)

        from modules.telegram.start import reply_parse
        for user_id in users: # ГДЕ ТО ТУТ НАДО ПРОВЕРИТЬ ПОДПИСАН ЛИ ПОЛЬЗОВАТЕЛЬ НА САЙТ, СЕЙЧАС ОТСЫЛАЮТСЯ ВСЕ ОБЪЯВЛЕНИЯ
            items_list: list = await db.get_relevant_records(user_id=user_id) # ПОЛУЧИТЬ САЙТЫ НА КОТОРЫЕ ПОДПИСАН ПОЛЬЗОВАТЕЛЬ - db.get_buttons_locked

            items_list = items_list[-20:]

            for item in items_list:
                builder = InlineKeyboardBuilder()

                builder.row(InlineKeyboardButton(text="To vacancy", url=item[4]))
                message = (f"*{item[3]}*\n"
                           f"|-🗺 {item[5]}\n"
                           f"|-🎙 language: {item[9].upper()}\n"
                           f"`{item[7]}`")

                parsed_message = await reply_parse(message)

                await bot_main.send_message(
                    chat_id=user_id,
                    text=parsed_message,
                    parse_mode="MarkdownV2",
                    reply_markup=builder.as_markup(),
                )

                await asyncio.sleep(3)
        await asyncio.sleep(60 * 10)


async def main():
    await asyncio.gather(main_bot())


if __name__ == '__main__':
    log_dir = os.path.join(f"{os.path.dirname(__file__)}/telegram_bot", 'TelegramLogs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    file_handler = logging.FileHandler(os.path.join(log_dir, 'logs_tg.log'))
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s - %(module)s - %(funcName)s  - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    try:
        asyncio.run(main())
    except KeyboardInterrupt as ex:
        print("Error: ", ex)