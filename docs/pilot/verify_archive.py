"""Rebuild public counts from the team's November 9 archive without extracting files."""

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import BadZipFile, ZipFile


ROOT = "Morocco_review_2026-11-09/"
MANIFEST_SHA256 = "409a4f377ca776e1320563565e02d2fa95782f106d94064dabaf4c5cfc5a0ea4"
STAGES = ["operational", "pilot", "announced", "insufficiently_supported"]


class VerificationError(Exception):
    """An archive or publication check failed."""


def check_manifests(archive):
    manifest = archive.read(ROOT + "manifest.json")
    if hashlib.sha256(manifest).hexdigest() != MANIFEST_SHA256:
        raise VerificationError("The archive manifest differs from the November 9 version.")
    for directory in (ROOT, ROOT + "llm/frozen/"):
        entries = json.loads(archive.read(directory + "manifest.json"))
        for name, expected in entries.items():
            digest = hashlib.sha256(archive.read(directory + name)).hexdigest()
            if digest != expected:
                raise VerificationError("An archived file differs from its recorded SHA-256.")


def keyed_rows(archive, filename):
    rows = {}
    for line in archive.read(ROOT + filename).splitlines():
        row = json.loads(line)
        key = row["record_id"]
        if key in rows:
            raise VerificationError("A record identifier occurs twice in the same table.")
        rows[key] = row
    return rows


def matrix(pairs):
    counts = [[0 for _ in STAGES] for _ in STAGES]
    for first, second in pairs:
        counts[STAGES.index(first)][STAGES.index(second)] += 1
    return counts


def reconstruct(archive):
    ref = keyed_rows(archive, "adjudicated_reference.jsonl")
    inputs = keyed_rows(archive, "llm/frozen/inputs.jsonl")
    predictions = {
        "rules": keyed_rows(archive, "llm/frozen/rule_predictions.jsonl"),
        "llm": keyed_rows(archive, "llm/run/accepted_predictions.jsonl"),
    }
    if any(method.keys() != inputs.keys() for method in predictions.values()):
        raise VerificationError("The frozen inputs and predictions cover different records.")
    if inputs.keys() - ref.keys() != {"R01"} or not ref.keys() <= inputs.keys():
        raise VerificationError("The adjudicated and sensitivity cohorts differ from the report.")

    primary = {key: row["label"] for key, row in ref.items()}
    # The reported sensitivity calculation restores the excluded record under
    # the alternate label documented in the results archive.
    sensitivity = {**primary, "R01": "insufficiently_supported"}
    matrices = {}
    for name, reference in (("primary", primary), ("all_15_sensitivity", sensitivity)):
        matrices[name] = {
            method: matrix((stage, rows[key]["label"]) for key, stage in reference.items())
            for method, rows in predictions.items()
        }

    reviews = json.loads(archive.read(ROOT + "normalized_reviews.json"))
    first, second = (reviews[key]["rows"] for key in ("yuxin", "supplied_noah_review"))
    # Column H contains the original stage, including one blank.
    if first.keys() != inputs.keys() or second.keys() != inputs.keys():
        raise VerificationError("A supplied review does not cover the original cohort.")
    pairs = ((first[key]["H"], second[key]["H"]) for key in inputs)
    review_counts = matrix(
        (a.replace(" ", "_"), b.replace(" ", "_")) for a, b in pairs if a and b
    )

    sectors = {}
    for key, stage in primary.items():
        sector = inputs[key]["sector"]
        counts = sectors.setdefault(sector, {"before": 0, "after": 0})
        counts["before"] += 1
        if stage != "insufficiently_supported":
            counts["after"] += 1
        elif ref[key]["reason_code"] != "outdated":
            raise VerificationError("The excluded sector counts include another reason code.")
    return {
        "stage_order": STAGES,
        "confusion_matrices": matrices,
        "review_counts": review_counts,
        "sectors": sectors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="path to Morocco_review_2026-11-09.zip")
    args = parser.parse_args()
    try:
        published = json.loads(Path(__file__).with_name("counts.json").read_text(encoding="utf-8"))
        with ZipFile(args.archive) as archive:
            check_manifests(archive)
            rebuilt = reconstruct(archive)
        if published != rebuilt:
            raise VerificationError("The reconstructed totals differ from the public counts.")
    except VerificationError as error:
        parser.exit(1, f"{error}\n")
    except (OSError, BadZipFile, KeyError, ValueError, TypeError) as error:
        parser.exit(1, f"Could not read the required archive and count tables ({type(error).__name__}).\n")
    print("Verified both SHA-256 manifests, both score cohorts, paired review counts, and sector counts.")


if __name__ == "__main__":
    main()
