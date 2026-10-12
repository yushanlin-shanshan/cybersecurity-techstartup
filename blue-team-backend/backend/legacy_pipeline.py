#!/usr/bin/env python3
"""Local, evidence-backed AIT-ADS investigation triage. Python 3.10+, stdlib only."""
import argparse
import collections
import datetime as dt
import hashlib
import html
import ipaddress
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
import zipfile

UTC = dt.timezone.utc
STAGES = {
    'discovery': r'\b(scan|scanning|nmap|wpscan|dirb|reconnaissance)\b',
    'credential_access': r'brute.?force|password crack|authentication fail|failed password|login fail|multiple.*authentication',
    'execution': r'webshell|reverse.shell|remote.*execution|command.*execution|shellcode|code injection|exploit',
    'privilege_escalation': r'privilege escalation|sudo|setuid|root access',
    'exfiltration': r'exfiltrat|dnsteal|dns.*tunnel',
    'impact': r'service.*stop|denial of service|ransomware',
}
PATTERNS = {k: re.compile(v, re.I) for k, v in STAGES.items()}

def get(obj, path, default=None):
    for part in path.split('.'):
        if not isinstance(obj, dict) or part not in obj:
            return default
        obj = obj[part]
    return obj

def timestamp(value, year):
    if isinstance(value, (int, float)) and math.isfinite(value):
        dt.datetime.fromtimestamp(value, UTC)
        return float(value)
    if not isinstance(value, str):
        return None
    try:
        return dt.datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=UTC).timestamp() if not re.search(r'(Z|[+-]\d\d:?\d\d)$', value) else dt.datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
    except ValueError:
        pass
    for fmt in ('%m/%d/%Y-%H:%M:%S.%f', '%d/%b/%Y:%H:%M:%S %z', '%Y-%m-%d %H:%M:%S', '%a %b %d %H:%M:%S.%f %Y', '%d/%m/%Y %H:%M:%S'):
        try:
            parsed = dt.datetime.strptime(value, fmt)
            return (parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)).timestamp()
        except ValueError:
            pass
    try:
        return dt.datetime.strptime(str(year) + ' ' + value, '%Y %b %d %H:%M:%S').replace(tzinfo=UTC).timestamp()
    except ValueError:
        return None

def raw_time(raw, year):
    audit = re.search(r'audit\((\d+(?:\.\d+)?):', raw)
    if audit:
        return timestamp(float(audit[1]), year)
    candidates = [raw[:26], raw[:19], raw[:15]] + re.findall(r'\[([^\]]+)\]', raw)
    try:
        parsed = json.loads(raw)
        candidates.insert(0, parsed.get('timestamp', parsed.get('@timestamp')))
    except (ValueError, AttributeError):
        pass
    for v in candidates:
        t = timestamp(v, year)
        if t is not None:
            return t
    return None

def ip(value):
    try:
        return str(ipaddress.ip_address(str(value)))
    except ValueError:
        return ''

def normalize_ait(record, name, number, year):
    obj = record.get('_source', record)
    if not isinstance(obj, dict):
        raise ValueError('record is not an object')
    aminer = 'LogData' in obj
    raw = '\n'.join(map(str, get(obj, 'LogData.RawLogData', []))) if aminer else str(obj.get('full_log', ''))
    description = str(get(obj, 'AnalysisComponent.AnalysisComponentName', 'AMiner anomaly')) if aminer else str(get(obj, 'data.alert.signature', get(obj, 'rule.description', 'Unknown alert')))
    sensor = 'AMiner' if aminer else ('Suricata' if get(obj, 'data.alert') or description.startswith('Suricata:') else 'Wazuh')
    host = str(get(obj, 'AMiner.ID', '') if aminer else get(obj, 'agent.ip', get(obj, 'agent.name', get(obj, 'predecoder.hostname', ''))))
    src = ip(get(obj, 'data.src_ip', get(obj, 'data.srcip', obj.get('src_ip'))))
    dst = ip(get(obj, 'data.dest_ip', get(obj, 'data.dstip', obj.get('dest_ip'))))
    if not src:
        match = re.match(r'(\d+\.\d+\.\d+\.\d+)\s', raw) if 'access' in str(obj.get('location', get(obj, 'LogData.LogResources', ''))) else re.search(r'\bfrom (\d+\.\d+\.\d+\.\d+)\b', raw)
        if match:
            src = ip(match[1])
    # Use event time, never the replay/collection timestamp when an event timestamp exists.
    candidates = [('data.timestamp', get(obj, 'data.timestamp')), ('predecoder.timestamp', get(obj, 'predecoder.timestamp'))]
    if aminer:
        times = get(obj, 'LogData.DetectionTimestamp', [])
        candidates = [('LogData.DetectionTimestamp[-1]', times[-1] if isinstance(times, list) and times else times)]
    t, basis = None, ''
    for field, value in candidates:
        t = timestamp(value, year)
        if t is not None:
            basis = field
            break
    if t is None:
        t = raw_time(raw, year)
        basis = 'raw_log' if t is not None else ''
    if t is None:
        t = timestamp(obj.get('timestamp', obj.get('@timestamp')), year)
        basis = 'collection_timestamp_fallback' if t is not None else ''
    if t is None:
        raise ValueError('no usable timestamp')
    try:
        level = max(0, min(15, int(get(obj, 'rule.level', 3))))
    except (TypeError, ValueError):
        level = 3
    severity = get(obj, 'data.alert.severity')
    if sensor == 'Suricata' and severity is not None:
        level = {1: 12, 2: 8, 3: 4}.get(int(severity), 3)
    # Stage terms are indicators in alert descriptions, not assertions that an attack succeeded.
    stages = [k for k, p in PATTERNS.items() if p.search(description)]
    signature = str(get(obj, 'data.alert.signature_id', get(obj, 'rule.id', description)))
    scenario = re.sub(r'_(wazuh|aminer)$', '', Path(name).stem)
    anchor = ['source', src] if src else (['host_signature', host, signature] if host else ['signature', signature])
    return dict(scenario=scenario, time=t, time_basis=basis, sensor=sensor, host=host, src=src, dst=dst, level=level, description=description, signature=signature, stages=stages, anchor=anchor, source=name, line=number)

