import os
import json
import requests
from datetime import datetime

JSON_FILE = "gpk_real_archive.json"

def load_queue_data():
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: файл {JSON_FILE} не найден.")
        return None

def get_latest(data, crossing, vehicle_type):
    """Извлекает последнее актуальное значение очереди из списка"""
    try:
        values = data.get(crossing, {}).get(vehicle_type, [])
        return values[-1] if values else 0
    except (IndexError, TypeError):
        return 0

def format_post_text(data):
    # Время берем из последней метки архива или текущее
    labels = data.get('brest', {}).get('labels', [])
    time_str = labels[-1] if labels else datetime.now().strftime("%d.%m.%Y %H:%M")
    
    text = f"🚗 Обстановка на выезд из РБ ({time_str}):\n\n"
    
    # Польша
    brest_cars = get_latest(data, 'brest', 'cars')
    brest_buses = get_latest(data, 'brest', 'buses')
    text += f"🇵🇱 Брест (Тересполь):\nЛегковые: {brest_cars} | Автобусы: {brest_buses}\n\n"
    
    # Литва
    kl_cars = get_latest(data, 'stone_log', 'cars')
    kl_trucks = get_latest(data, 'stone_log', 'trucks')
    text += f"🇱🇹 Каменный Лог (Мядининкай):\nЛегковые: {kl_cars} | Грузовые: {kl_trucks}\n\n"
    
    ben_cars = get_latest(data, 'benekainys', 'cars')
    ben_trucks = get_latest(data, 'benekainys', 'trucks')
    text += f"🇱🇹 Бенякони (Шальчининкай):\nЛегковые: {ben_cars} | Грузовые: {ben_trucks}\n\n"

    # Латвия
    grig_trucks = get_latest(data, 'grigorov', 'trucks')
    grig_cars = get_latest(data, 'grigorov', 'cars')
    text += f"🇱🇻 Григоровщина (Патерниеки):\nГрузовые: {grig_trucks} | Легковые: {grig_cars}\n\n"
    
    text += "📊 Графики и история очередей:\n"
    text += "🌐 https://roshansky.github.io/belarus-border-queue/\n"
    text += "📱 Приложение Dash Border в RuStore"
    
    return text

def post_to_facebook(message):
    page_id = os.environ.get("FB_PAGE_ID")
    token = os.environ.get("FB_PAGE_TOKEN")
    
    if not page_id or not token:
        print("Ошибка: Переменные FB_PAGE_ID или FB_PAGE_TOKEN не заданы.")
        return

    url = f"https://graph.facebook.com/v21.0/{page_id}/feed"
    payload = {
        "message": message,
        "access_token": token
    }
    
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print(f"✅ Пост успешно опубликован! ID: {response.json().get('id')}")
    else:
        print(f"❌ Ошибка публикации ({response.status_code}): {response.text}")

if __name__ == "__main__":
    archive = load_queue_data()
    if archive:
        message = format_post_text(archive)
        print("Подготовленный текст:\n" + "-" * 35)
        print(message)
        print("-" * 35)
        post_to_facebook(message)
