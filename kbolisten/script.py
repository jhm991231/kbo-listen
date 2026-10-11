"""03의 이벤트 시퀀스 → 캐스터 발화(utterance) 리스트 (04 노트북에서 다듬은 템플릿)

- 이벤트마다 판정 발화(call)를 하나씩 만든다. TTS 타임스탬프와 정답을 잇는 고리가 event_idx.
- 카운트 숫자는 재언급 발화(restate)에서만, 한글 단어로 말한다.
- 같은 클립은 항상 같은 대본이 나오도록 클립 ID로 난수 시드를 고정한다.
"""
import random
import zlib

TEAM = {
    "HT": "KIA", "SK": "SSG", "OB": "두산", "LG": "LG", "LT": "롯데",
    "SS": "삼성", "NC": "NC", "KT": "KT", "HH": "한화", "WO": "키움",
}
NUM = ["노", "원", "투", "쓰리"]
OUT = ["노아웃", "원아웃", "투아웃"]


def count_words(b, s, rng):
    """실제 중계에서 가장 많이 쓰는 '투앤원' 형식 위주 (04b 집계 기준). 볼을 먼저 말한다"""
    if (b, s) == (3, 2):
        core = "풀카운트"
    elif b == 0:
        core = f"노볼 {NUM[s]} 스트라이크"
    elif s == 0:
        core = f"{NUM[b]}볼"
    elif rng.random() < 0.7:
        core = f"{NUM[b]}앤{NUM[s]}"
    else:
        core = f"{NUM[b]}볼 {NUM[s]} 스트라이크"
    return rng.choice(["{}", "{}입니다", "카운트 {}", "볼카운트 {}"]).format(core)


def ordinal(n):
    return "초구" if n == 1 else f"{n}구"


# 04b에서 모은 실제 중계 표현 기반. {adj} 같은 자리는 FILL에서 무작위로 채운다
# (위치는 실제 투구 위치가 아니라 무작위 → 말투용 장식일 뿐, 정답과 무관)
FILL = {
    "adj":   ["바깥쪽", "몸쪽", "높은", "낮은"],
    "adv":   ["바깥쪽", "몸쪽", "높게", "낮게"],
    "side":  ["오른쪽", "왼쪽", "뒤로 가는"],
    "field": ["왼쪽", "오른쪽", "좌중간", "우중간", "중견수 앞"],
    "gap":   ["좌중간", "우중간", "좌익선상", "우익선상"],
    "pos":   ["유격수가", "2루수가", "3루수가", "1루수가", "좌익수가", "중견수가", "우익수가"],
}


def pick(options, rng):
    return rng.choice(options).format(**{k: rng.choice(v) for k, v in FILL.items()})


# 투구 판정 (타석이 이어지는 경우)
# 구종은 따로 무작위로 붙으므로 '떨어지는 공'처럼 구종을 암시하는 표현은 쓰지 않는다 (직구와 충돌)
CALL = {
    "B": ["볼", "볼이고요", "볼입니다", "{adj} 볼이고요", "{adj} 볼입니다",
          "{adv} 빠졌고요", "{adv} 빠집니다", "일단 빠집니다", "골라냅니다", "{adj} 공 골라냅니다"],
    "T": ["스트라이크", "스트라이크입니다", "{adj} 스트라이크", "{adj} 스트라이크입니다",
          "루킹 스트라이크", "그대로 들어오면서 스트라이크"],
    "S": ["헛스윙", "헛스윙이고요", "방망이 헛돕니다", "헛스윙 나옵니다", "{adj} 공에 헛스윙"],
    "F": ["파울", "파울이고요", "파울이 됐고요", "{side} 파울입니다", "먹혔고 파울입니다",
          "빗맞으면서 파울", "커트해냅니다"],
    "V": ["번트 대다가 헛스윙"],
    "W": ["번트 파울"],
    # 쳤는데 타석 결과가 없는 경우: 그 플레이에서 주자가 아웃돼 이닝 종료 (뒤에 runner_out이 이어짐)
    "H": ["쳤습니다! 타구 굴러갑니다", "쳤습니다, 타구 떠오릅니다"],
}

