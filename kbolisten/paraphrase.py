"""템플릿 대본(script.render_clip) → LLM 의역 + 검증

정답 숫자를 담은 발화(이닝·투수·타자 소개, 카운트 재언급, 공수 교대)는 그대로 두고,
판정을 말투로 전하는 발화(call)와 해설위원 잡담(comment, distract)만 바꾼다.

이 모듈은 LLM을 직접 부르지 않는다. 프롬프트를 만들고 응답을 해석·검증하는 것까지만 하고,
실제 생성은 07 노트북(vLLM)이 맡는다. 그래서 로컬에서 가짜 응답으로 테스트할 수 있다.

검증 단계
1. 형식 검사 (규칙): 없던 숫자·구종·투구 순서 금지, 카운트·아웃 수 새로 말하기 금지,
   근거 없는 반복 표현('또', '다시') 금지, 해설 코멘트의 판정 단어 금지, 길이 제한
2. 블라인드 분류 (생성과 다른 LLM): 의역 문장만 보고 판정 라벨을 고르게 해서 원래 판정과 같아야 통과
   (해설은 원문과 같은 분류여도 통과, judge_ok 참고)
실패한 발화는 다시 생성하고, 그래도 안 되면 원래 템플릿 문장을 쓴다.
"""
import json
import re

# --- 무엇을 바꾸나 -----------------------------------------------------------
# 판정 → 블라인드 분류 라벨. 상태머신에서 같은 효과를 내는 판정끼리 묶었다
# (루킹·헛스윙은 둘 다 스트라이크, 번트 파울은 파울)
PITCH_LABEL = {"B": "ball", "T": "strike", "S": "strike", "V": "strike", "F": "foul", "W": "foul"}
PA_LABEL = {
    "strikeout": "strikeout",
    "walk": "walk",
    "single": "reach", "double": "reach", "triple": "reach", "home_run": "reach", "field_error": "reach",
    "field_out": "out", "sac_fly": "out", "sac_bunt": "out",
    "double_play": "double_play",
}
# 야수선택·삼중살·타격방해·낫아웃 송구처럼 드물고 한 문장에 여러 정보가 섞인 경우는 템플릿 그대로 둔다


def expected_label(e):
    """이 이벤트의 판정 발화가 전해야 하는 라벨. 의역 대상이 아니면 None"""
    if e["type"] != "pitch":  # 피치클락·고의4구 등 투구 없는 이벤트는 그대로
        return None
    end, r = e.get("pa_end"), e["result"]
    if end is None:
        return PITCH_LABEL.get(r)  # 'H'(타구인데 타석 결과 없음)는 None → 그대로
    if r == "HBP":
        return "walk"
    if end == "strikeout":
        return "strikeout" if r in ("T", "S", "V", "W") else None
    if end == "walk":
        return "walk" if r == "B" else None
    return PA_LABEL.get(end) if r == "H" else None


def targets(utts, events):
    """의역할 발화 번호 → 기대 라벨. 해설위원 발화는 'none'(판정 정보 없음)이어야 한다"""
    out = {}
    for i, u in enumerate(utts):
        if u["kind"] == "call":
            label = expected_label(events[u["event_idx"]])
            if label:
                out[i] = label
        elif u["kind"] in ("comment", "distract"):
            out[i] = "none"
    return out


def repeat_ok(utts, events):
    """'또 파울', '다시 스트라이크'처럼 반복 표현을 써도 사실인 판정 발화 번호들.

    같은 타석의 바로 앞 투구가 같은 판정이고, 그 판정을 실제로 말했을 때만 (생략됐다면 정보가 샌다)
    """
    called = {u["event_idx"] for u in utts if u["kind"] == "call"}
    ok = set()
    for i, u in enumerate(utts):
        j = u["event_idx"]
        if u["kind"] != "call" or not j or j - 1 not in called:
            continue
        prev, cur = events[j - 1], events[j]
        if prev["ab"] == cur["ab"] and expected_label(prev) and expected_label(prev) == expected_label(cur):
            ok.add(i)
    return ok


