"""Build locale/ko/LC_MESSAGES/django.po, djangojs.po and matching .mo files (no GNU gettext)."""

# ruff: noqa: E501 — long English/Korean msgids and msgstrs in KO dict
from __future__ import annotations

import re
from pathlib import Path

import polib  # type: ignore[import-untyped]

BASE = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = BASE / "django_apps" / "web" / "templates"
PO_PATH = BASE / "locale" / "ko" / "LC_MESSAGES" / "django.po"
MO_PATH = BASE / "locale" / "ko" / "LC_MESSAGES" / "django.mo"
PO_JS_PATH = BASE / "locale" / "ko" / "LC_MESSAGES" / "djangojs.po"
MO_JS_PATH = BASE / "locale" / "ko" / "LC_MESSAGES" / "djangojs.mo"
JS_STATIC_ROOT = BASE / "django_apps" / "web" / "static" / "web" / "js"

# Manual overrides for Korean (fallback: English preserved).
KO: dict[str, str] = {
    # Nav / chrome
    "shapez2 planner": "shapez2 planner",
    "Primary navigation": "메인 메뉴",
    "Home": "홈",
    "Gallery": "갤러리",
    "Demo": "데모",
    "Solver": "솔버",
    "Pattern Lab": "패턴 랩",
    "Macro catalog": "매크로 목록",
    "Support": "후원",
    "Logout": "로그아웃",
    "Login": "로그인",
    "Sign up": "회원가입",
    "Language": "언어",
    "Account": "계정",
    # Footer
    "v0.1.0 scaffold": "v0.1.0 초기 버전",
    "GitHub · Shapez2Factory": "GitHub · Shapez2Factory",
    "Not affiliated with the official game; fan tooling for planning and analysis.": (
        "공식 작품과 무관한 팬 메이드 도구입니다. 공장 설계와 숫자 계산을 돕습니다."
    ),
    # Support
    "shapez2 planner - Support": "shapez2 planner · 후원",
    "to show support links here.": "을 켜 두면 아래에 후원 링크가 나타납니다.",
    # Home
    "shapez2 planner - Factory console": "shapez2 planner · 팩토리 콘솔",
    "Shapez 2 header art": "Shapez 2 헤더 일러스트",
    "Quick Solver": "퀵 솔버",
    "Open solver page": "솔버로 이동",
    "MVP": "MVP",
    "Quick solver shape preview": "도형 코드 미리보기",
    "Target shape code": "목표 도형 코드",
    "e.g. CuRuSuWu or SuSuSuSu": "예: CuRuSuWu, SuSuSuSu",
    "Shape preview": "도형 미리보기",
    "Original": "원본",
    "Layer": "레이어",
    "Quadrant": "사분면",
    "shapez 2 planner / solver / production stats / miner calculator": (
        "shapez 2 planner · 솔버 · 생산 분석 · 채굴 계산"
    ),
    "Solve Shapez 2 production chains.": "Shapez 2 공장 라인을 여기서 설계해 보세요.",
    "Shapez 2 box art": "Shapez 2 패키지 아트",
    "Shape Solver": "도형 솔버",
    "Find operation sequences to reach target shapes.": "목표 도형까지 어떤 공정을 거치면 되는지 짚어 줍니다.",
    "Production Planner": "생산 플래너",
    "Derive required inputs per minute from target output rate.": (
        "목표 생산량에서 분당 들어와야 할 재료를 역산합니다."
    ),
    "Miner Calculator": "채굴기 계산",
    "Estimate miners and machine load from raw demand.": (
        "원료 수요만 넣어도 채굴기 대수와 설비 부하를 가늠해 볼 수 있습니다."
    ),
    "Visual Graph": "그래프 보기",
    "Inspect recipes, bottlenecks, and waste in a flow graph.": (
        "플로우 그래프에서 레시피·병목·손실을 한 번에 훑습니다."
    ),
    # Solver
    "shapez2 planner | Shape solver": "shapez2 planner · 도형 솔버",
    "Shape solver": "도형 솔버",
    "Target": "목표",
    "Shape code": "도형 코드",
    "e.g. CuRuSuWu": "예: CuRuSuWu",
    "Apply": "적용",
    "Recipe graph": "레시피 그래프",
    "Solver Graph": "솔버 그래프",
    "POST solve": "POST 솔브",
    "Materialized graph": "수량 반영 그래프",
    "Enter a target shape and apply it to request a solver graph.": (
        "목표 도형 코드를 넣고 적용하면 솔버 그래프를 불러옵니다."
    ),
    "Current target:": "현재 목표:",
    "Live preview": "실시간 미리보기",
    "Matches the code in the target field (debounced).": (
        "위 목표 칸의 코드를 따라갑니다(입력 후 잠깐 멈추면 갱신)."
    ),
    # Pattern lab
    "shapez2 planner | Pattern Lab": "shapez2 planner · 패턴 랩",
    "Inspect pattern signatures and macro catalog candidates.": (
        "패턴 시그니처와 매크로 후보가 맞는지 가볍게 점검합니다."
    ),
    "e.g. CuRuSuSu or RcCuRcCu": "예: CuRuSuSu 또는 RcCuRcCu",
    "Analyze": "분석",
    "Analysis failed": "분석 실패",
    "canonical:": "정규 코드:",
    "Signature": "시그니처",
    "Canonical": "정규형",
    "Inventory goal": "인벤토리 목표",
    "Inventory signature": "인벤토리 시그니처",
    "Target batch": "목표 배치",
    "n/a": "해당 없음",
    "Symbol map": "기호 매핑",
    "Rotation variants": "회전 패턴",
    "Macro candidates": "매크로 후보",
    "Macro": "매크로",
    "Cost": "비용",
    "Dry-run": "드라이런",
    "Step source": "단계 출처",
    "Primitive steps": "기본 단계",
    "ready": "준비됨",
    "not generated": "아직 없음",
    "graph": "그래프",
    "DB": "DB",
    "Steps from graph_document": "graph_document 기준 단계",
    "Steps from database": "DB 단계",
    "No step metadata is registered for this macro.": (
        "이 매크로에는 단계 메타데이터가 아직 없습니다."
    ),
    "Batch source counts": "배치 소스 개수",
    "No batch source count could be computed.": "배치 소스 개수를 계산할 수 없습니다.",
    # Staff macro
    "shapez2 planner | Macro catalog (staff)": "shapez2 planner · 매크로 목록(스태프)",
    "Staff": "스태프",
    "Macro pattern catalog": "매크로 패턴 목록",
    "New recipe": "새 레시피",
    "Code": "코드",
    "Name": "이름",
    "Family": "패밀리",
    "Strategy": "전략",
    "Active": "활성",
    "Actions": "작업",
    "yes": "예",
    "no": "아니오",
    "Graph": "그래프",
    "Edit": "편집",
    "Delete": "삭제",
    "No macro recipes yet — create one.": "아직 매크로 레시피가 없습니다. 새로 만드세요.",
    "shapez2 planner | New macro recipe (staff)": "shapez2 planner · 새 매크로 레시피(스태프)",
    "New macro recipe": "새 매크로 레시피",
    "← Back to catalog": "← 카탈로그로",
    "Display name (optional)": "표시 이름(선택)",
    "Untitled macro": "제목 없는 매크로",
    "Cancel": "취소",
    "Create & open graph editor": "만들고 그래프 편집기로",
    "Staff · Recipe metadata": "스태프 · 레시피 정보",
    "← Catalog": "← 카탈로그",
    "Open graph editor →": "그래프 편집기 열기 →",
    "Staff · Recipe Graph Workbench": "스태프 · 레시피 그래프 작업대",
    "Catalog": "카탈로그",
    "Edit metadata": "메타데이터 편집",
    # Auth
    "Login - shapez2 planner": "로그인 · shapez2 planner",
    "Use your username or a social account.": "아이디·비밀번호 또는 소셜 계정으로 들어옵니다.",
    "Remember me": "로그인 상태 유지",
    "Social login": "소셜로 로그인",
    "Need an account?": "처음이신가요?",
    "Logout - shapez2 planner": "로그아웃 · shapez2 planner",
    "You will need to sign in again to use account features.": (
        "계정 기능을 쓰려면 다시 로그인해야 합니다."
    ),
    "Are you sure you want to logout?": "로그아웃할까요?",
    "Back to home": "홈으로",
    "Sign up - shapez2 planner": "회원가입 · shapez2 planner",
    "Create a username and password, or use a social account.": (
        "아이디와 비밀번호를 만들거나 소셜 계정으로 가입할 수 있습니다."
    ),
    "Create account": "가입하기",
    "Social sign up": "소셜로 가입",
    "Already have an account?": "이미 계정이 있나요?",
    # Social / allauth (existing)
    "Third-Party Login Failure": "외부 로그인 실패",
    "An error occurred while attempting to login via your third-party account.": (
        "외부 계정으로 로그인하는 동안 문제가 생겼습니다."
    ),
    "Back to sign in": "로그인으로 돌아가기",
    "Sign In": "로그인",
    "Continue": "계속",
    "Login Cancelled": "로그인 취소됨",
    "Signup": "회원가입",
    "Sign Up": "회원가입",
    "Almost there — one short form.": "거의 다 됐어요. 짧은 정보만 더 적어 주세요.",
    # blocktrans / titles with variables
    "shapez2 planner | Graph: {{ code }} (staff)": "shapez2 planner · 그래프 {{ code }}(스태프)",
    "shapez2 planner | Edit: {{ code }} (staff)": "shapez2 planner · 편집 {{ code }}(스태프)",
    "Connect {{ provider }}": "{{ provider }} 연결",
    "You are about to connect a new third-party account from {{ provider }}.": (
        "{{ provider }}에서 가져온 새 외부 계정을 연결합니다."
    ),
    "Sign in with {{ provider }}": "{{ provider }}(으)로 계속",
    "Continue to shapez2 planner with your {{ provider }} account.": (
        "{{ provider }} 계정으로 shapez2 planner에 들어갑니다."
    ),
    (
        "You are about to use your {{ provider_name }} account to login to {{ site_name }}. "
        "As a final step, please complete the following form:"
    ): (
        "{{ provider_name }} 계정으로 {{ site_name }}에 로그인합니다. "
        "마지막으로 아래 항목만 채워 주세요."
    ),
    (
        "You decided to cancel logging in to our site using one of your existing accounts. "
        'If this was a mistake, please proceed to <a href="{{ login_url }}">sign in</a>.'
    ): (
        "기존 계정으로 로그인을 취소했습니다. 실수였다면 "
        '<a href="{{ login_url }}">로그인</a>으로 계속해 주세요.'
    ),
    (
        "Manage macro recipes for Pattern Lab and solver catalog strategies. "
        "Use separate pages for metadata vs graph canvas."
    ): (
        "패턴 랩과 솔버용 매크로 레시피를 여기서 다룹니다. "
        "메타 정보와 그래프 캔버스는 페이지가 나뉘어 있습니다."
    ),
    ("From source shapes to target output: deterministic recipe graphs live here."): (
        "원료 도형에서 목표 출력까지, 결정적인 레시피 그래프를 한곳에서 봅니다."
    ),
    (
        "Set a target code below. The solver plans backward, validates the recipe by replaying operations, "
        "and renders the result as a forward graph with source, operation, and target nodes."
    ): (
        "아래에 목표 코드를 넣으면 솔버가 역으로 설계하고, 연산을 따라가며 검증한 뒤 "
        "소스·공정·목표 노드가 이어진 정방향 그래프로 펼쳐 줍니다."
    ),
    ("Query updates this page; preview uses the same shapez_core parser as Quick Solver."): (
        "검색하면 이 페이지가 갱신되고, 미리보기는 퀵 솔버와 같은 shapez_core 파서를 씁니다."
    ),
    (
        "Base inputs stay on the left, target outputs stay on the right, and stable previews render in a right-aligned layout style. "
        "Drag to pan and use the mouse wheel to zoom inside the graph frame."
    ): (
        "입력은 왼쪽, 결과는 오른쪽에 두고 미리보기는 오른쪽 정렬로 안정적으로 보입니다. "
        "드래그로 이동하고 휠로 확대·축소하세요."
    ),
    ("Preview updates as you type (debounced). Parsed with"): (
        "입력하는 대로 미리보기가 따라옵니다(잠깐 멈추면 반영). 파싱:"
    ),
    (
        "Generate recipes, estimate required inputs, calculate miner counts, "
        "and visualize production graphs for Shapez 2 factories."
    ): (
        "레시피를 만들고 필요 입력을 짐작하며 채굴기 대수를 계산하고 "
        "Shapez 2 공장 생산 그래프를 그립니다."
    ),
    (
        "Follow one target shape from recipe breakdown to inputs per minute, miner load, "
        "and bottleneck checks in a single planning surface."
    ): (
        "목표 도형 하나를 잡고 분해·분당 입력·채굴 부하·병목까지 "
        "한 화면에서 따라가 봅니다."
    ),
    (
        "This site is fan-made and not affiliated with the official game. If you would like to help "
        "with hosting and development time, you can use the channels below. Support is completely optional."
    ): (
        "이 사이트는 팬이 만든 것이며 공식과 무관합니다. 서버와 개발에 보태고 싶다면 "
        "아래 채널을 이용해 주세요. 후원은 부담 없이 선택 사항입니다."
    ),
    (
        "Fan-made planner; not affiliated with the official game. Support is optional and "
        "helps hosting and development."
    ): (
        "팬 메이드 플래너이며 공식과 무관합니다. 후원은 자유이며 서버와 개발을 돕습니다."
    ),
    ("In production, set the environment variables"): ("운영 환경에서는 다음 환경 변수를 설정하면"),
    (
        "Pattern DB entries stay as candidate metadata. Python strategy dry-runs decide whether a macro can actually produce an inventory-search action. "
        "When a recipe has a valid graph_document with operations, the step list below is derived from the graph (green badge); otherwise it comes from DB step rows (gray badge)."
    ): (
        "패턴 DB 줄은 후보 메타데이터로만 남습니다. 파이썬 전략 드라이런이 매크로가 실제로 인벤토리 검색 동작을 만들 수 있는지 판별합니다. "
        "레시피에 연산이 담긴 graph_document가 유효하면 아래 단계는 그래프에서 옵니다(녹색 배지); 아니면 DB 단계 행에서 옵니다(회색 배지)."
    ),
    (
        "Enter a shape code to inspect its symbolic signature, inventory-search skeleton, DB macro candidates, and strategy dry-run status."
    ): (
        "도형 코드를 넣으면 기호 시그니처·인벤토리 검색 뼈대·DB 매크로 후보·전략 드라이런 상태를 함께 봅니다."
    ),
    (
        "No active DB macro matched the inventory signature. Load the seed fixture or add a MacroRecipe in admin."
    ): (
        "인벤토리 시그니처와 맞는 활성 매크로가 DB에 없습니다. 시드 픽스처를 넣거나 관리자에서 MacroRecipe를 추가하세요."
    ),
    (
        "Creates a draft row with the placeholder graph-draft pattern family (solver macro lookup uses exact pattern signature — drafts do not match real patterns until you assign a real family on the metadata page). "
        "Recipe code, strategy, costs, and priority are set automatically or from the graph editor."
    ): (
        "placeholder graph-draft 패밀리로 초안 행을 만듭니다. 솔버 매크로 조회는 패턴 시그니처가 정확히 맞아야 하므로, 메타 페이지에서 실제 패밀리를 지정하기 전까지 초안은 실제 패턴과 맞지 않습니다. "
        "레시피 코드·전략·비용·우선순위는 자동으로 채우거나 그래프 편집기에서 가져옵니다."
    ),
    (
        "Family, slug code, strategy, and activation. Estimated costs and solver priority are derived from the recipe graph when you save from the graph editor (commit)."
    ): (
        "패밀리·슬러그·전략·활성 여부입니다. 예상 비용과 솔버 우선순위는 그래프 편집기에서 저장(커밋)할 때 레시피 그래프에서 끌어옵니다."
    ),
    "DB matches: {{ n }}": "DB 일치: {{ n }}개",
    "op {{ oc }} / stage {{ sc }}": "연산 {{ oc }} / 단계 {{ sc }}",
    "Step {{ i }}": "단계 {{ i }}",
    "in [{{ in_slots }}] -> out [{{ out_slots }}]": "입력 [{{ in_slots }}] -> 출력 [{{ out_slots }}]",
    "source x{{ c }}": "소스 x{{ c }}",
    "shapez2 planner - Gallery": "shapez2 planner · 갤러리",
    "shapez2 planner - Demo": "shapez2 planner · 데모",
}

