import os, time
from string import punctuation
from aiogram.filters.callback_data import CallbackData
from aiogram import Router, F, Bot, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, BotCommand, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from typing import Union

from main import db, bot_main, CUR_DICT_LANG
from dotenv import load_dotenv
load_dotenv()

router = Router()

class MyCallbackData(CallbackData, prefix="_"):
    param: str
@router.message(Command("start"))
@router.callback_query(F.data == "start")
async def start(clb) -> None:
    if type(clb) is Message:
        if str(clb.chat.id)[0] == '-':
            print('С группы сообщение')
            return
        chat_id = clb.chat.id
    elif type(clb) is CallbackQuery:
        chat_id = clb.message.chat.id

    await db.save_user(user_id=chat_id)
    if await db.get_user_status(user_id=chat_id) == 0:
        await settings(msg=clb)
        return

    user_language = await db.get_user_language(user_id=chat_id)

    text = CUR_DICT_LANG['start_menu_text'][user_language]

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=f'💼 {CUR_DICT_LANG['start_menu_buttons_text']['to_vacancies'][user_language]}',
        callback_data=f"prepare_vacancies")
    )
    builder.row(InlineKeyboardButton(
        text=f'👤 {CUR_DICT_LANG['start_menu_buttons_text']['support'][user_language]}',
        callback_data='help')
    )
    builder.add(InlineKeyboardButton(
        text=f'⚙️ {CUR_DICT_LANG['start_menu_buttons_text']['settings'][user_language]}',
        callback_data='settings')
    )
    builder.row(InlineKeyboardButton(
        text=f'❔ {CUR_DICT_LANG['start_menu_buttons_text']['about'][user_language]}',
        callback_data='info')
    )
    builder.add(InlineKeyboardButton(
        text=f'🔗 {CUR_DICT_LANG['start_menu_buttons_text']['more'][user_language]}',
        url='https://kanzu.fi')
    )

    clb: Message = clb
    previous_message = clb

    if type(clb) is Message:
        await bot_main.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        await previous_message.delete()
    elif type(clb) is CallbackQuery:
        await bot_main.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=clb.message.message_id,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.MARKDOWN_V2
        )


