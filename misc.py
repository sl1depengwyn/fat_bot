import logging
from aiogram import Bot, Dispatcher
import config
from aiogram.contrib.fsm_storage.memory import MemoryStorage


bot = Bot(token=config.token)
dp = Dispatcher(bot, storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)