# djangojs domain: legacy JS + React msgids (English -> Korean). Keys must match gettext/shapezUiT/t().
KO_JS: dict[str, str] = {
    # Legacy solver timeline / macro graph
    "Node info": "노드 정보",
    "Edit node": "노드 편집",
    "Select a node on the canvas.": "캔버스에서 노드를 골라 주세요.",
    "Select a node to view properties.": "노드를 고르면 속성이 보입니다.",
    "Node not found.": "노드를 찾지 못했습니다.",
    'Card <span class="font-semibold text-slate-400">right-click</span> → node info / edit node. Card <span class="font-semibold text-slate-400">double-click</span> → edit dialog.': (
        '카드 <span class="font-semibold text-slate-400">우클릭</span> — 노드 정보·편집. '
        '카드 <span class="font-semibold text-slate-400">더블클릭</span> — 편집 창.'
    ),
    "Close": "닫기",
    "After changing shape_code, role, or operation, apply to recompute the graph.": (
        "shape_code·역할·연산을 바꿨다면 적용해 그래프를 다시 계산하세요."
    ),
    # Recipe graph editor
    "Saved graph_document failed schema validation. Fix the JSON via Admin or API, then reopen.": (
        "저장된 graph_document가 스키마 검증을 통과하지 못했습니다. 관리자나 API에서 JSON을 고친 뒤 다시 여세요."
    ),
    (
        "The canvas has no nodes. Click or drag sources and operations from the left "
        "(auto-sync with DB step rows follows separate rules on save/recompute)."
    ): (
        "캔버스가 비어 있습니다. 왼쪽에서 소스·연산을 클릭하거나 끌어다 놓으세요. "
        "(DB 단계 행과 맞추는 규칙은 저장·재계산 때 따로 적용됩니다.)"
    ),
    (
        "Click or drag operations or an empty source from the left, connect handles, "
        "then Dry-run/Save."
    ): (
        "왼쪽에서 연산이나 빈 소스를 클릭·드래그해 두고 핸들을 이은 뒤 드라이런이나 저장을 실행하세요."
    ),
    "Search operations…": "연산 검색…",
    "Empty source material": "빈 소스 재료",
    "Default {code} — edit via double-click or recompute": "기본값 {code} — 더블클릭이나 재계산으로 고칩니다",
    "{value} — click (grid place) or drag to canvas (drop position)": (
        "{value} — 클릭하면 격자에, 끌면 캔버스에 놓습니다"
    ),
    "This operation is not in the recipe graph engine recompute list.": (
        "이 연산은 레시피 그래프 엔진의 재계산 목록에 없습니다."
    ),
    (
        "Could not load catalog operations. Refresh or check the macro-graph-initial-catalog script."
    ): (
        "카탈로그 연산을 불러오지 못했습니다. 새로고침하거나 macro-graph-initial-catalog 스크립트를 확인하세요."
    ),
    (
        "Click adds to the grid slot; drag to the canvas places at the drop coordinates "
        "(operations auto-create outputs through intermediate)."
    ): (
        "클릭하면 격자 칸에 들어가고, 끌어 놓으면 그 좌표에 배치됩니다 "
        "(연산은 중간 출력까지 자동으로 이어집니다)."
    ),
    "Nothing selected.": "선택된 것이 없습니다.",
    "1 · {id}": "1개 · {id}",
    "{n} nodes selected.": "{n}개 노드 선택됨.",
    "Select a node to see a summary.": "노드를 고르면 요약이 보입니다.",
    (
        "Multi-select — edit properties after selecting a single node (double-click)."
    ): "여러 개 선택 중 — 속성 편집은 노드 하나만 고른 뒤(더블클릭) 해 주세요.",
    "Operation": "연산",
    "Output": "출력",
    "Intermediate": "중간",
    "Source": "소스",
    "Operation node": "연산 노드",
    "Output node": "출력 노드",
    "Intermediate node": "중간 노드",
    "Source node": "소스 노드",
    "Close editor": "편집기 닫기",
    "node": "노드",
    "paint_color (single char)": "paint_color (한 글자)",
    "crystal_color (one letter, optional)": "crystal_color (한 글자·선택)",
    (
        "Leave empty for two-wire mode: fluid on upper in-1, target shape on lower in "
        "(same as painter)."
    ): (
        "비우면 2와선: 상단 in-1에 유체, 하단 in에 대상 도형(페인터와 동일)."
    ),
    "(read-only)": "(읽기 전용)",
    "Cancel": "취소",
    "Apply": "적용",
    "Select a node.": "노드를 선택해 주세요.",
    "Same fields as double-click edit. role is fixed.": (
        "더블클릭 편집과 같은 필드입니다. 역할(role)은 고정입니다."
    ),
    "Operation: {op}": "연산: {op}",
    "Source · role {role}": "소스 · 역할 {role}",
    "Intermediate · {code}": "중간 · {code}",
    "Intermediate — shape_code after dry-run": "중간 — 드라이런 뒤 shape_code 확정",
    "Delivery · {code}": "납품 · {code}",
    "Delivery — shape_code unset": "납품 — shape_code 미정",
    "{t} type": "{t} 유형",
    "Run Dry-run or Save for server validation.": "드라이런이나 저장으로 서버 검증을 돌리세요.",
    "No issues from the last dry-run/save.": "직전 드라이런·저장에서는 문제가 없었습니다.",
    (
        "Validation issues in the last result — check the footer message."
    ): "직전 결과에 검증 이슈가 있습니다. 아래 안내를 확인하세요.",
    "Connection attempt:": "연결 시도:",
    "Nodes {nodeCount} · Edges {edgeCount} · Outputs {outputCount}": (
        "노드 {nodeCount} · 간선 {edgeCount} · 출력 {outputCount}"
    ),
    "Local notes (this browser · per recipe only)": "로컬 메모(이 브라우저·레시피별)",
    (
        "Not saved to server · only one delivery line from intermediate→output is allowed."
    ): "서버에 저장되지 않습니다 · 중간→출력 납품선은 한 줄만 허용됩니다.",
    (
        "Operations not in the engine recompute list cannot be placed on the canvas."
    ): "엔진 재계산 목록에 없는 연산은 캔버스에 놓을 수 없습니다.",
}


