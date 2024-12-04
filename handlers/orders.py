# handlers/orders.py

from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from utils.misc import dispatcher as dp
from utils import db, kb  # noqa: F401
from utils.rate_limiter import OrderLimiter

class OrderForm(StatesGroup):
    title = State()
    description = State()
    price = State()

@dp.callback_query_handler(lambda c: c.data == 'create_order', state='*')
async def new_order_callback(cb: CallbackQuery):
    user = await db.get_user(user_id=cb.from_user.id)

    # Check if user is blocked
    if await OrderLimiter.is_blocked(user.id):
        await cb.message.reply("⛔ Вы заблокированы на 45 минут за слишком частое создание заказов.")
        return

    await OrderForm.title.set()
    await cb.message.reply("Введите заголовок заказа:")

@dp.message_handler(state=OrderForm.title)
async def process_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await OrderForm.next()
    await msg.reply("Введите описание заказа:")

@dp.message_handler(state=OrderForm.description)
async def process_description(msg: Message, state: FSMContext):
    await state.update_data(description=msg.text)
    await OrderForm.next()
    await msg.reply("Введите цену заказа:")

@dp.message_handler(state=OrderForm.price)
async def process_price(msg: Message, state: FSMContext):
    try:
        price = float(msg.text)
    except ValueError:
        await msg.reply("Цена должна быть числом. Пожалуйста, введите цену снова:")
        return

    await state.update_data(price=price)
    data = await state.get_data()

    user = await db.get_user(user_id=msg.from_user.id)

    # Check rate limit
    if await OrderLimiter.is_limited(user.id):
        await msg.reply("⛔ Вы сделали слишком много заказов. Пожалуйста, подождите 45 минут.")
        await state.finish()
        return

    await db.create_order(
        client_id=user.id,
        title=data['title'],
        description=data['description'],
        client_price=data['price']
    )

    await msg.reply("✅ Ваш заказ был успешно создан!")
    await state.finish()
