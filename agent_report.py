import json
import os
from google import genai

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

# 3. Промпт с жесткими временными рамками
system_prompt = f"""
Ты — ведущий эксперт-аналитик по пограничной логистике Беларуси.
Твоя цель — провести анализ очередей СТРОГО за прошедшую неделю и помочь водителям спланировать маршрут.

АНАЛИЗИРУЕМЫЙ ПЕРИОД: с {period_start} по {period_end}.

ПРАВИЛА АНАЛИЗА:
1. Анализируй ИСКЛЮЧИТЕЛЬНО события и цифры из предоставленного диапазона дат ({period_start} — {period_end}). Не упоминай старые рекорды прошлых недель и месяцев.
2. Не перечисляй сухие цифры по каждому часу — выявляй тренды (какие дни на этой неделе были самыми загруженными, в какое время очереди спадали).
3. Сравнивай пункты между собой (Польша vs Литва vs Латвия) по ситуации за эти 7 дней.
4. Дай практические рекомендации на предстоящую неделю и ближайшие выходные.

СТРУКТУРА ОТЧЕТА (используй красивый Markdown):
# 📅 Аналитический отчет за неделю ({period_start} — {period_end})
### 🚦 Главный итог недели
### 🚗 Легковые авто
### 🚌 Автобусы
### ✅ Рекомендации на предстоящую неделю

ДАННЫЕ ЗА 7 ДНЕЙ:
{compressed_data}
"""

# 4. Запрос к нейросети
print(f"Отправка данных в Gemini за период {period_start} — {period_end}...")

response = client.models.generate_content(
    model='gemini-3.5-flash',
    contents=system_prompt
)

# 5. Сохранение результата
report_output = {
    "period": f"{period_start} — {period_end}",
    "report_markdown": response.text
}

with open('weekly_report.json', 'w', encoding='utf-8') as f:
    json.dump(report_output, f, ensure_ascii=False, indent=2)

print("Отчет успешно обновлен и сохранен в weekly_report.json")
