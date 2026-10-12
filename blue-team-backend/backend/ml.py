"""Unsupervised batch triage and TF-IDF related-incident suggestions."""
from collections import defaultdict
import math
import re
import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from .legacy_pipeline import timestamp

FEATURE_NAMES = ('alert_count', 'maximum_severity', 'stage_count', 'sensor_count', 'host_count',
                 'destination_count', 'duration_seconds', 'signature_count', 'rarity_bits', 'alerts_per_minute')

def features(g):
    duration = max(0, timestamp(g['end'], 2022) - timestamp(g['start'], 2022))
    return [g['count'], g['max_level'], len(g['stages']), len(g['sensors']), len(g['hosts']),
            len(g['destinations']), duration, len(g['signature_counts']),
            -math.log2(max(g.get('rarest_signature_fraction', .1), 1e-12)),
            g['count'] / max(1, duration / 60)]

def enrich(groups):
    by_scenario = defaultdict(list)
    for g in groups:
        by_scenario[g['scenario']].append(g)
    training = []
    for scenario, rows in by_scenario.items():
        x = np.asarray([features(g) for g in rows], dtype=float)
        trained = len(rows) >= 20
        if trained:
            transformed = x.copy()
            transformed[:, [0, 6, 9]] = np.log1p(transformed[:, [0, 6, 9]])
            model = IsolationForest(n_estimators=150, contamination='auto', random_state=42, n_jobs=1)
            model.fit(transformed)
            anomaly = -model.score_samples(transformed)
            ordered = np.sort(anomaly)
            # Mid-ranks handle ties: identical feature vectors must not all become the highest anomaly.
            percentiles = 100 * (np.searchsorted(ordered, anomaly, 'left') + np.searchsorted(ordered, anomaly, 'right') - 1) / (2 * max(1, len(rows) - 1))
        else:
            anomaly = np.zeros(len(rows)); percentiles = np.zeros(len(rows))
        median = np.median(x, axis=0)
        scale = np.maximum(np.quantile(x, .75, axis=0) - np.quantile(x, .25, axis=0), 1)
        for i, g in enumerate(rows):
            delta = np.abs(x[i] - median) / scale
            context = [dict(feature=FEATURE_NAMES[j], observed=round(float(x[i, j]), 3), batch_median=round(float(median[j]), 3)) for j in np.argsort(delta)[::-1][:3]]
            g['ml'] = dict(enabled=trained, model='IsolationForest' if trained else None,
                           anomaly_percentile=round(float(percentiles[i]), 2), anomaly_score=round(float(anomaly[i]), 6) if trained else None,
                           reference_groups=len(rows), feature_context=context,
                           note='Within-scenario anomaly rank; not attack probability. Feature context is not a causal model attribution.' if trained else 'Fewer than 20 groups: rule-only ranking.')
            g['priority_components'] = dict(rule_points=round(.8 * g['score'], 2), anomaly_points=round(.2 * float(percentiles[i]), 2)) if trained else dict(rule_points=g['score'], anomaly_points=0.0)
            g['priority'] = round(sum(g['priority_components'].values()), 2)
            g['priority_band'] = 'high' if g['priority'] >= 70 else ('medium' if g['priority'] >= 40 else 'low')
            top = max(g['signature_counts'], key=g['signature_counts'].get)
            g['title'] = f"{g['anchor'][1]} · {top}"
            # Original payloads are served from the evidence database, not duplicated in the incident index.
            for e in g['evidence']:
                e.pop('original_record', None)
        training.append(dict(scenario=scenario, groups=len(rows), trained=trained, random_state=42, n_estimators=150, sklearn_version=sklearn.__version__, feature_names=list(FEATURE_NAMES), fit_mode='within-dataset unsupervised batch'))
    groups.sort(key=lambda g: (-g['priority'], g['id']))
    for rank, g in enumerate(groups, 1):
        g['rank'] = rank
    return training

class RelatedIndex:
    def __init__(self, groups):
        self.groups = groups
        self.ids = {g['id']: i for i, g in enumerate(groups)}
        documents = [' '.join(g['signature_counts']) for g in groups]
        documents = [doc if re.search(r'\w', doc) else 'unknown_alert' for doc in documents]
        self.matrix = TfidfVectorizer(ngram_range=(1, 2), max_features=8000, sublinear_tf=True, token_pattern=r'(?u)\b\w+\b').fit_transform(documents)

    def related(self, incident_id, limit=5):
        i = self.ids[incident_id]; target = self.groups[i]
        similarities = linear_kernel(self.matrix[i], self.matrix).ravel()
        answers = []
        for j in np.argsort(similarities)[::-1]:
            g = self.groups[j]
            if j == i or g['scenario'] != target['scenario'] or similarities[j] < .15:
                continue
            gap = max(0, timestamp(g['start'], 2022) - timestamp(target['end'], 2022), timestamp(target['start'], 2022) - timestamp(g['end'], 2022))
            if gap > 3600:
                continue
            shared = sorted(set(g['hosts'] + g['destinations']) & set(target['hosts'] + target['destinations']))
            same_anchor = g['anchor'] == target['anchor']
            if not shared and not same_anchor:
                continue
            answers.append(dict(id=g['id'], title=g['title'], priority=g['priority'], similarity=round(float(similarities[j]), 4),
                                shared_entities=shared, same_anchor=same_anchor, gap_minutes=round(gap / 60, 2),
                                reason='Similar alert descriptions, shared entities, and close event times. Review suggestion; not a confirmed common attack.'))
            if len(answers) == limit:
                break
        return answers
