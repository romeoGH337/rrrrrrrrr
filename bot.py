import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)
import requests
from bs4 import BeautifulSoup

# Логи
logging.basicConfig(level=logging.INFO)

# Стадии
(
    SELECT_CITIES, SELECT_CATEGORIES, SET_PRICE_RANGE,
    SET_SEARCH_QUERY, SAVE_CONFIG
) = range(5)

user_data = {}

CITIES = ["Минск", "Гомель", "Могилёв", "Витебск", "Гродно", "Брест", "Бобруйск", "Барановичи"]
CATEGORIES = {
    "Авто": ["Легковые", "Мото", "Запчасти"],
    "Недвижимость": ["Квартиры", "Дома", "Комнаты"],
    "Электроника": ["Телефоны", "Компьютеры"],
    "Работа": ["Вакансии", "Резюме"]
}

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {
        "cities": [],
        "categories": [],
        "price_min": 0,
        "price_max": 1000000,
        "search_query": "",
        "config_name": ""
    }
    kb = [
        ["Выбрать города", "Меню категорий"],
        ["Цена от/до", "Поиск"],
        ["Создать конфиг", "Парсинг"]
    ]
    reply_markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    await update.message.reply_text("Привет! Выбери действие:", reply_markup=reply_markup)

# Города
async def ask_cities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [CITIES[i:i+3] for i in range(0, len(CITIES), 3)]
    buttons.append(["✅ Готово"])
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await update.message.reply_text("Выбери до 3 городов:", reply_markup=reply_markup)
    return SELECT_CITIES

async def select_cities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    city = update.message.text
    if city == "✅ Готово":
        await start(update, context)
        return ConversationHandler.END
    if city in CITIES and len(user_data[user_id]["cities"]) < 3 and city not in user_data[user_id]["cities"]:
        user_data[user_id]["cities"].append(city)
    await update.message.reply_text(f"Выбрано: {', '.join(user_data[user_id]['cities'])}")
    return SELECT_CITIES

# Категории
async def ask_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[cat] for cat in CATEGORIES.keys()] + [["✅ Назад"]]
    reply_markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    await update.message.reply_text("Выбери категорию:", reply_markup=reply_markup)
    return SELECT_CATEGORIES

async def select_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if text == "✅ Назад":
        await start(update, context)
        return ConversationHandler.END
    if text in CATEGORIES:
        subcats = CATEGORIES[text]
        kb = [[sc] for sc in subcats] + [["✅ Назад к категориям"]]
        reply_markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
        await update.message.reply_text(f"Выбери подкатегорию в '{text}':", reply_markup=reply_markup)
        return SELECT_CATEGORIES
    for main, subs in CATEGORIES.items():
        if text in subs:
            full = f"{main} / {text}"
            if full not in user_data[user_id]["categories"]:
                user_data[user_id]["categories"].append(full)
            await update.message.reply_text(f"Добавлено: {full}")
            return SELECT_CATEGORIES
    await update.message.reply_text("Неизвестная опция.")
    return SELECT_CATEGORIES

# Цена
async def ask_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введи диапазон цены: например → 100 50000")
    return SET_PRICE_RANGE

async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        pmin, pmax = map(int, update.message.text.split())
        if pmin < 0 or pmax < pmin:
            raise ValueError
        user_data[user_id]["price_min"] = pmin
        user_data[user_id]["price_max"] = pmax
        await update.message.reply_text(f"Цена: от {pmin} до {pmax}")
    except:
        await update.message.reply_text("Ошибка! Введите два числа: мин и макс.")
        return
