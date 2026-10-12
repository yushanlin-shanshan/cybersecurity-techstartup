import argparse
import json
from pathlib import Path
from .config import Settings
from .pipeline import process_job, import_results
from .store import Store


def main():
    parser = argparse.ArgumentParser(description='Blue Team backend data utilities')
    parser.add_argument('--data-dir', type=Path, default=None)
    sub = parser.add_subparsers(dest='command', required=True)
    demo = sub.add_parser('demo', help='Load the bundled complete AIT russellmitchell scenario')
    imported = sub.add_parser('import-results', help='Import an existing Alert Investigator output folder')
    imported.add_argument('source', type=Path)
    run = sub.add_parser('analyze', help='Process alerts without an HTTP upload')
    run.add_argument('input', type=Path)
    run.add_argument('--scenario')
    run.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()
    if args.command == 'analyze' and args.limit < 0:
        parser.error('--limit must be nonnegative')
    settings = Settings.from_env()
    store = Store(args.data_dir or settings.data_dir)
    if args.command == 'demo':
        source = Path(__file__).resolve().parent.parent / 'demo'
        existing = store.job('demo')
        if existing:
            print(json.dumps(existing, indent=2)); return
        result = import_results(store, source, 'demo')
    elif args.command == 'import-results':
        result = import_results(store, args.source)
    else:
        job = store.create_job(dict(scenario=args.scenario, limit=args.limit, syslog_year=2022, gap_minutes=15, max_span_minutes=60))
        process_job(store, settings, job['id'], args.input.resolve())
        result = store.job(job['id'])
    print(json.dumps(result, indent=2))
    if result['status'] != 'ready':
        raise SystemExit(1)

if __name__ == '__main__':
    main()
