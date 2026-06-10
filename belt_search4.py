
import json, re

with open("documents/game_data/research_unlocks.json") as f:
    data = json.load(f)

# 전체 텍스트에서 LRUGlobalSpeed 관련 부분을 더 넓게 추출
text = json.dumps(data)
for m in re.finditer(r"LRUGlobalSpeed", text):
    s = max(0, m.start()-50)
    e = min(len(text), m.end()+500)
    print(f"...{text[s:e].replace(chr(10), ' ')}...")
    print("="*60)