def extract_trans_literals(html: str) -> list[str]:
    out: list[str] = []
    for pattern in (
        r'\{%\s*trans\s+"([^"]+)"',
        r"\{%\s*trans\s+'([^']+)'",
    ):
        out.extend(re.findall(pattern, html))
    return out


def extract_blocktrans(html: str) -> list[str]:
    msgs: list[str] = []
    for m in re.finditer(
        r"\{%\s*blocktrans[^%]*%\}(.*?)\{%\s*endblocktrans\s*%\}",
        html,
        re.DOTALL,
    ):
        inner = m.group(1)
        msgs.append(" ".join(inner.split()))
    return msgs


def collect_msgids() -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for path in sorted(TEMPLATE_ROOT.rglob("*.html")):
        t = path.read_text(encoding="utf-8")
        for s in extract_trans_literals(t) + extract_blocktrans(t):
            if s not in seen:
                seen.add(s)
                ordered.append(s)
    return ordered


def extract_js_double_quoted_calls(src: str) -> list[str]:
    """Best-effort: gettext(\"...\") and shapezUiT(\"...\")."""
    out: list[str] = []
    for pat in (
        r'gettext\s*\(\s*"([^"]*)"',
        r'shapezUiT\s*\(\s*"([^"]*)"',
    ):
        out.extend(re.findall(pat, src))
    return out


