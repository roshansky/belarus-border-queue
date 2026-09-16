import os
import json
import requests
from datetime import datetime

# 1. Чтение ваших данных (адаптируйте имя файла под ваш проект)
def load_queue_data():
    try:
        with open("latest_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Файл с данными не найден.")
        return None

# 2. Формирование шаблона поста
def format_post_text(data):
    # Получаем текущее время
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # Собираем текст поста
    text = f"🚗 Обстановка на границе РБ на {now}:\n\n"
    
    # ВНИМАНИЕ: Замените ключи 'brest_cars' и т.д. на те, что реально используются в вашем JSON
    text += "🔹 Брест (Тересполь):\n"
    text += f"Легковые: {data.get('brest_cars', 0)} | Автобусы: {data.get('brest_buses', 0)}\n\n"
    
    text += "🔹 Каменный Лог (Мядининкай):\n"
    text += f"Легковые: {data.get('kamlog_cars', 0)} | Грузовые: {data.get('kamlog_trucks', 0)}\n\n"
    
    text += "🔹 Бенякони (Шальчининкай):\n"
    text += f"Легковые: {data.get('benyakoni_cars', 0)} | Грузовые: {data.get('benyakoni_trucks', 0)}\n\n"
    
    text += "📊 Смотрите графики онлайн в приложении Dash Border!\n"
    text += "🌐 Сайт проекта: https://roshansky.github.io/belarus-border-queue/"
    
    return text

# 3. Отправка на публичную страницу Facebook
def post_to_facebook(message):
    page_id = os.environ.get("FB_PAGE_ID")
    token = os.environ.get("FB_PAGE_TOKEN")
    
    if not page_id or not token:
        print("Ошибка: Не найдены токены Facebook в переменных окружения.")
        return

    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    payload = {
        "message": message,
        "access_token": token
    }
    
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print(f"Пост успешно опубликован! ID: {response.json().get('id')}")
    else:
        print("Ошибка публикации:", response.text)

if __name__ == "__main__":
    queue_data = load_queue_data()
    if queue_data:
        post_message = format_post_text(queue_data)
        post_to_facebook(post_message)
