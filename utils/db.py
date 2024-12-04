from utils import models
import datetime
from sqlalchemy import select, update, or_, func, delete, text
import json
from utils.plugins import tags

async def user_exists(user_id: int = None, username: str = None) -> bool:
    if username is None and user_id is None:
        return False

    query = select(models.Users).where(or_(models.Users.username == username, models.Users.id == user_id))
    async with models.Session() as session:
        result = (await session.execute(query)).fetchone()
    return True if result else False


async def create_user(user_id: int, username: str, full_name: str, phone: str, role: str) -> models.Users:
    user = models.Users(id=user_id, username=username, full_name=full_name, phone_number=phone, role=role)
    async with models.Session.begin() as session:
        session.add(user)
        await session.commit()
    return user


async def modify_user(user_id: str = None, username: str = None, **kwargs) -> models.Users:
    exists = await user_exists(user_id=user_id, username=username)
    if not exists:
        return None
    query = update(models.Users).where(or_(models.Users.username == username, models.Users.id == user_id))
    for key, value in kwargs.items():
        query = query.values({key: value})
    async with models.Session() as session:
        await session.execute(query)
        await session.commit()
    return True


async def get_user(user_id: str = None, username: str = None) -> models.Users:
    exists = await user_exists(user_id=user_id, username=username)
    if not exists:
        return None
    query = select(models.Users).where(or_(models.Users.username == username, models.Users.id == user_id))
    async with models.Session() as session:
        result = (await session.execute(query)).fetchone()
    return result[0]


async def get_all_orders() -> list[models.Orders]:
    """вывод всех заказов"""
    async with models.Session() as session:
        result = await session.execute(select(models.Orders))
        orders = result.scalars().all()
    return orders


async def get_order_by_id(order_id: int) -> models.Orders:
    """вывести только те заказы, которые создал юзер"""
    async with models.Session() as session:
        result = await session.execute(select(models.Orders).where(models.Orders.id == order_id))
        order = result.scalar_one_or_none()
    return order


async def create_order(client_id: int, title: str, description: str, client_price: float, performer_id: int, tags: list) -> models.Orders:
    order = models.Orders(
        client_id=client_id,
        title=title,
        description=description,
        client_price=client_price,
        performer_id=performer_id,
        final_price=-1.0,
        status=0,
        tags=tags  # Save tags as a comma-separated string
    )
    async with models.Session.begin() as session:
        session.add(order)
        await session.commit()
    return order


async def get_orders_by_user(user_id: int): # аналог get_order_by_id
    query = select(models.Orders).where(models.Orders.client_id == user_id)
    async with models.Session() as session:
        result = await session.execute(query)
        return result.scalars().all()


async def raise_order(order_id: str, current_time: datetime.datetime): # поднимаем с колен заказы, а могли бы ССР
    query = update(models.Orders).where(models.Orders.id == order_id).values(last_raised=current_time,
                                                                             timestamp=current_time)
    async with models.Session() as session:
        await session.execute(query)
        await session.commit()


async def update_order_accepted(order_id: str, accepted: bool):  # принимаем или отклоняем отклик от исполнителя
    async with models.Session.begin() as session:
        await session.execute(update(models.Orders).where(models.Orders.id == order_id).values(accepted=accepted))
        await session.commit()


async def remove_from_favorites(user_id: int, order_id: str):
    query = delete(models.Favorites).where(models.Favorites.user_id == user_id, models.Favorites.order_id == order_id)
    async with models.Session.begin() as session:
        await session.execute(query)
        await session.commit()


async def update_order_status(order_id: str, status: int):  # обновляем заказ
    async with models.Session.begin() as session:
        await session.execute(update(models.Orders).where(models.Orders.id == order_id).values(status=status))
        await session.commit()


async def get_all_orders_paginated(page: int, items_per_page: int):
    query = select(models.Orders).where(models.Orders.accepted is False).order_by(
        models.Orders.timestamp.desc()).offset((page - 1) * items_per_page).limit(items_per_page)
    async with models.Session() as session:
        result = await session.execute(query)
        orders = result.scalars().all()
        total_orders = await session.scalar(
            select(func.count()).select_from(models.Orders).where(models.Orders.accepted is False))
        return orders, total_orders


async def get_favorite_orders_paginated(user_id: int, page: int, items_per_page: int):
    query = select(models.Orders).join(models.Favorites).where(models.Favorites.user_id == user_id).order_by(
        models.Orders.timestamp.desc()).offset((page - 1) * items_per_page).limit(items_per_page)
    async with models.Session() as session:
        result = await session.execute(query)
        orders = result.scalars().all()
        total_orders = await session.scalar(
            select(func.count()).select_from(models.Orders).join(models.Favorites).where(models.Favorites.user_id == user_id))
    return orders, total_orders


async def get_orders_by_user_paginated(user_id: int, page: int, items_per_page: int):
    query = select(models.Orders).where(models.Orders.client_id == user_id).order_by(
        models.Orders.timestamp.desc()).offset((page - 1) * items_per_page).limit(items_per_page)
    async with models.Session() as session:
        result = await session.execute(query)
        orders = result.scalars().all()
        total_orders = await session.scalar(
            select(func.count()).select_from(models.Orders).where(models.Orders.client_id == user_id))
    return orders, total_orders


async def get_feedback_by_id(feedback_id: str) -> models.Feedbacks: # отклик
    async with models.Session() as session:
        result = await session.execute(select(models.Feedbacks).where(models.Feedbacks.id == feedback_id))
        feedback = result.scalar_one_or_none()
    return feedback


async def create_feedback(order_id: str, performer_id: int, price: float, description: str,
                          deadline_days: int) -> models.Feedbacks:
    feedback = models.Feedbacks(
        order_id=order_id,
        performer_id=performer_id,
        price=price,
        description=description,
        deadline_days=deadline_days
    )
    async with models.Session.begin() as session:
        session.add(feedback)
        await session.commit()
    return feedback


