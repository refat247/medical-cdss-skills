from pathlib import Path
from scripts.source_inventory_completeness import audit as inventory_audit
from scripts.recommendation_boundary_validator import validate as boundary_validate
from scripts.footnote_binding_validator import validate as footnote_validate
from scripts.source_section_validator import validate as section_validate
from scripts.prompt_semantics_validator import validate as prompt_validate
from scripts.normalization_fidelity_validator import validate as norm_validate
from scripts.repair_fidelity_validator import validate as repair_validate
from scripts.semantic_promotion_gate import evaluate as promotion_evaluate

ROOT=Path(__file__).parents[1]
F=ROOT/'fixtures'/'dyslipidemia_regression'

def test_source_inventory_detects_130_131_style_missing():
    r=inventory_audit(F/'source_inventory.csv',F/'extraction_missing.csv')
    assert not r['pass'] and r['missing']==['SRC-003']

def test_source_inventory_detects_duplicate_source_row_mapping():
    r=inventory_audit(F/'source_inventory.csv',F/'extraction_duplicate.csv')
    assert not r['pass'] and 'SRC-001' in r['duplicate_accounting']

def test_source_inventory_detects_node_mapped_to_multiple_source_rows():
    r=inventory_audit(F/'source_inventory.csv',F/'extraction_node_twice.csv')
    assert not r['pass'] and 'NODE-SHARED' in r['duplicate_node_mapping']


def test_source_inventory_detects_node_mapped_to_no_source_row():
    r=inventory_audit(F/'source_inventory.csv',F/'extraction_orphan_node.csv')
    assert not r['pass'] and r['orphan_nodes']==['NODE-ORPHAN']

def test_source_inventory_good_passes():
    assert inventory_audit(F/'source_inventory.csv',F/'extraction_good.csv')['pass']

def test_boundary_detects_header_doi_table_and_neighbour_heading():
    r=boundary_validate(F/'boundary_failures.csv')
    assert not r['pass']
    blob=' '.join(x['issue'] for x in r['issues'])
    assert 'boundary contamination' in blob and 'unbound associated source object' in blob

def test_footnote_binding_detects_wrong_attachment_and_missing_definition():
    r=footnote_validate(F/'footnote_failures.csv')
    assert not r['pass']
    blob=' '.join(x['issue'] for x in r['issues'])
    assert 'displayed footnote not bound' in blob and 'required footnote definition dropped' in blob

def test_source_section_wrong_chapter_detected_even_if_page_provenance_not_considered():
    r=section_validate(F/'section_nodes_wrong.csv',F/'source_inventory.csv')
    assert not r['pass'] and any('source_section' in x['issue'] for x in r['issues'])

def test_prompt_leak_fragment_synonym_review_and_meaningless_prompt_fail_closed():
    r=prompt_validate(F/'prompt_failures.csv')
    assert not r['pass']
    ids={x['id'] for x in r['issues']}
    assert {'CASE-LEAK','CASE-FRAG','CASE-SYN','CASE-MEANINGLESS'} <= ids

def test_operator_unit_and_exact_typo_mutation_detected():
    r=norm_validate(F/'normalization_failures.csv')
    assert not r['pass']
    blob=' '.join(x['issue'] for x in r['issues'])
    assert 'protected token mutation' in blob and 'exact source text changed' in blob

def test_allowed_normalization_passes():
    assert norm_validate(F/'normalization_good.csv')['pass']

def test_unsupported_repairs_become_defects():
    r=repair_validate(F/'repair_failures.csv')
    assert not r['pass']
    ids={x['id'] for x in r['issues']}
    assert {'R-TIER','R-FOOT','R-TABLE','R-THRESH'} <= ids

def test_visual_pass_cannot_override_semantic_critical_high():
    r=promotion_evaluate(F/'defects_open.csv',F/'gates_all_pass.json')
    assert not r['pass'] and r['promotion_outcome']=='REPAIR_REQUIRED'
    assert r['unresolved_defect_count_by_severity']['CRITICAL']==1
    assert r['unresolved_defect_count_by_severity']['HIGH']==2

def test_full_certification_when_semantic_blockers_closed_and_all_gates_pass():
    r=promotion_evaluate(F/'defects_closed.csv',F/'gates_all_pass.json')
    assert r['pass'] and r['promotion_outcome']=='FULLY_CERTIFIED_CANONICAL'

