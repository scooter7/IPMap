#!/usr/bin/env python3
"""
Merge the three already-generated campaign dashboards (Colorado, Apollo Small,
Apollo Large) into one tabbed dashboard. Reuses the verified data embedded in
each HTML — no re-geocoding. Normalizes Colorado's employer/emp_* schema to the
unified company/comp_* schema.
"""
import re
import json

from dashboard_template_merged import HTML_TEMPLATE

OUTPUT = '/Users/scootervineburgh/Desktop/Kathi/dashboard.html'

def grab(s, var):
    m = re.search(r'const ' + var + r' = (\[.*?\]);', s, re.S) \
        or re.search(r'const ' + var + r' = (\{.*?\});', s, re.S)
    return json.loads(m.group(1))

# Campaign source files. kind: 'apollo' already in unified schema; 'colorado' needs mapping.
SOURCES = [
    {'key': 'colorado',     'label': 'Colorado Small',  'noun': 'Employer',
     'file': 'colorado_click_map.html', 'kind': 'colorado',
     'targets_var': 'EMPLOYERS', 'summary_var': 'EMP_SUMMARY'},
    {'key': 'apollo_small', 'label': 'Apollo Small',    'noun': 'Company',
     'file': 'apollo_click_map.html', 'kind': 'apollo',
     'targets_var': 'COMPANIES', 'summary_var': 'COMP_SUMMARY'},
    {'key': 'apollo_large', 'label': 'Apollo Large',    'noun': 'Company',
     'file': 'apollo_large_click_map.html', 'kind': 'apollo',
     'targets_var': 'COMPANIES', 'summary_var': 'COMP_SUMMARY'},
]

def norm_colorado_point(p):
    return {
        'ip': p['ip'], 'clicks': p['clicks'], 'impr': p.get('impr'),
        'lat': p['lat'], 'lon': p['lon'],
        'city': p.get('city', ''), 'region': p.get('region', ''), 'org': p.get('org', ''),
        'hostname': '',
        'company': p.get('employer', ''), 'comp_id': p.get('emp_id'),
        'website': '',
        'comp_addr': p.get('emp_addr', ''),
        'comp_address': p.get('emp_address', ''), 'comp_city': p.get('emp_city', ''),
        'comp_state': p.get('emp_state', ''), 'comp_country': 'United States',
        'comp_zip': p.get('emp_zip', ''), 'comp_zip4': p.get('emp_zip4', ''),
        'comp_lat': p.get('emp_lat'), 'comp_lon': p.get('emp_lon'),
        'comp_precision': p.get('emp_precision', ''),
        'match_type': 'geo',
        'dist_km': p.get('dist_km'), 'dist_mi': p.get('dist_mi'), 'conf': p.get('conf', 'none'),
    }

def norm_colorado_target(e):
    return {
        'name': e.get('name', ''), 'address': e.get('address', ''), 'city': e.get('city', ''),
        'state': e.get('state_orig') or 'Colorado', 'zip': e.get('zip', ''),
        'website': '', 'lat': e['lat'], 'lon': e['lon'], 'precision': e.get('precision', ''),
    }

def norm_apollo_target(e):
    return {
        'name': e.get('name', ''), 'address': e.get('address', ''), 'city': e.get('city', ''),
        'state': e.get('state', ''), 'zip': e.get('zip', ''), 'website': e.get('website', ''),
        'lat': e['lat'], 'lon': e['lon'], 'precision': e.get('precision', ''),
    }

def norm_colorado_summary(r):
    return {**r, 'company': r.get('employer', r.get('company', '')),
            'website': '', 'country': 'United States'}

def norm_colorado_stats(st):
    return {
        'total_clicks': st['total_clicks'], 'unique_ips': st['unique_ips'],
        'mapped_ips': st['mapped_ips'], 'matched': st['matched'],
        'geocoded_companies': st.get('geocoded_employers', st.get('geocoded_companies', 0)),
        'domain': 0,
        'total_impr': st.get('total_impr', 0),
    }

campaigns, order = {}, []
for src in SOURCES:
    s = open('/Users/scootervineburgh/Desktop/Kathi/' + src['file'], encoding='utf-8').read()
    points = grab(s, 'DATA')
    targets = grab(s, src['targets_var'])
    summary = grab(s, src['summary_var'])
    stats = grab(s, 'STATS')

    if src['kind'] == 'colorado':
        points = [norm_colorado_point(p) for p in points]
        targets = [norm_colorado_target(e) for e in targets]
        summary = [norm_colorado_summary(r) for r in summary]
        stats = norm_colorado_stats(stats)
    else:
        targets = [norm_apollo_target(e) for e in targets]
        # apollo points/summary/stats already unified

    campaigns[src['key']] = {
        'label': src['label'], 'targetNoun': src['noun'],
        'points': points, 'targets': targets, 'summary': summary, 'stats': stats,
    }
    order.append({'key': src['key'], 'label': src['label']})
    print(f"{src['key']}: {len(points)} points, {len(targets)} targets, {len(summary)} summary rows")

html = (HTML_TEMPLATE
        .replace('/*__CAMPAIGNS__*/', json.dumps(campaigns))
        .replace('/*__CAMP_ORDER__*/', json.dumps(order)))
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"\nDone -> {OUTPUT}  ({len(html):,} bytes)")
