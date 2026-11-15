"""Transparent educational indicators. Not a calibrated drought prediction model."""
from __future__ import annotations
import hashlib
import json
from math import isfinite
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class Scenario(BaseModel):
    id: str
    region: str
    date: str
    rainfall_mm_30d: float | None = Field(default=None, ge=0)
    rainfall_baseline_mm_30d: float | None = Field(default=None, gt=0)
    reservoir_pct: float | None = Field(default=None, ge=0, le=100)
    demand_mld: float | None = Field(default=None, ge=0)
    supply_mld: float | None = Field(default=None, ge=0)
    last_observation_days: int = Field(ge=0)
    missing_fields: int = Field(ge=0)
    source_type: Literal['synthetic','observed']

class AIResponse(BaseModel):
    summary: str = Field(min_length=10)
    evidence_ids: list[str] = Field(default_factory=list)
    recommended_checks: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    @field_validator('evidence_ids','recommended_checks','caveats',mode='before')
    @classmethod
    def ensure_list(cls, v):
        return [v] if isinstance(v,str) else v

def fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()

def indicators(s: Scenario) -> dict:
    """Simple, dimensionally explicit ratios; missing data remains missing."""
    rainfall_ratio = None if s.rainfall_mm_30d is None or s.rainfall_baseline_mm_30d is None else round(s.rainfall_mm_30d/s.rainfall_baseline_mm_30d,3)
    supply_gap_mld = None if s.demand_mld is None or s.supply_mld is None else round(max(0,s.demand_mld-s.supply_mld),3)
    coverage = None if s.demand_mld is None or s.supply_mld is None or s.demand_mld == 0 else round(s.supply_mld/s.demand_mld,3)
    flags=[]
    if s.last_observation_days > 7: flags.append('STALE_DATA')
    if s.missing_fields or any(getattr(s,k) is None for k in ('rainfall_mm_30d','reservoir_pct','supply_mld')): flags.append('INCOMPLETE_DATA')
    if rainfall_ratio is not None and rainfall_ratio < .6: flags.append('LOW_RAINFALL_RATIO')
    if s.reservoir_pct is not None and s.reservoir_pct < 35: flags.append('LOW_STORAGE')
    if supply_gap_mld is not None and supply_gap_mld > 0: flags.append('SUPPLY_GAP')
    return {'id':s.id,'region':s.region,'rainfall_ratio':rainfall_ratio,'reservoir_pct':s.reservoir_pct,'supply_gap_mld':supply_gap_mld,'supply_demand_ratio':coverage,'flags':flags,'data_usable':not any(f in flags for f in ('STALE_DATA','INCOMPLETE_DATA')),'source_type':s.source_type}

def readiness(s: Scenario, demand_reduction_pct: float, additional_supply_mld: float=0) -> dict:
    """What-if arithmetic, not an operational water allocation recommendation."""
    if not 0 <= demand_reduction_pct <= 100 or additional_supply_mld < 0 or not isfinite(demand_reduction_pct) or not isfinite(additional_supply_mld):
        raise ValueError('Invalid intervention inputs')
    if s.demand_mld is None or s.supply_mld is None:
        return {'available':False,'reason':'Demand or supply observation is missing'}
    adjusted_demand=s.demand_mld*(1-demand_reduction_pct/100)
    adjusted_supply=s.supply_mld+additional_supply_mld
    return {'available':True,'adjusted_demand_mld':round(adjusted_demand,3),'adjusted_supply_mld':round(adjusted_supply,3),'remaining_gap_mld':round(max(0,adjusted_demand-adjusted_supply),3),'note':'Hypothetical arithmetic only; feasibility, water rights, and physical constraints are not assessed.'}

def verify_evidence_ids(response: AIResponse, available_ids: list[str]) -> bool:
    return bool(response.evidence_ids) and set(response.evidence_ids).issubset(set(available_ids))
