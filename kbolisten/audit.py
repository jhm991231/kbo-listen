"""의역 사람 점검: 표본 추출 → 블라인드 판정 웹페이지 → 채점

검증(Gemma)을 통과해 반영된 의역에서 라벨별로 표본을 뽑아, 사람이 원문·정답을 모른 채
문장만 보고 판정을 고르게 한다. 정답 키는 페이지와 다른 파일에 둔다.
"""
import json
import random
from collections import Counter, defaultdict

from . import paraphrase as P

# 라벨별 표본 수 (합 100). 드문 라벨도 몇 개는 보이도록 최소치를 두고 나머지는 빈도 순
QUOTA = {"ball": 15, "strike": 12, "foul": 12, "out": 10, "reach": 8, "strikeout": 8, "walk": 6,
         "double_play": 4, "none": 25}

# 페이지에 보여줄 선택지 (번호 키로도 고를 수 있음). 검증 LLM에 준 선택지와 같은 구성
CHOICES = [
    ("ball", "볼"),
    ("strike", "스트라이크 (루킹·헛스윙)"),
    ("foul", "파울"),
    ("strikeout", "삼진"),
    ("walk", "볼넷·몸에 맞는 공"),
    ("reach", "안타·장타·홈런·실책 (타자 출루)"),
    ("out", "범타 아웃 (땅볼·뜬공·희생타)"),
    ("double_play", "병살"),
    ("none", "판정 정보 없음 (잡담·일반론)"),
]


def sample_items(rows, clips_by_id, quota=QUOTA, seed=0):
    """rows = 07의 scripts.jsonl 내용, clips_by_id = clip_id → 이벤트가 있는 클립"""
    pool = defaultdict(list)
    for r in rows:
        events = clips_by_id[r["clip_id"]]["events"]
        for i, u in enumerate(r["utts"]):
            if "orig" not in u:  # 의역이 반영된 발화만
                continue
            label = "none" if u["kind"] in ("comment", "distract") else P.expected_label(events[u["event_idx"]])
            pool[label].append({"clip_id": r["clip_id"], "utt": i, "speaker": u["speaker"], "kind": u["kind"],
                                "text": u["text"], "orig": u["orig"], "label": label})
    rng = random.Random(seed)
    items = []
    for label, n in quota.items():
        items += rng.sample(pool[label], min(n, len(pool[label])))
    rng.shuffle(items)  # 라벨 순서가 드러나지 않게 섞는다
    for k, it in enumerate(items):
        it["id"] = k
    return items


def write_page(items, path):
    """정답 없이 문장·화자만 담은 판정 페이지 (단일 HTML, 인터넷 없이 열림)"""
    blind = [{"id": it["id"], "who": "캐스터" if it["speaker"] == "caster" else "해설위원", "text": it["text"]}
             for it in items]
    data = json.dumps({"items": blind, "choices": CHOICES}, ensure_ascii=False).replace("</", "<\\/")
    path.write_text(PAGE.replace("__DATA__", data), encoding="utf-8")


def score(key_items, result):
    """key_items = 정답 키, result = 페이지에서 내려받은 결과 → 라벨별 일치율과 틀린 문장"""
    answers = {int(a["id"]): a for a in result["answers"]}
    by_label = defaultdict(Counter)
    wrong, awkward = [], []
    for it in key_items:
        a = answers.get(it["id"])
        if a is None:
            continue
        ok = a["label"] == it["label"]
        by_label[it["label"]]["n"] += 1
        by_label[it["label"]]["ok"] += ok
        if not ok:
            wrong.append({**it, "human": a["label"]})
        if a.get("awkward"):
            awkward.append(it)
    n = sum(c["n"] for c in by_label.values())
    ok = sum(c["ok"] for c in by_label.values())
    return {"n": n, "ok": ok, "by_label": {k: dict(v) for k, v in by_label.items()},
            "wrong": wrong, "awkward": awkward}


PAGE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>의역 점검</title>
<style>
:root {
  --bg: #f7f6f3; --card: #ffffff; --ink: #1f1f1d; --muted: #6b6a66; --line: #e2e0da;
  --accent: #2f5d8a; --accent-ink: #ffffff; --pick: #e7eef6; --warn: #b4542d;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #161615; --card: #1f1f1e; --ink: #ecebe7; --muted: #a09e98; --line: #34332f;
          --accent: #7fa8d1; --accent-ink: #10161c; --pick: #26313c; --warn: #e08a63; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
       font: 16px/1.6 "Pretendard", "Apple SD Gothic Neo", "Malgun Gothic", system-ui, sans-serif; }
main { max-width: 640px; margin: 0 auto; padding: 32px 16px 48px; }
h1 { font-size: 18px; margin: 0 0 4px; }
.sub { color: var(--muted); font-size: 14px; margin: 0 0 24px; }
.bar { height: 4px; background: var(--line); border-radius: 2px; overflow: hidden; margin-bottom: 8px; }
.bar > div { height: 100%; background: var(--accent); width: 0; transition: width .15s; }
.count { color: var(--muted); font-size: 13px; margin-bottom: 16px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 24px; }
.who { color: var(--muted); font-size: 13px; margin-bottom: 6px; }
.text { font-size: 21px; line-height: 1.5; margin-bottom: 22px; word-break: keep-all; }
.choices { display: grid; gap: 8px; }
button { font: inherit; color: inherit; cursor: pointer; }
.choice { text-align: left; background: transparent; border: 1px solid var(--line); border-radius: 8px;
          padding: 10px 12px; display: flex; gap: 10px; align-items: baseline; }