# --- 1단계: 형식 검사 ----------------------------------------------------------
# 원칙: 빼는 건 괜찮고, 틀리게 말하거나 없던 정보를 만드는 건 안 된다
COUNT_WORDS = re.compile(r"(노|원|투|쓰리|[0-3])\s?(앤|볼(?!넷)|스트라이크|아웃)|풀\s?카운트|카운트")
# 앞 투구를 끌어오는 표현 ('다음 공도 헛스윙'의 '공도' 포함)
OTHER_PITCH = re.compile(r"연속|또|다시|이번에도|공도|두 번|세 번|앞선|아까|방금 전")
JUDGE_WORDS = re.compile(r"볼|스트라이크|파울|아웃|삼진|안타|홈런|병살|실책|희생|루타|헛스윙|카운트|사구")
ORDINAL = re.compile(r"초구|\d+구")
# 한글·숫자·영문·기본 문장부호 밖의 문자 (영문은 위에서 따로 검사)
FOREIGN = re.compile(r"[^가-힣ㄱ-ㆎA-Za-z0-9\s.,!?~·…'\"()\-:%]")
PITCH_NAMES = ["직구", "포심", "투심", "슬라이더", "스위퍼", "커브", "체인지업", "포크", "스플리터",
               "커터", "싱커", "너클"]
# 공(물건)을 '볼'이라고 부르면 볼 판정처럼 들린다. 땅볼·뜬볼·파울볼·볼넷·볼카운트는 제외
BARE_BALL = re.compile(r"(?<![땅뜬울])볼(?!넷|\s?카운트)")
# 판정마다 섞이면 안 되는 다른 판정 단어 (예: 파울인데 '헛스윙, 파울입니다' → 듣는 사람도 키워드 모델도 헷갈림)
CONFLICT = {
    "ball": re.compile(r"헛스윙|헛돌|스트라이크|파울|커트|삼진"),
    "strike": re.compile(r"파울|커트|볼넷|삼진"),
    "foul": re.compile(r"헛스윙|헛돌|스트라이크|삼진"),
    "strikeout": re.compile(r"파울|커트|볼넷"),
    "walk": re.compile(r"스트라이크|헛스윙|파울|삼진"),
    "reach": re.compile(r"아웃|삼진|볼넷|병살"),
    "out": re.compile(r"안타|홈런|루타|볼넷|삼진|병살"),
    "double_play": re.compile(r"안타|홈런|루타|볼넷|삼진"),
}


def check_form(orig, new, kind, repeat_ok=False, label=None):
    """통과하면 None, 아니면 탈락 이유. repeat_ok = 반복 표현이 사실인가(repeat_ok()), label = 기대 라벨"""
    new = new.strip()
    if not new or "\n" in new:
        return "빈 문장/여러 줄"
    if len(new) > max(2.5 * len(orig), 30):
        return "너무 김"
    if re.search(r"[A-Za-z]", new) and not re.search(r"[A-Za-z]", orig):
        return "영어 섞임"
    if FOREIGN.search(new):  # 태국 문자 등이 섞여 나온 적 있음 ('ตรง구로 들어옵니다')
        return "한글 외 문자"
    if kind == "call":
        # 구속·구종·'초구'는 빼도 되지만, 원문에 없던 숫자·구종·순서가 생기면 지어낸 것
        if set(re.findall(r"\d+", new)) - set(re.findall(r"\d+", orig)):
            return "없던 숫자"
        if any(p in new and p not in orig for p in PITCH_NAMES):
            return "없던 구종"
        if set(ORDINAL.findall(new)) - set(ORDINAL.findall(orig)):
            return "없던 투구 순서"
        if COUNT_WORDS.search(new) and not COUNT_WORDS.search(orig):
            return "카운트·아웃 수를 새로 말함"
        if label != "ball" and BARE_BALL.search(new) and not BARE_BALL.search(orig):
            return "볼 판정이 아닌데 '볼'"
        conflict = CONFLICT.get(label)
        if conflict and conflict.search(new) and not conflict.search(orig):
            return "다른 판정 단어 섞임"
        # '또 파울'은 흔한 표현이지만, 앞 투구가 실제로 같은 판정이고 그걸 말했을 때만 사실이다
        if OTHER_PITCH.search(new) and not OTHER_PITCH.search(orig) and not repeat_ok:
            return "근거 없는 반복 표현"
    elif kind == "comment":
        if JUDGE_WORDS.search(new):
            return "해설에 판정 단어"
        if OTHER_PITCH.search(new) and not OTHER_PITCH.search(orig):
            return "다른 투구 언급"
    elif kind == "distract":
        if not JUDGE_WORDS.search(new):  # 방해 코멘트는 판정 단어가 남아 있어야 의미가 있다
            return "방해 코멘트에 판정 단어 없음"
    return None


