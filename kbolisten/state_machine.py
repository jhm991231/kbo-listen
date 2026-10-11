"""볼카운트·아웃 상태머신 (참가자 제공용)

중계에서 알아들은 '일'을 순서대로 넣으면 B-S-O를 계산해 준다.
야구 규칙(4볼 볼넷, 3스트라이크 삼진, 2스트라이크 후 파울 등)은 여기서 처리하므로
참가자는 음성에서 무슨 일이 일어났는지만 알아내면 된다.

    t = CountTracker()
    t.ball(); t.foul(); t.foul(); t.foul()   # 1-2 (2스트라이크 후 파울은 그대로)
    t.set_count(2, 2)                         # "투앤투" 같은 카운트 언급으로 보정
    t.in_play(outs=1)                         # 땅볼 아웃 → 카운트 리셋, 1아웃

시각이 붙은 일 목록으로 질의에 답하려면 answer_queries()를 쓴다.
"""
from dataclasses import asdict, dataclass


@dataclass
class State:
    b: int = 0
    s: int = 0
    o: int = 0


class CountTracker:
    def __init__(self):
        self.state = State()

    # --- 투구 ---------------------------------------------------------------
    def ball(self):
        """볼. 투구 없이 주어지는 볼(피치클락 위반 등)도 같다. 4개면 볼넷"""
        self.state.b += 1
        if self.state.b == 4:
            self._end_pa()

    def strike(self):
        """루킹·헛스윙·번트 헛스윙·2스트라이크 후 번트 파울. 투구 없는 스트라이크도 같다. 3개면 삼진"""
        self.state.s += 1
        if self.state.s == 3:
            self.out()
            self._end_pa()

    def foul(self):
        """일반 파울. 2스트라이크 이후에는 카운트가 그대로"""
        self.state.s = min(self.state.s + 1, 2)

    def in_play(self, outs=0):
        """타구로 타석 종료. outs = 그 플레이에서 나온 아웃 수 (안타 0, 땅볼 아웃 1, 병살 2 …)"""
        self.out(outs)
        self._end_pa()

    def walk(self):
        """투구와 상관없이 타자가 1루로 나가며 타석 종료 (사구, 고의4구 등)"""
        self._end_pa()

    # --- 투구와 별개인 일 -----------------------------------------------------
    def out(self, n=1):
        """아웃 추가 (주루사·견제사 등). 카운트는 그대로"""
        self.state.o = min(self.state.o + n, 3)

    # --- 중계에서 직접 들은 상태로 보정 ----------------------------------------
    def set_count(self, b, s):
        """'투앤원', '풀카운트' 같은 카운트 언급"""
        self.state.b, self.state.s = b, s

    def set_outs(self, o):
        """'원아웃, 타석에는 ~' 같은 아웃카운트 언급"""
        self.state.o = o

    def new_batter(self):
        """새 타자 소개. 놓친 타석 종료가 있어도 카운트를 리셋"""
        self._end_pa()

    def _end_pa(self):
        self.state.b = self.state.s = 0


def answer_queries(actions, query_times):
    """시각이 붙은 일 목록으로 질의에 답한다.

    actions: [(t, 메서드 이름, 인자 dict), ...]  예) (12.3, "ball", {}), (15.0, "set_count", {"b": 1, "s": 2})
    query_times: 질의 시각 리스트
    반환: [{"t", "b", "s", "o"}, ...]  ← 평가 코드의 예측 파일 형식 그대로
    시각 t의 답 = t까지 일어난 일을 모두 반영한 상태
    """
    tracker = CountTracker()
    actions = sorted(actions, key=lambda a: a[0])
    answers, i = [], 0
    for qt in sorted(query_times):
        while i < len(actions) and actions[i][0] <= qt:
            _, name, kwargs = actions[i]
            getattr(tracker, name)(**kwargs)
            i += 1
        answers.append({"t": qt, **asdict(tracker.state)})
    return answers


def _selftest():
    def run(*calls):
        t = CountTracker()
        for name, *args in calls:
            getattr(t, name)(*args)
        return (t.state.b, t.state.s, t.state.o)

    assert run(("ball",), ("foul",), ("foul",), ("foul",)) == (1, 2, 0)          # 2S 후 파울 유지
    assert run(("ball",), ("ball",), ("ball",), ("ball",)) == (0, 0, 0)          # 볼넷 → 리셋, 아웃 없음
    assert run(("strike",), ("foul",), ("strike",)) == (0, 0, 1)                 # 삼진 → 1아웃
    assert run(("in_play", 2),) == (0, 0, 2)                                     # 병살
    assert run(("ball",), ("out",)) == (1, 0, 1)                                 # 주루사: 카운트 유지
    assert run(("set_outs", 2), ("in_play", 2)) == (0, 0, 3)                     # 아웃은 3에서 멈춤
    assert run(("ball",), ("set_count", 2, 2), ("foul",)) == (2, 2, 0)          # 카운트 언급으로 보정

    got = answer_queries(
        [(1.0, "ball", {}), (3.0, "strike", {}), (5.0, "in_play", {"outs": 1})],
        [0.5, 2.0, 4.0, 6.0],
    )
    assert [(a["b"], a["s"], a["o"]) for a in got] == [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 0, 1)]
    print("상태머신 테스트 통과")


if __name__ == "__main__":
    _selftest()
