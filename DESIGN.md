---
name: KBO-Listen
description: 야구 중계를 듣고 그 순간의 볼카운트를 맞히는 음성인식 챌린지
colors:
  ground: "#ffffff"
  ink: "#16191d"
  ink-2: "#4a5059"
  ink-3: "#6b717b"
  rule: "#e3e6ea"
  rule-strong: "#c9ced5"
  panel: "#f5f7f9"
  blue: "#1f5fbf"
  blue-ink: "#174a96"
  blue-wash: "#eaf1fb"
typography:
  display:
    fontFamily: "system-ui, -apple-system, Segoe UI, Apple SD Gothic Neo, Malgun Gothic, Noto Sans KR, sans-serif"
    fontSize: "clamp(30px, 3.4vw, 42px)"
    fontWeight: 700
    lineHeight: 1.22
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "system-ui, -apple-system, Segoe UI, Apple SD Gothic Neo, Malgun Gothic, Noto Sans KR, sans-serif"
    fontSize: "26px"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.015em"
  title:
    fontFamily: "system-ui, -apple-system, Segoe UI, Apple SD Gothic Neo, Malgun Gothic, Noto Sans KR, sans-serif"
    fontSize: "18px"
    fontWeight: 700
    lineHeight: 1.4
  body:
    fontFamily: "system-ui, -apple-system, Segoe UI, Apple SD Gothic Neo, Malgun Gothic, Noto Sans KR, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.7
    fontFeature: "tnum"
  label:
    fontFamily: "system-ui, -apple-system, Segoe UI, Apple SD Gothic Neo, Malgun Gothic, Noto Sans KR, sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.4
  code:
    fontFamily: "ui-monospace, SFMono-Regular, Cascadia Mono, Consolas, D2Coding, monospace"
    fontSize: "13.5px"
    lineHeight: 1.6
rounded:
  tag: "4px"
  chip: "6px"
  button: "7px"
  panel: "8px"
  figure: "10px"
spacing:
  gutter: "24px"
  section: "40px"
  column-gap: "56px"
components:
  button-primary:
    backgroundColor: "{colors.blue}"
    textColor: "{colors.ground}"
    rounded: "{rounded.button}"
    padding: "0 18px"
    height: "42px"
  button-primary-hover:
    backgroundColor: "{colors.blue-ink}"
  button-secondary:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    rounded: "{rounded.button}"
    padding: "0 18px"
    height: "42px"
  query-row:
    backgroundColor: "{colors.blue-wash}"
    textColor: "{colors.blue-ink}"
  key-box:
    backgroundColor: "{colors.panel}"
    rounded: "{rounded.panel}"
    padding: "14px 18px"
  tag:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.tag}"
    padding: "1px 7px"
---

# Design System: KBO-Listen

## Overview

**Creative North Star: "The Benchmark Page"**

ML·음성 벤치마크 사이트의 정석(CHiME Challenge, Hugging Face Open ASR Leaderboard)을 그대로 따르되 마감을 끝까지 다듬은 페이지입니다. 채점자가 과제의 입력, 출력, 질의 시점, 어려운 이유를 한 번에 정확히 이해하는 것이 목표라서, 장식보다 표와 정의와 실제 예시가 화면을 차지합니다.

흰 바탕에 짙은 먹색 글자, 강조색은 파랑 하나뿐입니다. 첫 화면은 제목과 실제 중계 한 장면(발화와 질의가 섞인 표)을 나란히 놓고, 아래는 고정 목차와 본문 한 열로 된 문서입니다. 마케팅 랜딩, 흔한 AI 템플릿(그라데이션, 아이콘 카드, 큰 숫자 타일 줄)은 쓰지 않습니다.

**Key Characteristics:**
- 시스템 서체 하나, 글꼴 파일 없음
- 강조색은 파랑 하나, 질의 행과 링크와 주 버튼에만
- 숫자는 tabular-nums, 표는 오른쪽 정렬
- 모든 숫자에 범위(test만인지 dev+test인지)를 붙인다

## Colors

먹색과 회색 단계 위에 파랑 하나를 올린 학술 문서 팔레트입니다.

