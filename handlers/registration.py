from aiogram.types import Message, ContentType, CallbackQuery
from aiogram.dispatcher import FSMContext

from utils.misc import dispatcher as dp
from utils import db
from utils import kb


@dp.message_handler(content_types=ContentType.CONTACT, state='phone_verification')
async def hanle_phone_verification(msg: Message, state: FSMContext):
	phone_number = msg.contact.phone_number

	await state.set_state('role_picker')
	await state.set_data({"phone": phone_number})

	await msg.reply('<b>✅ Ваш номер телефона был подтвержден!</b>', reply=False)
	await msg.reply('<b>❓ Пожалуйста, укажите кем вы являетесь:</b>',
					reply=False,
					reply_markup=kb.role_picker)


@dp.callback_query_handler(state='role_picker')
async def handle_role_picker(cb: CallbackQuery, state: FSMContext):
	msg = cb.message
	role = cb.data.split("::")[-1]
	role_human = '💼 Заказчик' if role == 'client' else '🧑‍💻 Исполнитель'
	data = await state.get_data()
	await state.finish()

	await db.create_user(cb.from_user.id,
						cb.from_user.username,
						cb.from_user.full_name,
						data.get('phone'),
						role)

	await msg.reply(f'<b>💎 Вы выбрали роль <i>{role_human}</i></b>', reply=False)
	await msg.reply_photo('https://i.imgur.com/xpaBR4N.png',
						f'<b>⭐ Добро пожаловать, {cb.from_user.first_name}!</b>',
						reply=False,
						reply_markup=await kb.get_main_menu(role))