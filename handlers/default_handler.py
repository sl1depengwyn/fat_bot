from aiogram import types
from misc import dp
from . import diet


@dp.message_handler(content_types=types.ContentTypes.ANY)
async def all_other_messages(message: types.Message):
    await message.answer("Вкусно?", reply_markup=await diet.get_diet_keyboard())
