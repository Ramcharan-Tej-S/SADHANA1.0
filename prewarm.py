# prewarm.py — parse every document in uploads/ into the cache ahead of time.
"""
Run this before a demo. It parses each file once and stores the result keyed by
content hash, so uploading any of them during the demo returns in ~0.2s instead
of waiting on OCR and the model.

    python prewarm.py              # warm every file in uploads/
    python prewarm.py --clear      # drop the cache and start over
"""
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CACHE_DIR, UPLOAD_DIR
from agents.syllabus_parser_agent import parse_document

PARSEABLE = (".pdf", ".txt", ".png", ".jpg", ".jpeg", ".webp")


def digest_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:32]


def main():
    if "--clear" in sys.argv:
        removed = 0
        for name in os.listdir(CACHE_DIR) if os.path.isdir(CACHE_DIR) else []:
            os.remove(os.path.join(CACHE_DIR, name))
            removed += 1
        print(f"Cleared {removed} cached parses.")
        return

    os.makedirs(CACHE_DIR, exist_ok=True)
    files = sorted(f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(PARSEABLE))
    if not files:
        print(f"No parseable files in {UPLOAD_DIR}")
        return

    print(f"Warming {len(files)} file(s) into {CACHE_DIR}\n")
    warmed = skipped = failed = 0

    for name in files:
        path = os.path.join(UPLOAD_DIR, name)
        digest = digest_of(path)
        target = os.path.join(CACHE_DIR, f"syllabus-{digest}.json")

        if os.path.exists(target):
            print(f"  [skip]  {name[:58]}")
            skipped += 1
            continue

        t0 = time.time()
        try:
            parsed = parse_document(path, "", "syllabus")
            with open(target, "w", encoding="utf-8") as f:
                json.dump(parsed, f)
            topics = sum(len(u.get("topics", [])) for u in parsed.get("units", []))
            print(f"  [ok]    {name[:58]:<58} {time.time() - t0:5.1f}s  {topics} topics via {parsed.get('_route')}")
            warmed += 1
        except Exception as exc:
            print(f"  [FAIL]  {name[:58]:<58} {str(exc)[:60]}")
            failed += 1

    print(f"\nWarmed {warmed}, skipped {skipped}, failed {failed}.")
    if warmed:
        print("Those uploads will now return in well under a second.")


if __name__ == "__main__":
    main()
