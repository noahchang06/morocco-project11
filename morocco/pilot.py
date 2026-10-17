"""Reproducible proposal for a 20-document feasibility pilot, not a sampled benchmark."""
import json
from pathlib import Path
from .study import read_jsonl

SELECTION = [
('NVIDIA Datacenters.pdf','deployment lead','Infrastructure project reporting; verify stage and AI use-case eligibility.'),
('Al-Khwarizmi Program1.pdf','deployment lead','Extracted title concerns an AI hub; filename mismatch needs metadata correction.'),
('Institut Jazari ROOT.pdf','boundary case','Institution founding is not by itself evidence of deployed AI.'),
('AI in Education.pdf','deployment lead','Check for specific implemented or planned education use cases.'),
('AI in Morocco.pdf','discovery context','Potential organization leads; verify claims against original sources.'),
('AIReadinessAssessmentMorocco_Report_23-03-24.pdf','discovery context','Readiness context and potential deployment leads.'),
('EHEI-JST_51630-Chouraik+Resent.pdf','discovery context','Research paper; distinguish proposed systems from deployment evidence.'),
('1017-Article Text-3470-1-10-20240709.pdf','discovery context','French-language research source; assess concrete organization-level claims.'),
('Al-Khwarizmi Program.pdf','boundary case','Research funding/program announcements do not establish operation.'),
('Morocco Moves AI Strategy Into Implementation, Targets MAD 100 Bln in GDP Value by 2030 _ Maroc.ma.pdf','boundary case','National implementation claims need organization-specific evidence.'),
('Roadmap.pdf','policy context','Use policy context to check announcement versus demonstrated deployment.'),
('Rapport de Synthèse ANG.pdf','discovery context','Long Morocco AI report; screen for attributable deployment claims.'),
('AI reform.pdf','extraction challenge','Spaced text requires visual reading-order review.'),
('DigitalMorroco2030.pdf','extraction challenge','No meaningful extracted text; inspect and arrange OCR.'),
('ai readiness evaluation.pdf','extraction challenge','No meaningful extracted text; inspect and arrange OCR.'),
('French/Right to Privacy.pdf','boundary case','Regulatory text is context, not evidence of any particular deployment.'),
('canva-sante-en.pdf','sector context','Health-sector context; check for organization-specific AI evidence.'),
('French/health.pdf','translation review','Possible related health document; verify translation group manually.'),
('Enseignement-EN.pdf','sector context','Education strategy; screen for eligible claims.'),
('French/higher education.pdf','translation review','Possible counterpart to English education document; verify manually.')]


def main():
    root=Path('data/processed')
    rows=read_jsonl(root/'inventory.jsonl'); pages=read_jsonl(root/'pages.jsonl')
    by_path={r['path']:r for r in rows}
    out=Path('data/pilot');out.mkdir(parents=True,exist_ok=True)
    selected=[]
    for name,role,reason in SELECTION:
        r=by_path[name]
        selected.append({'document_id':r['document_id'],'path':name,'role':role,'selection_reason':reason,'eligibility':'pending human review','empty_pages':r.get('empty_pages',[])})
    (out/'selection.json').write_text(json.dumps(selected,indent=2,ensure_ascii=False)+'\n')
    quality=[]
    for r in rows:
        texts=[p['text'] for p in pages if p['document_id']==r['document_id']]
        text=''.join(texts)
        controls=sum(ord(c)<32 and c not in '\n\r\t' for c in text)
        quality.append({'path':r['path'],'document_id':r['document_id'],'characters':len(text.strip()),'empty_pages':r.get('empty_pages',[]),'control_character_fraction':controls/max(1,len(text)),'review_flags':(['no meaningful text'] if len(text.strip())<100 else [])+(['possible font encoding corruption'] if controls/max(1,len(text))>.01 else [])})
    (out/'extraction-quality.json').write_text(json.dumps(quality,indent=2,ensure_ascii=False)+'\n')
    md='# Proposed 20-document pilot\n\nThis purposive feasibility selection is not a representative sample or the matched English/French search experiment. Context documents may yield zero eligible deployments. Arabic sources remain preserved in the corpus but outside the original English/French study scope. No labels are assigned.\n\n'
    for i,r in enumerate(selected,1):md+=f"{i}. **{r['path']}** — {r['role']}. {r['selection_reason']}\n\n"
    Path('pilot-plan.md').write_text(md.rstrip() + '\n')

if __name__=='__main__':main()
