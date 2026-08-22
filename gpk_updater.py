import requests
import json
import os
import time
from datetime import datetime, timedelta
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://gpk.gov.by/local/ajax/order-archive.php"
PAGE_URL = "https://gpk.gov.by/situation-at-the-border/arkhiv-ocheredey/"
JSON_FILE = "gpk_real_archive.json" 

CROSSINGS = {
    'brest': 'Брест', 'kozlovichi': 'Козловичи', 'berestovitsa': 'Берестовица', 
    'bruzgi': 'Брузги', 'stone_log': 'Каменный Лог', 'benekainys': 'Бенякони', 
    'grigorov': 'Григоровщина'
}

def load_archive():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: pass
    archive = {}
    for key in CROSSINGS.keys():
        archive[key] = {"timestamps": [], "labels": [], "buses": [], "cars": [], "trucks": []}
    return archive

def save_archive(data):
    for code in data:
        if not data[code]["timestamps"]: continue
        combined = list(zip(data[code]["timestamps"], data[code]["labels"], data[code]["trucks"], data[code]["cars"], data[code]["buses"]))
        combined.sort(key=lambda x: x[0]) 
        
        data[code]["timestamps"] = [x[0] for x in combined]
        data[code]["labels"] = [x[1] for x in combined]
        data[code]["trucks"] = [x[2] for x in combined]
        data[code]["cars"] = [x[3] for x in combined]
        data[code]["buses"] = [x[4] for x in combined]

    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def update_data():
    now = datetime.now()
    now_time = now.strftime('%H:%M:%S')
    print(f"\n[{now_time}] 🔄 Лечим архив и скачиваем свежие данные...")
    
    archive = load_archive()
    
    # --- ХИРУРГИЧЕСКАЯ ОЧИСТКА ---
    # Удаляем из архива мусор за последние 2 дня, чтобы переписать их начисто
    cutoff_date = now - timedelta(days=2)
    cutoff_ts = int(datetime(cutoff_date.year, cutoff_date.month, cutoff_date.day).timestamp() * 1000)
    
    for code in archive:
        valid_indices = [i for i, ts in enumerate(archive[code]["timestamps"]) if ts < cutoff_ts]
        archive[code]["timestamps"] = [archive[code]["timestamps"][i] for i in valid_indices]
        archive[code]["labels"] = [archive[code]["labels"][i] for i in valid_indices]
        archive[code]["trucks"] = [archive[code]["trucks"][i] for i in valid_indices]
        archive[code]["cars"] = [archive[code]["cars"][i] for i in valid_indices]
        archive[code]["buses"] = [archive[code]["buses"][i] for i in valid_indices]

    # --- СКАЧИВАЕМ ЗАНОВО ---
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": PAGE_URL
    }
    
    try: session.get(PAGE_URL, headers={"User-Agent": headers["User-Agent"]}, verify=False, timeout=5)
    except: pass

    start_date = now - timedelta(days=2)
    current_date = start_date
    
    target_crossings = list(CROSSINGS.keys())
    added_records = 0
    
    while current_date <= now:
        date_str = current_date.strftime("%d.%m.%Y")
        
        for code in target_crossings:
            payload = {'ppr': code, 'date': date_str}
            try:
                time.sleep(1.0) 
                response = session.post(API_URL, data=payload, headers=headers, verify=False, timeout=10)
                api_data = response.json()
                
                if api_data.get("isSuccess") and "ITEMS" in api_data:
                    for item in api_data["ITEMS"]:
                        time_label = item.get("NAME", "")
                        if not time_label: continue
                        
                        dt_obj = datetime.strptime(time_label, "%d.%m.%Y %H:%M")
                        
                        # САМОЕ ВАЖНОЕ: Отсекаем часы, которые еще не наступили!
                        if dt_obj > now:
                            continue
                            
                        ts = int(dt_obj.timestamp() * 1000)
                        lbl = dt_obj.strftime("%d %b, %H:%M")
                        
                        def get_val(key_type):
                            val = item.get(f"PROPERTY_{code.upper()}_OUT_{key_type}_VALUE_NUM", "0")
                            try: return int(float(val))
                            except: return 0
                                
                        archive[code]["timestamps"].append(ts)
                        archive[code]["labels"].append(lbl)
                        archive[code]["trucks"].append(get_val('G'))
                        archive[code]["cars"].append(get_val('L'))
                        archive[code]["buses"].append(get_val('A'))
                        added_records += 1
                            
            except Exception as e:
                pass
                
        current_date += timedelta(days=1)

    if added_records > 0:
        save_archive(archive)
        print(f"  ✅ Успех! Очищено от будущих нулей и добавлено актуальных замеров: {added_records}.")
    else:
        print("  ⚠️ Не удалось получить новые данные.")

if __name__ == "__main__":
    update_data()