"""B-S-O 질의 평가

사용법:
    python -m kbolisten.evaluate --gt gt.json --pred pred.json [--meta meta.jsonl] [--out score.json]

정답과 예측 파일 형식은 같다:
    {"clip_id": [{"t": 13.59, "b": 0, "s": 1, "o": 0}, ...], ...}

- 예측에는 정답 파일의 모든 질의 시각 t에 대한 답이 있어야 한다. 빠진 질의는 오답으로 센다.
- 정답에 없는 시각의 예측은 무시한다.
- 주 지표는 B-S-O 세 값이 모두 맞은 비율(exact).
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

FIELDS = ("b", "s", "o")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_groups(meta_path):
    """meta.jsonl → clip_id별 그룹 이름 (split, split/track)"""
    groups = {}
    with Path(meta_path).open(encoding="utf-8") as f:
        for line in f:
            m = json.loads(line)
            groups[m["clip_id"]] = [m["split"], f"{m['split']}/{m['track']}"]
    return groups


def key(t):
    # 질의 시각은 소수 셋째 자리까지 쓰므로 그 단위로 맞춘다
    return round(float(t), 3)


def evaluate(gt, pred, groups=None):
    counts = defaultdict(lambda: {"n": 0, "missing": 0, "exact": 0, "b": 0, "s": 0, "o": 0})

    for cid, answers in gt.items():
        guesses = {key(p["t"]): p for p in pred.get(cid, [])}
        names = ["all"] + (groups or {}).get(cid, [])
        for a in answers:
            p = guesses.get(key(a["t"]))
            for name in names:
                c = counts[name]
                c["n"] += 1
                if p is None:
                    c["missing"] += 1
                    continue
                hits = [int(p[f]) == a[f] for f in FIELDS]
                c["exact"] += all(hits)
                for f, hit in zip(FIELDS, hits):
                    c[f] += hit

    return {
        name: {"n": c["n"], "missing": c["missing"],
               **{m: round(c[m] / c["n"], 4) for m in ("exact", *FIELDS)}}
        for name, c in sorted(counts.items(), key=lambda kv: (kv[0] != "all", kv[0]))
    }


def main():
    ap = argparse.ArgumentParser(description="B-S-O 질의 평가")
    ap.add_argument("--gt", required=True)
    ap.add_argument("--pred", required=True)
    ap.add_argument("--meta", help="meta.jsonl을 주면 split·트랙별 점수도 계산")
    ap.add_argument("--out", help="점수를 JSON으로 저장할 경로")
    args = ap.parse_args()

    groups = load_groups(args.meta) if args.meta else None
    scores = evaluate(load_json(args.gt), load_json(args.pred), groups)

    print(f"{'group':<12} {'n':>6} {'exact':>7} {'ball':>7} {'strike':>7} {'out':>7} {'missing':>8}")
    for name, s in scores.items():
        print(f"{name:<12} {s['n']:>6} {s['exact']:>7.2%} {s['b']:>7.2%} {s['s']:>7.2%} {s['o']:>7.2%} {s['missing']:>8}")

    if args.out:
        Path(args.out).write_text(json.dumps(scores, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