def normalize(record, name, number, year):
    if isinstance(record, dict) and 'description' in record and not any(k in record for k in ('rule', 'LogData', '_source')):
        canonical = {'data': {'timestamp': record.get('timestamp'), 'src_ip': record.get('source_ip'), 'dest_ip': record.get('destination_ip')},
                     'agent': {'ip': record.get('host', '')},
                     'rule': {'description': record['description'], 'level': record.get('severity', 3), 'id': record.get('rule_id', record['description'])},
                     'full_log': record.get('raw_log', '')}
        alert = normalize_ait(canonical, name, number, year)
        alert['sensor'] = str(record.get('sensor', 'custom'))[:100]
        return alert
    return normalize_ait(record, name, number, year)

def bounded_lines(stream):
    while True:
        line = stream.readline(8 * 1024 * 1024 + 1)
        if not line:
            break
        if len(line) > 8 * 1024 * 1024:
            raise ValueError('Record exceeds the 8 MB line limit')
        yield line

def inputs(path, scenario):
    if path.is_file() and path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path) as z:
            for name in sorted(z.namelist()):
                if name.endswith(('.json', '.jsonl', '.ndjson')) and (not scenario or Path(name).name.startswith(scenario + '_')):
                    with z.open(name) as f:
                        yield name, f
    else:
        paths = sorted(path.rglob('*.json')) + sorted(path.rglob('*.jsonl')) + sorted(path.rglob('*.ndjson')) if path.is_dir() else [path]
        for p in paths:
            if scenario and not p.name.startswith(scenario + '_'):
                continue
            with p.open('rb') as f:
                yield str(p), f

def db_open(path):
    con = sqlite3.connect(path)
    con.execute('PRAGMA journal_mode=WAL')
    return con

def ingest(con, path, scenario, year, limit, out, max_alerts=None, progress=None):
    con.executescript('CREATE TABLE alerts(id INTEGER PRIMARY KEY, scenario TEXT, time REAL, anchor TEXT, sensor TEXT, signature TEXT, level INTEGER, normalized TEXT, raw TEXT, group_id TEXT); CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);')
    counts = collections.Counter(input=0, accepted=0, rejected=0, fallback_times=0)
    with (out / 'rejected.jsonl').open('w') as rejected:
        for name, f in inputs(path, scenario):
            print('Reading', name, file=sys.stderr)
            for number, line in enumerate(bounded_lines(f), 1):
                if not line.strip():
                    continue
                counts['input'] += 1
                if max_alerts and counts['input'] > max_alerts:
                    raise ValueError('Input exceeds MAX_ALERTS; choose an explicit prefix limit or a smaller scenario')
                try:
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        raise ValueError('expected JSON object per line')
                    a = normalize(record, name, number, year)
                    con.execute('INSERT INTO alerts(scenario,time,anchor,sensor,signature,level,normalized,raw) VALUES (?,?,?,?,?,?,?,?)', (a['scenario'], a['time'], json.dumps(a['anchor']), a['sensor'], a['signature'], a['level'], json.dumps(a), json.dumps(record)))
                    counts['accepted'] += 1
                    counts['fallback_times'] += a['time_basis'] == 'collection_timestamp_fallback'
                except (ValueError, TypeError, KeyError, OverflowError, OSError) as e:
                    counts['rejected'] += 1
                    rejected.write(json.dumps(dict(source=name, line=number, error=str(e))) + '\n')
                if counts['input'] % 10000 == 0:
                    con.commit()
                    if progress:
                        progress(dict(counts))
                if limit and counts['input'] >= limit:
                    break
            con.commit()
            if limit and counts['input'] >= limit:
                break
    if not counts['accepted']:
        raise ValueError('No valid alerts found. See rejected.jsonl; input must contain one JSON object per line.')
    con.execute('CREATE INDEX alert_order ON alerts(scenario,anchor,time,id)')
    return dict(counts)

