from pathlib import Path
import json
import zipfile
from . import legacy_pipeline as core
from .ml import enrich

def validate_input(path, settings):
    if path.stat().st_size > settings.max_upload_bytes:
        raise ValueError('Upload exceeds configured size limit')
    if path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path) as z:
            members = [i for i in z.infolist() if i.filename.endswith(('.json', '.jsonl', '.ndjson'))]
            if not members:
                raise ValueError('ZIP must contain JSONL alerts in .json, .jsonl, or .ndjson files')
            if len(z.infolist()) > 1000 or sum(i.file_size for i in z.infolist()) > settings.max_expanded_bytes:
                raise ValueError('ZIP expanded size or member count exceeds configured limits')
            if any(i.flag_bits & 1 for i in members):
                raise ValueError('Encrypted ZIP files are unsupported')


def process_job(store, settings, job_id, path):
    folder = store.folder(job_id)
    options = store.job(job_id)['parameters']
    try:
        store.update_job(job_id, 'running', 'validating')
        validate_input(path, settings)
        with core.db_open(folder / 'evidence.sqlite') as con:
            store.update_job(job_id, 'running', 'ingesting')
            counts = core.ingest(con, path, options.get('scenario'), options['syslog_year'], options['limit'], folder,
                                 max_alerts=settings.max_alerts,
                                 progress=lambda count: store.update_job(job_id, 'running', 'ingesting', dict(counts=count)))
            store.update_job(job_id, 'running', 'correlating', dict(counts=counts))
            groups = core.aggregate(con, options['gap_minutes'] * 60, options['max_span_minutes'] * 60)
        store.update_job(job_id, 'running', 'training_ml', dict(counts=counts, groups=len(groups)))
        training = enrich(groups)
        store.index_groups(job_id, groups)
        summary = dict(counts=counts, groups=len(groups), training=training, labels_used=False,
                       partial_input=bool(options['limit']), scoring='0.8 * rule score + 0.2 * within-scenario anomaly percentile; rule-only for <20 groups')
        (folder / 'summary.json').write_text(json.dumps(summary, indent=2))
        store.update_job(job_id, 'ready', 'complete', summary)
    except Exception as e:
        # Do not include provider credentials or arbitrary traceback data in public job status.
        message = str(e)[:500] if isinstance(e, (ValueError, zipfile.BadZipFile, OSError)) else 'Processing failed; see server logs.'
        import logging
        logging.getLogger(__name__).exception('Job %s failed', job_id)
        store.update_job(job_id, 'failed', 'failed', error=message)


def import_results(store, source, job_id=None):
    source = Path(source).resolve()
    metadata = json.loads((source / 'summary.json').read_text())
    job = store.create_job(dict(imported_results=True, source=str(source)), job_id)
    folder = store.folder(job['id'])
    try:
        store.update_job(job['id'], 'running', 'importing_existing_results')
        # sqlite backup also handles a source database that still has a WAL.
        import sqlite3
        with sqlite3.connect(f'file:{source / "evidence.sqlite"}?mode=ro', uri=True) as src, sqlite3.connect(folder / 'evidence.sqlite') as dest:
            src.backup(dest)
        groups = [json.loads(line) for line in (source / 'groups.jsonl').open()]
        training = enrich(groups)
        store.index_groups(job['id'], groups)
        summary = dict(counts=metadata['counts'], groups=len(groups), training=training, labels_used=False, partial_input=bool(metadata.get('limit')))
        (folder / 'summary.json').write_text(json.dumps(summary, indent=2))
        store.update_job(job['id'], 'ready', 'complete', summary)
        return store.job(job['id'])
    except Exception:
        store.update_job(job['id'], 'failed', 'failed', error='Import failed')
        raise
