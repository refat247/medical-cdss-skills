"""Source fidelity, formulation ownership, unsafe text and legacy behavior tests."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
import build_guide as builder
from reference_layout import validate_entry, render_entry, check_reference_artifact, density_findings


def entry():
    lines = ['Example drug\n', 'Regular syrup: 125 mg/5 ml\n', 'Example: 0.5 ml/kg/dose; use this preparation only.\n',
             'DS/Forte: 250 mg/5 ml\n', 'Example: 0.25 ml/kg/dose\n', 'Loading: 5 mg/kg.\n',
             'Dilution: 1:1000; Inj. Example.\n', 'Maintenance: 2.5 mg/kg/dose\n', 'requires clinical/source review']
    roles = ['heading','preparation','example','preparation','example','loading','dilution','maintenance','review']
    rows=[];start=0
    for i,(line,role) in enumerate(zip(lines,roles)):
        end=start+len(line)
        group='regular' if i in [1,2] else 'ds' if i in [3,4] else ''
        rows.append({'start':start,'end':end,'role':role,'group':group});start=end
    return {'schema':'reference-entry-v1','source_text':''.join(lines),'rows':rows,
            'explanation_bn':'Concentration বদলালে ml বদলায়।','locator':'Supplied fixture, not a clinical source'}


class ReferenceTests(unittest.TestCase):
    def test_exact_text_and_relationship(self):
        e=entry();out=render_entry(e,'reference-1')
        self.assertEqual(check_reference_artifact(out),[])
        self.assertLess(out.index('data-formulation="regular"'),out.index('0.5 ml/kg/dose'))
        self.assertLess(out.index('data-formulation="ds"'),out.index('0.25 ml/kg/dose'))
        self.assertIn('lang="bn"',out)
    def test_missing_overlap_reorder_rejected(self):
        for kind in ['gap','overlap','reorder','tail','bool','role']:
            e=entry()
            if kind=='gap':e['rows'][1]['start']+=1
            if kind=='overlap':e['rows'][1]['start']-=1
            if kind=='reorder':e['rows'][1],e['rows'][2]=e['rows'][2],e['rows'][1]
            if kind=='tail':e['rows'].pop()
            if kind=='bool':e['rows'][0]['start']=False
            if kind=='role':e['rows'][0]['role']='verified'
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate_entry(e)
    def test_group_reuse_rejected(self):
        e=entry();e['rows'][-1]['group']='regular'
        with self.assertRaises(ValueError):validate_entry(e)
    def test_tampering_detected(self):
        out=render_entry(entry(),'reference-1')
        self.assertTrue(check_reference_artifact(out.replace('0.5 ml/kg/dose','0.8 ml/kg/dose',1)))
        self.assertTrue(check_reference_artifact(out.replace('data-start="0"','data-start="1"',1)))
        self.assertTrue(check_reference_artifact(out+out))
        self.assertTrue(check_reference_artifact(out.replace('data-formulation="regular"', 'data-formulation="ds"', 1)))
        self.assertTrue(check_reference_artifact(out.replace('reference-heading', 'reference-dose', 1)))
    def test_escaped_untrusted_source(self):
        s='Dose: <script>alert(1)</script> & </script> **unchanged**'
        e={'schema':'reference-entry-v1','source_text':s,'rows':[{'start':0,'end':len(s),'role':'source'}]}
        out=render_entry(e,'reference-1')
        self.assertNotIn('<script>alert',out);self.assertEqual(check_reference_artifact(out),[])
    def test_markdown_fence_and_legacy(self):
        md='# Book\n\n## Section\n\n### Chapter\n\n```reference-entry\n'+json.dumps(entry(),ensure_ascii=False)+'\n```\n\nOrdinary prose.\n\n- ordinary bullet\n'
        title,sections,intro=builder.parse_markdown(md)
        self.assertEqual(sections[0]['chapters'][0]['blocks'][0][0],'reference')
        out=builder.render(title,'investigation',sections,intro=intro)
        self.assertEqual(check_reference_artifact(out),[])
        self.assertIn('<li>ordinary bullet</li>',out)
        self.assertIn('<p>Ordinary prose.</p>',out)
    def test_repeat_entry_has_unique_ids(self):
        e=entry();sections=[{'title':'S','chapters':[{'title':'C','blocks':[('reference',e),('reference',e)]}]}]
        out=builder.render('Book','investigation',sections)
        self.assertEqual(check_reference_artifact(out),[])
        self.assertIn('data-reference-id="reference-2"',out)
    def test_malformed_fence_fails(self):
        for body in ['```reference-entry\n{}\n```','```reference-entry\n{}']:
            with self.assertRaises((ValueError,json.JSONDecodeError)):builder.parse_markdown('# B\n## S\n### C\n'+body)
    def test_density_is_report_only(self):
        t='Dose: 10 mg/kg/day; Syrup: 100 mg/5 ml. '+('source text '*25)
        findings=density_findings([{'title':'S','chapters':[{'title':'C','blocks':[('ul',[t])]}]}],[])
        self.assertEqual(len(findings),1)
        self.assertEqual(findings[0]['status'],'READABILITY REVIEW REQUIRED')
    def test_strict_density_cli(self):
        import sys
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'input.md';out=Path(folder)/'guide.html'
            source.write_text('# B\n## S\n### C\n'+('Dense source words '*30))
            with patch.object(sys,'argv',['build',str(source),'--out',str(out),'--density-policy','error']),self.assertRaises(SystemExit) as caught:
                builder.main()
            self.assertEqual(caught.exception.code,3);self.assertFalse(out.exists())
    def test_cli_artifact_and_census_loss(self):
        import sys
        from unittest.mock import patch
        import check_guide
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'input.md';out=Path(folder)/'guide.html'
            source.write_text('# Book\n## Section\n### Chapter\n```reference-entry\n'+json.dumps(entry(),ensure_ascii=False)+'\n```',encoding='utf-8')
            with patch.object(sys,'argv',['build',str(source),'--out',str(out)]):builder.main()
            with patch.object(sys,'argv',['check',str(out)]):self.assertEqual(check_guide.main(),0)
            text=out.read_text()
            import re
            text=re.sub(r'<section class="reference-entry".*?</section>','',text,flags=re.S)
            out.write_text(text)
            with patch.object(sys,'argv',['check',str(out)]):self.assertEqual(check_guide.main(),1)

if __name__=='__main__':unittest.main()
