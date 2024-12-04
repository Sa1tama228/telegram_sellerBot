from aiogram.types import CallbackQuery
from utils.misc import dispatcher as dp
from utils import db
from utils import kb

@dp.callback_query_handler(lambda c: c.data == 'back_to::main_menu')
async def back_to_main(cb: CallbackQuery):
    msg = cb.message
    user = await db.get_user(user_id=cb.from_user.id)

    await msg.reply(f'<b>⭐ Добро пожаловать, {cb.from_user.first_name}!</b>',
                    reply_markup=await kb.get_main_menu(user.role))