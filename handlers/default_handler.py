from aiogram import types
from misc import dp


@dp.message_handler(content_types=types.ContentTypes.ANY)
async def all_other_messages(message: types.Message):
    await message.answer("Любое другое сообщение")
