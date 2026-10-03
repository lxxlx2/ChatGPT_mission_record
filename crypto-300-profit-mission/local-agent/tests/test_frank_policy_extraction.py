import hashlib,json
from scripts.frank_extract_local_policy import ROOT,SOURCE,JSON,MARKDOWN,extract,render

def test_machine_policy_exactly_matches_source_bound_extraction():
    assert json.loads(JSON.read_text())==extract()

def test_markdown_and_machine_policy_are_identical_in_content():
    assert MARKDOWN.read_text()==render(json.loads(JSON.read_text()))

def test_path_c_single_buy_branch_is_preserved_and_not_silently_replaced():
    p=json.loads(JSON.read_text());g=next(g for g in p['groups'] if g['name']=='PRECONFIRM_PATH_C')
    assert any('single active BUY >= 15,000 USD equivalent; OR' in x['text'] for x in g['predicates'])
    assert any('>= 25,000 USD equivalent' in x['text'] and '>=2 BUY swaps' in x['text'] for x in g['predicates'])
    assert p['status']=='FROZEN' and p['enabled'] is True and p['frozen'] is True
    mapped=p['mapping']['FRANK_ACCUMULATION_SIGNAL']
    assert mapped['count_min']==2 and mapped['quote_quantity_min']=='25000' and mapped['window_seconds']==3600
    assert mapped['single_branch']=='PATH_C_SINGLE_LARGE_BUY = NOT_ACCUMULATION'

def test_preconfirm_paths_and_conviction_persistence_paths_are_not_confused():
    p=extract();assert p['preconfirm_path_names']==['S','C'];assert not p['preconfirm_path_a_exists'] and not p['preconfirm_path_b_exists']
    g=next(g for g in p['groups'] if g['name']=='PERSISTENCE_PATH_A_B');assert [x['line'] for x in g['predicates']]==[203,204]

def test_all_extracted_predicates_are_bound_to_exact_canonical_lines():
    p=extract();raw=SOURCE.read_bytes();lines=raw.decode().splitlines()
    assert hashlib.sha256(raw).hexdigest()==p['source']['sha256']
    for g in p['groups']:
        for x in g['predicates']:assert x['text']==lines[x['line']-1]

def test_missing_numeric_parameters_are_not_invented():
    assert all(value is None for value in extract()['unspecified'].values())

def test_authorized_non_behavior_veto_removal_does_not_invent_policy_pass():
    p=extract();g=next(g for g in p['groups'] if g['name']=='SUSPECTED_CONVICTION')
    assert next(x for x in g['predicates'] if x['line']==316)['treatment']=='REMOVED_NON_BEHAVIOR_AUTHORITY'
    assert p['delivery_target']['gpt_required'] is False and p['amount_policy']['non_usdc_without_reliable_conversion']=='UNDETERMINED'
    assert p['delivery_target']['historical_delivery_allowed'] is False
