
import json, re

with open("documents/game_data/research_unlocks.json") as f:
    text = f.read()

data = json.loads(text)

# BeltSpeed 관련 검색
def search_belt_speed(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}" if path else k
            if "belt" in k.lower() or "speed" in k.lower():
                print(f"[{new_path}] = {json.dumps(v, ensure_ascii=False)[:300]}")
            search_belt_speed(v, new_path)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            search_belt_speed(v, f"{path}[{i}]")

# 더 간단하게: 전체 텍스트에서 BeltSpeed 관련 부분 추출
for m in re.finditer("BeltSpeed|belt_speed|BeltTier", text, re.IGNORECASE):
    s = max(0, m.start()-100)
    e = min(len(text), m.end()+200)
    print(f"...{text[s:e].replace(chr(10), ' ')}...")
    print("---")

# 처음 5개 출력만
