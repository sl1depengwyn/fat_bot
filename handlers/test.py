from misc import dp, bot
from aiogram import types


@dp.message_handler(commands=['test'])
async def test(message: types.Message):
    await bot.send_message(385474228, "asd")
