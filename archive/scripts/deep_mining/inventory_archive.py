from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]

ARCHIVE = ROOT / "archive"

counter = Counter()

for f in ARCHIVE.rglob("*"):

    if f.is_file():

        ext = f.suffix.lower()

        if ext:
            counter[ext] += 1
        else:
            counter["no_extension"] += 1

print("\nARCHIVE INVENTORY\n")

for k, v in sorted(counter.items()):
    print(k, ":", v)
