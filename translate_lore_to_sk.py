import os
import yaml
import requests
import time

# === CONFIGURATION ===
LORE_DIR = r"c:/Users/echov/Desktop/Kódenie/Elena/lore"
API_URL = "https://api-free.deepl.com/v2/translate"  # Or use Google Translate API endpoint
API_KEY = "YOUR_DEEPL_API_KEY"  # <-- DOPLŇ SVOJ API KEY!
BATCH_SIZE = 10  # Number of files per batch
SLEEP_BETWEEN_CALLS = 1.2  # seconds (to avoid rate limits)

# === TRANSLATION FUNCTION ===
def translate_text(text, source_lang="EN", target_lang="SK"):
    if not text or not text.strip():
        return text
    data = {
        "auth_key": API_KEY,
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang
    }
    try:
        response = requests.post(API_URL, data=data)
        if response.status_code == 200:
            return response.json()["translations"][0]["text"]
        else:
            print(f"Translation error: {response.status_code} {response.text}")
            return text
    except Exception as e:
        print(f"Exception during translation: {e}")
        return text

# === YAML VALUE TRANSLATION ===
def translate_yaml_values(obj):
    if isinstance(obj, dict):
        return {k: translate_yaml_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [translate_yaml_values(i) for i in obj]
    elif isinstance(obj, str):
        # Only translate if not a variable/identifier
        if len(obj) < 2 or obj.isupper() or obj.startswith('char_') or obj.startswith('faction_'):
            return obj
        # Heuristic: skip if looks like a code/ID
        if any(c in obj for c in [":", "_", ".", "/"]):
            return obj
        # Otherwise, translate
        return translate_text(obj)
    else:
        return obj

# === MAIN BULK TRANSLATION ===
def process_all_yaml():
    all_files = []
    for root, dirs, files in os.walk(LORE_DIR):
        for file in files:
            if file.endswith('.yaml'):
                all_files.append(os.path.join(root, file))
    print(f"Found {len(all_files)} YAML files.")
    for idx, path in enumerate(all_files):
        print(f"[{idx+1}/{len(all_files)}] Processing: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
            except Exception as e:
                print(f"YAML parse error in {path}: {e}")
                continue
        translated = translate_yaml_values(data)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(translated, f, allow_unicode=True, sort_keys=False)
        time.sleep(SLEEP_BETWEEN_CALLS)
    print("\n✅ Bulk translation complete!")

if __name__ == "__main__":
    process_all_yaml()
