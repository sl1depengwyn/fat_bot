from aiogram import types
from misc import dp
from . import diet
from . import admin


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await diet.initial_step(message)


@dp.message_handler(commands=['admin'])
async def cmd_start(message: types.Message):
    await admin.admin_panel(message)