# 타석 종료
STRIKEOUT = {
    "T": ["루킹 삼진!", "{adj} 스트라이크, 삼진입니다", "그대로 서서 삼진 당합니다"],
    "S": ["헛스윙 삼진!", "{adj} 공에 헛스윙, 삼진입니다", "방망이 헛돌면서 삼진"],
    "V": ["번트 헛스윙, 삼진"],
    "W": ["쓰리번트 파울, 삼진입니다"],
}
IN_PLAY = {
    "single": ["안타입니다", "{field} 안타", "좋은 코스로 빠져나가는 안타입니다", "쳤습니다! 안타!"],
    "double": ["{gap} 2루타!", "{gap} 빠집니다, 2루타", "쳤습니다! 2루타!"],
    "triple": ["{gap} 3루타!", "쳤습니다! 3루타!"],
    "home_run": ["큰 타구! 넘어갑니다! 홈런!", "담장 넘어갑니다, 홈런입니다!"],
    "field_out": ["잡아냅니다, 아웃", "땅볼이고요, 잡아서 처리합니다", "뜬공, 잡았습니다",
                  "{pos} 처리합니다", "평범한 타구, 아웃"],
    "double_play": ["땅볼, 병살로 연결됩니다", "더블 플레이!"],
    "triple_play": ["트리플 플레이! 삼중살입니다"],
    "sac_fly": ["외야 뜬공, 희생플라이"],
    "sac_bunt": ["번트, 희생번트 성공합니다"],
    "field_error": ["쳤습니다, 아 실책! 타자 살아나갑니다"],
    "fielders_choice": ["땅볼, 야수선택으로 타자 1루"],
    "catcher_interference": ["포수 타격방해, 타자 1루로"],
}
WALK = ["볼넷입니다", "볼넷이네요", "볼넷으로 걸어 나갑니다", "볼넷, 1루로 걸어 나갑니다"]
HBP = ["아, 몸에 맞는 공", "몸쪽 공, 맞았습니다. 사구"]

# 투구 없는 이벤트
NO_PITCH = {
    "auto_ball": ["피치클락 위반, 볼이 하나 주어집니다", "투수 피치클락 위반, 볼"],
    "auto_strike": ["타자 피치클락 위반, 스트라이크 선언됩니다"],
    "ibb": ["고의4구, 1루로 내보냅니다"],
    "walk_award": ["1루로 걸어 나갑니다"],
    "runner_out": ["주자 아웃! 이대로 이닝 종료됩니다"],
}

# 발화 노브 기본값. Easy/Hard 프리셋은 이 값들을 덮어써서 만든다
KNOBS = {
    "p_restate": 0.3,   # 판정 뒤 카운트 재언급 (K2)
    "p_ja": 0.25,       # 판정 앞 '자,'
    "p_first": 0.3,     # '초구' 언급 (실제 중계에서 초구는 가끔 말함)
    "p_ordinal": 0.05,  # '3구' 같은 2구 이후 순서 언급 (실제로는 거의 안 함, 04b 집계)
    "p_pitch": 0.3,     # 구종 언급
    "p_speed": 0.5,     # 구종을 말할 때 구속도 붙일 확률
    "p_omit": 0.0,      # 판정 생략 (K1). 같은 타석에서 나중에 카운트 재언급이 있는 투구만 대상
    "p_back": 0.1,      # 이벤트 뒤 해설위원 맞장구
    "p_comment": 0.15,  # 이벤트 뒤 해설위원 코멘트
    "p_distract": 0.0,  # 코멘트 중 방해 코멘트 비율 (판정 단어가 있지만 지금 상태에 대한 말이 아님)
}

# --- 해설위원 ---------------------------------------------------------------
# 해설위원은 상태(B-S-O)를 바꾸는 정보를 전달하지 않는다 → event_idx 없음, 질의와 무관
BACKCHANNEL = ["네.", "그렇죠.", "예, 맞습니다.", "네, 그렇습니다."]

# 일반 코멘트: 방금 일어난 일과 어긋나지 않게, 판정 단어(볼·스트라이크·파울·아웃 등)는 쓰지 않는다
COMMENT = {
    "ball": ["유인구에 잘 참았습니다.", "선구안이 좋네요.", "제구가 조금 흔들리는 모습이에요."],
    "strike": ["좋은 코스로 들어왔어요.", "타자가 예상하지 못한 공이었네요.", "투수가 적극적으로 승부하고 있습니다."],
    "foul": ["타이밍은 맞고 있어요.", "끈질기게 버티네요.", "조금만 앞에서 맞았으면 좋았을 텐데요."],
    "hit": ["노림수가 정확했어요.", "공략을 잘했습니다.", "좋은 타격이었습니다."],
    "out": ["투수가 잘 막아냈어요.", "수비가 깔끔했습니다.", "타구가 정면으로 갔네요."],
    "strikeout": ["결정구가 좋았습니다.", "마지막 공이 정말 좋았어요."],
    "walk": ["투수 입장에서는 아쉬운 장면이죠.", "출루에 성공했습니다."],
    "clock": ["요즘은 이런 장면도 종종 나오죠.", "템포를 조금 더 신경 써야겠네요."],
    "general": ["오늘 컨디션이 좋아 보입니다.", "양 팀 모두 집중력이 좋네요.", "중요한 순간입니다."],
}