.choice:hover { border-color: var(--accent); }
.choice.on { background: var(--pick); border-color: var(--accent); }
.key { color: var(--muted); font-size: 13px; min-width: 1em; font-variant-numeric: tabular-nums; }
.row { display: flex; justify-content: space-between; align-items: center; margin-top: 18px; gap: 8px; flex-wrap: wrap; }
.ghost { background: transparent; border: 1px solid var(--line); border-radius: 8px; padding: 8px 12px; }
.ghost.on { border-color: var(--warn); color: var(--warn); }
.primary { background: var(--accent); color: var(--accent-ink); border: 0; border-radius: 8px; padding: 10px 16px; }
.hint { color: var(--muted); font-size: 13px; margin-top: 16px; }
.done { text-align: center; }
</style>
</head>
<body>
<main>
  <h1>의역 문장 점검</h1>
  <p class="sub">문장만 보고, 이 말이 알려주는 판정을 고르세요. 정답은 보이지 않습니다.</p>
  <div class="bar"><div id="fill"></div></div>
  <div class="count" id="count"></div>
  <div id="view"></div>
  <p class="hint">숫자 키 1–9로 선택하면 다음 문장으로 넘어가요 · 문장이 어색하면 고르기 <b>전에</b> A ·
    ← 이전 · 중간에 닫아도 이 브라우저에 저장돼요</p>
</main>
<script>
const DATA = __DATA__;
const KEY = "kbo-audit-v1";
let state = { pos: 0, answers: {} };
try { const s = JSON.parse(localStorage.getItem(KEY)); if (s && s.answers) state = s; } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} };
const view = document.getElementById("view");

function render() {
  const n = DATA.items.length, done = Object.keys(state.answers).length;
  document.getElementById("fill").style.width = (100 * done / n) + "%";
  document.getElementById("count").textContent = `${done} / ${n} 완료`;
  if (state.pos >= n) return renderDone();
  const it = DATA.items[state.pos], a = state.answers[it.id] || {};
  view.innerHTML = `<div class="card">
    <div class="who">${state.pos + 1}번 · ${it.who}</div>
    <div class="text"></div>
    <div class="choices">${DATA.choices.map(([k, name], i) =>
      `<button class="choice ${a.label === k ? "on" : ""}" data-k="${k}"><span class="key">${i + 1}</span>${name}</button>`).join("")}</div>
    <div class="row">
      <button class="ghost" id="prev" ${state.pos === 0 ? "disabled" : ""}>← 이전</button>
      <button class="ghost ${a.awkward ? "on" : ""}" id="awk">어색함${a.awkward ? " ✓" : ""}</button>
    </div></div>`;
  view.querySelector(".text").textContent = it.text;
  view.querySelectorAll(".choice").forEach(b => b.onclick = () => pick(b.dataset.k));
  document.getElementById("prev").onclick = prev;
  document.getElementById("awk").onclick = toggleAwk;
}
function pick(k) {
  const it = DATA.items[state.pos];
  state.answers[it.id] = { ...(state.answers[it.id] || {}), id: it.id, label: k };
  state.pos += 1; save(); render();
}
function prev() { if (state.pos > 0) { state.pos -= 1; save(); render(); } }
function toggleAwk() {
  const it = DATA.items[state.pos]; if (!it) return;
  const a = state.answers[it.id] || { id: it.id };
  a.awkward = !a.awkward; state.answers[it.id] = a; save(); render();
}
function renderDone() {
  const missing = DATA.items.filter(it => !(state.answers[it.id] || {}).label).length;
  view.innerHTML = `<div class="card done">
    <p>${missing ? `아직 ${missing}개가 남았어요.` : "모두 끝났어요. 결과 파일을 저장해 주세요."}</p>
    <div class="row" style="justify-content:center">
      <button class="ghost" id="back">← 돌아가기</button>
      <button class="primary" id="dl">결과 저장 (audit_result.json)</button>
    </div></div>`;
  document.getElementById("back").onclick = () => { state.pos = Math.max(0, DATA.items.length - 1); render(); };
  document.getElementById("dl").onclick = () => {
    const blob = new Blob([JSON.stringify({ answers: Object.values(state.answers) }, null, 1)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = "audit_result.json"; a.click();
  };
}
document.addEventListener("keydown", e => {
  if (state.pos >= DATA.items.length) return;
  const i = parseInt(e.key, 10);
  if (i >= 1 && i <= DATA.choices.length) pick(DATA.choices[i - 1][0]);
  else if (e.key === "a" || e.key === "A") toggleAwk();
  else if (e.key === "ArrowLeft") prev();
});
render();
</script>
</body>
</html>
"""
