"""Build offline evidence collection or prediction-free reviewer packets."""
import argparse
import json
from pathlib import Path
from .study import read_jsonl, validate
from .evidence import prepare


def build(processed, output, records=None, as_of_date=None, outdated_years=2):
    pages=read_jsonl(Path(processed)/'pages.jsonl')
    if records is not None:
        dates={r.get('as_of_date') for r in records if r.get('as_of_date')}
        if len(dates)>1:
            raise ValueError('Reviewer records contain inconsistent evidence cutoffs')
        cutoff=as_of_date or next(iter(dates),None)
        data=prepare(records,pages,cutoff,outdated_years)
        mode='labels'
    else:
        rows=read_jsonl(Path(processed)/'inventory.jsonl')
        data=[{'title':r['path'],'pages':[p for p in pages if p['document_id']==r['document_id']]} for r in rows if 'document_id' in r]
        mode='evidence'
    payload=json.dumps(data,ensure_ascii=True).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    Path(output).write_text(HTML.replace('__MODE__',json.dumps(mode)).replace('__DATA__',payload),encoding='utf-8')

HTML=r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Morocco evidence review</title>
<style>body{font:16px system-ui;max-width:1050px;margin:30px auto;padding:20px;background:#f3f6f7;color:#193342}section{background:white;padding:20px;border-radius:12px;margin:20px 0}input,select,textarea,button{font:inherit;padding:9px;margin:5px;max-width:95%}label{display:block}button{background:#17516a;color:white;border:0;border-radius:6px;cursor:pointer}#text{white-space:pre-wrap;max-height:450px;overflow:auto;background:#eef3f5;padding:18px}#text pre{white-space:pre-wrap;font:inherit}#status{color:#8b3300}textarea{width:90%}</style>
<h1>Morocco deployment review</h1><p id="intro"></p><p>Offline tool. Export before closing or reloading: work is held in memory, with no automatic save.</p>
<section><input id="filter" placeholder="Filter documents"><select id="item"></select><div id="paging"><button id="prev">Previous page</button><span id="num"></span><button id="next">Next page</button></div><div id="text" dir="auto"></div><button id="capture">Use selected passage</button><p id="selection"></p></section>
<section id="fields"><h2>Deployment details</h2><p>Verify extracted text against the PDF. Keep dates and negation in your selection.</p></section>
<section id="saved-records"><h2>Saved records</h2><p id="saved-summary">No saved records.</p><button id="new-record">New record</button><select id="saved-record"></select><button id="load-record">Load record</button><button id="delete-record">Delete record</button><br><select id="saved-evidence"></select><button id="load-evidence">Load evidence</button><button id="delete-evidence">Delete evidence</button></section>
<section id="labels"><h2>Independent review</h2><p>First verify the organization, AI task and Moroccan location against the supplied sources. Keep model outputs and other reviewers’ labels hidden. If a field needs correction, describe it in notes; this is not an uncertainty label.</p><label>Reviewer ID <input id="reviewer"></label><label>Guide version <input id="guide" value="2026-11-08-execution-v1"></label><label>Human field verification <select id="review-status"><option value="">Choose verification status</option><option value="confirmed">Confirmed</option><option value="needs_correction">Needs correction</option></select></label><fieldset id="annotation"><legend>Stage annotation after field verification</legend><label>Label <select id="label"><option value="">Choose label</option><option>operational</option><option>pilot</option><option>announced</option><option>insufficiently_supported</option></select></label><label>Reason code (required only for insufficiently_supported) <select id="reason-code"><option value="">Choose reason</option><option>outdated</option><option>conflicting</option><option>ambiguous</option><option>unverified</option></select></label><label>Rationale <textarea id="rationale"></textarea></label><label>Exact decisive quote <textarea id="decisive-quote" placeholder="Copy verbatim from the selected evidence context, preserving line breaks and spaces."></textarea></label><label>Evidence index (0-based: first passage is 0) <input id="evidence-index" type="number" min="0" step="1"></label><p>A maturity label requires an exact quote and its evidence index. For insufficiently_supported, both may be left empty when no passage supports a stage.</p></fieldset><label><input id="translation-assisted" type="checkbox"> French translation assistance used</label><label>Notes (required for corrections; describe any French translation assistance) <textarea id="notes"></textarea></label></section>
<section><button id="save">Save entry</button><button id="export">Export JSONL</button><label>Resume export <input id="resume" type="file" accept=".jsonl"></label><p id="status" role="status"></p></section>
<script>
const data=__DATA__,mode=__MODE__,$=id=>document.getElementById(id);
let current=0,page=0,selected=null,saved={},editingId=null;
const requiredFields=['record_id','organization_id','organization','use_case','moroccan_location'];
const recordFields=[...requiredFields,'sector','partner','organization_origin','ownership','as_of_date'];
const evidenceFields=['source_date','source_type','language','source_url'];
const fields=[...recordFields,...evidenceFields];
$('intro').textContent=mode==='evidence'?'Select exact evidence and record the organization, use case and Moroccan location. Reuse a record ID to add supporting passages.':'Verify fields and label independently using the same label-free evidence packet supplied to both classifiers. No model predictions, screening decisions or other reviewers’ labels are included.';
$('fields').hidden=mode!=='evidence';$('saved-records').hidden=mode!=='evidence';$('labels').hidden=mode!=='labels';$('capture').hidden=mode!=='evidence';$('paging').hidden=mode!=='evidence';$('filter').hidden=mode!=='evidence';
for(const k of fields){const l=document.createElement('label');l.textContent=k.replaceAll('_',' ')+(requiredFields.includes(k)?'':' (optional)');const input=document.createElement('input');input.id=k;if(k==='source_date'||k==='as_of_date')input.type='date';if(k==='source_url')input.type='url';l.append(input);$('fields').append(l)}
function status(s){$('status').textContent=s+' Saved entries: '+Object.keys(saved).length}
const stageLabels=['operational','pilot','announced','insufficiently_supported'],reasonCodes=['outdated','conflicting','ambiguous','unverified'];
const nonempty=x=>typeof x==='string'&&x.trim().length>0;
function labelError(r){
 const d=data.find(d=>d.record_id===r.record_id);
 if(!d||!nonempty(r.reviewer_id))return 'Wrong reviewer packet or missing reviewer ID.';
 if(!nonempty(r.annotation_guide_version))return 'Guide version required.';
 if(typeof r.notes!=='string'||typeof r.translation_assisted!=='boolean')return 'Notes and translation-assistance status required.';
 if(r.review_status==='needs_correction'){
  if(!r.notes.trim())return 'Describe the field correction in notes.';
  if(r.label!==null)return 'A record needing correction must have a null label.';
  return '';
 }
 if(r.review_status!=='confirmed')return 'Choose a human field-verification status.';
 if(!stageLabels.includes(r.label)||!nonempty(r.rationale))return 'Label and rationale required after field verification.';
 if(r.label==='insufficiently_supported'){
  if(!reasonCodes.includes(r.reason_code))return 'Choose one reason code for insufficiently_supported.';
 }else if(r.reason_code!==null)return 'Reason code must be null for maturity labels.';
 if(r.label==='insufficiently_supported'&&(r.quote===''||r.quote===null)&&r.evidence_index===null)return '';
 if(!nonempty(r.quote)||!Number.isInteger(r.evidence_index)||r.evidence_index<0||r.evidence_index>=d.evidence.length)return 'An exact decisive quote and valid 0-based evidence index are required.';
 const e=d.evidence[r.evidence_index];
 if(!(e.context??e.quote).includes(r.quote))return 'Quote must match the selected evidence context exactly, including spaces and line breaks.';
 return '';
}
function labelControls(){$('annotation').disabled=$('review-status').value!=='confirmed';$('reason-code').disabled=$('label').value!=='insufficiently_supported'}
function readLabel(){const confirmed=$('review-status').value==='confirmed',label=confirmed?$('label').value:null,index=$('evidence-index').value;return {record_id:data[current].record_id,reviewer_id:$('reviewer').value.trim(),review_status:$('review-status').value,label,rationale:confirmed?$('rationale').value.trim():'',reason_code:label==='insufficiently_supported'?$('reason-code').value:null,quote:confirmed?$('decisive-quote').value:'',evidence_index:confirmed&&index!==''?Number(index):null,notes:$('notes').value.trim(),translation_assisted:$('translation-assisted').checked,annotation_guide_version:$('guide').value.trim()}}
function showLabel(r){$('review-status').value=r?.review_status||'';$('label').value=r?.label||'';$('rationale').value=r?.rationale||'';$('reason-code').value=r?.reason_code||'';$('decisive-quote').value=r?.quote||'';$('evidence-index').value=r?.evidence_index??'';$('notes').value=r?.notes||'';$('translation-assisted').checked=r?.translation_assisted===true;if(r){$('reviewer').value=r.reviewer_id;$('guide').value=r.annotation_guide_version}labelControls()}
function showPacket(d){const {evidence,...metadata}=d;$('text').replaceChildren();const details=document.createElement('pre');details.textContent=JSON.stringify(metadata,null,2);$('text').append(details);evidence.forEach((e,i)=>{const heading=document.createElement('h3');heading.textContent='Evidence index '+i;const {context,...source}=e,details=document.createElement('pre');details.textContent=JSON.stringify(source,null,2);const passage=document.createElement('pre');passage.textContent=context??e.quote;$('text').append(heading);$('text').append(details);$('text').append(passage)})}
$('review-status').onchange=labelControls;$('label').onchange=labelControls;
function refreshEvidence(preferred){if(mode!=='evidence')return;const r=saved[$('saved-record').value];$('saved-evidence').replaceChildren();if(!r)return;(r.evidence||[]).forEach((e,i)=>{const o=document.createElement('option');o.value=i;o.textContent=(i+1)+'. '+e.document_id+', physical page '+e.page;$('saved-evidence').append(o)});if(preferred!==undefined&&r.evidence[preferred])$('saved-evidence').value=String(preferred)}
function refreshSaved(preferred){if(mode!=='evidence')return;const ids=Object.keys(saved);$('saved-record').replaceChildren();for(const id of ids){const o=document.createElement('option');o.value=id;o.textContent=id+' — '+(saved[id].organization||'');$('saved-record').append(o)}$('saved-summary').textContent=ids.length?ids.length+' saved record'+(ids.length===1?'':'s')+'. Load one to edit its details or passages.':'No saved records.';if(!ids.length){$('saved-evidence').replaceChildren();return}$('saved-record').value=preferred&&saved[preferred]?preferred:ids[0];refreshEvidence()}
function loadEvidence(){const r=saved[$('saved-record').value],i=Number($('saved-evidence').value);if(!r||!r.evidence[i])return;const e=r.evidence[i],doc=data.findIndex(d=>d.pages.some(p=>p.document_id===e.document_id));if(doc<0)return status('The saved source document is not in this review packet.');$('filter').value='';refresh();current=doc;$('item').value=String(doc);page=Math.max(0,data[doc].pages.findIndex(p=>p.document_id===e.document_id&&p.page===e.page));show();selected={...e};for(const k of evidenceFields)$(k).value=e[k]||'';$('selection').textContent='Loaded '+(e.end-e.start)+' characters on physical page '+e.page}
function loadRecord(){const id=$('saved-record').value,r=saved[id];if(!r)return;editingId=id;for(const k of recordFields)$(k).value=r[k]||'';refreshEvidence();loadEvidence();status('Loaded '+id+'.')}
function show(){selected=null;$('selection').textContent='';const d=data[current];if(!d)return;if(mode==='evidence'){$('text').textContent=d.pages[page]?.text||'[No extracted text; inspect PDF]';$('num').textContent=`Physical page ${page+1} / ${d.pages.length}`}else{showPacket(d);showLabel(saved[d.record_id])}}
function refresh(){$('item').replaceChildren();data.forEach((d,i)=>{if(mode==='evidence'&&!d.title.toLowerCase().includes($('filter').value.toLowerCase()))return;const o=document.createElement('option');o.value=i;o.textContent=mode==='evidence'?d.title:d.record_id+' — '+d.organization;$('item').append(o)});if($('item').options.length){current=Number($('item').value);page=0;show()}else{$('text').textContent='No matching documents';selected=null}}
$('filter').oninput=refresh;$('item').onchange=()=>{current=Number($('item').value);page=0;show()};$('prev').onclick=()=>{page=Math.max(0,page-1);show()};$('next').onclick=()=>{page=Math.min(data[current].pages.length-1,page+1);show()};
$('capture').onclick=()=>{const s=window.getSelection();if(!s.rangeCount)return;const r=s.getRangeAt(0);if(!$('text').contains(r.startContainer)||!$('text').contains(r.endContainer))return;const before=r.cloneRange();before.selectNodeContents($('text'));before.setEnd(r.startContainer,r.startOffset);const quote=r.toString();if(!quote.trim())return;const start=Array.from(before.toString()).length;selected={...data[current].pages[page],start,end:start+Array.from(quote).length,quote};delete selected.text;$('selection').textContent=`Selected ${selected.end-start} characters on physical page ${selected.page}`};
$('save').onclick=()=>{if(mode==='evidence'){if(!selected)return status('Select a passage first.');const entered={};for(const k of recordFields){entered[k]=$(k).value.trim()||null;if(requiredFields.includes(k)&&!entered[k])return status('Complete '+k);}if(editingId&&editingId!==entered.record_id)return status('Record ID cannot be changed while editing.');const old=saved[entered.record_id];if(old&&editingId!==entered.record_id&&requiredFields.slice(1).some(k=>old[k]!==entered[k]))return status('Record ID has conflicting deployment details. Load the record to edit it.');const r=old&&editingId!==entered.record_id?{...old}:entered;r.evidence=old?.evidence||[];const e={...selected};for(const k of evidenceFields)e[k]=$(k).value.trim()||null;const match=r.evidence.findIndex(x=>x.document_id===e.document_id&&x.page===e.page&&x.start===e.start&&x.end===e.end);if(match<0)r.evidence.push(e);else r.evidence[match]=e;saved[r.record_id]=r;editingId=r.record_id;refreshSaved(r.record_id);refreshEvidence(match<0?r.evidence.length-1:match);}else{if(!data[current])return status('No record selected.');const row=readLabel(),error=labelError(row);if(error)return status(error);if(Object.values(saved).some(r=>r.reviewer_id!==row.reviewer_id))return status('Use one reviewer per export.');saved[row.record_id]=row;}status('Saved. Export before closing.');};
$('saved-record').onchange=()=>refreshEvidence();$('load-record').onclick=loadRecord;$('load-evidence').onclick=loadEvidence;
$('new-record').onclick=()=>{editingId=null;for(const k of fields)$(k).value='';selected=null;$('selection').textContent='';status('Ready for a new record. Select a passage.')};
$('delete-record').onclick=()=>{const id=$('saved-record').value;if(!saved[id]||!confirm('Delete saved record '+id+'?'))return;delete saved[id];if(editingId===id)editingId=null;for(const k of fields)$(k).value='';selected=null;$('selection').textContent='';refreshSaved();status('Deleted '+id+'.')};
$('delete-evidence').onclick=()=>{const id=$('saved-record').value,r=saved[id],i=Number($('saved-evidence').value);if(!r||!r.evidence[i])return;if(r.evidence.length===1)return status('A record needs evidence. Delete the record instead.');if(!confirm('Delete this evidence passage?'))return;r.evidence.splice(i,1);refreshEvidence(Math.max(0,i-1));loadEvidence();status('Deleted evidence passage.')};
$('export').onclick=()=>{if(!Object.keys(saved).length)return status('Nothing saved.');const u=URL.createObjectURL(new Blob([Object.values(saved).map(x=>JSON.stringify(x)).join('\n')+'\n'],{type:'application/x-ndjson'}));const a=document.createElement('a');a.href=u;a.download=mode==='evidence'?'records.jsonl':'reviewer-labels.jsonl';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)};
$('resume').onchange=async()=>{try{const rows=(await $('resume').files[0].text()).split(/\r?\n/).filter(x=>x.trim()).map(JSON.parse),next={};for(const r of rows){if(!r.record_id||next[r.record_id])throw Error('Missing or duplicate ID');if(mode==='evidence'&&(!Array.isArray(r.evidence)||!r.evidence.length))throw Error('Expected evidence records');if(mode==='labels'){const error=labelError(r);if(error)throw Error(error);if(Object.values(next).some(x=>x.reviewer_id!==r.reviewer_id))throw Error('Use one reviewer per export.');}next[r.record_id]=r;}saved=next;if(mode==='labels'&&rows.length){$('reviewer').value=rows[0].reviewer_id;$('guide').value=rows[0].annotation_guide_version;}show();refreshSaved();if(mode==='evidence'&&Object.keys(saved).length)loadRecord();status('Imported.')}catch(e){status('Import failed: '+e.message)}finally{$('resume').value=''}};refresh();refreshSaved();
</script></html>'''

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--processed',default='data/processed');p.add_argument('--records');p.add_argument('--output',required=True)
    p.add_argument('--as-of-date');p.add_argument('--outdated-years',type=int,default=2)
    a=p.parse_args();build(a.processed,a.output,read_jsonl(a.records) if a.records else None,a.as_of_date,a.outdated_years)
