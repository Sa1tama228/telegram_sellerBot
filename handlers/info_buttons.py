from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils.misc import dispatcher as dp
from utils import kb
from utils.rate_limiter import OrderLimiter
from utils import db
import datetime
import json


class OrderForm(StatesGroup):
	title = State()
	description = State()
	price = State()
	tags = State()


class FeedbackForm(StatesGroup):
	price = State()
	description = State()
	deadline_days = State()


class TagFilterForm(StatesGroup):
	tags = State()


ITEMS_PER_PAGE = 5


@dp.callback_query_handler(lambda c: c.data == 'go::faq')
async def handle_faq(cb: CallbackQuery, state: FSMContext):
	await state.finish()
	msg = cb.message
	await msg.reply(
		'<b>❓ Часто задаваемые вопросы</b>\n\n'
		'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer sagittis tempor varius. '
		'Nulla lectus sapien, sollicitudin eget nisl et, faucibus cursus ante. Aliquam vitae eros efficitur, '
		'efficitur lectus placerat, dapibus dolor. Nulla элит purus, ornare.',
		reply_markup=kb.back_main_menu,
		parse_mode='HTML'
	)
	await msg.delete()


# Existing callback query handler for `filter_orders`
@dp.callback_query_handler(lambda c: c.data == 'filter_orders')
async def filter_orders(cb: CallbackQuery, state: FSMContext):
	user_id = cb.from_user.id
	selected_tags = await db.get_user_selected_tags(user_id)
	await cb.message.reply("Выберите теги для фильтрации заказов:", reply_markup=kb.create_tags_keyboard(selected_tags))
	await TagFilterForm.tags.set()


# Обработчик для выбора тегов
@dp.callback_query_handler(lambda c: c.data.startswith('tag::'), state=TagFilterForm.tags)
async def process_tag_filter_selection(cb: CallbackQuery, state: FSMContext):
	user_id = cb.from_user.id
	tag = cb.data.split('::')[1]
	selected_tags = await db.get_user_selected_tags(user_id)

	if tag in selected_tags:
		selected_tags.remove(tag)
	else:
		selected_tags.append(tag)

	print(f"Обновленные теги для пользователя {user_id}: {selected_tags}")  # Лог обновленных тегов
	await db.update_user_selected_tags(user_id, selected_tags)
	await cb.message.edit_reply_markup(reply_markup=kb.create_tags_keyboard(selected_tags))


@dp.callback_query_handler(lambda c: c.data == 'tags_done', state=TagFilterForm.tags)
async def finalize_tag_filter(cb: CallbackQuery, state: FSMContext):
	user_id = cb.from_user.id
	selected_tags = await db.get_user_selected_tags(user_id)
	print(f"Финальные теги для пользователя {user_id}: {selected_tags}")  # Лог финальных тегов
	await cb.message.reply("Фильтрация заказов обновлена.", reply_markup=kb.back_main_menu)

	# Perform search immediately after saving tags
	page = 1
	orders, total_orders = await db.get_all_orders_paginated_filtered(page, ITEMS_PER_PAGE, selected_tags)
	total_pages = (total_orders + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

	if not orders:
		await cb.message.reply("Нет доступных заказов.", reply_markup=kb.back_main_menu)
		await state.finish()
		return

	orders_text = "<b>Список всех заказов:</b>\n\n"
	for order in orders:
		tags = json.loads(order.tags) if order.tags else []
		tags_text = ", ".join(tags)
		orders_text += f"📌 <b>Название:</b> {order.title}\n"
		orders_text += f"💵 <b>Цена:</b> {order.client_price} руб.\n"
		orders_text += f"🏷️ <b>Теги:</b> {tags_text}\n\n"

	await cb.message.reply(orders_text, reply_markup=kb.create_orders_keyboard(orders, page, total_pages), parse_mode='HTML')
	await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'go::rules')
