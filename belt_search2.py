
import json, re

with open("documents/game_data/belts_pipes_transport.json") as f:
    data = json.load(f)

# 모든 항목에서 ConveyorSpeed와 ValidResearchSpeeds 추출
for item in data:
    guid = item.get("source_guid", "???")
    snap = item.get("definition_snapshot", {})
    
    # 재귀적으로 컨베이어 스피드 관련 필드 찾음
    def find_speed(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                if "ConveyorSpeed" in k or "speed_id" in k.lower():
                    print(f"  {new_path} = {json.dumps(v)[:200]}")
                find_speed(v, new_path)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                find_speed(v, f"{path}[{i}]")
    
    # Speed 관련 텍스트 검색
    snap_str = json.dumps(snap)
    speed_hits = list(re.finditer("ConveyorSpeed|steps_per_second|ItemsPerSecond|ItemThroughput", snap_str, re.IGNORECASE))
    if speed_hits:
        print(f"=== {guid} ===")
        for m in speed_hits[:5]:
            s = max(0, m.start()-20)
            e = min(len(snap_str), m.end()+120)
            print(f"  ...{snap_str[s:e]}...")
        
        # ValidResearchSpeeds
        vr_hits = list(re.finditer("ValidResearchSpeeds", snap_str))
        for m in vr_hits[:3]:
            s = max(0, m.start()-10)
            e = min(len(snap_str), m.end()+50)
            print(f"  ValidResearchSpeeds: ...{snap_str[s:e]}...")