def iso(t):
    return dt.datetime.fromtimestamp(t, UTC).isoformat()

def aggregate(con, gap, span):
    total = dict(con.execute('SELECT scenario,count(*) FROM alerts GROUP BY scenario'))
    frequencies = {(s, sensor, sig): n for s, sensor, sig, n in con.execute('SELECT scenario,sensor,signature,count(*) FROM alerts GROUP BY scenario,sensor,signature')}
    groups = []
    current = None
    updates = []
    def finish(g):
        if g is None:
            return
        g['rarest_signature_fraction'] = g.pop('min_frequency')
        rarity = max(0, min(15, 3 * math.log2(1 / g['rarest_signature_fraction'])))
        components = dict(severity=round(g['max_level'] / 15 * 40, 2), stage_diversity=min(20, 5 * len(g['stages'])), sensor_diversity=10 if len(g['sensors']) > 1 else 0, rarity=round(rarity, 2), volume=round(min(10, 2 * math.log2(1 + g['count'])), 2), destination_breadth=min(5, len(g['destinations'])))
        g['score_components'] = components
        g['score'] = round(sum(components.values()), 2)
        g['start'], g['end'] = iso(g['start']), iso(g['end'])
        g['sensors'] = sorted(g['sensors'])
        g['stages'] = sorted(g['stages'])
        g['destinations'] = sorted(g['destinations'])
        g['hosts'] = sorted(g['hosts'])
        g['signature_counts'] = dict(g['signature_counts'])
        g['explanation'] = f"{g['count']} alerts share {g['anchor']} within a bounded session. Highest normalized severity: {g['max_level']}/15. Description indicators: {', '.join(g['stages']) or 'none'}. Sensors: {', '.join(g['sensors'])}. Score is a triage heuristic, not an attack probability."
        groups.append(g)
    for ident, scenario, t, anchor, norm in con.execute('SELECT id,scenario,time,anchor,normalized FROM alerts ORDER BY scenario,anchor,time,id'):
        a = json.loads(norm)
        if current is None or (scenario, anchor) != current['key'] or t - current['last'] > gap or t - current['start'] > span:
            finish(current)
            gid = hashlib.sha256(f'{scenario}|{anchor}|{ident}'.encode()).hexdigest()[:16]
            current = dict(id=gid, key=(scenario, anchor), scenario=scenario, anchor=json.loads(anchor), start=t, end=t, last=t, count=0, max_level=0, sensors=set(), stages=set(), hosts=set(), destinations=set(), signature_counts=collections.Counter(), evidence={}, min_frequency=1.0)
        g = current
        g['last'] = g['end'] = t
        g['count'] += 1
        if a['level'] >= g['max_level']:
            g['max_level'] = a['level']
            g['evidence']['highest_severity'] = ident
        fraction = frequencies[(scenario, a['sensor'], a['signature'])] / total[scenario]
        if fraction <= g['min_frequency']:
            g['min_frequency'] = fraction
            g['evidence']['rarest_signature'] = ident
        g['sensors'].add(a['sensor'])
        g['evidence'].setdefault('sensor:' + a['sensor'], ident)
        for stage in a['stages']:
            g['stages'].add(stage)
            g['evidence'].setdefault('stage:' + stage, ident)
        if a['dst']:
            g['destinations'].add(a['dst'])
        if a['host']:
            g['hosts'].add(a['host'])
        g['signature_counts'][a['description']] += 1
        updates.append((g['id'], ident))
        if len(updates) >= 10000:
            con.executemany('UPDATE alerts SET group_id=? WHERE id=?', updates)
            updates.clear()
    finish(current)
    con.executemany('UPDATE alerts SET group_id=? WHERE id=?', updates)
    con.execute('CREATE INDEX alert_group ON alerts(group_id,id)')
    con.commit()
    groups.sort(key=lambda g: (-g['score'], g['id']))
    for rank, g in enumerate(groups, 1):
        g['rank'] = rank
        g.pop('key'); g.pop('last')
        evidence = []
        for reason, ident in g['evidence'].items():
            norm, raw = con.execute('SELECT normalized,raw FROM alerts WHERE id=?', (ident,)).fetchone()
            evidence.append(dict(reason=reason, alert_id=ident, **json.loads(norm), original_record=json.loads(raw)))
        g['evidence'] = evidence
    return groups