async def get_feedbacks_by_order(order_id: str) -> list[models.Feedbacks]:
    async with models.Session() as session:
        result = await session.execute(select(models.Feedbacks).where(models.Feedbacks.order_id == order_id))
        feedbacks = result.scalars().all()
    return feedbacks


async def update_feedback_status(feedback_id: str, status: int):
    async with models.Session.begin() as session:
        await session.execute(update(models.Feedbacks).where(models.Feedbacks.id == feedback_id).values(status=status))
        await session.commit()

# Добавление заказа в избранное
async def add_to_favorites(user_id: int, order_id: str):
    favorite = models.Favorites(user_id=user_id, order_id=order_id)
    async with models.Session.begin() as session:
        session.add(favorite)
        await session.commit()

# Получение избранных заказов пользователя
async def get_favorite_orders(user_id: int) -> list[models.Orders]:
    query = select(models.Orders).join(models.Favorites).where(models.Favorites.user_id == user_id)
    async with models.Session() as session:
        result = await session.execute(query)
        orders = result.scalars().all()
    return orders

async def is_performer_feedback_exists(performer_id: int, order_id: str) -> bool:
    query = select(models.Feedbacks).where(
        models.Feedbacks.performer_id == performer_id,
        models.Feedbacks.order_id == order_id
    )
    async with models.Session() as session:
        result = await session.execute(query)
        feedback = result.scalar_one_or_none()
    return feedback is not None

async def update_order(order_id: str, **kwargs):
    query = update(models.Orders).where(models.Orders.id == order_id)
    for key, value in kwargs.items():
        query = query.values({key: value})
    async with models.Session() as session:
        await session.execute(query)
        await session.commit()


async def delete_order(order_id: str, user_id: int):
    order = await get_order_by_id(order_id)
    if not order:
        return

    # Сохранение удаленного заказа в лог
    deleted_order = models.DeletedOrders(
        id=order.id,
        title=order.title,
        description=order.description,
        client_id=order.client_id,
        client_price=order.client_price,
        performer_id=order.performer_id,
        final_price=order.final_price,
        status=order.status,
        timestamp=order.timestamp,
        last_raised=order.last_raised,
        accepted=order.accepted,
        deleted_at=datetime.datetime.utcnow()
    )
    async with models.Session.begin() as session:
        session.add(deleted_order)

    # Удаление заказа
    query = delete(models.Orders).where(models.Orders.id == order_id, models.Orders.client_id == user_id)
    async with models.Session() as session:
        await session.execute(query)
        await session.commit()


async def move_feedback_to_accepted(feedback_id: str):
    feedback = await get_feedback_by_id(feedback_id)
    accepted_feedback = models.AcceptedFeedbacks(
        id=feedback.id,
        order_id=feedback.order_id,
        performer_id=feedback.performer_id,
        price=feedback.price,
        description=feedback.description,
        deadline_days=feedback.deadline_days
    )
    async with models.Session.begin() as session:
        session.add(accepted_feedback)
        await session.execute(delete(models.Feedbacks).where(models.Feedbacks.id == feedback_id))
        await session.commit()

async def move_feedback_to_declined(feedback_id: str):
    feedback = await get_feedback_by_id(feedback_id)
    declined_feedback = models.DeclinedFeedbacks(
        id=feedback.id,
        order_id=feedback.order_id,
        performer_id=feedback.performer_id,
        price=feedback.price,
        description=feedback.description,
        deadline_days=feedback.deadline_days
    )
    async with models.Session.begin() as session:
        session.add(declined_feedback)
        await session.execute(delete(models.Feedbacks).where(models.Feedbacks.id == feedback_id))
        await session.commit()


async def get_all_orders_with_status_zero_paginated(page: int, items_per_page: int):
    query = select(models.Orders).where(models.Orders.status == 0).order_by(
        models.Orders.timestamp.desc()).offset((page - 1) * items_per_page).limit(items_per_page)
    async with models.Session() as session:
        result = await session.execute(query)
        orders = result.scalars().all()
        total_orders = await session.scalar(
            select(func.count()).select_from(models.Orders).where(models.Orders.status == 0))
        return orders, total_orders


async def get_all_orders_paginated_filtered(page: int, items_per_page: int, selected_tags: list):
    async with models.Session() as session:
        query = select(models.Orders).where(models.Orders.accepted == False).order_by(models.Orders.timestamp.desc())
        result = await session.execute(query)
        all_orders = result.scalars().all()

        # Фильтрация заказов по тегам
        filtered_orders = []
        for order in all_orders:
            order_tags = json.loads(order.tags) if order.tags else []
            if any(tag in order_tags for tag in selected_tags):
                filtered_orders.append(order)

        total_orders = len(filtered_orders)
        start = (page - 1) * items_per_page
        end = start + items_per_page
        paginated_orders = filtered_orders[start:end]

    return paginated_orders, total_orders

async def update_user_selected_tags(user_id: int, selected_tags: list):
    print(f"Сохраняем теги для пользователя {user_id}: {selected_tags}")
    query = update(models.Users).where(models.Users.id == user_id).values(selected_tags=json.dumps(selected_tags))
    async with models.Session() as session:
        await session.execute(query)
        await session.commit()

async def get_user_selected_tags(user_id: int) -> list:
    query = select(models.Users.selected_tags).where(models.Users.id == user_id)
    async with models.Session() as session:
        result = await session.execute(query)
        selected_tags = result.scalar_one_or_none()
    print(f"Полученные теги для пользователя {user_id}: {selected_tags}")
    return json.loads(selected_tags) if selected_tags else list(tags.values())
