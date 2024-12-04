from aiogram.types import CallbackQuery

from utils.misc import dispatcher as dp
from utils import db
from utils import kb


@dp.callback_query_handler(lambda c: c.data.startswith('switch_role::'))
async def handle_switch_role(cb: CallbackQuery):
	msg = cb.message
	role = cb.data.split("::")[-1]
	role_human = '💼 Заказчик' if role == 'client' else '🧑‍💻 Исполнитель'

	await db.modify_user(user_id=cb.from_user.id, role=role)

	await msg.edit_caption(f'✅ Ваша роль была изменена на <b>{role_human}</b>',
							reply_markup=kb.back_main_menu)