# 방해 코멘트: 판정·카운트 단어가 들어 있지만 일반론이라 지금 상태와 무관 (키워드만 세면 틀림)
DISTRACT = [
    "볼 배합이 좋네요.",
    "스트라이크 존을 넓게 쓰고 있어요.",
    "투 스트라이크 이후에는 아무래도 타자가 불리해지죠.",
    "초구 스트라이크가 정말 중요하거든요.",
    "이런 상황에서 볼넷을 주면 안 되죠.",
    "풀카운트까지 가면 투수도 부담이 크죠.",
    "삼진 욕심보다는 맞혀 잡는 게 좋습니다.",
    "파울로 계속 걷어내는 게 타자 입장에선 최선이에요.",
    "원아웃 이후의 실점이 제일 뼈아프거든요.",
]
# 회상: 같은 클립에서 앞서 실제로 볼이 있었을 때만 쓴다
RECALL_BALL = ["아까 그 공은 볼 판정이 조금 아쉬웠어요.", "앞선 볼도 비슷한 코스였죠."]


def outcome(e):
    """이벤트 → 해설 코멘트 분류"""
    end = e.get("pa_end")
    if end == "strikeout":
        return "strikeout"
    if end in ("walk", "catcher_interference") or e.get("result") == "HBP":
        return "walk"
    if end in ("single", "double", "triple", "home_run", "field_error"):
        return "hit"
    if end is not None:
        return "out"
    if e["type"] in ("auto_ball", "auto_strike"):
        return "clock"
    return {"B": "ball", "F": "foul", "H": None}.get(e["result"], "strike")


def analyst_line(e, ball_seen, rng, k):
    """이벤트 뒤 해설위원 발화 하나 (없으면 None)"""
    r = rng.random()
    if r < k["p_comment"]:
        if rng.random() < k["p_distract"]:
            pool = DISTRACT + (RECALL_BALL if ball_seen else [])
            return {"kind": "distract", "text": rng.choice(pool)}
        kind = outcome(e)
        pool = COMMENT[kind] if kind and rng.random() < 0.7 else COMMENT["general"]
        return {"kind": "comment", "text": rng.choice(pool)}
    if r < k["p_comment"] + k["p_back"]:
        return {"kind": "backchannel", "text": rng.choice(BACKCHANNEL)}
    return None

# 생략해도 되는 판정: 타석이 이어지는 일반 투구만 (타석 종료·투구 없는 이벤트는 항상 말함)
OMITTABLE = {"B", "T", "S", "F", "V", "W"}


def plan_omissions(events, restated, rng, p_omit):
    """판정을 생략할 이벤트와, 그 때문에 질의하면 안 되는 이벤트를 고른다.

    i를 생략하면 같은 타석의 다음 재언급(앵커) j가 나오기 전까지는 카운트를 알 수 없으므로
    i ~ j-1은 질의 제외(dark). j는 재언급을 들은 뒤라 다시 질의할 수 있다.
    """
    omit, dark = set(), set()
    for i, e in enumerate(events):
        if e["type"] != "pitch" or "pa_end" in e or e["result"] not in OMITTABLE:
            continue
        anchor = next((j for j in range(i, len(events))
                       if events[j]["ab"] == e["ab"] and restated[j]), None)
        if anchor is not None and rng.random() < p_omit:
            omit.add(i)
            dark.update(range(i, anchor))
    return omit, dark


def call_text(e, rng, k):
    """이벤트 하나 → 판정 발화 문장"""
    if e["type"] != "pitch":
        text = pick(NO_PITCH[e["type"]], rng)
        if e["type"] == "auto_strike" and e.get("pa_end") == "strikeout":
            text += ", 삼진"
        return text

    r, end = e["result"], e.get("pa_end")
    if end is None:
        verdict = pick(CALL[r], rng)
    elif r == "H":
        verdict = pick(IN_PLAY[end], rng)
    elif r == "HBP":
        verdict = pick(HBP, rng)
    elif end == "walk":
        verdict = pick(WALK, rng)
    elif end == "strikeout":
        verdict = pick(STRIKEOUT[r], rng)
    else:  # 드문 조합 (예: 낫아웃 후 1루 송구 아웃)
        verdict = pick(CALL[r], rng) + ", " + pick(IN_PLAY.get(end, ["아웃"]), rng)

    # 앞부분은 대부분 생략: "바깥쪽 빠졌고요" / "초구, 볼" / "슬라이더, 볼" / "131킬로 슬라이더, 볼"
    head = []
    p_order = k["p_first"] if e["pitch"] == 1 else k["p_ordinal"]
    if rng.random() < p_order:
        head.append(ordinal(e["pitch"]))
    if e["pitch_name"] and rng.random() < k["p_pitch"]:
        if e["speed"] and rng.random() < k["p_speed"]:
            head.append(f"{e['speed']}킬로")
        head.append(e["pitch_name"])
    return f"{' '.join(head)}, {verdict}" if head else verdict


