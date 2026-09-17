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

# 3. Лаконичный промпт (лимит ~120-150 слов)
system_prompt = f"""
Ты — аналитик пограничных очередей Беларуси.
Сформируй предельно КРАТКИЙ и СУХОЙ отчет строго за неделю с {period_start} по {period_end}.

ЖЕСТКИЕ ТРЕБОВАНИЯ К ФОРМАТУ:
1. Общий объем отчета — СТРОГО ДО 120-150 СЛОВ.
2. Никаких приветствий, вводных рассуждений, эпитетов и шаблонных заключений.
3. Только факты, цифры пиков и конкретные дни/часы спада.
4. В каждом разделе используй не более 1-2 коротких тезисов.

СТРУКТУРА:
# 📅 Сводка за неделю ({period_start} — {period_end})
### 🚦 Главное
* (1-2 емких предложения об общем тренде и направлении с наибольшей нагрузкой)
### 🚗 Легковые
* (Пиковые дни и максимальные цифры в Бресте и на литовском направлении)
* (В какие дни/часы очереди были минимальными)
### 🚌 Автобусы
* (Где фиксировались задержки и когда было свободнее всего)
### 💡 Совет водителю
* (1 практическая рекомендация по выбору дня и времени выезда)

ДАННЫЕ:
{compressed_data}
"""

# 4. Запрос к нейросети с ограничением длины
print(f"Отправка данных в Gemini за период {period_start} — {period_end}...")

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=system_prompt,
    config=types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=600
    )
)

# 5. Сохранение результата
report_output = {
    "period": f"{period_start} — {period_end}",
    "report_markdown": response.text
}

with open('weekly_report.json', 'w', encoding='utf-8') as f:
    json.dump(report_output, f, ensure_ascii=False, indent=2)

print("Отчет успешно обновлен и сохранен в weekly_report.json")
