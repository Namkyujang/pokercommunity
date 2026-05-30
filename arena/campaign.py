"""Story mode — climb the ladder of pokercommunity's NPCs to MR. JOKER.

    cd .../pokercommunity
    python -m arena.campaign

Title screen -> rules -> pick opponent mode (fast rule bots, or talking local
LLM personas) -> duel each character in turn. Beat one and the next appears, with
intro and defeat dialogue. Lose all your chips and it's game over.
"""

from . import art
from .engine import HeadsUpTable
from .agents import make_persona
from .ollama_agent import make_ollama_persona
from .human import HumanAgent, ConsoleLogger
from .roster import ROSTER


def pause(msg="  [Enter] 계속  ") -> str:
    try:
        return input(art.DIM + msg + art.RESET).strip().lower()
    except EOFError:
        return "q"


def build_opponent(mode: str, archetype: str, samples: int):
    if mode == "llm":
        return make_ollama_persona(archetype)
    return make_persona(archetype, n_samples=samples)


# -- screens ----------------------------------------------------------------

def title_screen():
    art.clear()
    print("\n" + art.title_banner() + "\n")
    print("        " + art.DIM + "한 판의 실패에서 다시 시작된 이야기." + art.RESET)
    print("        " + art.DIM + "여섯 명의 도전자를 꺾고 최종보스에 도달하라." + art.RESET + "\n")
    return pause("  [Enter] 게임 시작   (q 종료)  ")


def rules_screen():
    art.clear()
    print(art.CYAN + art.BOLD + "  ─ 규칙 ─" + art.RESET + "\n")
    rules = [
        "• 1대1 텍사스 홀덤. 각자 카드 2장 + 공용 카드 5장.",
        "• 4번의 베팅 라운드: 프리플랍 → 플랍 → 턴 → 리버.",
        "• 카드 7장(내 2 + 공용 5) 중 최고 5장 족보로 승부.",
        "",
        "  너의 선택지 (매 차례):",
        "   f  =  폴드 (이 판 포기)",
        "   c  =  콜 / 체크 (받기 / 그냥 넘기기)",
        "   r  =  레이즈 (금액 입력, 또는 'r 100')",
        "",
        "• 상대 칩을 0으로 만들면 승리 → 다음 도전자 등장.",
        "• 네 칩이 0이 되면 게임 오버.",
        "",
        "  족보 (강함 순): 스트레이트플러시 > 포카드 > 풀하우스 >",
        "  플러시 > 스트레이트 > 트리플 > 투페어 > 원페어 > 하이카드",
    ]
    for r in rules:
        print("   " + r)
    print()
    return pause()


def mode_screen():
    art.clear()
    print(art.CYAN + art.BOLD + "  ─ 상대 모드 선택 ─" + art.RESET + "\n")
    print("   1)  " + art.BOLD + "규칙봇" + art.RESET +
          "      빠르고 즉각 반응. 추천 (처음이면 이거).")
    print("   2)  " + art.BOLD + "LLM 페르소나" + art.RESET +
          "  로컬 AI가 직접 추론. 매 수마다 속내를 말함.")
    print("        " + art.DIM + "(느림 · ollama 서버 필요 · qwen2.5:7b)" + art.RESET + "\n")
    while True:
        c = pause("   번호 입력 (1/2, q 종료): ")
        if c == "q":
            return None
        if c in ("1", ""):
            return "rule"
        if c == "2":
            return "llm"


def character_intro(ch, idx, total, mode):
    art.clear()
    boss = ch["key"] == "joker"
    print(art.DIM + f"  도전자 {idx}/{total}" + art.RESET + "\n")
    if boss:
        print(art.JOKER_FACE + "\n")
    title = art.MAGENTA + art.BOLD if boss else art.YELLOW + art.BOLD
    print(f"  ── {title}{ch['name']}{art.RESET}  ({ch['title']}) ──")
    print(f"  {art.DIM}성향: {ch['archetype']}   ·   판돈: {ch['stake']}{art.RESET}\n")
    print(art.speech(ch["name"], "", ch["intro"],
                     color=art.MAGENTA if boss else art.YELLOW))
    print()
    return pause("  [Enter] 대결 시작  ")


# -- one duel: play hands until someone busts -------------------------------

def duel(opp_agent, ch, mode) -> str:
    you = HumanAgent()
    logger = ConsoleLogger(human_seat=0, opp_name=ch["name"],
                           show_reasoning=(mode == "llm"))
    stake = ch["stake"]
    table = HeadsUpTable([you, opp_agent], stacks=(stake, stake), logger=logger)

    while table.stacks[0] > 0 and table.stacks[1] > 0:
        try:
            table.play_hand()
        except KeyboardInterrupt:
            return "quit"
        if table.stacks[0] <= 0 or table.stacks[1] <= 0:
            break
        if pause("\n  [Enter] 다음 핸드  (q 기권): ") == "q":
            return "quit"
    return "win" if table.stacks[1] <= 0 else "loss"


def ending_screen(won_all: bool):
    art.clear()
    if won_all:
        print(art.JOKER_FACE + "\n")
        print(art.YELLOW + art.BOLD +
              "   🏆  당신은 미스터 조커를 쓰러뜨렸다.\n" + art.RESET)
        print("   " + art.DIM +
              "7년 전 만들다 멈춘 게임이, 마침내 끝을 봤다." + art.RESET + "\n")
    else:
        print(art.MAGENTA + art.BOLD + "   💀  GAME OVER" + art.RESET + "\n")
        print("   " + art.DIM + "칩이 바닥났다. 다시 도전하라." + art.RESET + "\n")


# -- main -------------------------------------------------------------------

def main():
    if title_screen() == "q":
        return
    if rules_screen() == "q":
        return
    mode = mode_screen()
    if mode is None:
        return

    total = len(ROSTER)
    for idx, ch in enumerate(ROSTER, 1):
        if character_intro(ch, idx, total, mode) == "q":
            return
        opp = build_opponent(mode, ch["archetype"], ch["samples"])
        result = duel(opp, ch, mode)

        if result == "quit":
            print("\n  기권했다. 다음 기회에.")
            return
        if result == "loss":
            print("\n" + art.speech(ch["name"], ch["title"], ch["on_win"],
                                    color=art.MAGENTA if ch["key"] == "joker" else art.RED))
            ending_screen(won_all=False)
            return
        # win
        print("\n" + art.speech(ch["name"], ch["title"], ch["on_lose"], color=art.GREEN))
        print("\n  " + art.GREEN + art.BOLD + f"✦ {ch['name']} 격파! ✦" + art.RESET)
        if pause("\n  [Enter] 다음 도전자에게  ") == "q":
            return

    ending_screen(won_all=True)


if __name__ == "__main__":
    main()
