# Poker Community — 페르소나 포커 아레나

> 대학 입학 전, 형과 함께 만들려다 실패한 터미널 포커 게임이 있었다.
> 난이도마다 다른 NPC가 등장하고, 각 NPC는 고유한 성격을 가진다 —
> 누구는 블러프를 남발하고, 누구는 한 방을 노리고, 최종 보스는 감정 없이 냉정하게.
> 그때는 포커 엔진(누가 이겼는지 판정하는 것)조차 완성하지 못했고,
> 그 "성격 있는 NPC"는 코드가 아니라 머릿속 상상으로만 존재했다.
>
> 이 저장소는 그 게임을 다시 살려낸 것이다. 그리고 한 걸음 더 나아가,
> 그 성격(persona)을 **LLM이 직접 연기**하게 만들어,
> *"성격을 부여하면 모델의 의사결정이 실제로 바뀌는가?"* 를 측정하는 **연구 도구**가 되었다.

---

## 🎮 게임으로 즐기기 — 스토리 모드

```bash
python3 -m arena.campaign
```
(또는 `play_poker.command` / 바탕화면 `포커게임` 더블클릭)

타이틀 → 규칙 → 상대 모드 선택(규칙봇 / 로컬 LLM) → 6명의 도전자를 차례로 격파하고
**최종 보스 Mr. Joker** 에 도달하라. 캐릭터마다 대사가 있고, 터미널에 ASCII 카드가 그려진다.

| # | 캐릭터 | 칭호 | 성향 |
|---|--------|------|------|
| 1 | Marcus | 허세왕 | 블러퍼 — 약한 패에도 마구 레이즈 |
| 2 | Mr. Volovski | 한탕주의자 | 하이롤러 — 크게 베팅, 한 방 노림 |
| 3 | Pokerbot | 냉혈 기계 | 냉정 — 확률대로만 |
| 4 | Checkmate | 수읽기의 달인 | 냉정 — 타이트하고 끈질김 |
| 5 | Mr. Mafia | 조직의 보스 | 하이롤러 — 위협적 |
| 6 | **Mr. Joker** | 🃏 최종보스 | 가차없는 밸류 + 갑작스런 블러프, 절대 안 읽힘 |

조작: `f` 폴드 · `c` 콜/체크 · `r` 레이즈 (`r 100` 처럼 한 번에도 가능)

단판 연습:
```bash
python3 -m arena.human --vs rule:calm        # 규칙봇과 1:1
python3 -m arena.human --vs ollama:bluffer   # 로컬 LLM과 1:1 (속내를 말함)
```

---

## 🔬 연구 도구로서 — 무엇을 측정하는가

게임을 **게임으로** 키운 게 아니라 **실험 장비**로 키웠다. 게임 규칙은 고정하고,
**페르소나만 변수로 바꿔가며** 모든 결정과 그 *이유* 를 기록한다.

핵심 질문: **페르소나가 진짜 베팅을 바꾸는가, 아니면 말투만 바꾸는가?**

이를 위해:
- 모든 캐릭터(규칙봇·LLM·사람)는 **동일한 `decide(상황) → 행동` 인터페이스**에 꽂힌다.
- 모든 결정은 **이유(LLM의 경우 chain-of-thought)와 함께 JSONL로 로깅** 된다.
- 규칙봇이 **baseline**, LLM 페르소나가 **비교 대상**이다.

### 지금까지의 발견

**통제 실험(동일 시나리오를 모든 페르소나에 그대로 입력 → 카드 운 제거):**
- **페르소나가 의사결정을 지배한다.** 동일 상황에서 LLM 블러퍼와 냉정은 **95%** 다른 결정.
- **"공격적" 라벨이 합리성을 덮어쓴다.** LLM 블러퍼의 공격성은 패 세기와 **상관 0.00**
  (카드를 무시하고 다 레이즈), 냉정은 패 세기를 더 따른다. → 라벨이 모델의 합리성 자체를 바꾼다.

**게임 결과(규칙봇):**
- **빈도 ≠ 수익.** 블러퍼는 *판* 을 가장 많이 이기지만(블라인드 훔치기) 돈은 잃고,
  냉정은 판은 적게 이겨도 모든 시드에서 흑자. 공격성은 빈도를, 규율은 돈을 산다.

이는 *"페르소나를 LLM 추론을 들여다보는 렌즈로 쓴다"* 는 방향의 첫 통제 실험이다.
방법·표·시드 변동성·한계까지 정리한 결과 보고서는 **[`REPORT.md`](REPORT.md)** 참고.

```bash
python3 -m arena.probe --scenarios 200                        # ★ 통제 실험: 고정 시나리오 배터리
python3 -m arena.probe --backend ollama --scenarios 20 --personas bluffer,calm
python3 -m arena.tournament --hands 200                       # 규칙봇 라운드로빈 + 행동/수익 표
python3 -m arena.llm_run --p0 ollama:bluffer --p1 rule:calm   # LLM vs baseline
python3 -m arena.analyze <trajectory.jsonl>                   # 행동 시그니처 분석
```

---

## 🗂️ 구조

```
arena/
  cards.py        카드/덱 (rank를 2–14 정수로 → 족보 계산이 단순해짐)
  evaluator.py    7장 중 최고 5장 족보 판정 (원래 막혔던 부분)
  equity.py       몬테카를로 승률 — 모든 에이전트 공통의 '진실' 신호
  engine.py       1v1 노리밋 홀덤 엔진 + 깔끔한 decide() 인터페이스 + 로깅 훅
  agents.py       규칙 기반 페르소나 (bluffer/highroller/calm/joker)
  llm_agent.py    Anthropic LLM 페르소나 (동일 인터페이스)
  ollama_agent.py 로컬 LLM 페르소나 (무료, 오프라인 · qwen2.5:7b)
  trajectory.py   JSONL 궤적 로거 (연구 자산)
  probe.py        ★ 고정 시나리오 통제 실험 (eq~공격성 상관 등)
  analyze.py / tournament.py / run.py / llm_run.py   실험 러너 & 분석
  human.py        사람이 직접 플레이 (ASCII 카드 + 상대 중계)
  art.py          터미널 그래픽 (카드/배너/말풍선)
  roster.py       캠페인 캐릭터 + 대사
  campaign.py     스토리 모드 진행

main.py, opp.py, start.py, game/   ← 입학 전 원본 시도 (그대로 보존)
```

자세한 사용법은 [`arena/README.md`](arena/README.md) 참고.