def end_sentence(text):
    """이미 '!'나 '.'로 끝나면 그대로, 아니면 마침표를 붙인다"""
    return text if text.endswith(("!", ".")) else text + "."


def render_clip(clip, knobs=None):
    """클립 → 발화 리스트. 각 발화: {kind, event_idx, speaker, text}

    판정을 생략한 이벤트는 call 발화가 없고, 생략 때문에 알 수 없는 구간의 call 발화에는 "query": False가 붙는다.
    speaker는 "caster" 또는 "analyst". 해설위원 발화는 event_idx가 없다.
    """
    k = {**KNOBS, **(knobs or {})}
    rng = random.Random(zlib.crc32(clip["clip_id"].encode()))
    events = clip["events"]

    # 재언급 위치를 먼저 정해야 생략 가능한 투구(뒤에 앵커가 있는 투구)를 고를 수 있다
    restated = [
        "pa_end" not in e and e.get("result") != "H" and (e["b"], e["s"]) != (0, 0)  # 타구 직후·0-0은 재언급 안 함
        and rng.random() < k["p_restate"]
        for e in events
    ]
    omit, dark = plan_omissions(events, restated, rng, k["p_omit"]) if k["p_omit"] > 0 else (set(), set())

    away, home = TEAM.get(clip["away"], clip["away"]), TEAM.get(clip["home"], clip["home"])
    batting = away if clip["half"] == "top" else home
    sc = clip["score"]

    utts = [{
        "kind": "intro", "event_idx": None,
        "text": f"{clip['inning']}회{'초' if clip['half'] == 'top' else '말'}, {batting} 공격입니다. "
                f"스코어 {away} {sc['away']} 대 {home} {sc['home']}.",
    }]

    pitcher, ab, outs = None, None, 0
    ball_seen = False  # 회상 코멘트("아까 그 볼…")는 앞서 실제로 볼이 있었을 때만
    for i, e in enumerate(events):
        if e["pitcher"] != pitcher:
            verb = "마운드에는" if pitcher is None else "투수 교체, 마운드에"
            utts.append({"kind": "pitcher", "event_idx": None, "text": f"{verb} {e['pitcher']}."})
            pitcher = e["pitcher"]
        if e["ab"] != ab:
            utts.append({"kind": "batter", "event_idx": None, "text": f"{OUT[outs]}, 타석에는 {e['batter']}."})
            ab = e["ab"]

        if i not in omit:
            text = call_text(e, rng, k)
            if rng.random() < k["p_ja"]:  # 실제 중계에서 자주 붙는 '자,'
                text = "자, " + text
            utt = {"kind": "call", "event_idx": i, "text": end_sentence(text)}
            if i in dark:
                utt["query"] = False
            utts.append(utt)

        if "pa_end" in e:
            outs = e["o"]
        elif restated[i]:
            utts.append({"kind": "restate", "event_idx": i, "text": end_sentence(count_words(e["b"], e["s"], rng))})

        # 해설위원: 캐스터가 이 이벤트에 대해 무언가 말한 뒤에만 (판정도 재언급도 없는 투구 뒤에는 끼어들지 않음)
        if i not in omit or restated[i]:
            line = analyst_line(e, ball_seen, rng, k)
            if line:
                utts.append({**line, "event_idx": None, "speaker": "analyst"})
        ball_seen = ball_seen or e.get("result") == "B"

    # 마지막 아웃은 다음 타자 소개가 없어서 따로 말해준다 (주루사 멘트에는 이미 '이닝 종료'가 있음)
    last = events[-1]
    if last["o"] == 3 and last["type"] != "runner_out":
        utts.append({"kind": "inning_end", "event_idx": len(events) - 1, "text": "쓰리아웃, 공수 교대합니다."})

    for u in utts:
        u.setdefault("speaker", "caster")
    return utts


def queryable(utts, n_events):
    """질의해도 되는 이벤트 번호: 발화가 하나라도 있고, query=False 표시가 없는 이벤트"""
    spoken, blocked = set(), set()
    for u in utts:
        if u["event_idx"] is None:
            continue
        spoken.add(u["event_idx"])
        if u.get("query") is False:
            blocked.add(u["event_idx"])
    return [i for i in range(n_events) if i in spoken and i not in blocked]


# TTS 입력 직전에만 읽는 대로 바꾼다 (대본 원문은 그대로 둠)
# KIA는 영어 단어처럼 읽혀서 '기아'로. 숫자·SSG는 그대로도 잘 읽음 (05 청취 확인)
READ_AS = {"KIA": "기아"}


def tts_text(text):
    for src, dst in READ_AS.items():
        text = text.replace(src, dst)
    return text