# --- 생성 프롬프트 -------------------------------------------------------------
# 목소리별 말투. 같은 목소리는 클립이 달라도 비슷한 성격으로 말하게 한다
STYLE = {
    "caster_m38_steady": "담담하고 안정적인 캐스터. 군더더기 없이 짧게 말한다.",
    "caster_m40_baritone": "여유 있고 자신감 있는 베테랑 캐스터. 장면을 조금 더 생생하게 묘사한다.",
    "caster_m35_anchor": "정확하고 또렷한 캐스터. 정돈된 문장으로 말한다.",
    "analyst_a40_warm": "선수 출신의 친근한 해설위원. 편하게 대화하듯 말한다.",
    "analyst_a45_clear": "분석적인 해설위원. 차분하게 이유를 짚는다.",
}
DEFAULT_STYLE = {"캐스터": "프로야구 중계 캐스터.", "해설위원": "프로야구 해설위원."}

GEN_SYSTEM = """너는 한국 프로야구 TV 중계 대본을 다듬는 작가다.
템플릿으로 만든 딱딱한 대본을 실제 생중계처럼 자연스럽고 다양한 말로 바꾼다.

규칙
- [바꿀 것] 표시된 줄만 바꾼다. [고정] 줄은 문맥 참고용이다.
- 각 줄의 판정 결과는 절대 바꾸지 않는다. 듣는 사람이 볼은 볼로, 헛스윙은 헛스윙으로, 파울은 파울로,
  안타는 안타로, 아웃은 아웃으로 바로 알아들을 수 있어야 한다. 판정이 모호해지면 실패다.

캐스터 [판정] 줄
- 생중계 말투로 짧게 끊는다. 대부분 2~8어절. 글로 쓴 설명문, 번역투, 어색한 동사(실패합니다, 드러눕니다 등)는 쓰지 않는다.
- 모든 줄을 '~입니다'로 끝내지 않는다. '~고요', '~죠', '~습니다!', 명사로 끊기 등을 섞는다.
- 공은 '공'이라고 부른다. '볼'이라는 단어는 볼 판정일 때만 쓴다.
- 구속(예: 151킬로), 구종 이름, '초구'는 남겨도 빼도 되지만 바꾸거나 새로 지어내지 않는다.
- 볼카운트·아웃 수(예: 투앤원, 원아웃)는 새로 말하지 않는다.
- '또 파울'처럼 앞 투구를 언급할 때는 대본 앞줄에 실제로 그 판정이 있을 때만 쓴다.
- '볼', '파울' 같은 판정 단어 없이 묘사로만 전해도 된다. 단, 판정이 분명하게 들려야 한다.

해설위원 줄
- 대화하듯 편하게 말한다. '~죠', '~거든요', '~네요', '~어요'.
- [코멘트] 줄: 볼·스트라이크·파울·아웃·삼진·안타·홈런 같은 판정 단어를 쓰지 않는다.
- [일반론] 줄: 판정·카운트 단어(볼, 스트라이크, 풀카운트, 볼넷, 삼진, 아웃 등)를 반드시 하나 이상 넣는다.
  단, 지금 공이나 지금 타석 이야기가 아니라 야구 일반에 대한 이야기로 들려야 한다.

좋은 예
- 볼: "바깥으로 흘러 나갑니다." / "참아냅니다." / "높았어요, 볼." / "몸쪽 붙였는데 빠졌고요."
- 루킹 스트라이크: "바깥쪽 꽉 찹니다." / "그대로 꽂힙니다, 스트라이크." / "서서 보고만 있었네요."
- 헛스윙: "방망이 나왔다가 헛돕니다." / "따라 나가다 헛스윙." / "배트가 허공을 가릅니다."
- 파울: "뒤로 걷어냅니다." / "3루 쪽 관중석으로, 파울." / "끈질기게 커트해 냅니다."
- 삼진: "돌아섭니다! 삼진!" / "서서 당합니다, 삼진." / "헛스윙, 그대로 물러납니다. 삼진."
- 안타: "깨끗하게 빠져나갑니다, 안타!" / "외야 앞에 뚝 떨어집니다!" / "담장까지 굴러갑니다!"
- 범타 아웃: "정면이네요, 잡아서 처리합니다." / "높이 떴고요, 편안하게 잡습니다." / "땅볼, 송구 여유 있게 아웃."
- 해설 코멘트: "저건 잘 참았어요." / "타이밍이 점점 맞아 들어가거든요." / "투수가 원하는 대로 됐죠."
- 해설 일반론: "카운트 싸움에서 밀리면 투수가 정말 힘들어지거든요." / "볼넷 하나가 큰 이닝으로 이어지는 경우가 많죠."

- 한 줄은 한 문장 또는 짧은 두 문장. 영어를 쓰지 않는다. 같은 표현을 반복하지 말고 줄마다 다르게 쓴다.

출력: 바꾼 줄만 JSON 객체로. 키는 줄 번호(문자열), 값은 새 문장. 다른 말은 쓰지 않는다.
예: {"3": "바깥으로 살짝 벗어납니다.", "5": "쉽게 물러서지 않네요."}"""

