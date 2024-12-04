from aiogram.types import Message
from aiogram.dispatcher import FSMContext

from utils.misc import dispatcher as dp
from utils import db
from utils import kb


@dp.message_handler(commands=['start'], state='*')
async def handle_start(msg: Message, state: FSMContext):
	await state.finish()
	await msg.reply('💼', reply=False) # Просто отсылаем прикольный эмодзик с анимацией

	user = await db.get_user(user_id=msg.from_user.id)

	if not await db.user_exists(user_id=msg.from_user.id):
		# Если человека нет в базе ставим стейт и отправляем кнопку для отправки номера (жди докс)

		await state.set_state('phone_verification')
		await msg.reply_photo('https://i.imgur.com/xpaBR4N.png',
						'<b>⭐ Здравствуйте!</b>\n' \
						'Перед тем как начать, мне нужно подтвердить ваш номер телефона. Пожалуйста нажми на кнопку <i>ниже</i> чтобы продолжить.',
						reply=False,
						reply_markup=kb.phone_verification)
	else:
		# Если юзер в базе найден, выкидываем ему приветственное сообщение и главное меню бота
		# NOTE: Сюда можно еще статистику за день какую-нибудь пихнуть кстати, к примеру сколько за сегодня заказов добавлено, сколько принято и тд
		
		await msg.reply_photo('https://i.imgur.com/xpaBR4N.png',
				  		f'<b>⭐ Добро пожаловать, {msg.from_user.first_name}!</b>',
						reply=False,
						reply_markup=await kb.get_main_menu(user.role))