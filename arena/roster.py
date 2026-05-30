"""The campaign roster — the original pokercommunity NPCs, reborn with personas,
dialogue, and an escalating difficulty ladder that ends at MR. JOKER.

Each character maps to a persona archetype (bluffer / highroller / calm / joker)
that drives both the rule bot and the LLM. `stake` = chips each side starts the
duel with (bigger = longer fight); `samples` tunes the rule bot's skill.
"""

ROSTER = [
    {
        "key": "marcus", "name": "Marcus", "title": "허세왕",
        "archetype": "bluffer", "stake": 200, "samples": 40,
        "intro": "흐흐, 신참이군.\n내 블러프에 몇 번이나 속아 넘어갈지 볼까?",
        "on_lose": "마, 말도 안 돼...\n내 허세가 안 통하다니!",   # player beats Marcus
        "on_win": "거봐, 포커는 배짱이야.\n넌 아직 멀었어, 꼬맹아.",   # Marcus beats player
    },
    {
        "key": "volovski", "name": "Mr. Volovski", "title": "한탕주의자",
        "archetype": "highroller", "stake": 240, "samples": 60,
        "intro": "한 방이면 다 끝나는 거야.\n겁먹는 놈이 지는 거고.",
        "on_lose": "이럴 수가...\n내 한 방이 빗나갔어!",
        "on_win": "하하! 큰 거 한 방,\n이게 바로 인생이지!",
    },
    {
        "key": "pokerbot", "name": "Pokerbot", "title": "냉혈 기계",
        "archetype": "calm", "stake": 280, "samples": 100,
        "intro": "확률은 거짓말을 하지 않는다.\n계산을 시작한다. 삐빅—",
        "on_lose": "오류... 예측 범위를 벗어났다...\n시스템... 종료...",
        "on_win": "예측대로다.\n인간은 비효율적이다.",
    },
    {
        "key": "checkmate", "name": "Checkmate", "title": "수읽기의 달인",
        "archetype": "calm", "stake": 320, "samples": 140,
        "intro": "네 다음 수가 전부 보여.\n체크메이트까지 몇 수 안 남았군.",
        "on_lose": "내 수읽기가...\n틀렸다고...?",
        "on_win": "체크메이트.\n처음부터 정해진 결과였어.",
    },
    {
        "key": "mafia", "name": "Mr. Mafia", "title": "조직의 보스",
        "archetype": "highroller", "stake": 360, "samples": 160,
        "intro": "이 테이블은 내 구역이야.\n칩 두고 조용히 꺼지는 게 좋을 거다.",
        "on_lose": "크윽... 조직에 뭐라고 보고하지...",
        "on_win": "세상은 힘 있는 자의 것이지.\n잘 가라, 풋내기.",
    },
    {
        "key": "joker", "name": "Mr. Joker", "title": "최종보스 · 광대 가면",
        "archetype": "joker", "stake": 500, "samples": 200,
        "intro": "키히히! 드디어 여기까지 왔구나.\n자, 진짜 게임을 시작해볼까?\n난 절대, 절대 읽히지 않아.",
        "on_lose": "...하. 하하하!\n재밌어, 넌 정말 재밌는 놈이야.\n이 조커를 이기다니!",
        "on_win": "키히히히! 농담은 여기까지.\n넌 처음부터 내 손바닥 안이었어.",
    },
]