# v2.2.1 focused hardening regressions
import csv, json
from scripts.source_inventory_certification import certify as source_inventory_certify
from scripts.semantic_promotion_gate import REQUIRED_GATES


def _write_csv(path, fieldnames, rows):
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fieldnames); w.writeheader(); w.writerows(rows)


def _write_gates(path, overrides=None):
    base=json.loads((F/'gates_all_pass.json').read_text())
    if overrides: base.update(overrides)
    path.write_text(json.dumps(base))
    return path


def test_source_lock_waived_cannot_certify(tmp_path):
    g=_write_gates(tmp_path/'g.json',{'source_lock':'WAIVED'})
    r=promotion_evaluate(F/'defects_closed.csv',g)
    assert not r['pass'] and 'source_lock' in r['failed_gates']


def test_every_non_independent_gate_rejects_waived(tmp_path):
    for gate in [x for x in REQUIRED_GATES if x!='independent_visual_qa']:
        g=_write_gates(tmp_path/f'{gate}.json',{gate:'WAIVED'})
        r=promotion_evaluate(F/'defects_closed.csv',g)
        assert not r['pass'] and gate in r['failed_gates']


def test_explicit_independent_qa_waiver_is_only_valid_waiver(tmp_path):
    g=_write_gates(tmp_path/'g.json',{
        'independent_visual_qa':'WAIVED',
        'independent_visual_qa_policy':'required_unless_explicit_user_waiver',
        'independent_visual_qa_waiver_explicit':True,
        'independent_visual_qa_waiver_reason':'user explicitly accepted release without second-runtime QA',
    })
    r=promotion_evaluate(F/'defects_closed.csv',g)
    assert r['pass'] and r['promotion_outcome']=='CANONICAL_WITH_EXPLICIT_INDEPENDENT_QA_WAIVER'


def test_unrecorded_independent_qa_waiver_fails(tmp_path):
    g=_write_gates(tmp_path/'g.json',{'independent_visual_qa':'WAIVED','independent_visual_qa_policy':'required_unless_explicit_user_waiver'})
    r=promotion_evaluate(F/'defects_closed.csv',g)
    assert not r['pass'] and 'independent_visual_qa' in r['failed_gates']


def test_unknown_high_family_blocks_promotion(tmp_path):
    d=tmp_path/'d.csv'; _write_csv(d,['defect_id','severity','defect_family','status'],[{'defect_id':'X','severity':'HIGH','defect_family':'new_semantic_family','status':'OPEN'}])
    r=promotion_evaluate(d,F/'gates_all_pass.json')
    assert not r['pass'] and r['promotion_outcome']=='REPAIR_REQUIRED'


def test_unknown_critical_family_blocks_promotion(tmp_path):
    d=tmp_path/'d.csv'; _write_csv(d,['defect_id','severity','defect_family','status'],[{'defect_id':'X','severity':'CRITICAL','defect_family':'future_family','status':'OPEN'}])
    r=promotion_evaluate(d,F/'gates_all_pass.json')
    assert not r['pass'] and r['promotion_outcome']=='REPAIR_REQUIRED'


def _inventory(path,n):
    fields=['source_recommendation_id','source_id','source_section_id','recommendation_table_id']
    _write_csv(path,fields,[{'source_recommendation_id':f'SRC-{i:03d}','source_id':'A','source_section_id':'ALL','recommendation_table_id':'ALL'} for i in range(1,n+1)])
    return path


def _census(path,expected):
    fields=['source_id','source_section_id','source_section_title','recommendation_table_id','recommendation_table_heading','page_location','expected_recommendation_row_count','standalone_narrative_recommendation_count','enumeration_method','reviewer','certification_status','independent_from_inventory_generation','semantic_review_status','deterministic_unavailable_reason','notes']
    _write_csv(path,fields,[{'source_id':'A','source_section_id':'ALL','source_section_title':'All recommendation tables','recommendation_table_id':'ALL','recommendation_table_heading':'38 recommendation tables','page_location':'guideline','expected_recommendation_row_count':str(expected),'standalone_narrative_recommendation_count':'0','enumeration_method':'structured_table_enumeration','reviewer':'independent reviewer','certification_status':'PASS','independent_from_inventory_generation':'yes','semantic_review_status':'PASS','deterministic_unavailable_reason':'','notes':'independently enumerated'}])
    return path


