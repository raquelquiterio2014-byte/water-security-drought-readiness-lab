"""Water Security & Drought Readiness Lab V1.0 — COP31 AI Solutions Lab Day 7."""
import json
import os
from pathlib import Path
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from core import Scenario, indicators, readiness, fingerprint
from ai_gateway import explain
from storage import initialize, add_review, reviews

ROOT=Path(__file__).resolve().parent
load_dotenv(ROOT/'.env')
SCENARIOS=[Scenario.model_validate(x) for x in json.loads((ROOT/'data/scenarios.json').read_text(encoding='utf-8'))]
REFERENCES=json.loads((ROOT/'data/references.json').read_text(encoding='utf-8'))
DB=ROOT/'local_data/reviews.sqlite3'
initialize(DB)
st.set_page_config(page_title='Water Security & Drought Readiness Lab',page_icon='💧',layout='wide')
st.markdown("""<style>.stApp{background:#081b30;color:#e9f7ff}h1,h2,h3{color:#b8ebff!important}[data-testid="stMetric"]{background:#103455;border:1px solid #226c91;padding:12px;border-radius:12px}</style>""",unsafe_allow_html=True)
st.title('💧 Water Security & Drought Readiness Lab V1.0')
st.caption('COP31 AI Solutions Lab | Day 7 | November 15, 2026 | Evidence first. Engineering second. Measurable impact as the goal.')
st.warning('All three basin scenarios are SYNTHETIC. Ratios and flags are educational rules, not calibrated drought forecasts. Missing data is not zero.')
if 'ai_result' not in st.session_state: st.session_state.ai_result=None
if 'ai_input' not in st.session_state: st.session_state.ai_input=None
metrics=[indicators(s) for s in SCENARIOS]
tabs=st.tabs(['📊 Overview','🌧️ Water Stress Monitoring','📡 Monitoring Gaps','🛟 Drought Readiness','🤖 AI & Human Review','📤 Export & Methodology'])
with tabs[0]:
    st.subheader('Illustrative water security overview')
    a,b,c=st.columns(3);a.metric('Synthetic basins',len(SCENARIOS));b.metric('Flagged data records',sum(not x['data_usable'] for x in metrics));c.metric('Local human reviews',len(reviews(DB)))
    st.dataframe(pd.DataFrame(metrics),hide_index=True,use_container_width=True)
    st.info('WMO, FAO AQUASTAT and UN-Water links are background references only. No live observations have been imported.')
with tabs[1]:
    st.subheader('Water stress monitoring — illustrative indicators')
    chosen=st.selectbox('Select synthetic basin',[s.region for s in SCENARIOS],key='stress')
    s=next(x for x in SCENARIOS if x.region==chosen);m=indicators(s)
    a,b,c=st.columns(3)
    a.metric('30-day rainfall / baseline','N/A' if m['rainfall_ratio'] is None else f"{m['rainfall_ratio']:.2f}")
    b.metric('Reservoir storage','N/A' if m['reservoir_pct'] is None else f"{m['reservoir_pct']:.1f}%")
    c.metric('Supply gap','N/A' if m['supply_gap_mld'] is None else f"{m['supply_gap_mld']:.2f} ML/day")
    st.write('**Rule-based flags:**',', '.join(m['flags']) or 'No thresholds triggered')
    st.json(s.model_dump())
with tabs[2]:
    st.subheader('Monitoring gaps and quality flags')
    rows=[{'Basin':s.region,'Last observation (days)':s.last_observation_days,'Missing field count':s.missing_fields,'Usable for educational comparison':indicators(s)['data_usable'],'Flags':', '.join(indicators(s)['flags'])} for s in SCENARIOS]
    st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
    st.markdown('**Illustrative quality rules:** observations older than 7 days are stale; absent required values are incomplete. These thresholds are teaching examples, not official standards.')
with tabs[3]:
    st.subheader('Drought readiness — transparent what-if scenarios')
    basin=st.selectbox('Choose basin',[s.region for s in SCENARIOS],key='readiness')
    s=next(x for x in SCENARIOS if x.region==basin)
    reduction=st.slider('Hypothetical demand reduction (%)',0,50,10)
    extra=st.number_input('Hypothetical additional supply (ML/day)',min_value=0.0,max_value=50.0,value=0.0,step=0.5)
    result=readiness(s,reduction,extra)
    if result['available']:
        st.metric('Remaining illustrative gap',f"{result['remaining_gap_mld']:.2f} ML/day")
        st.json(result)
    else: st.error(result['reason']+' — no gap is calculated.')
    st.caption('No claim of achievable savings, operational feasibility, water rights compliance or real-world impact.')
with tabs[4]:
    st.subheader('Gemini-assisted interpretation and human oversight')
    basin=st.selectbox('Choose scenario for AI',[s.region for s in SCENARIOS],key='ai')
    s=next(x for x in SCENARIOS if x.region==basin)
    st.caption('Only the selected synthetic scenario, calculated indicators and reference metadata are transmitted to Google when you click Generate. No personal data is needed.')
    if st.button('Generate Gemini explanation',type='primary'):
        try:
            with st.spinner('Contacting Gemini API...'):
                result=explain(s.model_dump(),indicators(s),REFERENCES,os.getenv('GEMINI_API_KEY','').strip(),os.getenv('GEMINI_MODEL','gemini-2.5-flash'))
            st.session_state.ai_result=result.model_dump();st.session_state.ai_input=s.model_dump()
            st.success('Structured API response received; independent human review is still required.')
        except Exception as exc: st.error(f'AI request failed: {exc}')
    if st.session_state.ai_result:
        st.json(st.session_state.ai_result)
        with st.form('human_review'):
            reviewer=st.text_input('Reviewer role / pseudonym',value='Educational reviewer')
            decision=st.selectbox('Review decision',['needs_revision','approved','rejected'])
            rationale=st.text_area('Review rationale',value='Check source provenance and all model claims before approval.')
            if st.form_submit_button('Save review'):
                try:
                    record=add_review(DB,st.session_state.ai_input['id'],decision,reviewer,rationale,st.session_state.ai_input,st.session_state.ai_result)
                    st.success(f'Local review #{record} saved.')
                except Exception as exc: st.error(str(exc))
with tabs[5]:
    st.subheader('Exports, evidence provenance and limitations')
    st.download_button('Export scenario indicators CSV',pd.DataFrame(metrics).to_csv(index=False).encode(),'indicators.csv','text/csv')
    st.download_button('Export review log CSV',pd.DataFrame(reviews(DB),columns=['id','created_utc','scenario_id','decision','reviewer','rationale','input_hash','output_hash']).to_csv(index=False).encode(),'reviews.csv','text/csv')
    export={'scenarios':[s.model_dump() for s in SCENARIOS],'indicators':metrics,'references':REFERENCES,'reviews':reviews(DB),'scenario_sha256':fingerprint([s.model_dump() for s in SCENARIOS])}
    st.download_button('Export full educational JSON',json.dumps(export,indent=2,ensure_ascii=False),'water_security_lab.json','application/json')
    st.markdown('**Background references (not sources of scenario measurements)**')
    for ref in REFERENCES: st.markdown(f"- [{ref['name']}]({ref['url']}) — {ref['note']}")
    st.markdown('**Methodology:** validate Pydantic schemas; calculate transparent ratios and flags; preserve missingness; compare hypothetical interventions; optionally request a structured Gemini explanation; require human review; export local records.')
    st.warning('No real measurements, calibrated drought classification, verified operational recommendations, measured water savings or tested Gemini API call are claimed. SQLite is local and hashes do not make it immutable.')
