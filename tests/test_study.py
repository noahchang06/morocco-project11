import unittest
from morocco.study import baseline, metrics, split, validate

class StudyTests(unittest.TestCase):
    def test_future_not_operational(self):
        for text in ['The system will deploy next year.', 'Le système sera déployé en 2027.']:
            self.assertEqual(baseline({'record_id': 'a', 'evidence': [{'quote': text}]})['label'], 'announced')

    def test_negation_and_conflicts_abstain(self):
        for text in ['The system is not in production.', 'It is in production. Another pilot is testing.']:
            self.assertEqual(baseline({'record_id': 'a', 'evidence': [{'quote': text}]})['label'], 'insufficiently_supported')

    def test_organization_disjoint(self):
        result = split([{'record_id': 'a', 'organization_id': 'org'}, {'record_id': 'b', 'organization_id': 'org'}])
        self.assertEqual(result['a'], result['b'])

    def test_metric_denominator(self):
        result = metrics({'a': 'pilot', 'b': 'operational'}, {'a': 'operational', 'b': 'operational'})
        self.assertEqual(result['false_operational_rate'], .5)
        with self.assertRaises(ValueError):
            metrics({'a': 'pilot'}, {})

    def test_exact_quote_required(self):
        r = dict(record_id='a', organization_id='o', organization='O', use_case='AI', moroccan_location='Rabat', evidence=[dict(document_id='d', page=1, start=0, end=3, quote='bad')])
        with self.assertRaises(ValueError):
            validate([r], [dict(document_id='d', page=1, text='yes')])
