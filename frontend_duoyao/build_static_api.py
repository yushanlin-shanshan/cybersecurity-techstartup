"""Write the static event snapshot that Netlify can serve.

The published site does not run serve.py or the Blue Team API.
Local `python3 serve.py` still answers /app-config.json itself, so this
file is only used when the dist directory is hosted as static files.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GROUPS = ROOT.parent / 'blue-team-backend' / 'demo' / 'groups.jsonl'
OUT = ROOT / 'dist' / 'api-static' / 'results.json'
CONFIG = ROOT / 'dist' / 'app-config.json'


def band(score):
    if score >= 70:
        return 'high'
    if score >= 40:
        return 'medium'
    return 'low'


def iso(unix_time):
    return datetime.fromtimestamp(unix_time, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def records_for(group):
    seen = set()
    records = []
    for item in group['evidence']:
        evidence_id = str(item['alert_id'])
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        records.append(item)
        if len(records) == 12:
            break
    return records


def explanation(group, records, score, priority_band):
    evidence_ids = [record['alert_id'] for record in records]
    highest = max(records, key=lambda record: record['level'])
    claims = [
        f"The group contains {group['count']} alerts sharing the {group['anchor'][0]} anchor {group['anchor'][1:]}, from {group['start']} to {group['end']}. This is a correlation hypothesis, not proof of a common attacker. [Evidence: {', '.join(str(item) for item in evidence_ids)}]",
        f"The highest recorded normalized severity is {group['max_level']}/15; supporting alert: {highest['description']}. [Evidence: {highest['alert_id']}]",
    ]
    for stage in group['stages']:
        supporting = [str(record['alert_id']) for record in records if stage in record.get('stages', [])]
        if supporting:
            claims.append(f"Alert descriptions include indicators of {stage.replace('_', ' ')}. These do not establish successful activity. [Evidence: {', '.join(supporting)}]")
    title = f"{group['anchor'][1]} · {max(group['signature_counts'], key=group['signature_counts'].get)}"
    summary = (
        f"Investigate {title}. Priority {score}/100 ({priority_band}), using the stored rule score. "
        f"{group['count']} alerts were grouped using a shared entity and bounded event times. "
        "This published copy does not include the optional model explanation."
    )
    return title, summary, claims


def incident(group):
    score = round(float(group['score']), 2)
    priority_band = band(score)
    records = records_for(group)
    title, summary, claims = explanation(group, records, score, priority_band)
    return {
        'id': group['id'],
        'title': title,
        'priority': priority_band,
        'score': score,
        'entity': group['anchor'][1] if len(group['anchor']) > 1 else ', '.join(group['hosts']) or 'Unknown',
        'start': group['start'],
        'end': group['end'],
        'alert_count': group['count'],
        'sources': group['sensors'],
        'summary': summary,
        'reasons': claims,
        'benign_explanations': [],
        'missing_context': [
            'Correlation and anomaly rank are not attack confirmation or calibrated probability.',
            'This Netlify copy uses the stored rule score. The Python API and optional model explanation are not running here.',
        ],
        'next_steps': [
            'Inspect the cited original records.',
            'Check shared addresses against expected scans, updates, and activity.',
        ],
        'evidence': [{
            'id': str(record['alert_id']),
            'timestamp': iso(record['time']),
            'title': record['description'],
            'description': f"{record.get('source') or 'Unknown file'} · line {record.get('line', 'unknown')} · {record.get('sensor') or 'Unknown detector'}",
            'source': record.get('sensor') or 'Unknown',
            'raw': record['original_record'],
        } for record in records],
        'backend': {'loaded': True, 'review_status': 'new'},
    }


def main():
    incidents = [incident(json.loads(line)) for line in GROUPS.read_text().splitlines() if line.strip()]
    incidents.sort(key=lambda item: (-item['score'], item['id']))
    payload = {
        'schema_version': 1,
        'mode': 'results',
        'dataset': {
            'name': 'russellmitchell',
            'description': f"{len(incidents):,} events from the bundled demo groups. Rule score only; the API service is not running on this host.",
        },
        'incidents': incidents,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, separators=(',', ':')))
    CONFIG.write_text(json.dumps({'job_id': 'demo', 'results_url': '/api-static/results.json'}, indent=2) + '\n')
    print(f'{len(incidents)} events, {OUT.stat().st_size} bytes')


if __name__ == '__main__':
    main()
