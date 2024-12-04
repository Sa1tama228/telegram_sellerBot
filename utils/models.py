import random
import string
import asyncio
import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, func, JSON
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base


def generate_id():
	characters = string.ascii_lowercase + string.digits
	return ''.join(random.choice(characters) for _ in range(15))


Base = declarative_base()

class UserRequest(Base):
    __tablename__ = 'user_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())


class Users(Base):
	__tablename__ = 'users'

	id = Column(Integer, primary_key=True, nullable=False)
	username = Column(String, nullable=False)
	full_name = Column(String, nullable=False)
	phone_number = Column(String, nullable=False)
	role = Column(String, nullable=False, comment='client, performer')
	selected_tags = Column(JSON, nullable=True)

	balance = Column(Integer, default=0)
	balance_hold = Column(Integer, default=0)

	orders_placed = Column(Integer, default=0)
	orders_completed = Column(Integer, default=0)

	bio = Column(String, default="")
	banner = Column(String, default="")
	portfolio = Column(String, default="")

	disabled = Column(Boolean, default=False)
	blocked_until = Column(DateTime, nullable=True)


class Orders(Base):
	__tablename__ = 'orders'

	id = Column(String, primary_key=True, default=generate_id)
	title = Column(String, nullable=False)
	description = Column(String, nullable=False)
	tags = Column(String, nullable=True)

	client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
	client_price = Column(Float, nullable=False)

	performer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
	final_price = Column(Float, default=-1.0)

	status = Column(Integer, default=0,
					comment='-1 - Deleted; 0 - Waiting; 1 - Started; 2 - Working; 3 - Waiting for review; 4 - Revisions; 5 - Approved; 6 - Declined;')
	timestamp = Column(DateTime, default=datetime.datetime.utcnow)
	last_raised = Column(DateTime, default=None)

	accepted = Column(Boolean, default=False)  # Добавление колонки accepted


class Feedbacks(Base):
	__tablename__ = 'feedbacks'

	id = Column(String, primary_key=True, default=generate_id)
	order_id = Column(String, ForeignKey('orders.id'), nullable=False)
	performer_id = Column(Integer, ForeignKey('users.id'), nullable=False)

	price = Column(Float, nullable=False)
	description = Column(String, nullable=False)
	deadline_days = Column(Integer, nullable=False)

	status = Column(Integer, default=0)

class Favorites(Base):
    __tablename__ = 'favorites'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    order_id = Column(String, ForeignKey('orders.id'), nullable=False)


class DeletedOrders(Base):
    __tablename__ = 'deleted_orders'

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    client_id = Column(Integer, nullable=False)
    client_price = Column(Float, nullable=False)
    performer_id = Column(Integer, nullable=False)
    final_price = Column(Float, default=-1.0)
    status = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    last_raised = Column(DateTime, default=None)
    accepted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, default=func.now())

class AcceptedFeedbacks(Base):
    __tablename__ = 'accepted_feedbacks'

    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey('orders.id'), nullable=False)
    performer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    deadline_days = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=func.now())

class DeclinedFeedbacks(Base):
    __tablename__ = 'declined_feedbacks'

    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey('orders.id'), nullable=False)
    performer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    deadline_days = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=func.now())

engine = create_async_engine("sqlite+aiosqlite:///db.db")
Session = async_sessionmaker(autoflush=True, bind=engine, expire_on_commit=False)

async def init_models():
    async with engine.begin() as conn:
		# !!!!!!!!!!!!!! В ПРОДЕ НЕ РАСКОМЕНЧИВАТЬ!!!! ДРОПАЕТ БАЗУ ВСЮ НАХУЙ ЕБ ТВОЮ МАТЬ
        # await conn.run_sync(Base.metadata.drop_all)
		# !!!!!!!!!!!!!! В ПРОДЕ НЕ РАСКОМЕНЧИВАТЬ!!!! ДРОПАЕТ БАЗУ ВСЮ НАХУЙ ЕБ ТВОЮ МАТЬ а так хотелось(
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
	asyncio.run(init_models())