def extract_js_single_quoted_calls(src: str) -> list[str]:
    """gettext('...') and shapezUiT('...') without embedded single quotes."""
    out: list[str] = []
    for pat in (
        r"gettext\s*\(\s*'([^']*)'",
        r"shapezUiT\s*\(\s*'([^']*)'",
    ):
        out.extend(re.findall(pat, src))
    return out


def collect_js_catalog_msgids() -> list[str]:
    seen: set[str] = set(KO_JS.keys())
    for path in sorted(JS_STATIC_ROOT.rglob("*.js")):
        if "vendor" in path.parts:
            continue
        src = path.read_text(encoding="utf-8")
        for s in extract_js_double_quoted_calls(src) + extract_js_single_quoted_calls(src):
            seen.add(s)
    return sorted(seen)


def write_po_file(
    msgids: list[str],
    ko_map: dict[str, str],
    po_path: Path,
    mo_path: Path,
    domain_label: str,
) -> None:
    po_path.parent.mkdir(parents=True, exist_ok=True)
    po = polib.POFile()
    po.metadata = {
        "Project-Id-Version": "shapez2-solver",
        "Language": "ko",
        "Content-Type": "text/plain; charset=UTF-8",
    }
    missing: list[str] = []
    for mid in msgids:
        ko = ko_map.get(mid)
        if ko is None:
            missing.append(mid)
            ko = mid
        po.append(polib.POEntry(msgid=mid, msgstr=ko))
    po.save(str(po_path))
    po.save_as_mofile(str(mo_path))
    if missing:
        print(
            f"WARN [{domain_label}]: missing KO mapping for",
            len(missing),
            "strings (using English)",
            flush=True,
        )
        for m in missing[:40]:
            safe = m.encode("ascii", errors="replace").decode("ascii")
            print(" -", safe[:200], flush=True)
        if len(missing) > 40:
            print(" ...", flush=True)


def main() -> None:
    msgids = collect_msgids()
    write_po_file(msgids, KO, PO_PATH, MO_PATH, "django")

    js_msgids = collect_js_catalog_msgids()
    write_po_file(js_msgids, KO_JS, PO_JS_PATH, MO_JS_PATH, "djangojs")


if __name__ == "__main__":
    main()
