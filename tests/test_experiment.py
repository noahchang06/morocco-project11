import json
from pathlib import Path
import tempfile
import unittest
from morocco.experiment import agreement, bootstrap, check_predictions, evaluate, freeze, verify, write_jsonl
from morocco.review import build
from morocco.study import split

class ExperimentTests(unittest.TestCase):
    def fixture(self):
        records=[];pages=[]
        for i in range(40):
            text='The AI system is in production.'
            pages.append(dict(document_id=str(i),page=1,text=text))
            records.append(dict(record_id=str(i),organization_id='org'+str(i),organization='Synthetic',use_case='Synthetic AI',moroccan_location='Synthetic location',label='SECRET_LABEL',evidence=[dict(document_id=str(i),page=1,start=0,end=len(text),quote=text)]))
        return records,pages

    def test_freeze_evaluate_and_tamper(self):
        records,pages=self.fixture()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);run=p/'run'
            freeze(records,pages,run,'fixture-model','2026-10-17')
            self.assertNotIn('SECRET_LABEL',(run/'inputs.jsonl').read_text())
            predictions=[dict(record_id=r['record_id'],label='operational',quote=r['evidence'][0]['quote'],evidence_index=0) for r in records]
            write_jsonl(p/'pred.jsonl',predictions)
            assignments=split(records)
            gold=[dict(record_id=r['record_id'],label='operational') for r in records if assignments[r['record_id']]=='test']
            write_jsonl(p/'gold.jsonl',gold)
            result=evaluate(run,p/'pred.jsonl',p/'gold.jsonl',p/'results',iterations=100)
            # Fixed four-class macro-F1 is .25 when only one class has support.
            self.assertEqual(result['metrics']['model']['macro_f1'],.25)
            self.assertEqual(result['bootstrap']['95_percent_intervals']['model_minus_rules'],[0,0])
            with self.assertRaises(FileExistsError):freeze(records,pages,run,'model','2026-10-17')
            (run/'inputs.jsonl').write_text('tampered')
            with self.assertRaises(ValueError):verify(run)

    def test_invalid_quote_and_missing_predictions(self):
        records,_=self.fixture();r=records[:1]
        with self.assertRaises(ValueError):check_predictions(r,[])
        with self.assertRaises(ValueError):check_predictions(r,[dict(record_id='0',label='operational',quote='invented',evidence_index=0)])
        check_predictions(r,[dict(record_id='0',label='insufficiently_supported',quote='',evidence_index=None)])

    def test_agreement(self):
        a={'a':'pilot','b':'operational'}
        self.assertEqual(agreement(a,a)['cohen_kappa'],1)
        self.assertEqual(agreement(a,{'a':'operational','b':'pilot'})['cohen_kappa'],-1)
        self.assertIsNone(agreement({'a':'pilot'},{'a':'pilot'})['cohen_kappa'])

    def test_review_packet_hides_labels_and_escapes_scripts(self):
        records,pages=self.fixture()
        records[0]['organization']='</script><script>bad()</script>'
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);write_jsonl(p/'pages.jsonl',pages)
            build(p,p/'packet.html',records)
            html=(p/'packet.html').read_text()
            self.assertNotIn('SECRET_LABEL',html)
            self.assertNotIn('</script><script>bad()',html)

if __name__=='__main__':unittest.main()