def test_130_inventory_fails_against_census_expecting_131(tmp_path):
    r=source_inventory_certify(_census(tmp_path/'c.csv',131),_inventory(tmp_path/'i.csv',130))
    assert not r['pass'] and r['census_expected_recommendations']==131 and r['inventory_recommendations']==130


def test_131_inventory_passes_against_census_131(tmp_path):
    r=source_inventory_certify(_census(tmp_path/'c.csv',131),_inventory(tmp_path/'i.csv',131))
    assert r['pass'] and r['census_expected_recommendations']==131


def test_census_must_be_independent_from_inventory_generation(tmp_path):
    c=_census(tmp_path/'c.csv',1)
    rows=list(csv.DictReader(open(c,encoding='utf-8'))); rows[0]['independent_from_inventory_generation']='no'
    _write_csv(c,rows[0].keys(),rows)
    r=source_inventory_certify(c,_inventory(tmp_path/'i.csv',1))
    assert not r['pass'] and any('not attested independent' in x['issue'] for x in r['issues'])


def test_extracted_blank_node_fails(tmp_path):
    a=tmp_path/'a.csv'; _write_csv(a,['source_recommendation_id','decision_node_id','accounting_status'],[
        {'source_recommendation_id':'SRC-001','decision_node_id':'','accounting_status':'EXTRACTED'},
        {'source_recommendation_id':'SRC-002','decision_node_id':'NODE-002','accounting_status':'EXTRACTED'},
        {'source_recommendation_id':'SRC-003','decision_node_id':'NODE-003','accounting_status':'EXTRACTED'},])
    r=inventory_audit(F/'source_inventory.csv',a)
    assert not r['pass'] and any('blank decision_node_id' in x['issue'] for x in r['issues'])


def test_adjudicated_explanatory_only_disposition_passes(tmp_path):
    a=tmp_path/'a.csv'; _write_csv(a,['source_recommendation_id','decision_node_id','accounting_status','adjudication_reason','reviewer','semantic_review_status'],[
        {'source_recommendation_id':'SRC-001','decision_node_id':'NODE-001','accounting_status':'EXTRACTED'},
        {'source_recommendation_id':'SRC-002','decision_node_id':'NODE-002','accounting_status':'EXTRACTED'},
        {'source_recommendation_id':'SRC-003','decision_node_id':'','accounting_status':'EXPLANATORY_ONLY','adjudication_reason':'no independent clinical decision','reviewer':'reviewer','semantic_review_status':'PASS'},])
    assert inventory_audit(F/'source_inventory.csv',a)['pass']


def test_unknown_accounting_status_fails(tmp_path):
    a=tmp_path/'a.csv'; _write_csv(a,['source_recommendation_id','decision_node_id','accounting_status'],[
        {'source_recommendation_id':'SRC-001','decision_node_id':'NODE-001','accounting_status':'EXTRACTED'},
        {'source_recommendation_id':'SRC-002','decision_node_id':'NODE-002','accounting_status':'EXTRACTED'},
        {'source_recommendation_id':'SRC-003','decision_node_id':'','accounting_status':''},])
    assert not inventory_audit(F/'source_inventory.csv',a)['pass']


def _foot(path, **kw):
    fields=['recommendation_id','footnote_id','marker_id','recommendation_marker_ids','scope','source_locator','source_owner_recommendation_id','source_scope_id','required_for_meaning','display_location','binding_status','semantic_adjudication','notes']
    base={'recommendation_id':'R1','footnote_id':'F1','marker_id':'*','recommendation_marker_ids':'*','scope':'recommendation','source_locator':'p1:t1:f1','source_owner_recommendation_id':'R1','source_scope_id':'','required_for_meaning':'yes','display_location':'on_screen','binding_status':'PASS','semantic_adjudication':'PASS','notes':''}
    base.update(kw); _write_csv(path,fields,[base]); return path


def test_standard_footnote_template_valid_binding_passes(tmp_path):
    assert footnote_validate(_foot(tmp_path/'f.csv'))['pass']


def test_standard_footnote_wrong_marker_fails(tmp_path):
    r=footnote_validate(_foot(tmp_path/'f.csv',marker_id='†'))
    assert not r['pass'] and any('not present on recommendation' in x['issue'] for x in r['issues'])


