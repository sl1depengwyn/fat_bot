from misc import dp, bot
from SQLighter import SQLighter
import config
from aiogram import types
from aiogram.utils.exceptions import BotBlocked
from aiogram.dispatcher.filters.state import State, StatesGroup

admin_commands = ['разослать рассылку', 'количество активных пользователей']
spam = ''


class Admin(StatesGroup):
    initial = State()
    admin = State()
    waiting_for_spam = State()
    waiting_for_confirmation = State()


def get_commands_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for btn in admin_commands:
        keyboard.add(btn)
    return keyboard


@dp.message_handler(commands=['admin'], state='*')
async def admin_panel(message: types.Message):
    db = SQLighter(config.db)
    if db.select_single(message.from_user.id)[2]:
        await Admin.admin.set()
        await message.answer("выберите действие", reply_markup=get_commands_keyboard())
    db.close()


@dp.message_handler(state=Admin.admin, content_types=types.ContentTypes.TEXT)
async def process_callback_initial_button(message: types.Message):
    if message.text.lower() not in admin_commands:
        await message.answer("выберите действие, используя клавиатуру ниже", reply_markup=get_commands_keyboard())
    elif message.text.lower() == admin_commands[0]:
        await message.answer("напишите текст рассылки:")
        await Admin.waiting_for_spam.set()
    elif message.text.lower() == admin_commands[1]:
        await get_number_of_users(message)


async def get_number_of_users(message: types.Message):
    db = SQLighter(config.db)
    await message.answer(db.get_number_of_active_users()[0])
    db.close()


@dp.message_handler(state=Admin.waiting_for_spam, content_types=types.ContentTypes.TEXT)
async def confirmation(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add('да')
    keyboard.add('нет')
    global spam
    spam = message.text
    await message.answer("подтвердите текст рассылки:", reply_markup=keyboard)
    await Admin.waiting_for_confirmation.set()


@dp.message_handler(state=Admin.waiting_for_confirmation, content_types=types.ContentTypes.TEXT)
async def send_spam(message: types.Message):
    if message.text.lower() not in {'да', 'нет'}:
        await message.answer("подтвердите текст рассылки(да, нет)")
    elif message.text.lower() == 'да':
        db = SQLighter(config.db)
        users_all = db.select_all()
        cnt = 0
        for user in users_all:
            try:
                await bot.send_message(user[0], spam)
                cnt += 1
                db.mark_unblocked(user[0])
            except BotBlocked:
                db.mark_blocked(user[0])
        db.close()
        await message.answer("сообщений отправлено: {}".format(cnt), reply_markup=get_commands_keyboard())
        await Admin.admin.set()
    elif message.text.lower() == 'нет':
        await message.answer("напишите текст рассылки:")
        await Admin.waiting_for_spam.set()
