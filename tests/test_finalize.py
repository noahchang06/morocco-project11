import copy
import json
from pathlib import Path
import tempfile
import unittest

from morocco.complete_batch import complete
from morocco.experiment import freeze,write_jsonl
from morocco.finalize import prepare_reviews,finalize,validate_reviews
from morocco.run_model import run


class FinalizationTests(unittest.TestCase):
    def setup_case(self,p):
        quote='The synthetic AI service is in production.'
        records=[dict(record_id=k,organization_id=k,organization='Synthetic',use_case='Fixture',moroccan_location='Rabat',
                      record_status='eligible_assistant_screened',eligibility_decision='include',eligibility_rationale='Synthetic screening',human_inclusion_confirmed=False,
                      evidence=[dict(document_id='d',page=1,start=0,end=len(quote),quote=quote,source_date='2026-01-01')]) for k in 'abcd']
        freeze(records,[dict(document_id='d',page=1,text=quote)],p/'frozen','synthetic','2026-11-08',
               split_map={k:'test' for k in 'abcd'},purpose='prediction_pending_human_review')
        labels=dict(a='operational',b='operational',c='pilot',d='announced')
        def annotation(k,person):
            return dict(record_id=k,reviewer_id=person,annotation_guide_version='2026-11-08-execution-v1',
                        review_status='confirmed',label=labels[k],reason_code=None,rationale='Synthetic human fixture',
                        quote=quote,evidence_index=0,notes='',translation_assisted=False)
        a=[annotation(k,'Noah') for k in 'abcd'];b=[annotation(k,'Yuxin') for k in 'abcd']
        write_jsonl(p/'a.jsonl',a);write_jsonl(p/'b.jsonl',b)
        def transport(body):
            k=json.loads(body['input'])['record_id']
            if k=='b':return dict(status='incomplete',model='synthetic',incomplete_details={'reason':'max_output_tokens'},output=[])
            pred={x:annotation(k,'ignored')[x] for x in ['record_id','label','quote','evidence_index','reason_code','rationale']}
            return dict(status='completed',model='synthetic',output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(pred))])])
        with self.assertRaises(ValueError):run(p/'frozen',p/'run',subset='test',transport=transport)
        complete(p/'frozen',p/'run',transport=transport)
        return a,b,quote

    def test_consensus_to_full_cohort_metrics_without_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);self.setup_case(p)
            state=prepare_reviews(p/'frozen',p/'a.jsonl',p/'b.jsonl',p/'review')
            self.assertEqual(state['status'],'ready_for_finalization')
            r=finalize(p/'frozen',p/'review',p/'run',p/'final',iterations=100)
            self.assertAlmostEqual(r['metrics']['model']['macro_f1'],2/3)
            self.assertEqual(r['metrics']['model']['response_failures'],1)
            self.assertEqual(json.loads((p/'final/agreement.json').read_text())['raw_agreement'],1)
            report=(p/'final/report_sections.md').read_text()
            self.assertIn('4 records',report)
            self.assertIn('3 accepted outputs and 1 response failures',report)
            self.assertIn('| model | 0.6667 |',report)
            old=json.loads((p/'frozen/config.json').read_text());self.assertEqual(old['purpose'],'prediction_pending_human_review')
            self.assertEqual((p/'final/human-reviewed-frozen/inputs.jsonl').read_bytes(),(p/'frozen/inputs.jsonl').read_bytes())

    def test_disagreements_require_distinct_adjudicator_and_keep_raw_agreement(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);a,b,q=self.setup_case(p);b[0]['label']='announced';write_jsonl(p/'b.jsonl',b)
            state=prepare_reviews(p/'frozen',p/'a.jsonl',p/'b.jsonl',p/'review')
            self.assertEqual(state['adjudication_ids'],['a'])
            html=(p/'review/adjudication-packet.html').read_text()
            self.assertIn('independent_annotations',html);self.assertNotIn('Synthetic truncated',html)
            with self.assertRaisesRegex(ValueError,'adjudication export'):
                finalize(p/'frozen',p/'review',p/'run',p/'missing',iterations=100)
            write_jsonl(p/'adjudication.jsonl',[a[0]])
            with self.assertRaisesRegex(ValueError,'distinct adjudicator'):
                finalize(p/'frozen',p/'review',p/'run',p/'same',p/'adjudication.jsonl',iterations=100)
            write_jsonl(p/'adjudication.jsonl',[dict(a[0],reviewer_id='Adjudicator')])
            finalize(p/'frozen',p/'review',p/'run',p/'final',p/'adjudication.jsonl',iterations=100)
            self.assertEqual(json.loads((p/'final/agreement.json').read_text())['raw_agreement'],.75)
            self.assertEqual(json.loads((p/'final/gold.jsonl').read_text().splitlines()[0])['reference_origin'],'adjudicated')

    def test_field_corrections_and_changed_reviews_block_finalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);a,b,q=self.setup_case(p)
            b[0].update(review_status='needs_correction',label=None,notes='Wrong organization')
            write_jsonl(p/'b.jsonl',b)
            state=prepare_reviews(p/'frozen',p/'a.jsonl',p/'b.jsonl',p/'review')
            self.assertEqual(state['status'],'blocked_field_corrections')
            self.assertFalse((p/'review/agreement.json').exists())
            with self.assertRaisesRegex(ValueError,'Field corrections'):
                finalize(p/'frozen',p/'review',p/'run',p/'blocked')
            (p/'review/reviewer-a.jsonl').write_text('changed')
            with self.assertRaisesRegex(ValueError,'Frozen artifact changed'):
                finalize(p/'frozen',p/'review',p/'run',p/'changed')

    def test_review_identity_quote_and_missing_raw_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);a,b,q=self.setup_case(p)
            write_jsonl(p/'b.jsonl',[dict(x,reviewer_id=' noah ') for x in b])
            with self.assertRaisesRegex(ValueError,'distinct independent'):
                prepare_reviews(p/'frozen',p/'a.jsonl',p/'b.jsonl',p/'same')
            b[0]['quote']='Invented quotation';write_jsonl(p/'b.jsonl',b)
            with self.assertRaisesRegex(ValueError,'Invalid evidence quotation'):
                prepare_reviews(p/'frozen',p/'a.jsonl',p/'b.jsonl',p/'badquote')
            b[0]['quote']=q;write_jsonl(p/'b.jsonl',b)
            prepare_reviews(p/'frozen',p/'a.jsonl',p/'b.jsonl',p/'review')
            next((p/'run/raw').glob('*.json')).unlink()
            with self.assertRaises(FileNotFoundError):
                finalize(p/'frozen',p/'review',p/'run',p/'noraw')

if __name__=='__main__':unittest.main()
