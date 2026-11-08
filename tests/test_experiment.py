import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from morocco.experiment import agreement, bootstrap, check_predictions, evaluate, freeze, verify, write_jsonl
from morocco.evidence import prepare
from morocco.review import build
from morocco.study import metrics, split

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
        records[0]['organization']='</script><script>bad()</script> & __MODE__'
        records[0].update(eligibility_decision='SECRET_SCREENING',eligibility_rationale='SECRET_SCREENING',model_prediction='SECRET_PREDICTION')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);write_jsonl(p/'pages.jsonl',pages)
            build(p,p/'packet.html',records)
            html=(p/'packet.html').read_text()
            self.assertNotIn('SECRET_LABEL',html)
            self.assertNotIn('SECRET_SCREENING',html)
            self.assertNotIn('SECRET_PREDICTION',html)
            self.assertNotIn('</script><script>bad()',html)
            payload=re.search(r'const data=(.*?),mode=',html).group(1)
            self.assertEqual(json.loads(payload),prepare(records,pages))

    @unittest.skipUnless(shutil.which('node'), 'Node is required to exercise the offline reviewer')
    def test_reviewer_validation_navigation_and_resume_export(self):
        records,pages=self.fixture()
        exact='The AI system is\n  in production.'
        pages[0]['text']=exact
        records[0]['evidence'][0].update(quote=exact,end=len(exact))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);write_jsonl(p/'pages.jsonl',pages)
            build(p,p/'packet.html',records[:3])
            html=(p/'packet.html').read_text()
            script=re.search(r'<script>(.*?)</script>',html,re.S).group(1)
            (p/'generated.js').write_text(script)
            subprocess.run(['node','--check',str(p/'generated.js')],check=True,capture_output=True,text=True)
            # Minimal DOM surface; execute the actual generated script and its event handlers.
            harness=r'''
const assert=require('node:assert/strict');
const elements=new Map();
class Element {
 constructor(tag='input'){this.tag=tag;this.value='';this.checked=false;this.children=[];this.textContent='';}
 append(e){this.children.push(e);if(e.tag==='option'&&this.children.length===1)this.value=String(e.value);}
 replaceChildren(){this.children=[];this.value='';}
 get options(){return this.children;}
 click(){}
}
const document={getElementById(id){if(!elements.has(id))elements.set(id,new Element());return elements.get(id);},createElement(tag){return new Element(tag);}};
let exported;
const URL={createObjectURL(blob){exported=blob;return 'blob:local';},revokeObjectURL(){}};
const setTimeout=callback=>callback();
'''
            guide=re.search(r'id="guide" value="([^"]+)"',html).group(1)
            self.assertEqual(guide,'2026-11-08-execution-v1')
            harness+='document.getElementById("guide").value='+json.dumps(guide)+';\n'+script
            harness+=r'''
(async()=>{
 assert.ok($('text').children.some(e=>e.textContent==='The AI system is\n  in production.')); // Copyable source line breaks.
 $('reviewer').value='independent-reviewer';
 $('label').value='operational';$('rationale').value='The text directly reports production use.';
 $('decisive-quote').value='The AI system is\n  in production.';$('evidence-index').value='0';
 $('save').onclick();assert.equal(Object.keys(saved).length,0); // No implicit verification.
 $('review-status').value='confirmed';$('review-status').onchange();
 $('rationale').value='';$('save').onclick();assert.equal(Object.keys(saved).length,0);
 $('rationale').value='The text directly reports production use.';
 for(const quote of ['Invented quotation','The AI system is in production.']){$('decisive-quote').value=quote;$('save').onclick();assert.equal(Object.keys(saved).length,0);}
 $('decisive-quote').value='The AI system is\n  in production.';
 for(const index of ['','-1','0.5','1']){$('evidence-index').value=index;$('save').onclick();assert.equal(Object.keys(saved).length,0);}
 $('evidence-index').value='0';$('notes').value='French wording checked with translation assistance.';$('translation-assisted').checked=true;
 $('save').onclick();assert.equal(saved['0'].evidence_index,0);assert.equal(saved['0'].reason_code,null);
 assert.equal(saved['0'].review_status,'confirmed');assert.equal(saved['0'].translation_assisted,true);
 const first=JSON.parse(JSON.stringify(saved['0']));
 $('item').value='1';$('item').onchange();assert.equal($('notes').value,'');assert.equal($('translation-assisted').checked,false);
 $('review-status').value='confirmed';$('label').value='insufficiently_supported';$('label').onchange();
 assert.equal($('reason-code').disabled,false);$('rationale').value='The stage wording is unresolved.';
 $('save').onclick();assert.equal(saved['1'],undefined);
 $('reason-code').value='ambiguous';$('save').onclick();assert.equal(saved['1'].label,'insufficiently_supported');
 assert.equal(saved['1'].quote,'');assert.equal(saved['1'].evidence_index,null);
 $('item').value='2';$('item').onchange();$('review-status').value='needs_correction';$('review-status').onchange();
 assert.equal($('annotation').disabled,true);$('label').value='operational';
 $('save').onclick();assert.equal(saved['2'],undefined);
 $('notes').value='The named location does not match the source.';$('save').onclick();
 assert.equal(saved['2'].label,null);assert.equal(saved['2'].review_status,'needs_correction');
 $('item').value='0';$('item').onchange();
 assert.equal($('decisive-quote').value,first.quote);assert.equal(Number($('evidence-index').value),0);
 assert.equal($('notes').value,first.notes);assert.equal($('translation-assisted').checked,true);
 $('export').onclick();const original=await exported.text();const before=JSON.parse(JSON.stringify(saved));
 saved={};$('reviewer').value='';$('guide').value='';
 const resume=async rows=>{$('resume').files=[{text:async()=>rows}];await $('resume').onchange();};
 await resume(original);assert.deepEqual(saved,before);assert.equal($('reviewer').value,first.reviewer_id);
 assert.equal($('guide').value,'2026-11-08-execution-v1');assert.equal($('notes').value,first.notes);
 $('export').onclick();assert.equal(await exported.text(),original);
 for(const change of [{quote:'Not in evidence'},{evidence_index:99},{reason_code:'ambiguous'},{review_status:'needs_correction',notes:'x'}, {review_status:'unknown'}]){
  await resume(JSON.stringify({...first,...change}));assert.deepEqual(saved,before);assert.match($('status').textContent,/Import failed/);
 }
 await resume(JSON.stringify(first)+'\n'+JSON.stringify({...before['1'],reviewer_id:'other'}));
 assert.deepEqual(saved,before);assert.match($('status').textContent,/one reviewer/);
 process.stdout.write(original);
})().catch(error=>{console.error(error);process.exitCode=1;});
'''
            (p/'review-test.js').write_text(harness)
            result=subprocess.run(['node',str(p/'review-test.js')],check=True,capture_output=True,text=True)
            rows=[json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(rows[2]['review_status'],'needs_correction')
            # The existing score/agreement layer rejects the null label, never
            # treating a field correction as an insufficiently-supported stage.
            with self.assertRaises(ValueError):
                agreement({r['record_id']:r['label'] for r in rows},{r['record_id']:'operational' for r in rows})
            with self.assertRaises(ValueError):
                metrics({r['record_id']:r['label'] for r in rows},{r['record_id']:'operational' for r in rows})

    def test_evidence_review_has_metadata_and_edit_controls(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            write_jsonl(p/'inventory.jsonl',[dict(path='source.pdf',document_id='doc-1')])
            write_jsonl(p/'pages.jsonl',[dict(document_id='doc-1',page=1,text='Verified source text.')])
            build(p,p/'review.html')
            html=(p/'review.html').read_text()
            for field in ('sector','partner','organization_origin','ownership','as_of_date','source_url'):
                self.assertIn("'"+field+"'",html)
            for control in ('saved-records','new-record','load-record','delete-record','load-evidence','delete-evidence'):
                self.assertIn('id="'+control+'"',html)
            self.assertIn('editingId',html)
            self.assertIn("$('resume').value=''",html)

if __name__=='__main__':unittest.main()
