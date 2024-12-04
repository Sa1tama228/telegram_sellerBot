import logging
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import utils.plugins as pl
from utils.rate_limiter import RateLimiter


token = pl.load().token
bot = Bot(token=token, parse_mode='HTML')
memory_storage = MemoryStorage()
dispatcher = Dispatcher(bot, storage=memory_storage)
dispatcher.middleware.setup(RateLimiter(limit=10, timeout=160))

logging.basicConfig(level=logging.INFO)