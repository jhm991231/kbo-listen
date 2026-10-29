"""Hugging Face에서 데이터셋 받기

사용법:
    python -m kbolisten.download [--splits dev test] [--out dataset]

저장소의 dataset/에는 평가 파일(질의, 메타, dev 정답)과 dev 음성 5클립만 들어 있다.
전체 음성은 https://huggingface.co/datasets/hyeonmin1/kbo-listen 에서 이 스크립트로 받는다.
이미 받은 파일은 건너뛴다. huggingface_hub가 필요하다 (pip install huggingface_hub).
"""
import argparse

REPO_ID = "hyeonmin1/kbo-listen"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", nargs="+", default=["dev", "test"], choices=["train", "dev", "test"])
    ap.add_argument("--out", default="dataset")
    args = ap.parse_args()

    from huggingface_hub import snapshot_download

    path = snapshot_download(REPO_ID, repo_type="dataset", local_dir=args.out,
                             allow_patterns=[f"{s}/*" for s in args.splits])
    print("받은 위치:", path)


if __name__ == "__main__":
    main()
