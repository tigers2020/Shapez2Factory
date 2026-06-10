
import json, re

with open("documents/game_data/belts_pipes_transport.json") as f:
    text = f.read()

targets = ["Throughput", "Speed", "Capacity", "ItemRate", "itemsPer", "rate", "scale"]
for t in targets:
    hits = list(re.finditer(t, text, re.IGNORECASE))
    if hits:
        for m in hits[:3]:
            start = max(0, m.start()-60)
            end = min(len(text), m.end()+80)
            snippet = text[start:end].replace("\n", " ")
            print(f"[{t}] ...{snippet}...")
    else:
        print(f"[{t}] NOT FOUND")

d = json.loads(text)
if isinstance(d, list):
    for i, item in enumerate(d[:3]):
        print(f"--- Item {i}: {item.get('source_guid', '???')} ---")
        snap = item.get("definition_snapshot", {})
        str_snap = json.dumps(snap)
        for t2 in ["Throughput", "Speed", "Capacity", "ItemRate"]:
            hits2 = list(re.finditer(t2, str_snap, re.IGNORECASE))
            if hits2:
                for m2 in hits2[:3]:
                    s2 = max(0, m2.start()-40)
                    e2 = min(len(str_snap), m2.end()+60)
                    print(f"  [{t2}] ...{str_snap[s2:e2]}...")
