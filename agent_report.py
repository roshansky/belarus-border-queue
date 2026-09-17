import json
import os
from google import genai
from google.genai import types

# 1. Настройка доступа к Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Ключ GEMINI_API_KEY не найден в переменных окружения")

client = genai.Client(api_key=api_key)

# 2. Загрузка и фильтрация данных (строго последние 7 дней)
file_path = 'gpk_real_archive.json'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
except FileNotFoundError:
    print(f"Файл {file_path} не найден. Проверьте путь.")
    raw_data = {}

# Замеры каждые 2 часа = 12 замеров в сутки. 7 дней = 84 замера.
POINTS_PER_WEEK = 7 * 12

weekly_data = {}
period_start = ""
period_end = ""

for point_key, point_val in raw_data.items():
    labels = point_val.get("labels", [])
    count = min(len(labels), POINTS_PER_WEEK)
    
    weekly_data[point_key] = {
        "labels": labels[-count:],
        "cars": point_val.get("cars", [])[-count:],
        "buses": point_val.get("buses", [])[-count:],
        "trucks": point_val.get("trucks", [])[-count:]
    }
    
    if not period_start and labels:
        period_start = labels[-count]
        period_end = labels[-1]

compressed_data = json.dumps(weekly_data, ensure_ascii=False)

# 3. Лаконичный промпт с запретом черновиков
system_prompt = f"""
Ты — аналитик пограничных очередей Беларуси.
Сформируй предельно КРАТКИЙ и СУХОЙ отчет строго за неделю с {period_start} по {period_end}.

СТРОГИЕ ПРАВИЛА:
1. Отвечай ИСКЛЮЧИТЕЛЬНО на русском языке.
2. СРАЗУ начинай ответ с символа "#" и заголовка. Никаких черновиков, вступительных мыслей или заметок на английском!
3. Общий объем отчета — около 100-140 слов (по 1-2 коротких тезиса на пункт).
4. Только факты, пиковые цифры и время спада очередей.

СТРУКТУРА:
# 📅 Сводка за неделю ({period_start} — {period_end})
### 🚦 Главное
* (1-2 емких предложения об общем тренде недели)
### 🚗 Легковые
* (Пики в Бресте и на Литву: максимальные цифры и дни)
* (В какие дни и часы было свободнее всего)
### 🚌 Автобусы
* (Где и когда фиксировались задержки)
### 💡 Совет водителю
* (1 конкретная рекомендация по выезду)

ДАННЫЕ:
{compressed_data}
"""

# 4. Запрос к Gemini с автоматическим перебором моделей
print(f"Отправка данных в Gemini за период {period_start} — {period_end}...")

candidate_models = [
    os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
    "gemini-flash-latest",
    "gemini-3-flash"
]

response = None
for model_name in candidate_models:
    try:
        print(f"Пробуем запросить отчет через {model_name}...")
        response = client.models.generate_content(
            model=model_name,
            contents=system_prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=2048,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )
        print(f"Успех! Отчет сформирован моделью: {model_name}")
        break
    except Exception as e:
        print(f"Предупреждение: модель {model_name} вернула ошибку: {e}")

if not response:
    raise RuntimeError("Ошибка: ни одна из доступных моделей Gemini не смогла сгенерировать отчет.")

# 5. Сохранение результата
report_output = {
    "period": f"{period_start} — {period_end}",
    "report_markdown": response.text
}

with open('weekly_report.json', 'w', encoding='utf-8') as f:
    json.dump(report_output, f, ensure_ascii=False, indent=2)

print("Отчет успешно обновлен и сохранен в weekly_report.json")