def test_standard_footnote_wrong_recommendation_attachment_fails(tmp_path):
    r=footnote_validate(_foot(tmp_path/'f.csv',source_owner_recommendation_id='R2'))
    assert not r['pass'] and any('does not match recommendation' in x['issue'] for x in r['issues'])


def test_table_scoped_footnote_passes_when_declared(tmp_path):
    assert footnote_validate(_foot(tmp_path/'f.csv',scope='table',marker_id='',recommendation_marker_ids='',source_owner_recommendation_id='',source_scope_id='T1'))['pass']


def test_required_footnote_dropped_fails(tmp_path):
    r=footnote_validate(_foot(tmp_path/'f.csv',display_location='omitted'))
    assert not r['pass'] and any('required footnote definition dropped' in x['issue'] for x in r['issues'])


def _norm(path,src,norm,kind):
    _write_csv(path,['record_id','text_handling_policy','source_text','normalized_text','transformation_type','transformation_log','validation_status'],[{'record_id':'N','text_handling_policy':'SOURCE_NATIVE_NORMALIZED','source_text':src,'normalized_text':norm,'transformation_type':kind,'transformation_log':'audited transform','validation_status':'PASS'}]); return path


def test_citation_reference_number_removal_passes(tmp_path):
    assert norm_validate(_norm(tmp_path/'n.csv','Statin therapy is recommended.1,2','Statin therapy is recommended.','citation_reference_number_removal'))['pass']


def test_citation_superscript_removal_passes(tmp_path):
    assert norm_validate(_norm(tmp_path/'n.csv','Statin therapy is recommended.¹²','Statin therapy is recommended.','citation_reference_number_removal'))['pass']


def test_threshold_mutation_still_fails(tmp_path):
    assert not norm_validate(_norm(tmp_path/'n.csv','LDL-C ≥190 mg/dL','LDL-C ≥120 mg/dL','ocr_spacing_repair'))['pass']


def test_dose_mutation_fails(tmp_path):
    assert not norm_validate(_norm(tmp_path/'n.csv','Dose 180 mg daily','Dose 80 mg daily','ocr_spacing_repair'))['pass']


def test_risk_percentage_mutation_fails(tmp_path):
    assert not norm_validate(_norm(tmp_path/'n.csv','10-y risk 7.5%','10-y risk 5%','ocr_spacing_repair'))['pass']


def _repair(path, **kw):
    fields=['repair_id','defect_id','defect_severity','original_state','proposed_repair','repair_authority','source_support','source_support_status','source_is_approved','source_lock_status','evidence_boundary_relocked','user_authority','clinical_content_changed','source_wording_changed','pedagogic_only_change','normalization_only_change','affected_case_ids','affected_slide_ids','change_type','binding_evidence','source_object_link','adjudication','post_repair_validation']
    base={'repair_id':'R','defect_id':'D','defect_severity':'CRITICAL','original_state':'LDL ≥190','proposed_repair':'LDL ≥120','repair_authority':'user','source_support':'','source_support_status':'','source_is_approved':'','source_lock_status':'','evidence_boundary_relocked':'no','user_authority':'user requested','clinical_content_changed':'yes','source_wording_changed':'yes','pedagogic_only_change':'no','normalization_only_change':'no','affected_case_ids':'C','affected_slide_ids':'S','change_type':'threshold','binding_evidence':'','source_object_link':'','adjudication':'PASS','post_repair_validation':'PASS'}
    base.update(kw); _write_csv(path,fields,[base]); return path


def test_user_authority_only_clinical_threshold_repair_fails(tmp_path):
    r=repair_validate(_repair(tmp_path/'r.csv'))
    assert not r['pass'] and any('approved locked source' in x['issue'] for x in r['issues'])


def test_formally_expanded_relocked_approved_source_repair_can_pass(tmp_path):
    r=repair_validate(_repair(tmp_path/'r.csv',source_support='Source C p.4 threshold',source_support_status='VERIFIED',source_is_approved='yes',source_lock_status='LOCKED',evidence_boundary_relocked='yes',repair_authority='approved source after relock'))
    assert r['pass']


def test_dyslipidemia_38_table_131_row_regression_fixture():
    census=F/'source_census_38_tables_131.csv'
    good=source_inventory_certify(census,F/'source_inventory_131.csv')
    bad=source_inventory_certify(census,F/'source_inventory_130_truncated.csv')
    assert good['pass'] and good['census_expected_recommendations']==131
    assert not bad['pass'] and bad['inventory_recommendations']==130
