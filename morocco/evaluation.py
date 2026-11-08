"""Score response failures without turning them into deployment-stage labels."""
from .study import LABELS, metrics


def failure_metrics(gold, predictions):
    """None denotes an explicitly logged response failure, never a gold label.

    Each failure contributes a false negative to its gold class and no false
    positive to a deployment class. Macro-F1 still averages exactly four stages.
    """
    if not gold or set(gold) != set(predictions):
        raise ValueError('Require nonempty gold and exactly matching prediction IDs')
    if any(v not in LABELS for v in gold.values()) or any(
            v is not None and v not in LABELS for v in predictions.values()):
        raise ValueError('Unknown label')
    failed = sum(v is None for v in predictions.values())
    if not failed:
        result = metrics(gold, predictions)
        return {**result, 'prediction_columns': LABELS, 'response_failures': 0,
                'accepted_predictions': len(gold), 'output_coverage': 1.0}
    matrix = [[0] * 5 for _ in LABELS]
    for key, actual in gold.items():
        predicted = predictions[key]
        matrix[LABELS.index(actual)][4 if predicted is None else LABELS.index(predicted)] += 1
    scores = {}
    for i, label in enumerate(LABELS):
        tp, support = matrix[i][i], sum(matrix[i])
        predicted = sum(row[i] for row in matrix)
        scores[label] = {'precision': tp / predicted if predicted else 0,
                         'recall': tp / support if support else 0,
                         'f1': 2 * tp / (support + predicted) if support + predicted else 0,
                         'support': support}
    op_count = sum(row[0] for row in matrix)
    false_op = op_count - matrix[0][0]
    return {'n': len(gold), 'macro_f1': sum(s['f1'] for s in scores.values()) / 4,
            'per_label': scores, 'labels': LABELS, 'confusion_matrix': matrix,
            'prediction_columns': (*LABELS, 'invalid_output'),
            'response_failures': failed, 'accepted_predictions': len(gold) - failed,
            'output_coverage': (len(gold) - failed) / len(gold),
            'false_operational_numerator': false_op, 'operational_prediction_denominator': op_count,
            'false_operational_rate': false_op / op_count if op_count else None}