def report(groups, counts, out, args):
    metadata = dict(input=str(args.input.resolve()), counts=counts, groups=len(groups), gap_minutes=args.gap, max_span_minutes=args.max_span, syslog_year=args.syslog_year, scenario=args.scenario, limit=args.limit, dataset='https://zenodo.org/records/8263181', labels_used=False)
    (out / 'summary.json').write_text(json.dumps(metadata, indent=2))
    with (out / 'groups.jsonl').open('w') as f:
        for g in groups:
            f.write(json.dumps(g) + '\n')
    cards = []
    for g in groups[:args.top]:
        esc = lambda x: html.escape(str(x))
        examples = ''.join(f"<details><summary>{esc(e['reason'])} · record {e['alert_id']} · {esc(e['source'])}:{e['line']}</summary><pre>{esc(json.dumps(e['original_record'], indent=2))}</pre></details>" for e in g['evidence'])
        cards.append(f"<article><h2>#{g['rank']} · Score {g['score']} · {esc(g['scenario'])}</h2><p>{esc(g['start'])} → {esc(g['end'])}</p><p>{esc(g['explanation'])}</p><p>Group ID: <code>{g['id']}</code></p><pre>{esc(json.dumps(g['score_components'], indent=2))}</pre><details><summary>Alert descriptions and counts</summary><pre>{esc(json.dumps(g['signature_counts'], indent=2))}</pre></details>{examples}</article>")
    (out / 'report.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Alert investigations</title><style>body{font:16px system-ui;background:#f2f5f9;color:#17263b;max-width:1100px;margin:32px auto;padding:0 20px}article{background:white;padding:24px;border-radius:12px;margin:20px 0;border:1px solid #ccd5df}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}summary{cursor:pointer;padding:10px}h2{font-size:21px}code{font-size:14px}</style><h1>Alert investigation queue</h1><p>Evidence-backed heuristic triage. Shared entities and time proximity suggest relationships; analyst review is required. Description indicators do not prove attack success.</p><p>' + html.escape(json.dumps(metadata)) + f'</p><p>Showing top {min(args.top,len(groups))} of {len(groups)} groups. Complete queue: groups.jsonl; all original records and memberships: evidence.sqlite.</p>' + ''.join(cards) + '</html>')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    run = sub.add_parser('analyze')
    run.add_argument('input', type=Path, help='AIT ZIP, directory, or JSONL file')
    run.add_argument('--out', type=Path, required=True)
    run.add_argument('--scenario')
    run.add_argument('--gap', type=float, default=15, help='session idle gap in minutes')
    run.add_argument('--max-span', type=float, default=60, help='maximum session span in minutes')
    run.add_argument('--syslog-year', type=int, default=2022, help='year for yearless AIT event timestamps')
    run.add_argument('--limit', type=int, default=0, help='input prefix limit; 0 reads all')
    run.add_argument('--top', type=int, default=100, help='number of groups in HTML; JSONL contains all')
    ev = sub.add_parser('evidence')
    ev.add_argument('database', type=Path)
    ev.add_argument('--group', required=True)
    args = p.parse_args()
    if args.command == 'evidence':
        if not args.database.is_file():
            p.error('database does not exist')
        with sqlite3.connect(f'file:{args.database.resolve()}?mode=ro', uri=True) as con:
            for ident, norm, raw in con.execute('SELECT id,normalized,raw FROM alerts WHERE group_id=? ORDER BY time,id', (args.group,)):
                print(json.dumps(dict(alert_id=ident, normalized=json.loads(norm), original_record=json.loads(raw))))
        return
    if args.gap <= 0 or args.max_span <= 0 or args.limit < 0 or args.top <= 0:
        p.error('gap, max-span, top must be positive; limit must be nonnegative')
    args.out.mkdir(parents=True, exist_ok=True)
    database = args.out / 'evidence.sqlite'
    if database.exists():
        p.error('output database exists; choose a fresh --out directory')
    with db_open(database) as con:
        counts = ingest(con, args.input, args.scenario, args.syslog_year, args.limit, args.out)
        groups = aggregate(con, args.gap * 60, args.max_span * 60)
        report(groups, counts, args.out, args)
        con.execute('INSERT INTO meta VALUES (?,?)', ('summary', (args.out / 'summary.json').read_text()))
    print(json.dumps(dict(counts=counts, groups=len(groups), report=str(args.out / 'report.html')), indent=2))

if __name__ == '__main__':
    main()
