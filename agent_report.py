import json
import os
from google import genai # Обновленный импорт новой библиотеки

# 1. Настройка доступа к Gemini
# Скрипт возьмет ключ GEMINI_API_KEY из переменных окружения (секретов GitHub)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Ключ GEMINI_API_KEY не найден в переменных окружения")

# Инициализация нового клиента
client = genai.Client(api_key=api_key)

# 2. Загрузка данных 
# ВАЖНО: Убедитесь, что этот скрипт запускается после того, 
# как будет создан history.json!
file_path = 'history.json' 

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
except FileNotFoundError:
    print(f"Файл {file_path} не найден. Проверьте путь.")
    raw_data = {}

# Для простоты передаем весь JSON.
compressed_data = json.dumps(raw_data, ensure_ascii=False)

# 3. Формирование промпта
system_prompt = f"""
Ты — эксперт-аналитик по пограничной логистике. Твоя цель — помочь водителям легковых авто и автобусов выбрать оптимальный маршрут для пересечения границы Беларуси.

ПРАВИЛА АНАЛИЗА:
1. ЗАПРЕЩЕНО просто перечислять данные из JSON. Называй цифру только если это рекорд недели или важное сравнение.
2. Ищи закономерности (в какие дни очереди обычно меньше).
3. Дай четкую рекомендацию, какой пункт выбрать на ближайшие выходные.

СТРУКТУРА ОТЧЕТА (используй Markdown):
- 🚦 Главный итог
- 🚗 Легковые авто
- 🚌 Автобусы
- ✅ Рекомендация на неделю

ДАННЫЕ ЗА НЕДЕЛЮ:
{compressed_data}
"""

# 4. Запрос к нейросети
print("Отправка данных в Gemini...")

# Новый синтаксис вызова модели
response = client.models.generate_content(
    model='gemini-1.5-flash',
    contents=system_prompt
)

# 5. Сохранение результата
# Упаковываем ответ в JSON, чтобы ваше приложение могло легко его прочитать
report_output = {
        "report_markdown": response.text
}

with open('weekly_report.json', 'w', encoding='utf-8') as f:
    json.dump(report_output, f, ensure_ascii=False, indent=2)

print("Отчет успешно сгенерирован и сохранен в weekly_report.json")
