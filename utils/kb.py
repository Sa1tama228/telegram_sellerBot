from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from utils.plugins import tags  # ПЕРЕНЕС СПИСОК ТЕГОВ ТУДА


####################################################
# Backs

back_main_menu = InlineKeyboardMarkup().row(
    InlineKeyboardButton('⬅️ Назад в главное меню', callback_data='back_to::main_menu')
)

back_to_orders = InlineKeyboardMarkup().row(
    InlineKeyboardButton('⬅🚪 Назад к списку заказов', callback_data='back_to::orders')
)

# Backs
####################################################

####################################################
# Registration

phone_verification = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(
    KeyboardButton('✅ Подтвердить номер телефона', request_contact=True)
)

role_picker = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("💼 Я заказчик", callback_data="pick::client"),
    InlineKeyboardButton("🧑‍💻 Я исполнитель", callback_data="pick::performer"),
)

# Registration
####################################################

####################################################
# Functions


async def get_main_menu(role: str):
    markup = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🛒 Биржа заказов (все заказы)", callback_data="view_all_orders"),
        InlineKeyboardButton("👤 Мой профиль", callback_data="go::profile"),
        InlineKeyboardButton("❓ Чаво", callback_data="go::faq"),
        InlineKeyboardButton("📕 Правила сервиса", callback_data="go::rules"),
        InlineKeyboardButton("📋 Создать заказ", callback_data="create_order"),
        InlineKeyboardButton("⭐ Избранные заказы", callback_data='view_favorite_orders'),
        InlineKeyboardButton("📈 Поднять заказ", callback_data='raise_order'),
    )
    return markup


async def get_profile_menu(role: str):
    markup = InlineKeyboardMarkup(row_width=2).row(
        InlineKeyboardButton("🔁 Стать Исполнителем", callback_data="switch_role::performer")
            if role == 'client' else
        InlineKeyboardButton("🔁 Стать Заказчиком", callback_data="switch_role::client")
    ).add(
        InlineKeyboardButton("📥 Пополнить", callback_data='balance::topup'),
        InlineKeyboardButton("📤 Вывести", callback_data='balance::withdraw')
    ).row(
        InlineKeyboardButton("⚙️ Настроить профиль", callback_data='profile::settings')
    )

    return markup


def create_profile_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton('Мои заказы', callback_data='user_orders'),
        InlineKeyboardButton('⬅️ Назад в главное меню', callback_data='back_to::main_menu')
    )
    return keyboard


def create_responses_keyboard(order_id, feedbacks):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for feedback in feedbacks:
        keyboard.add(
            InlineKeyboardButton('Принять', callback_data=f'accept_response_{feedback.id}'),
            InlineKeyboardButton('Отклонить', callback_data=f'reject_response_{feedback.id}')
        )
    keyboard.add(InlineKeyboardButton('⬅️ Назад в меню', callback_data='back_to::main_menu'))
    return keyboard


def create_order_details_keyboard(order_id, is_own_order=False, is_favorite=False):
    keyboard = InlineKeyboardMarkup(row_width=1)
    if is_own_order:
        keyboard.add(
            InlineKeyboardButton('Просмотреть отклики', callback_data=f'view_responses_{order_id}')
        )
    keyboard.add(
        InlineKeyboardButton(
            'Удалить из избранного' if is_favorite else 'Добавить в избранное',
            callback_data=f'add_to_favorites_{order_id}'
        ),
        InlineKeyboardButton('⬅️ Назад к списку заказов', callback_data='back_to::orders')
    )
    if is_own_order:
        keyboard.add(
            InlineKeyboardButton('✏️ Изменить заказ', callback_data=f'edit_order_{order_id}'),
            InlineKeyboardButton('🗑️ Удалить заказ', callback_data=f'delete_order_{order_id}')
        )
    return keyboard


def create_favorite_orders_keyboard(orders, page, total_pages):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for order in orders:
        keyboard.add(InlineKeyboardButton(f"Заказ: {order.title}", callback_data=f"select_order_{order.id}"))

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton('⬅️ Назад', callback_data=f'favorite_orders_page_{page - 1}'))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton('➡️ Вперед', callback_data=f'favorite_orders_page_{page + 1}'))

    keyboard.row(*nav_buttons)
    keyboard.add(InlineKeyboardButton('⬅️ Назад в главное меню', callback_data='back_to::main_menu'))
    return keyboard


def create_orders_keyboard(orders, page, total_pages):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for order in orders:
        keyboard.add(InlineKeyboardButton(f"Заказ: {order.title}", callback_data=f"select_order_{order.id}"))

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton('⬅️ Назад', callback_data=f'page_{page - 1}'))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton('➡️ Вперед', callback_data=f'page_{page + 1}'))

    keyboard.row(*nav_buttons)
    keyboard.add(InlineKeyboardButton('⬅️ Назад в главное меню', callback_data='back_to::main_menu'))
    keyboard.add(InlineKeyboardButton("🔍 Поиск по тегам", callback_data='filter_orders'))
    return keyboard


def create_user_orders_keyboard(orders, page, total_pages):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for order in orders:
        keyboard.add(InlineKeyboardButton(f"Заказ: {order.title}", callback_data=f"select_order_{order.id}"))

    nav_buttons = []
    if total_pages >= 1:
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(' Назад', callback_data=f'user_orders_page_{page - 1}'))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton('➡️ Вперед', callback_data=f'user_orders_page_{page + 1}'))

    keyboard.row(*nav_buttons)
    keyboard.add(InlineKeyboardButton('⬅️ Назад в меню', callback_data='back_to::main_menu'))
    return keyboard

########################################################################################
# теги
########################################################################################


def create_tags_keyboard(selected_tags):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for tag_name, tag_code in tags.items():
        button_text = f"✅ {tag_name}" if tag_code in selected_tags else tag_name
        keyboard.add(InlineKeyboardButton(button_text, callback_data=f"tag::{tag_code}"))

    keyboard.add(InlineKeyboardButton('Готово', callback_data='tags_done'))
    return keyboard

# def create_order_details_keyboard(order_id, is_own_order=False):
#     keyboard = InlineKeyboardMarkup(row_width=1)
#     keyboard.add(
#         InlineKeyboardButton('Просмотреть отклики', callback_data=f'view_responses_{order_id}'),
#         InlineKeyboardButton('Добавить в избранное', callback_data=f'add_to_favorites_{order_id}'),
#         InlineKeyboardButton('⬅️ Назад к списку заказов', callback_data='back_to::orders')
#     )
#     if is_own_order:
#         keyboard.add(
#             InlineKeyboardButton('✏️ Изменить заказ', callback_data=f'edit_order_{order_id}'),
#             InlineKeyboardButton('🗑️ Удалить заказ', callback_data=f'delete_order_{order_id}')
#         )
#
#     return keyboard

# Functions
####################################################
