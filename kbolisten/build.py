"""데이터셋 구성: 클립 샘플링, 트랙별 노브, 목소리 배정 (06·07·08 공용)

MODE = "pilot"(설계 검증용 20클립) 또는 "main"(본 데이터셋 1,300클립).
같은 MODE면 어느 노트북에서 불러도 같은 클립·같은 대본·같은 목소리가 나온다 (시드 고정).
"""
import random
import zlib

from .script import KNOBS, render_clip

# split: (easy, hard) 클립 수
PLANS = {
    "pilot": {"train": (3, 3), "dev": (2, 2), "test": (5, 5)},
    # 파일럿에서 클립 2개짜리 트랙 점수가 60%↔96%로 크게 흔들려서 dev/test를 넉넉하게
    "main": {"train": (500, 500), "dev": (50, 50), "test": (100, 100)},
}
# 결과 폴더 이름 (Drive kbo-listen/ 아래)
DIRS = {
    "pilot": {"paraphrase": "paraphrase_pilot", "dataset": "dataset_pilot_v5"},
    "main": {"paraphrase": "paraphrase_main", "dataset": "dataset_main"},
}

SPECIAL = {"pitch_clock", "hbp", "ibb", "walk_award", "runner_out"}
RARE = {"pitch_clock", "walk_award", "runner_out"}  # 투구 없이 상태가 바뀌는 드문 이벤트
MAX_PITCHES = 35  # 너무 긴 반 이닝은 제외 (Qwen3 정렬 모델이 긴 클립에서 무너짐)

# Easy: 템플릿 그대로 (키워드로도 풀 수 있는 기본 난이도)
# Hard: 판정 생략(K1) + 방해 코멘트 + LLM 의역 + 드문 이벤트 절반
#  의역을 두 트랙에 다 했더니(파일럿 v4) Easy도 키워드로 안 풀려서 트랙 차이가 사라졌음 → Hard만
TRACK_KNOBS = {
    "easy": {"p_omit": 0.0, "p_back": 0.10, "p_comment": 0.15, "p_comment_pa": 0.6, "p_distract": 0.0,
             "paraphrase": False},
    "hard": {"p_omit": 0.5, "p_back": 0.15, "p_comment": 0.35, "p_comment_pa": 0.7, "p_distract": 0.5,
             "paraphrase": True},
}


def sample(clips, plan, seed=42):
    """split별로 Easy(특수 이벤트 없음) / Hard(절반은 드문 이벤트 클립) 클립을 뽑는다"""
    rng = random.Random(seed)
    ok = [c for c in clips if c["n_pitches"] <= MAX_PITCHES]
    picked, used = [], set()

    def take(pool, n, track):
        pool = [c for c in pool if c["clip_id"] not in used]
        chosen = rng.sample(pool, min(n, len(pool)))
        used.update(c["clip_id"] for c in chosen)
        picked.extend({**c, "track": track} for c in chosen)
        return len(chosen)

    for split, (n_easy, n_hard) in plan.items():
        pool = [c for c in ok if c["split"] == split]
        got_easy = take([c for c in pool if not SPECIAL & set(c["tags"])], n_easy, "easy")
        n_rare = take([c for c in pool if RARE & set(c["tags"])], n_hard // 2, "hard")
        got_hard = n_rare + take([c for c in pool if not RARE & set(c["tags"])], n_hard - n_rare, "hard")
        if (got_easy, got_hard) != (n_easy, n_hard):  # 후보가 모자라면 알려준다 (조용히 적게 뽑지 않도록)
            print(f"⚠ {split}: easy {got_easy}/{n_easy}, hard {got_hard}/{n_hard} (드문 이벤트 {n_rare})")
    return picked


def assign_voices(clip_id, casters, analysts):
    """클립 ID로 캐스터 1명 + 해설 1명을 고정 배정 (조합이 고르게 나오도록)"""
    h = zlib.crc32(clip_id.encode())
    return {"caster": casters[h % len(casters)], "analyst": analysts[(h // len(casters)) % len(analysts)]}


def prepare(clips, mode, voices):
    """클립 샘플링 → 트랙별 노브 → 목소리 배정 → 템플릿 대본. voices = voices.json 내용"""
    casters = sorted(v for v, info in voices.items() if info["role"] == "caster")
    analysts = sorted(v for v, info in voices.items() if info["role"] == "analyst")
    picked = sample(clips, PLANS[mode])
    for c in picked:
        c["knobs"] = {**KNOBS, **TRACK_KNOBS[c["track"]]}
        c["voices"] = assign_voices(c["clip_id"], casters, analysts)
        c["utts"] = render_clip(c, c["knobs"])
    return picked
