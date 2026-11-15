import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from core import Scenario,AIResponse,indicators,readiness,fingerprint,verify_evidence_ids
from storage import add_review,reviews

DATA=json.loads((Path(__file__).resolve().parents[1]/'data/scenarios.json').read_text())
def scenario(i=0): return Scenario.model_validate(DATA[i])
def test_three_examples(): assert len(DATA)==3
def test_valid_scenarios(): assert all(Scenario.model_validate(d) for d in DATA)
def test_ratio(): assert indicators(scenario())['rainfall_ratio']==round(24/90,3)
def test_gap(): assert indicators(scenario())['supply_gap_mld']==3
def test_low_storage(): assert 'LOW_STORAGE' in indicators(scenario())['flags']
def test_stale(): assert 'STALE_DATA' in indicators(scenario(1))['flags']
def test_missing_not_zero(): assert indicators(scenario(2))['rainfall_ratio'] is None
def test_missing_supply_gap(): assert indicators(scenario(2))['supply_gap_mld'] is None
def test_unusable_missing(): assert not indicators(scenario(2))['data_usable']
def test_readiness_reduction(): assert readiness(scenario(),25)['remaining_gap_mld']==0
def test_readiness_no_data(): assert not readiness(scenario(2),10)['available']
def test_invalid_reduction():
    with pytest.raises(ValueError): readiness(scenario(),101)
def test_invalid_negative_supply():
    with pytest.raises(ValueError): readiness(scenario(),10,-1)
def test_schema_rejects_bad_storage():
    with pytest.raises(ValidationError): Scenario.model_validate({**DATA[0],'reservoir_pct':110})
def test_fingerprint_stable(): assert fingerprint({'a':1,'b':2})==fingerprint({'b':2,'a':1})
def test_evidence_ids_good(): assert verify_evidence_ids(AIResponse(summary='An educational scenario only.',evidence_ids=['BASIN_A']),['BASIN_A'])
def test_evidence_ids_bad(): assert not verify_evidence_ids(AIResponse(summary='An educational scenario only.',evidence_ids=['UNKNOWN']),['BASIN_A'])
def test_audit_roundtrip(tmp_path):
    db=tmp_path/'audit.sqlite3'; add_review(db,'BASIN_A','needs_revision','Reviewer','Check inputs',{'a':1},{'b':2});assert reviews(db)[0]['decision']=='needs_revision'
def test_audit_reject_invalid(tmp_path):
    with pytest.raises(ValueError): add_review(tmp_path/'a.db','BASIN_A','wrong','Reviewer','Check inputs',{}, {})
def test_ai_list_normalization(): assert AIResponse(summary='This is an educational explanation.',evidence_ids='BASIN_A').evidence_ids==['BASIN_A']