async def handle_rules(cb: CallbackQuery, state: FSMContext):
	await state.finish()
	msg = cb.message
	await msg.reply(
		'<b>📕 Правила сервиса</b>\n\n'
		'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer sagittis tempor varius. '
		'Nullа lectus sapien, sollicitudin eget nisl et, faucibus cursus ante. Aliquam vitae eros efficitur, '
		'efficitur lectus placerat, dapibus dolor. Nulla элит purus, ornare.',
		reply_markup=kb.back_main_menu,
		parse_mode='HTML'
	)
	await msg.delete()


@dp.callback_query_handler(lambda c: c.data == 'create_order', state='*')
async def new_order_callback(cb: CallbackQuery, state: FSMContext):
	msg = cb.message
	await state.finish()  # Clear previous state
	await OrderForm.title.set()
	await msg.reply("Введите заголовок заказа:")
	await msg.delete()


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
	await OrderForm.next()
	await msg.reply("Выберите теги для заказа:", reply_markup=kb.create_tags_keyboard([]))


@dp.callback_query_handler(lambda c: c.data.startswith('tag::'), state=OrderForm.tags)
async def process_tag_selection(cb: CallbackQuery, state: FSMContext):
	tag = cb.data.split('::')[1]
	data = await state.get_data()
	selected_tags = data.get('tags', [])

	if tag in selected_tags:
		selected_tags.remove(tag)
	else:
		selected_tags.append(tag)

	await state.update_data(tags=selected_tags)
	await cb.message.edit_reply_markup(reply_markup=kb.create_tags_keyboard(selected_tags))


@dp.callback_query_handler(lambda c: c.data == 'tags_done', state=OrderForm.tags)
async def save_order_with_tags(cb: CallbackQuery, state: FSMContext):
	data = await state.get_data()
	user = await db.get_user(user_id=cb.from_user.id)
	performer_id = cb.from_user.id

	selected_tags = data.get('tags', [])

	if not selected_tags:
		await cb.message.reply("⛔Вы должны выбрать как минимум один тег для заказа.", reply_markup=kb.create_tags_keyboard(selected_tags))
		return

	if await OrderLimiter.is_limited(user.id):
		await cb.message.reply("⛔ Вы сделали слишком много заказов. Пожалуйста, подождите 45 минут.")
		await state.finish()
		return

	await db.create_order(
		client_id=user.id,
		title=data['title'],
		description=data['description'],
		client_price=data['price'],
		performer_id=performer_id,
		tags=json.dumps(selected_tags)  # Сериализация списка тегов в строку JSON
	)

	await cb.message.reply("✅ Ваш заказ был успешно создан!", reply_markup=kb.back_main_menu, parse_mode='HTML')
	await state.finish()
	await cb.message.delete()


