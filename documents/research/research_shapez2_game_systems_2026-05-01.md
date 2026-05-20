# shapez 2 — 게임 시스템 분석 (참고 문서)

> 역할: 게임 시스템 분석가  
> 작성일: 2026-05-01  
> 목적: shapez2Solver 프로젝트의 도메인·기획 참고용 요약

[![shapez 2 | Factory & Strategy game | Available now on Steam](https://images.openai.com/static-rsc-4/njjhbA-CeZ0OlnmbbwrLDEF9NMFbL01HjYcb_21R8TuVVn4jI6Wr71H9pUh9ba_MvVjOda1HoOZlKVsoXI5Uha3Ob-mGZanAuustzVNws1636btUKagmLQ5lfk2XcLQAFGJ2fJQ8EQNPiMlp5WMoTX00-9S4iDB_ivviajaeBBI?purpose=inline)](https://shapez2.com/?utm_source=chatgpt.com)

## 근거 / 신뢰도

| 근거                                  | 신뢰도 | 사용한 이유                                   |
| ----------------------------------- | --: | ---------------------------------------- |
| 공식 사이트                              |  높음 | 게임 개요, 핵심 시스템, 1.0 출시 정보 확인              |
| Steam 상점 / Steam FAQ / SteamDB 패치노트 |  높음 | 출시일, 가격, 플랫폼, 시스템 요구사항, 1.0 변경점 확인       |
| PC Gamer 기사                         |  중간 | 1.0 업데이트와 Manufacture Mode의 의미를 보조적으로 해석 |

---

# shapez 2 핵심 요약

**shapez 2**는 우주 공간에서 기하학적 도형을 채굴, 분해, 회전, 절단, 색칠, 적층해서 목표 도형을 자동 생산하는 **3D 공장 자동화 / 물류 최적화 게임**이다. 적, 전투, 시간제한, 자원 고갈이 없고, 순수하게 공장 설계와 최적화에 집중하는 구조다. 정확도: 높음. ([shapez 2][1])

## 기본 정보

| 항목              | 내용                                                              |
| --------------- | --------------------------------------------------------------- |
| 장르              | 공장 자동화, 시뮬레이션, 전략, 퍼즐, 샌드박스                                     |
| 개발사             | tobspr Games                                                    |
| 퍼블리셔            | tobspr Games, Gamirror Games                                    |
| 플랫폼             | Windows, macOS, SteamOS/Linux                                   |
| 모드              | 싱글플레이어                                                          |
| Early Access 출시 | 2024년 8월 15일                                                    |
| 1.0 정식 출시       | 2026년 4월 23일                                                    |
| 한국어             | Steam 상점 기준 한국어 인터페이스 지원                                        |
| 현재 Steam 기능     | Steam Achievements, Steam Workshop, Steam Cloud, Family Sharing |

정확도: 높음. Steam 상점은 출시일을 **2026년 4월 23일**, Early Access 출시일을 **2024년 8월 15일**로 표시하고 있으며, 개발사/퍼블리셔/언어/Steam 기능도 함께 명시한다. ([Steam Store][2])

---

# 게임플레이 구조

## 1. 목표

중앙 허브 역할의 **Vortex** 또는 관련 플랫폼에 특정 도형을 대량으로 공급해서 연구, 건물, 업그레이드, 새 시스템을 해금한다. Steam 설명 기준, 플레이어는 도형을 생산·배송해서 기술을 해금하고 공장을 확장한다. 정확도: 높음. ([Steam Store][2])

## 2. 기본 생산 흐름

일반적인 흐름은 다음과 같다.

```text
원본 도형 채굴
→ 벨트/기차로 운송
→ 절단 / 회전 / 색칠 / 적층 / 조합
→ 목표 도형 완성
→ Vortex 또는 Trade Station에 납품
→ 연구/업그레이드/새 목표 해금
```

공식 사이트는 핵심 조작을 **cutting, rotating, stacking, painting**으로 설명하고, Steam도 도형을 분해·색칠·적층·재조립하는 방식이라고 설명한다. 정확도: 높음. ([shapez 2][1])

---

# shapez 1과 다른 점

| 구분    | shapez 1 | shapez 2                 |
| ----- | -------- | ------------------------ |
| 시점/공간 | 2D 평면 중심 | 3D 우주 플랫폼                |
| 건설 구조 | 평면 확장    | **3개 레이어 기반 다층 공장**      |
| 운송    | 벨트 중심    | 벨트 + 우주 벨트 + 기차          |
| 색칠    | 페인트/색 조합 | 유체 기반 페인팅 포함             |
| 규모    | 무한 평면 확장 | 플랫폼, 기차, 블루프린트 기반 대규모 확장 |
| 깊이    | 미니멀 자동화  | 연구, 모드, 기차, 다층 설계, 모딩 지원 |

공식 FAQ에 따르면 shapez 2는 기본 구조는 shapez 1과 비슷하지만, 3D 월드가 건설 레이어를 추가하고, 공간 플랫폼 때문에 “공간 자체”도 관리 대상이 된다. 또한 기차, 페인팅용 유체, 유연한 연구 시스템, 새 게임 모드, Hexagonal shapes, 내부 작동을 보여주는 애니메이션 건물 등이 추가되었다. 정확도: 높음. ([Steam Community][3])

---

# 핵심 시스템

## 1. Multi-Layer 3D Factory

공장과 플랫폼을 **세 개의 건설 레이어**에 걸쳐 설계할 수 있다. 단순히 옆으로 넓히는 게 아니라, 위아래 레이어와 연결해서 공간 효율을 높이는 방식이다. 정확도: 높음. ([Steam Store][2])

## 2. Space Train

대규모 공장에서 장거리 운송을 담당한다. 1.0 패치에서 기차 처리량도 강화되어, 패키지 크기가 **180 → 360 shapes**, 유체는 **1,800 → 3,600 liters**로 증가했다. 정확도: 높음. ([SteamDB][4])

## 3. Research / Upgrade

목표 도형을 납품하면 새 건물, 메커니즘, 업그레이드가 해금된다. Steam 설명은 연구 시스템이 새 건물, 메커니즘, 업그레이드를 열어 공장 설계 방식을 확장한다고 설명한다. 정확도: 높음. ([Steam Store][2])

## 4. Blueprint Library

공장 설계를 저장, 불러오기, 보내기, 공유할 수 있다. 대규모 모듈형 공장을 만들 때 핵심 기능이다. 정확도: 높음. ([Steam Store][2])

## 5. Make-Anything-Machine, MAM

고급 단계에서는 어떤 목표 도형이 들어와도 자동으로 생산 라인을 재구성하거나 신호 기반으로 처리하는 **Make-Anything-Machine** 설계가 가능하다. 공식 사이트는 고급 wiring system으로 MAM을 만들 수 있다고 설명한다. 정확도: 높음. ([shapez 2][1])

---

# 1.0 업데이트 핵심

2026년 4월 23일 1.0 출시와 함께 가장 큰 변화는 다음이다.

| 항목                  | 내용                                      |
| ------------------- | --------------------------------------- |
| Manufacture Mode    | 새 게임 모드. 영구적·대규모 공장 중심                  |
| Classic Mode 확장     | 기존 경험을 Classic Mode로 정리하고 추가 마일스톤/도형 추가 |
| Modding             | Steam Workshop 기반 공식 모딩 지원              |
| Achievements        | 83개 업적 추가                               |
| Visual Improvements | 파이프, 기차, 유체, 와이어, 셰이더 등 비주얼 개선          |
| New Tutorial        | 튜토리얼 재작업                                |
| New Shapes          | X, Y 도형 추가                              |
| Codex               | 150페이지 이상으로 확장된 게임 내 설명서                |
| QoL                 | 배치, 미리보기, UI, 통계, 업그레이드 화면 개선           |

정확도: 높음. SteamDB에 올라온 1.0 패치노트는 Manufacture Mode, 83개 업적, Steam Workshop 모딩, Classic Mode 확장, 비주얼 개선, 새 튜토리얼, X/Y 도형, 확장된 Codex 등을 명시한다. ([SteamDB][4])

---

# 게임 모드

## Certification

처음 하는 사람용 약 1시간짜리 입문 시나리오. 기본 조작과 핵심 시스템을 익힌 뒤 Classic으로 자연스럽게 넘어가도록 설계되어 있다. 정확도: 높음. ([SteamDB][4])

## Classic Mode

Early Access 시절의 기존 shapez 2 경험을 정리한 모드다. 물류, 도형 퍼즐, 공장 자동화가 섞인 전통적인 진행 방식이다. 정확도: 높음. ([SteamDB][4])

## Manufacture Mode

1.0에서 추가된 새 모드. 특정 도형만 만들고 폐기하는 구조보다, **영구적으로 쓰이는 대규모 공장**을 짓는 방향을 강화한다. Trade Station을 통해 도형을 교환하고 Vortex Platform을 재건하는 것이 목표다. 정확도: 높음. ([SteamDB][4])

## Hexagonal Mode

기본 4분할 도형 대신 6분할 구조를 사용하는 실험적 고난도 모드다. 공식 FAQ는 Hexagonal mode가 layer당 6 segments를 제공한다고 설명한다. 정확도: 높음. ([Steam Community][3])

---

# 난이도와 플레이 감각

shapez 2는 Factorio, Satisfactory, Dyson Sphere Program처럼 공장 자동화를 다루지만, 전투·전력난·자원 고갈·생존 압박이 거의 없다. 그래서 “공장 설계 퍼즐”과 “처리량 최적화”에 더 집중한다. Steam 설명도 모든 건물이 무료이고, 자원이 고갈되지 않으며, 적이나 시간제한이 없다고 명시한다. 정확도: 높음. ([Steam Store][2])

플레이 감각은 대략 이렇게 보면 된다.

| 좋아할 가능성 높음         | 안 맞을 가능성 있음        |
| ------------------ | ------------------ |
| 자동화 퍼즐 좋아함         | 전투/생존/스토리 중심 원함    |
| 벨트 정리, 처리량 최적화 좋아함 | 자원 채굴 경쟁, 비용 관리 원함 |
| 대규모 공장 스케일링 좋아함    | 목표가 명확한 캠페인만 원함    |
| MAM, 회로, 로직 설계 좋아함 | 반복 납품 구조를 지루해함     |

---

# 시스템 요구사항

## Windows 기준

| 구분      | 최소                  | 권장                  |
| ------- | ------------------- | ------------------- |
| OS      | Windows 10 64-bit   | Windows 11 64-bit   |
| CPU     | Intel Core i5-10400 | Intel Core i5-12600 |
| RAM     | 8 GB                | 16 GB               |
| GPU     | GTX 750 Ti          | RTX 2060            |
| DirectX | 11                  | 11                  |
| 저장공간    | 2 GB                | 2 GB                |

정확도: 높음. Steam 상점의 시스템 요구사항 기준이다. ([Steam Store][2])

사용자 PC가 RTX 4090급이면 성능상 병목은 GPU보다 대규모 공장 시뮬레이션 CPU/메모리 쪽에서 날 가능성이 더 크다. 공식 FAQ는 보통 40,000 buildings 정도로 게임을 끝낼 수 있고, 100,000 buildings까지 매우 부드럽게, 500,000~1,000,000 buildings도 시스템에 따라 플레이 가능하다고 설명한다. 정확도: 중간~높음. ([Steam Community][3])

---

# 가격 / 구매 정보

현재 Steam 상점 기준 기본판은 정가 **$29.99**, 20% 할인가는 **$23.99**로 표시되어 있고, 할인 종료일은 **5월 7일**로 표시된다. 정확도: 높음, 단 가격은 지역·세일·시점에 따라 바뀔 수 있다. ([Steam Store][2])

Supporter Edition은 추가 음악과 철도 장식 요소가 포함된 후원 성격의 에디션이다. Steam FAQ도 Supporter Edition은 기본적으로 개발사 후원용이며, 추가 음악과 rail twisters/train loops가 보너스라고 설명한다. 정확도: 높음. ([Steam Community][3])

---

# 도형 레이어·핀(Pin) 메커닉

> **근거·신뢰도**: 아래 규칙 중 핀 푸셔·레이어 상한·페인터와의 관계는 플레이 커뮤니티 정리와 게임 내 동작 관찰에 가깝다. 공식 Codex 문구와 1:1 대응하지 않을 수 있으므로 **중간** 신뢰도로 취급하고, 솔버 구현은 `django_apps/shapez_solver/services/operation_engine.py`의 열(column) 단위 수직 모델에 맞춘다.

## 핵심 규칙

### 지지(Support)와 중력

- **핀은 수직 지지대**로, 자기 위에 쌓인 레이어를 받친다.
- **수평으로는 다른 도형 부품과 “연결”되지 않는다** — 옆 사분면의 핀만으로는 아래가 비어 있는 부품이 떠 있지 않게 만들 수 없다.
- **아래(같은 열)에 지지가 없고**, 핀 옆 인접만 있는 상태의 도형 부품은 **떨어진다**(게임 내 물리; 수평 인접만으로는 고정되지 않음).

### 레이어 상한(5th layer rule)

- 한 도형 스택에는 **최대 4개의 레이어**(일반)가 있다. **Insane 모드**에서는 **5레이어**까지 허용된다.
- 상한을 넘기면 **가장 위 레이어 전체**가 파괴된다(상단 슬라이스 제거).

### 핀 푸셔(Pin Pusher)

- 기존 도형 **아래**로 전면 핀 레이어를 밀어 넣어, 시각적으로는 도형 전체가 **한 레이어 위로 밀리는** 효과와 같다.
- shapez2Solver의 `pin_pusher` 연산은 동일하게 **하단에 `P-`가 가득한 레이어를 prepend**하는 모델로 표현한다.

### 색과 무관(Color neutrality)

- 핀은 **색이 없으며** 페인터로 **칠해지지 않는다**. 색칠 연산은 도형 부품만 바꾸고 핀은 `P-`로 남는다.

## 커뮤니티에서 쓰는 응용

- **고립 핀 / 핀 타워만 남기기**: 레이어 한도에 맞춰 핀을 반복 밀어 넣으면, 상단 도형 부분이 한도 규칙으로 **“팝”**되어 떨어지고 핀 기둥만 남는 식의 구성이 가능하다.
- **떨어지는 핀 트릭**: 아래 베이스에 **구멍(빈 사분면)**이 있을 때, 그 열 위에 있던 핀은 **아래 지지층이나 바닥**까지 내려간다(수직 열 기준).
- **페인터 통과**: 핀은 그대로 두고 위에 얹힌 도형 부품만 색이 바뀐다.

## shapez2Solver 구현 한계(명시)

- 엔진은 **사분면마다 독립인 수직 열**에 대해, 빈 칸을 통과해 비어 있지 않은 부품을 아래로 모으는 **안정 압축(stable compaction)** 만 수행한다.
- **“옆 핀만 인접하고 아래는 비어 있다”**는 **2D 지지 그래프**가 필요한 낙하는 이 모델에 포함하지 않았다. 필요하면 후속으로 별도 규칙을 추가한다.

---

# 호환성 / 제한사항

| 항목             | 상태                         |
| -------------- | -------------------------- |
| Steam Deck     | 작동은 하지만 공식 지원은 아님          |
| 컨트롤러           | 현재 콘솔 컨트롤러 공식 지원 없음        |
| 콘솔 출시          | 현재 계획 없음                   |
| 멀티플레이/코옵       | 현재 계획 없음                   |
| 4K / Ultrawide | 지원                         |
| 1.0 이전 세이브     | 호환 안 됨                     |
| 1.0 이전 블루프린트   | 호환은 되지만 경고 표시, 향후 지원 중단 가능 |

정확도: 높음. 공식 FAQ와 1.0 패치노트 기준이다. ([Steam Community][3])

---

# 입문 루트 추천

1. **Certification 먼저 플레이**  
   기본 조작, 레이어, 벨트, 생산 흐름을 익히는 용도.

2. **Classic Regular로 진행**  
   shapez 2의 기본 도형 퍼즐과 물류 구조를 이해하기 좋음.

3. **블루프린트 습관화**  
   같은 모듈을 반복 확장하는 게임이라, 작은 생산 블록을 저장해두는 게 중요함.

4. **처음부터 완벽한 공장 만들려고 하지 말기**  
   이 게임은 무료 삭제/재배치/재설계가 전제다. 스파게티 → 정리 → 모듈화 순서가 정상이다.

5. **기차는 중후반부터 적극 사용**  
   가까운 거리는 벨트, 장거리/대량 운송은 기차로 분리하는 게 구조적으로 깔끔하다.

---

# 관련 연구 (처리량·소행성)

- 소행성 Space Belt/Pipe 절대 처리량: [`../game_rules/shapez2_asteroid_space_transport_throughput.md`](../game_rules/shapez2_asteroid_space_transport_throughput.md) (`CANON`). 구 커뮤니티 초안: [`research_shapez2_space_transport_throughput_2026-05-18.md`](research_shapez2_space_transport_throughput_2026-05-18.md) (`SUPERSEDED`)

---

# 결론

**shapez 2는 “전투 없는 Factorio식 도형 자동화 퍼즐”에 가깝다.**  
핵심 재미는 자원을 캐는 게 아니라, **도형 생산 공정을 어떻게 모듈화하고, 처리량을 늘리고, 대규모 공장으로 확장하느냐**에 있다.

현재 1.0 기준으로는 콘텐츠가 크게 확장되었고, 특히 **Manufacture Mode + Steam Workshop 모딩 + 83개 업적 + Classic 확장** 때문에 Early Access 때보다 완성도가 높아진 상태다. 자동화, 로직 설계, MAM, 대규모 시스템 최적화를 좋아하면 꽤 잘 맞는 게임이다.

---

## 참고 링크

[1]: https://shapez2.com/ "shapez 2 | Factory & Strategy game | Available now on Steam | 1.0 Release out April 23rd"  
[2]: https://store.steampowered.com/app/2162800/shapez_2__Factory/ "Save 20% on shapez 2 - Factory on Steam"  
[3]: https://steamcommunity.com/app/2162800/discussions/0/806849231160779528/ "shapez 2 - 1.0 Release FAQ :: shapez 2 - Factory General Discussions"  
[4]: https://steamdb.info/patchnotes/22785032/ "shapez 2 - 1.0 is OUT NOW! · shapez 2 - Factory update for 23 April 2026 · SteamDB"