KIND_TAG = {"call": "판정", "comment": "코멘트", "distract": "일반론"}


def gen_messages(utts, todo, voices):
    """클립 하나를 한 번에 의역하는 대화. todo = 이번에 바꿀 발화 번호들"""
    lines = []
    for i, u in enumerate(utts):
        who = "캐스터" if u["speaker"] == "caster" else "해설위원"
        if i in todo:
            lines.append(f"{i} [바꿀 것][{KIND_TAG[u['kind']]}] {who}: {u['text']}")
        else:
            lines.append(f"{i} [고정] {who}: {u['text']}")
    style = "\n".join(f"- {role}: {STYLE.get(name, DEFAULT_STYLE[role])}"
                      for role, name in (("캐스터", voices["caster"]), ("해설위원", voices["analyst"])))
    user = f"말투\n{style}\n\n대본\n" + "\n".join(lines)
    return [{"role": "system", "content": GEN_SYSTEM}, {"role": "user", "content": user}]


def parse_gen(text):
    """LLM 응답 → {발화 번호: 새 문장}. JSON을 못 찾으면 빈 dict"""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        return {}
    try:
        obj = json.loads(m.group())
    except json.JSONDecodeError:
        return {}
    return {int(k): v.strip() for k, v in obj.items() if str(k).isdigit() and isinstance(v, str)}


# --- 2단계: 블라인드 분류 ------------------------------------------------------
# 검증 LLM은 원문도 정답도 모른 채 문장 하나만 보고 고른다
LABELS = {
    "A": ("ball", "볼"),
    "B": ("strike", "스트라이크 (루킹 또는 헛스윙)"),
    "C": ("foul", "파울"),
    "D": ("strikeout", "삼진 (타자 아웃)"),
    "E": ("walk", "볼넷 또는 몸에 맞는 공 (타자 1루로)"),
    "F": ("reach", "안타·장타·홈런·실책 (타자가 살아서 나감)"),
    "G": ("out", "타구가 잡히거나 처리되어 타자 아웃 (땅볼·뜬공·희생타 등)"),
    "H": ("double_play", "병살 (아웃 2개)"),
    "I": ("none", "방금 공이나 지금 타석의 결과를 알려주지 않음 (잡담, 일반론, 감상)"),
}
JUDGE_SYSTEM = (
    "야구 중계에서 나온 문장 하나를 읽고, 이 문장이 '방금 던진 공' 또는 '방금 끝난 타석'의 결과로 "
    "무엇을 알려주는지 고른다. 야구 일반에 대한 이야기나 감상이면 I를 고른다.\n\n"
    + "\n".join(f"{k}. {desc}" for k, (_, desc) in LABELS.items())
    + "\n\n알파벳 하나만 답한다."
)


def judge_messages(utt):
    who = "캐스터" if utt["speaker"] == "caster" else "해설위원"
    return [{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": f"{who}: {utt['text']}"}]


def parse_judge(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    m = re.search(r"[A-I]", text)
    return LABELS[m.group()][0] if m else None


def judge_ok(label, pred_para, pred_orig):
    """검증 통과 기준.

    판정 발화: 의역 분류가 원래 판정과 같아야 한다.
    해설 발화: 검증 모델은 원문 해설도 30%쯤 '정보 있음'으로 잘못 고른다 (예: 일반론 속 '볼넷'을 볼넷으로).
      원문은 설계상 상태 정보가 없으므로, 의역이 '정보 없음'이거나 원문과 같은 분류면 원문보다 헷갈리게 만든 건 아니다.
    """
    if label == "none":
        return pred_para is not None and pred_para in ("none", pred_orig)
    return pred_para == label


# --- 적용 ----------------------------------------------------------------------
def apply(utts, accepted):
    """통과한 의역만 반영. 원문은 orig에 남겨 둔다 (검수·재현용)"""
    out = []
    for i, u in enumerate(utts):
        if i in accepted:
            u = {**u, "orig": u["text"], "text": accepted[i]}
        out.append(u)
    return out
