# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

static HTML/CSS, single file per page, deployed on GitHub Pages (`docs/`). No build step.

## Users

Primary: the course graders (professor and TAs of Ajou University "Automatic Speech Recognition", Fall 2026). They review the challenge for completeness, originality, and reproducibility, and need to grasp the task precisely and check the design rationale and result numbers quickly.
Secondary: students who would take part — they download the data, develop on train/dev, and submit test predictions.

## Product Purpose

KBO-Listen is a speech-recognition challenge: listen to a synthesized Korean baseball broadcast and answer, at given query times, the current ball–strike–out count. Success for this site: a visitor leaves understanding the task exactly — input, output, when a query is asked, and why it is hard.

## Positioning

The benchmark measures understanding, not transcription. Calls are skipped, described without judgment words, and mixed with misleading analyst talk, so better ASR alone barely helps (baseline CER 12.5% → 3.8% raises Hard exact by only 3.4 points). Ground truth comes from real KBO pitch-by-pitch records, so every answer is factual.

## Operating Context

- Deliverables due 2026-10-29: homepage, benchmark dataset, baseline code, evaluation code.
- Dataset on Hugging Face (`hyeonmin1/kbo-listen`), code on GitHub (`jhm991231/kbo-listen`).
- Submission: participants open a GitHub issue with `pred.json`; organizer scores against private test labels.
- Online rule: the answer at time t may use only speech that finished by t.

## Capabilities and Constraints

- 1,300 half-inning clips, ~35 h, 20,846 queries. train 1,000 / dev 100 / test 200, Easy and Hard tracks split 1:1.
- Hard = skipped calls, distractor analyst lines, LLM-paraphrased calls, rare events.
- Baselines: Whisper large-v3 and Qwen3-ASR + keyword rules + state machine.
- Synthetic audio only; no crowd noise; five voices shared across splits; queries cover B-S-O only.

## Brand Commitments

Name: KBO-Listen. Korean-language site. Must not read as a marketing landing page or a generic AI template (user-stated). Must stay an academic challenge, not a fan site.
Visual direction (2026-10-29, design proposal 1): the category standard for ML/speech benchmark sites, executed at full craft. Quality bar: CHiME Challenge and the Hugging Face Open ASR Leaderboard.

## Evidence on Hand

- Real numbers: dataset stats, baseline scores (dev+test and test-only), human audit of paraphrases (97.3% judgment agreement on 75 call sentences, 13% awkward).
- Audio clips exist on Drive/Hugging Face; no screenshots or illustrations yet.
- No participants, testimonials, or external results exist; none may be invented.

## Product Principles

- Make the task unambiguous before anything else.
- Show the mechanism with real examples (an utterance stream with query times), not adjectives.
- Every number shown is a measured result, with its scope stated (dev+test vs test).
- Honest about limits.
