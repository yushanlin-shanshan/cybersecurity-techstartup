// Copy into your existing frontend. No framework-specific dependencies.
export type Job = {
  id: string;
  status: 'queued' | 'running' | 'ready' | 'failed';
  phase: string;
  error: string | null;
  summary: { counts?: Record<string, number>; groups?: number; partial_input?: boolean };
};
export type Incident = {
  id: string;
  rank: number;
  scenario: string;
  title: string;
  count: number;
  start: string;
  end: string;
  anchor: string[];
  hosts: string[];
  destinations: string[];
  sensors: string[];
  stages: string[];
  score: number;
  score_components: Record<string, number>;
  priority: number;
  priority_band: 'high' | 'medium' | 'low';
  priority_components: Record<string, number>;
  ml: { enabled: boolean; model: string | null; anomaly_percentile: number; note: string };
  review: { status: 'new' | 'investigating' | 'resolved' | 'dismissed'; disposition: 'unreviewed' | 'suspicious' | 'benign' | 'confirmed'; note: string };
};
export type Evidence = { alert_id: number; normalized: Record<string, unknown>; original_record: Record<string, unknown> };
export type Explanation = {
  mode: 'local' | 'llm';
  answer: string;
  claims: { text: string; evidence_ids: number[] }[];
  benign_explanations: { text: string; evidence_ids: number[]; verification: string }[];
  benign_assessment: string;
  model?: string;
  next_steps: string[];
  caveats: string[];
  evidence_ids: number[];
  fallback_reason?: string;
};
export type Page<T> = { items: T[]; total: number; limit: number; offset: number };
export type AnalysisOptions = { dataset_name?: string; allow_llm?: boolean; scenario?: string; gap_minutes?: number; max_span_minutes?: number; syslog_year?: number; limit?: number };
export type RelatedIncident = { id: string; title: string; priority: number; similarity: number; reason: string; shared_entities: string[]; same_anchor: boolean; gap_minutes: number };

export class BlueTeamAPI {
  private base: string;
  constructor(baseURL: string, private getToken?: () => string | undefined) {
    this.base = baseURL.replace(/\/$/, '');
  }
  private path(job: string, suffix = '') {
    return `/api/v1/jobs/${encodeURIComponent(job)}${suffix}`;
  }
  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    const token = this.getToken?.();
    if (token) headers.set('Authorization', `Bearer ${token}`);
    const response = await fetch(this.base + path, { ...init, headers });
    if (!response.ok) {
      const body = await response.text();
      throw new Error(`Backend ${response.status}: ${body}`);
    }
    return response.json() as Promise<T>;
  }
  jobs() { return this.request<{ items: Job[] }>('/api/v1/jobs'); }
  job(id: string) { return this.request<Job>(this.path(id)); }
  upload(file: File, options: AnalysisOptions = {}) {
    const form = new FormData();
    form.append('file', file);
    for (const [key, value] of Object.entries(options)) if (value !== undefined) form.append(key, String(value));
    return this.request<Job>('/api/v1/jobs', { method: 'POST', body: form });
  }
  ingestRecords(records: Record<string, unknown>[], options: AnalysisOptions = {}, filename = 'custom.jsonl') {
    return this.request<Job>('/api/v1/jobs/batch', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ records, filename, ...options }) });
  }
  async waitForJob(id: string, timeoutMs = 30 * 60 * 1000, signal?: AbortSignal) {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      signal?.throwIfAborted();
      const job = await this.request<Job>(this.path(id), { signal });
      if (job.status === 'ready') return job;
      if (job.status === 'failed') throw new Error(job.error || 'Analysis failed');
      await new Promise<void>((resolve, reject) => {
        signal?.throwIfAborted();
        const done = () => { signal?.removeEventListener('abort', abort); resolve(); };
        const timer = setTimeout(done, 1000);
        const abort = () => { clearTimeout(timer); signal?.removeEventListener('abort', abort); reject(signal?.reason || new Error('Aborted')); };
        signal?.addEventListener('abort', abort, { once: true });
      });
    }
    throw new Error('Analysis is still running; keep polling the job endpoint.');
  }
  incidents(job: string, filters: { limit?: number; offset?: number; scenario?: string; band?: string; status?: string; search?: string; min_priority?: number; include_dismissed?: boolean } = {}) {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) if (value !== undefined) query.set(key, String(value));
    return this.request<Page<Incident>>(this.path(job, `/incidents?${query}`));
  }
  incident(job: string, id: string) {
    return this.request<{ incident: Incident; explanation: Explanation; representative_evidence: Evidence[] }>(this.path(job, `/incidents/${encodeURIComponent(id)}`));
  }
  evidence(job: string, id: string, limit = 50, offset = 0) {
    return this.request<Page<Evidence>>(this.path(job, `/incidents/${encodeURIComponent(id)}/evidence?limit=${limit}&offset=${offset}`));
  }
  related(job: string, id: string) {
    return this.request<{ items: RelatedIncident[] }>(this.path(job, `/incidents/${encodeURIComponent(id)}/related`));
  }
  ask(job: string, id: string, question: string, useLLM = false) {
    return this.request<Explanation>(this.path(job, `/incidents/${encodeURIComponent(id)}/ask`), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, use_llm: useLLM }) });
  }
  feedback(job: string, id: string, review: Incident['review']) {
    return this.request<Incident>(this.path(job, `/incidents/${encodeURIComponent(id)}/feedback`), { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(review) });
  }
  stats(job: string) {
    return this.request<{ job: Job; total_incidents: number; breakdown: Record<string, unknown>[] }>(this.path(job, '/stats'));
  }
}
