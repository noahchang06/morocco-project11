"""Recompute the November 9 pilot tables from the adjacent aggregate counts.

Run with Python 3: python3 docs/pilot/scorecard.py
Rows are reference stages, columns are predictions. For review agreement,
rows and columns refer to the two original reviews before reconciliation.
"""

import json
from pathlib import Path


def classification_scores(matrix, stages):
    actual = [sum(row) for row in matrix]
    predicted = [sum(column) for column in zip(*matrix)]
    f1 = {}
    for index, stage in enumerate(stages):
        denominator = actual[index] + predicted[index]
        f1[stage] = 2 * matrix[index][index] / denominator if denominator else 0

    op = stages.index("operational")
    false_op = predicted[op] - matrix[op][op]
    return {
        "n": sum(actual),
        "macro_f1": sum(f1.values()) / len(stages),
        "stage_f1": f1,
        "false_operational_count": false_op,
        "operational_predictions": predicted[op],
        "false_operational_rate": false_op / predicted[op] if predicted[op] else None,
    }


def review_agreement(matrix):
    rows = [sum(row) for row in matrix]
    columns = [sum(column) for column in zip(*matrix)]
    n = sum(rows)
    matches = sum(row[index] for index, row in enumerate(matrix))
    observed = matches / n
    expected = sum(a * b for a, b in zip(rows, columns)) / n**2
    return {
        "n": n,
        "matches": matches,
        "raw_agreement": observed,
        "cohen_kappa": (observed - expected) / (1 - expected) if expected < 1 else None,
    }


def sector_table(sectors):
    table = {}
    for condition in ("before", "after"):
        counts = {name: values[condition] for name, values in sectors.items()}
        n = sum(counts.values())
        table[condition] = {
            "n": n,
            "represented_sectors": sum(value > 0 for value in counts.values()),
            "sectors": {
                name: {"count": value, "percent": round(100 * value / n, 1)}
                for name, value in counts.items()
            },
        }
    return table


def main():
    path = Path(__file__).with_name("counts.json")
    counts = json.loads(path.read_text(encoding="utf-8"))
    scores = {
        cohort: {
            method: classification_scores(matrix, counts["stage_order"])
            for method, matrix in methods.items()
        }
        for cohort, methods in counts["confusion_matrices"].items()
    }
    scores["review_agreement"] = review_agreement(counts["review_counts"])
    scores["sector_table"] = sector_table(counts["sectors"])
    print(json.dumps(scores, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