# Updated `view_all_orders` to include tag filtering
# @dp.callback_query_handler(lambda c: c.data == 'view_all_orders' or c.data.startswith('page_'))
# async def view_all_orders(callback_query: CallbackQuery, state: FSMContext):
#     user_id = callback_query.from_user.id
#     msg = callback_query.message
#     if 'page_' in callback_query.data:
#         page = int(callback_query.data.split('_')[1])
#     else:
#         page = 1
#
#     selected_tags = await db.get_user_selected_tags(user_id)
#
#     orders, total_orders = await db.get_all_orders_paginated_filtered(page, ITEMS_PER_PAGE, selected_tags)
#     total_pages = (total_orders + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
#
#     if not orders:
#         await msg.reply("Нет доступных заказов.", reply_markup=kb.back_main_menu)
#         await msg.delete()
#         return
#
#     orders_text = "<b>Список всех заказов:</b>\n\n"
#     for order in orders:
#         orders_text += f"📌 <b>Название:</b> {order.title}\n"
#         orders_text += f"💵 <b>Цена:</b> {order.client_price} руб.\n\n"
#
#     await msg.reply(orders_text, reply_markup=kb.create_orders_keyboard(orders, page, total_pages), parse_mode='HTML')
#     await msg.delete()
@dp.callback_query_handler(lambda c: c.data == 'view_all_orders' or c.data.startswith('page_'))
async def view_all_orders(callback_query: CallbackQuery, state: FSMContext):
	user_id = callback_query.from_user.id
	msg = callback_query.message
	if 'page_' in callback_query.data:
		page = int(callback_query.data.split('_')[1])
	else:
		page = 1

	orders, total_orders = await db.get_all_orders_with_status_zero_paginated(page, ITEMS_PER_PAGE)
	total_pages = (total_orders + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

	if not orders:
		await msg.reply("Нет доступных заказов.", reply_markup=kb.back_main_menu)
		await msg.delete()
		return

	orders_text = "<b>Список всех заказов:</b>\n\n"
	for order in orders:
		tags = json.loads(order.tags) if order.tags else []
		tags_text = ", ".join(tags)
		orders_text += f"📌 <b>Название:</b> {order.title}\n"
		orders_text += f"💵 <b>Цена:</b> {order.client_price} руб.\n"
		orders_text += f"🏷️ <b>Теги:</b> {tags_text}\n\n"

	await msg.reply(orders_text, reply_markup=kb.create_orders_keyboard(orders, page, total_pages), parse_mode='HTML')
	await msg.delete()


@dp.callback_query_handler(lambda c: c.data.startswith('raise_order_'))
async def raise_order(cb: CallbackQuery):
	order_id = cb.data.split('_')[2]
	user_id = cb.from_user.id

	order = await db.get_order_by_id(order_id)

	if not order:
		await cb.message.reply("Заказ не найден.", reply_markup=kb.back_main_menu)
		await cb.message.delete()
		return

	if order.client_id != user_id:
		await cb.message.reply("Вы можете поднимать только свои заказы.", reply_markup=kb.back_main_menu)
		await cb.message.delete()
		return

	current_time = datetime.datetime.utcnow()
	if order.last_raised and (current_time - order.last_raised).total_seconds() < 3 * 3600:
		await cb.message.reply("Вы можете поднимать заказ только раз в 3 часа.", reply_markup=kb.back_main_menu)
		await cb.message.delete()
		return

	await db.raise_order(order_id, current_time)
	await cb.message.reply("✅ Ваш заказ был успешно поднят!", reply_markup=kb.back_main_menu)
	await cb.message.delete()


@dp.callback_query_handler(lambda c: c.data.startswith('accept_response_'))
async def accept_response(callback_query: CallbackQuery):
	feedback_id = callback_query.data.split('_')[-1]
	feedback = await db.get_feedback_by_id(feedback_id)
	if not feedback:
		await callback_query.message.reply("Отклик не найден.", reply_markup=kb.back_to_orders)
		await callback_query.message.delete()
		return

	order = await db.get_order_by_id(feedback.order_id)
	if not order:
		await callback_query.message.reply("Заказ не найден.", reply_markup=kb.back_to_orders)
		await callback_query.message.delete()
		return

	user_id = callback_query.from_user.id
	if order.client_id != user_id:
		await callback_query.message.reply("Вы можете принять отклик только на свои заказы.",
											reply_markup=kb.back_to_orders)
		await callback_query.message.delete()
		return

	if feedback.performer_id == user_id:
		await callback_query.message.reply("Вы не можете принять собственный отклик.", reply_markup=kb.back_to_orders)
		await callback_query.message.delete()
		return

	# Перемещение отклика в принятые
	await db.move_feedback_to_accepted(feedback_id)
	await db.update_order_status(order.id, 2)  # Обновление статуса заказа на "Working"

	# Получение информации о заказчике и исполнителе
	client = await db.get_user(user_id=order.client_id)
	performer = await db.get_user(user_id=feedback.performer_id)

	client_tag = f"@{client.username}" if client.username else client.full_name
	performer_tag = f"@{performer.username}" if performer.username else performer.full_name

	# Отправка уведомлений
	await dp.bot.send_message(client.id, f"Вы приняли отклик от {performer_tag} на заказ {order.title}.")
	await dp.bot.send_message(performer.id,
							  f"Ваш отклик на заказ {order.title} был принят. Контактные данные заказчика: {client_tag}")

	await callback_query.message.reply("Вы приняли отклик. Контактные данные отправлены обоим пользователям.",
									   reply_markup=kb.back_to_orders)
	await callback_query.message.delete()


@dp.callback_query_handler(lambda c: c.data == 'user_orders')  # или c.data.startswith('user_orders_page_'))
async def view_user_orders(callback_query: CallbackQuery):
	user_id = callback_query.from_user.id

	if 'user_orders_page_' in callback_query.data:
		page = int(callback_query.data.split('_')[-1])
	else:
		page = 1

	orders, total_orders = await db.get_orders_by_user_paginated(user_id, page, ITEMS_PER_PAGE)
	total_pages = (total_orders + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

	if not orders:
		await callback_query.message.reply("У вас нет заказов.", reply_markup=kb.create_profile_keyboard())
		return

	orders_text = "<b>Ваши заказы:</b>\n\n"
	for order in orders:
		orders_text += (
			f"🆔 <b>ID:</b> {order.id}\n"
			f"📌 <b>Название:</b> {order.title}\n"
			f"💵 <b>Цена:</b> {order.client_price} руб.\n"
			f"🔍 <b>Статус:</b> {order.status}\n"
			f"📥 <a href='view_responses_{order.id}'>Просмотреть отклики</a>\n\n"
		)

	await callback_query.message.reply(orders_text, reply_markup=kb.create_user_orders_keyboard(
		orders, page, total_pages), parse_mode='HTML')


@dp.callback_query_handler(lambda c: c.data == 'raise_order')
async def show_user_orders(cb: CallbackQuery):
	user_id = cb.from_user.id
	orders = await db.get_orders_by_user(user_id)

	if not orders:
		await cb.message.reply("У вас нет заказов для поднятия.", reply_markup=kb.back_main_menu)
		return

	orders_text = "<b>Ваши заказы:</b>\n\n"
	for order in orders:
		orders_text += f"🆔 <b>ID:</b> {order.id}\n"
		orders_text += f"📌 <b>Название:</b> {order.title}\n"
		orders_text += f"💵 <b>Цена:</b> {order.client_price} руб.\n\n"

	await cb.message.reply(orders_text, reply_markup=create_raise_orders_keyboard(orders), parse_mode='HTML')
	await cb.message.delete()


def create_raise_orders_keyboard(orders):
	keyboard = InlineKeyboardMarkup(row_width=1)
	for order in orders:
		keyboard.add(InlineKeyboardButton(f"Поднять {order.title}", callback_data=f"raise_order_{order.id}"))
	keyboard.add(InlineKeyboardButton('⬅️ Назад в главное меню', callback_data='back_to::main_menu'))
	return keyboard


@dp.callback_query_handler(lambda c: c.data.startswith('select_order_'))
async def select_order(callback_query: CallbackQuery):
	order_id = callback_query.data.split('_')[-1]
	order = await db.get_order_by_id(order_id)
	if not order:
		await callback_query.message.reply("Заказ не найден.", reply_markup=kb.back_to_orders)
		await callback_query.message.delete()
		return

	user_id = callback_query.from_user.id
	user = await db.get_user(user_id=user_id)  # Получение пользователя
	is_own_order = (order.client_id == user_id)

	# Проверка, находится ли заказ в избранном
	favorite_orders = await db.get_favorite_orders(user_id)
	is_favorite = any(fav_order.id == order_id for fav_order in favorite_orders)

	order_text = (
		f"<b>Детали заказа:</b>\n\n"
		f"🆔 <b>ID:</b> {order.id}\n"
		f"📌 <b>Название:</b> {order.title}\n"
		f"📝 <b>Описание:</b> {order.description}\n"
		f"💵 <b>Цена:</b> {order.client_price} руб.\n"
		f"🔍 <b>Статус:</b> {order.status}\n"
	)

	reply_markup = InlineKeyboardMarkup(row_width=1)
	if user.role == 'performer' and not is_own_order:
		reply_markup.add(InlineKeyboardButton("Откликнуться", callback_data=f'respond_order_{order.id}'))

	# Adding the remaining buttons
	reply_markup.inline_keyboard.extend(kb.create_order_details_keyboard(order.id, is_own_order=is_own_order, is_favorite=is_favorite).inline_keyboard)

	await callback_query.message.reply(order_text, reply_markup=reply_markup, parse_mode='HTML')
	await callback_query.message.delete()



@dp.callback_query_handler(lambda c: c.data.startswith('respond_order_'))
async def respond_order(callback_query: CallbackQuery):
	order_id = callback_query.data.split('_')[-1]
	performer_id = callback_query.from_user.id
	'''эта хуйня странно работает, прочекай пожалуйста'''

	order = await db.get_order_by_id(order_id)

	if order.client_id == performer_id:
		await callback_query.message.reply("Вы не можете откликнуться на собственный заказ.",
										   reply_markup=kb.back_main_menu)
		await callback_query.message.delete()
		return

	await FeedbackForm.price.set()
	state = dp.current_state(user=performer_id)
	async with state.proxy() as data:
		data['order_id'] = order_id
		data['performer_id'] = performer_id

	await callback_query.message.reply("Введите вашу цену за выполнение заказа:")
	await callback_query.message.delete()


@dp.message_handler(state=FeedbackForm.price)
async def process_feedback_price(message: Message, state: FSMContext):
	try:
		price = float(message.text)
	except ValueError:
		await message.reply("Цена должна быть числом. Пожалуйста, введите цену снова:")
		return

	async with state.proxy() as data:
		order_id = data['order_id']
		order = await db.get_order_by_id(order_id)
		client_price = order.client_price

		min_price = client_price * 0.8
		max_price = client_price * 1.2

		if price < min_price or price > max_price:
			await message.reply(f"Цена должна быть в пределах от {min_price:.2f} до {max_price:.2f} руб. Пожалуйста, введите цену снова:")
			return

		data['price'] = price

	await FeedbackForm.next()
	await message.reply("Введите описание того, что вы предлагаете сделать:")



@dp.message_handler(state=FeedbackForm.description)
async def process_feedback_description(message: Message, state: FSMContext):
	description = message.text
	async with state.proxy() as data:
		data['description'] = description

	await FeedbackForm.next()
	await message.reply("Введите количество дней, необходимых для выполнения заказа:")


@dp.message_handler(state=FeedbackForm.deadline_days)
async def process_feedback_deadline_days(message: Message, state: FSMContext):
	try:
		deadline_days = int(message.text)
	except ValueError:
		await message.reply("Количество дней должно быть числом. Пожалуйста, введите снова:")
		return

	async with state.proxy() as data:
		data['deadline_days'] = deadline_days

		# Сохраняем отклик
		await db.create_feedback(
			order_id=data['order_id'],
			performer_id=data['performer_id'],
			price=data['price'],
			description=data['description'],
			deadline_days=data['deadline_days']
		)

	# Получаем заказчика и отправляем уведомление
	order = await db.get_order_by_id(data['order_id'])
	customer = await db.get_user(user_id=order.client_id)
	performer = await db.get_user(user_id=data['performer_id'])

	await message.reply("Вы успешно откликнулись на заказ.", reply_markup=kb.back_main_menu)
	await state.finish()

	await dp.bot.send_message(customer.id, f"Пользователь {performer.full_name}"
										   f" откликнулся на ваш заказ {order.title} с предложением {data['price']} $"
										   f". и сроком {data['deadline_days']} дней.")


@dp.callback_query_handler(lambda c: c.data == 'back_to::orders')
async def back_to_orders(cb: CallbackQuery):
	user_id = cb.from_user.id
	page = 1

	orders, total_orders = await db.get_orders_by_user_paginated(user_id, page, ITEMS_PER_PAGE)
	total_pages = (total_orders + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

	if not orders:
		await cb.message.reply("У вас нет заказов.", reply_markup=kb.create_profile_keyboard())
		return

	orders_text = "<b>Ваши заказы:</b>\n\n"
	for order in orders:
		orders_text += f"🆔 <b>ID:</b> {order.id}\n"
		orders_text += f"📌 <b>Название:</b> {order.title}\n"
		orders_text += f"💵 <b>Цена:</b> {order.client_price} руб.\n"
		orders_text += f"🔍 <b>Статус:</b> {order.status}\n"
		orders_text += f"📥 <b><a href='view_responses_{order.id}'>Просмотреть отклики</a></b>\n\n"

	await cb.message.reply(orders_text, reply_markup=kb.create_user_orders_keyboard(
		orders, page, total_pages), parse_mode='HTML')
	await cb.message.delete()

@dp.callback_query_handler(lambda c: c.data == 'view_favorite_orders' or c.data.startswith('favorite_orders_page_'))
async def view_favorite_orders(callback_query: CallbackQuery):
	user_id = callback_query.from_user.id
	if 'favorite_orders_page_' in callback_query.data:
		page = int(callback_query.data.split('_')[-1])
	else:
		page = 1

	orders, total_orders = await db.get_favorite_orders_paginated(user_id, page, ITEMS_PER_PAGE)
	total_pages = (total_orders + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

	if not orders:
		await callback_query.message.reply("У вас нет избранных заказов.", reply_markup=kb.back_main_menu)
		await callback_query.message.delete()
		return

	orders_text = "<b>Избранные заказы:</b>\n\n"
	for order in orders:
		orders_text += f"🆔 <b>ID:</b> {order.id}\n"
		orders_text += f"📌 <b>Название:</b> {order.title}\n"
		orders_text += f"💵 <b>Цена:</b> {order.client_price} руб.\n\n"

	await callback_query.message.reply(
		orders_text,
		reply_markup=kb.create_favorite_orders_keyboard(orders, page, total_pages),
		parse_mode='HTML'
	)
	await callback_query.message.delete()


@dp.callback_query_handler(lambda c: c.data == 'go::profile')
async def handle_profile(cb: CallbackQuery):
	user_id = cb.from_user.id
	user = await db.get_user(user_id=user_id)
	if not user:
		await cb.message.reply("Пользователь не найден.", reply_markup=kb.back_main_menu)
		return

	# Получаем количество заказов пользователя
	orders, total_orders = await db.get_orders_by_user_paginated(user_id, 1, 1)  # Получаем общее количество заказов
	profile_text = (
		f"<b>Профиль пользователя:</b>\n\n"
		f"👤 <b>Имя:</b> {user.full_name}\n"
		f"📞 <b>Телефон:</b> {user.phone_number}\n"
		f"💰 <b>Баланс:</b> {user.balance} руб.\n"
		f"📋 <b>Заказы размещены:</b> {total_orders}\n"
		f"✅ <b>Заказы выполнены:</b> {user.orders_completed}\n"
	)

	await cb.message.reply(profile_text, reply_markup=kb.create_profile_keyboard(), parse_mode='HTML')


@dp.callback_query_handler(lambda c: c.data.startswith('view_responses_'))
async def view_responses(callback_query: CallbackQuery):
	user_id = callback_query.from_user.id
	order_id = callback_query.data.split('_')[-1]
	order = await db.get_order_by_id(order_id)

	# Проверка, является ли пользователь владельцем заказа
	if order.client_id != user_id:
		await callback_query.message.reply("Вы можете просматривать отклики только на свои заказы.", reply_markup=kb.back_main_menu)
		await callback_query.message.delete()
		return

	feedbacks = await db.get_feedbacks_by_order(order_id)
	if not feedbacks:
		await callback_query.message.reply("Нет откликов на этот заказ.", reply_markup=kb.back_to_orders)
		await callback_query.message.delete()
		return

	responses_text = "<b>Отклики на заказ:</b>\n\n"
	for feedback in feedbacks:
		performer = await db.get_user(user_id=feedback.performer_id)
		responses_text += (
			f"👤 <b>Исполнитель:</b> {performer.full_name}\n"
			f"💵 <b>Предложенная цена:</b> {feedback.price} руб.\n"
			f"📝 <b>Описание:</b> {feedback.description}\n"
			f"📅 <b>Срок выполнения:</b> {feedback.deadline_days} дней\n"
			f"🆔 <b>ID отклика:</b> {feedback.id}\n\n"
		)

	await callback_query.message.reply(responses_text, reply_markup=kb.create_responses_keyboard(order_id, feedbacks),
									   parse_mode='HTML')
	await callback_query.message.delete()


@dp.callback_query_handler(lambda c: c.data.startswith('user_orders_page_'))
async def view_user_orders_page(callback_query: CallbackQuery):
	user_id = callback_query.from_user.id
	page = int(callback_query.data.split('_')[-1])

	orders, total_orders = await db.get_orders_by_user_paginated(user_id, page, ITEMS_PER_PAGE)
	total_pages = (total_orders + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

	if not orders:
		await callback_query.message.reply("У вас нет заказов.", reply_markup=kb.create_profile_keyboard())
		return

	orders_text = "<b>Ваши заказы:</b>\n\n"
	for order in orders:
		orders_text += (
			f"🆔 <b>ID:</b> {order.id}\n"
			f"📌 <b>Название:</b> {order.title}\n"
			f"💵 <b>Цена:</b> {order.client_price} руб.\n"
			f"🔍 <b>Статус:</b> {order.status}\n"
			f"📥 <a href='view_responses_{order.id}'>Просмотреть отклики</a>\n\n"
		)

	await callback_query.message.edit_text(
		orders_text,
		reply_markup=kb.create_user_orders_keyboard(orders, page, total_pages),
		parse_mode='HTML'
	)

@dp.callback_query_handler(lambda c: c.data.startswith('reject_response_'))
async def reject_response(callback_query: CallbackQuery):
	feedback_id = callback_query.data.split('_')[-1]
	feedback = await db.get_feedback_by_id(feedback_id)
	if not feedback:
		await callback_query.message.reply("Отклик не найден.", reply_markup=kb.back_main_menu)
		await callback_query.message.delete()
		return

	# Перемещение отклика в отклоненные
	await db.move_feedback_to_declined(feedback_id)
	await callback_query.message.reply("Вы отклонили отклик.", reply_markup=InlineKeyboardMarkup().add(
		InlineKeyboardButton('⬅️ Назад в профиль', callback_data='back_to::profile')
	))
	await callback_query.message.delete()

	performer = await db.get_user(user_id=feedback.performer_id)
	await dp.bot.send_message(performer.id, f"Ваш отклик на заказ {feedback.description} был отклонен.")


@dp.callback_query_handler(lambda c: c.data.startswith('add_to_favorites_'))
async def add_to_favorites(callback_query: CallbackQuery):
	order_id = callback_query.data.split('_')[-1]
	user_id = callback_query.from_user.id

	favorites = await db.get_favorite_orders(user_id)
	favorite_order_ids = {order.id for order in favorites}

	if order_id in favorite_order_ids:
		await db.remove_from_favorites(user_id, order_id)
		await callback_query.message.reply("Заказ удален из избранного!", reply_markup=kb.back_to_orders)
	else:
		await db.add_to_favorites(user_id, order_id)
		await callback_query.message.reply("Заказ добавлен в избранное!", reply_markup=kb.back_to_orders)

	await callback_query.message.delete()


@dp.callback_query_handler(lambda c: c.data == 'view_favorite_orders')#  or c.data.startswith('favorite_orders_page_'))
async def view_favorite_orders_(callback_query: CallbackQuery):
	user_id = callback_query.from_user.id
	if 'favorite_orders_page_' in callback_query.data:
		page = int(callback_query.data.split('_')[-1])
	else:
		page = 1

	orders, total_orders = await db.get_favorite_orders_paginated(user_id, page, ITEMS_PER_PAGE)
	total_pages = (total_orders + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

	if not orders:
		await callback_query.message.reply("У вас нет избранных заказов.", reply_markup=kb.back_main_menu)
		await callback_query.message.delete()
		return

	orders_text = "<b>Избранные заказы:</b>\n\n"
	for order in orders:
		orders_text += f"🆔 <b>ID:</b> {order.id}\n"
		orders_text += f"📌 <b>Название:</b> {order.title}\n"
		orders_text += f"💵 <b>Цена:</b> {order.client_price} руб.\n\n"

	await callback_query.message.reply(
		orders_text,
		reply_markup=kb.create_favorite_orders_keyboard(orders, page, total_pages),
		parse_mode='HTML'
	)
	await callback_query.message.delete()

@dp.callback_query_handler(lambda c: c.data.startswith('edit_order_'))
async def edit_order(callback_query: CallbackQuery):
	order_id = callback_query.data.split('_')[-1]
	order = await db.get_order_by_id(order_id)
	if not order:
		await callback_query.message.reply("Заказ не найден.", reply_markup=kb.back_to_orders)
		await callback_query.message.delete()
		return

	await OrderForm.title.set()
	state = dp.current_state(user=callback_query.from_user.id)
	async with state.proxy() as data:
		data['order_id'] = order_id

	await callback_query.message.reply("Введите новый заголовок заказа:")
	await callback_query.message.delete()


@dp.message_handler(state=OrderForm.title)
async def process_edit_title(msg: Message, state: FSMContext):
	await state.update_data(title=msg.text)
	await OrderForm.next()
	await msg.reply("Введите новое описание заказа:")


@dp.message_handler(state=OrderForm.description)
async def process_edit_description(msg: Message, state: FSMContext):
	await state.update_data(description=msg.text)
	await OrderForm.next()
	await msg.reply("Введите новую цену заказа:")


@dp.message_handler(state=OrderForm.price)
async def process_edit_price(msg: Message, state: FSMContext):
	try:
		price = float(msg.text)
	except ValueError:
		await msg.reply("Цена должна быть числом. Пожалуйста, введите цену снова:")
		return

	async with state.proxy() as data:
		order_id = data['order_id']
		await db.update_order(order_id, title=data['title'], description=data['description'], client_price=price)

	await msg.reply("✅ Ваш заказ был успешно изменен!", reply_markup=kb.back_to_orders)
	await state.finish()
	await msg.delete()


@dp.callback_query_handler(lambda c: c.data.startswith('delete_order_'))
async def delete_order(callback_query: CallbackQuery):
	order_id = callback_query.data.split('_')[-1]
	user_id = callback_query.from_user.id

	order = await db.get_order_by_id(order_id)
	if not order:
		await callback_query.message.reply("Заказ не найден.", reply_markup=kb.back_to_orders)
		await callback_query.message.delete()
		return

	if order.client_id != user_id:
		await callback_query.message.reply("Вы можете удалить только свои заказы.", reply_markup=kb.back_to_orders)
		await callback_query.message.delete()
		return

	await db.delete_order(order_id, user_id)
	await callback_query.message.reply("✅ Ваш заказ был успешно удален!", reply_markup=kb.back_to_orders)
	await callback_query.message.delete()



@dp.callback_query_handler(lambda c: c.data == 'back_to::profile')
async def back_to_profile(cb: CallbackQuery):
	await handle_profile(cb)
