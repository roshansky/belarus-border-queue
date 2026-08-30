import json
import os
import google.generativeai as genai

# 1. Настройка доступа к Gemini
# Скрипт возьмет ключ GEMINI_API_KEY, который вы только что добавили в GitHub Secrets
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Ключ GEMINI_API_KEY не найден в переменных окружения")

genai.configure(api_key=api_key)

# Используем актуальную модель 1.5 Flash (она быстрее и дешевле Pro, отлично подходит для текста)
model = genai.GenerativeModel('gemini-1.5-flash') 

# 2. Загрузка данных 
# Укажите здесь имя вашего JSON-файла, который формирует gpk_history.py
file_path = 'history.json' 

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
except FileNotFoundError:
    print(f"Файл {file_path} не найден. Проверьте путь.")
    raw_data = {}

# Для простоты передаем весь JSON. Если файл очень большой, 
# здесь нужно написать логику среза только за последние 7 дней.
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
response = model.generate_content(system_prompt)

# 5. Сохранение результата
# Упаковываем ответ в JSON, чтобы ваше Kotlin-приложение и веб-дашборд могли легко его прочитать
report_output = {
        "report_markdown": response.text
}

with open('weekly_report.json', 'w', encoding='utf-8') as f:
    json.dump(report_output, f, ensure_ascii=False, indent=2)

print("Отчет успешно сгенерирован и сохранен в weekly_report.json")