@router.callback_query(F.data == "info")
@router.message(Command("info"))
async def info(msg: Union[Message, CallbackQuery]):
    """
    Shows info about current service and options which are used in.
    In addition, it should present how to use current service,
    for what purpose and to which benefits it leads

    :return: It doesn't return any values, but texts to user such text:
    """
    user_language: str = await db.get_user_language(user_id=msg.from_user.id)

    text = CUR_DICT_LANG['info_text'][user_language]
    parsed_text = await reply_parse(text)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=f'◀️ {CUR_DICT_LANG['general_to_menu_text'][user_language]}', callback_data="start"))

    answer_method = msg if isinstance(msg, Message) else msg.message

    await answer_method.answer(
        text=parsed_text,
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    await answer_method.delete()


@router.callback_query(F.data == "settings")
@router.message(Command("settings"))
async def settings(msg: Union[Message, CallbackQuery]):
    """
    Shows short description about language selection and 3 buttons:
    - Finland
    - English
    - Russian

    :return:
    """
    language: str = await db.get_user_language(user_id=msg.from_user.id)

    text = CUR_DICT_LANG['settings_text'][language]
    parsed_text = await reply_parse(text)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='🇫🇮 Finnish', callback_data='set_finnish_lang'))
    builder.row(InlineKeyboardButton(text='🇺🇸 English', callback_data='set_english_lang'))
    builder.row(InlineKeyboardButton(text='🇷🇺Русский', callback_data='set_russian_lang'))
    builder.row(InlineKeyboardButton(
        text=f'◀️ {CUR_DICT_LANG['command_start_text'][language]}',
        callback_data="start")
    )

    answer_method = msg if isinstance(msg, Message) else msg.message
    await answer_method.answer(
        text=parsed_text,
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    await answer_method.delete()


@router.callback_query(F.data == "set_russian_lang")
async def set_russian_lang(clb: CallbackQuery):
    await db.set_user_language(user_id=clb.from_user.id, language='ru')
    return await set_lang(msg=clb)


@router.callback_query(F.data == "set_english_lang")
async def set_english_lang(clb: CallbackQuery):
    await db.set_user_language(user_id=clb.from_user.id, language='en')
    return await set_lang(msg=clb)


@router.callback_query(F.data == "set_finnish_lang")
async def set_finnish_lang(clb: CallbackQuery):
    await db.set_user_language(user_id=clb.from_user.id, language='fi')
    return await set_lang(msg=clb)


async def set_lang(msg):
    if await db.get_user_status(user_id=msg.from_user.id) == 0:
        await db.set_user_status(user_id=msg.from_user.id, status=1)
        await info(msg=msg)
    else:
        return await start(clb=msg)


@router.callback_query(F.data == "help")
@router.message(Command("help"))
async def help(msg: Union[Message, CallbackQuery]):
    """
    Shows short description about applying users issues or questions
    regarding our service.

    :return: It doesn't return any values, but texts to user such text:

    Text: example
    """
    language: str = await db.get_user_language(user_id=msg.from_user.id)

    text = CUR_DICT_LANG['help_text'][language]

    parsed_text = await reply_parse(text)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=f'◀️ {CUR_DICT_LANG['general_to_menu_text'][language]}', callback_data="start"))

    answer_method = msg if isinstance(msg, Message) else msg.message
    await answer_method.answer(
        text=parsed_text,
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    await answer_method.delete()


@router.callback_query(F.data == "prepare_vacancies")
async def prepare_vacancies(clb: CallbackQuery):
    language: str = await db.get_user_language(user_id=clb.from_user.id)

    buttons_data = ['Barona', 'Eezy', 'Oikotie'] # СЮДА НАДО ПЕРЕДАВАТЬ СПИСОК САЙТОВ НА КОТОРЫЕ ПОЛЬЗОВАТЕЛЬ ПОДПИСЫВАЕТСЯ
    # pprint(buttons_data)

    buttons_locked: list = []
    if type(clb) is CallbackQuery:
        buttons_locked = await db.get_buttons_locked(user_telegram_id=clb.message.chat.id)
    elif type(clb) is Message:
        buttons_locked = await db.get_buttons_locked(user_telegram_id=clb.chat.id)

    # pprint(buttons_locked)

    builder = InlineKeyboardBuilder()
    for index, button in enumerate(buttons_data):
        if index % 2 == 0:
            builder_state = True
        else:
            builder_state = False

        if button in buttons_locked:
            button_text = f'✅ {button}'
        else:
            button_text = f'{button}'

        callback_data = MyCallbackData(param=button).pack()
        if builder_state:
            builder.row(InlineKeyboardButton(text=button_text, callback_data=callback_data))
        else:
            builder.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    # print(buttons_locked)
    # print(type(buttons_locked))
    # print(len((buttons_locked)))
    if len(buttons_locked) > 0:
        builder.row(InlineKeyboardButton(text='💼 Вы успешно подписались! Ждите!', callback_data='start'))
    # builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='start'))

    text = """
⬇️ Из представленных организаций ниже, выберете те, в которых вы хотите получать предложения:    
    """

    if type(clb) is CallbackQuery:
        message = clb.bot.edit_message_reply_markup
        await message(
            chat_id=clb.message.chat.id,
            message_id=clb.message.message_id,
            reply_markup=builder.as_markup()
        )

        await clb.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    elif type(clb) is Message:
        previous_message = clb

        clb: Message = clb

        await clb.answer(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.MARKDOWN_V2
        )

        await previous_message.delete()


@router.callback_query(MyCallbackData.filter())
async def handle_callback(clb: types.CallbackQuery, callback_data: MyCallbackData):
    param = callback_data.param
    # print(clb.message.chat.id)
    await db.switch_buttons_locked(user_telegram_id=clb.message.chat.id, name=param)
    # await clb.message.answer(f"Button clicked with parameter: {param}")
    print(f'name:@{clb.from_user.first_name} id:{clb.message.chat.id} pressed:{param}')
    try:
        await prepare_vacancies(clb)
    except Exception as ex:
        pass


@router.callback_query(F.data == 'button_name')
async def button_name(clb) -> None:
    print(f'Нажата кнопка с названием {button_name}')
    await db.switch_buttons_locked(user_telegram_id=clb.chat.id, name=button_name)





async def reply_parse(replied_message: str) -> str:
    """
    Modifies given text into parsed text, using \\

    :param replied_message:
    :return: modified text
    """
    modified_text = ""
    for char in replied_message:
        if char in punctuation and char not in "`*_":
            modified_text += "\\" + char
        else:
            modified_text += char

    return modified_text