### Primary
- **Ledger Blue** (#1f5fbf): 링크, 주 버튼, 포커스 링.
- **Ledger Blue Ink** (#174a96): 호버 상태, 질의 행의 답 글자.
- **Query Wash** (#eaf1fb): 예시 표에서 질의 행의 바탕, 선택 영역.

### Neutral
- **Ground** (#ffffff): 페이지 바탕.
- **Ink** (#16191d): 본문과 제목.
- **Ink 2** (#4a5059): 보조 문장, 정의의 설명, 내비게이션.
- **Ink 3** (#6b717b): 캡션, 표 머리, 시각 표시.
- **Rule** (#e3e6ea) / **Rule Strong** (#c9ced5): 표 줄, 구분선, 보조 버튼 테두리.
- **Panel** (#f5f7f9): 요점 상자, 코드 블록, 태그 바탕.

### Named Rules
**The One Blue Rule.** 파랑은 "누를 수 있는 것"과 "질의"에만 씁니다. 표의 최고점은 굵기로만 표시하고 색을 바꾸지 않습니다.

## Typography

**Body Font:** system-ui (Apple SD Gothic Neo, Malgun Gothic, Noto Sans KR로 대체)
**Mono Font:** ui-monospace (Consolas, D2Coding으로 대체)

**Character:** 운영체제 기본 한글 고딕 하나로 위계를 크기와 굵기로만 만듭니다. 문서처럼 읽히는 것이 목적입니다.

### Hierarchy
- **Display** (700, clamp(30px, 3.4vw, 42px), 1.22): 첫 화면 제목 하나. `text-wrap: balance`, 끊기면 안 되는 구절은 `.nw`로 묶음.
- **Headline** (700, 26px, 1.3): 섹션 제목(h2). 폰에서는 23px.
- **Title** (700, 18px, 1.4): 섹션 안 소제목(h3).
- **Body** (400, 16px, 1.7): 본문. 폭은 콘텐츠 열(최대 820px)을 꽉 채워 표 폭과 맞춥니다. 한글은 `word-break: keep-all`.
- **Label** (600, 13px): 표 머리, 시각, 화자.
- **Code** (13.5px, 1.6): 코드 블록과 파일 이름.

### Named Rules
**The Same Width Rule.** 본문 폭은 표 폭과 같습니다. 본문만 좁게 두면 표 옆에서 어색해집니다.

## Layout

최대 폭 1200px, 좌우 여백 24px. 첫 화면은 두 열(제목 1 : 예시 1.05, 간격 56px), 문서 부분은 200px 고정 목차와 최대 820px 본문 열(간격 56px)입니다. 섹션 사이는 40px. 헤더는 56px 높이로 위에 붙어 있고, 앵커 이동 시 `scroll-padding-top: 72px`.

960px 이하에서 첫 화면은 한 열이 되고 목차는 숨깁니다. 640px 이하에서는 헤더 내비게이션을 숨기고, 정의 목록과 규칙 두 열을 한 열로 바꾸고, 예시 표의 화자 열을 뺍니다. 넓은 표는 가로로 스크롤하며 첫 열을 고정하고, 넘칠 때만 오른쪽 끝을 흐리게 합니다.

## Elevation & Depth

그림자는 없습니다. 깊이는 1px 선과 Panel 바탕색으로만 나눕니다. 위에 붙은 헤더도 반투명 흰 바탕과 아래 선 하나입니다.

## Shapes

모서리는 작게 둥급니다: 태그 4px, 파이프라인 칸 6px, 버튼 7px, 요점 상자와 코드 8px, 예시 표 10px. 표 자체에는 테두리 상자를 두르지 않고 가로줄만 씁니다. 화살표는 유니코드 문자 대신 SVG 마스크로 그립니다.

## Components

### Buttons
- **Shape:** 7px, 높이 42px, 좌우 18px, 15px 600.
- **Primary:** Ledger Blue 바탕에 흰 글자. 호버는 Blue Ink.
- **Secondary:** 흰 바탕, Rule Strong 테두리, 호버 시 테두리만 Ink 3.
- **Focus:** 2px 파랑 외곽선, 3px 띄움.

### Example figure (중계 한 장면)
- 10px 모서리의 표. 머리는 Panel 바탕에 제목과 설명.
- 행마다 시각, 화자, 발화. 질의 행은 Query Wash 바탕에 답을 Blue Ink 650으로.
- 아래에 "설명을 위해 꾸민 장면" 캡션.

### Data tables
- 가로줄만, 머리 13px Ink 3, 숫자 열 오른쪽 정렬과 nowrap.
- 최고점은 700 굵기. 표 아래에 지표 설명(`dl.legend`).
- 좁은 표 520px, 넓은 표 820px 최소 폭. 넘치면 가로 스크롤, 첫 열 고정.

### Key box / Tag / Code
- 요점 상자: Panel 바탕, 8px, 14×18px 안쪽 여백.
- 태그: 12px 600, Panel 바탕, 4px. 리더보드의 "베이스라인" 표시.
- 코드 블록: Panel 바탕, 8px, 가로 스크롤.

### Pipeline / Steps
- 파이프라인: 테두리 칸들을 SVG 화살표로 잇고, 줄이 바뀌어도 화살표는 칸 앞에 붙음.
- 단계 목록: 26px 원 안의 번호(CSS counter)와 본문 두 열.

### Navigation
- 위에 붙은 헤더: 이름 왼쪽, 섹션 링크 오른쪽 14px Ink 2.
- 본문 왼쪽 목차: 1px 세로선, 호버 시 해당 항목에 선이 진해짐.

## Do's and Don'ts

- **Do** 모든 숫자에 범위를 적는다 (test 200클립인지, dev+test 300클립인지).
- **Do** 설명보다 실제 예시(발화와 질의 시각이 섞인 표)를 먼저 보여준다.
- **Do** 한계와 출처를 숨기지 않고 페이지 끝에 적는다.
- **Don't** 그라데이션, 그림자, 아이콘 카드, 큰 숫자 타일 줄을 쓰지 않는다.
- **Don't** 파랑 외의 강조색을 추가하지 않는다.
- **Don't** 참가자, 후기, 외부 결과처럼 존재하지 않는 것을 만들어 넣지 않는다.
