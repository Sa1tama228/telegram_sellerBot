# utils/rate_limiter.py
'''ВСЕ ОГРАНИЧЕНИЯ ЗА СПАМ/ФЛУД И ПРОЧУЮ ПОЕБОТУ СЮДА ПИХАТЬ'''
import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, and_
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler

from utils.models import UserRequest, Base, Orders, Users

DATABASE_URL = 'sqlite:///db.db'

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

class RateLimiter(BaseMiddleware):
    def __init__(self, limit: int = 5, timeout: int = 60):
        self.limit = limit
        self.timeout = timeout
        super(RateLimiter, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        user_id = message.from_user.id
        current_time = datetime.datetime.utcnow()
        cutoff_time = current_time - datetime.timedelta(seconds=60)

        session = Session()

        # Удаляем устаревшие записи
        session.query(UserRequest).filter(UserRequest.timestamp < cutoff_time).delete()
        session.commit()

        # Получаем количество запросов за последние 60 секунд
        recent_requests = session.query(UserRequest).filter(
            and_(UserRequest.user_id == user_id, UserRequest.timestamp >= cutoff_time)
        ).count()

        if recent_requests >= self.limit:
            await message.reply("⛔ Вы сделали слишком много запросов. Пожалуйста, подождите.")
            session.close()
            raise CancelHandler()

        # Сохраняем текущий запрос
        new_request = UserRequest(user_id=user_id, timestamp=current_time)
        session.add(new_request)
        session.commit()
        session.close()

class OrderLimiter:
    @staticmethod
    async def is_limited(user_id: int, limit: int = 3, timeout: int = 45):
        current_time = datetime.datetime.utcnow()
        cutoff_time = current_time - datetime.timedelta(seconds=60)

        session = Session()

        # Получаем количество заказов за последние 60 секунд
        recent_orders = session.query(Orders).filter(
            and_(Orders.client_id == user_id, Orders.timestamp >= cutoff_time)
        ).count()

        if recent_orders >= limit:
            # Блокируем пользователя на timeout минут
            block_until = current_time + datetime.timedelta(minutes=timeout)
            session.query(Users).filter(Users.id == user_id).update({"blocked_until": block_until})
            session.commit()
            session.close()
            return True

        session.close()
        return False

    @staticmethod
    async def is_blocked(user_id: int):
        current_time = datetime.datetime.utcnow()

        session = Session()

        user = session.query(Users).filter(Users.id == user_id).first()

        if user.blocked_until and user.blocked_until > current_time:
            session.close()
            return True

        session.close()
        return False
