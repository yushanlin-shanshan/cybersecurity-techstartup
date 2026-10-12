// Read-only adapter for blue-team-backend's /api/v1 API.
export class BlueTeamBackend {
  constructor(base, job='demo', fetcher=(...args)=>fetch(...args)) {
    const url=new URL(base);
    if(!['http:','https:'].includes(url.protocol)||url.username||url.password||url.search||url.hash)throw Error('Enter a plain HTTP(S) backend base URL, without credentials or query parameters.');
    this.base=url.href.replace(/\/$/,'');this.job=job.trim();this.fetcher=fetcher;
    if(!this.job)throw Error('A job ID is required.');
    this.path=`/api/v1/jobs/${encodeURIComponent(this.job)}`;
  }
  async get(path){
    const response=await this.fetcher(this.base+path,{credentials:'omit',signal:AbortSignal.timeout(20000)});
    if(!response.ok)throw Error(`Backend HTTP ${response.status}${response.status===401?': authentication required; this connector supports a local backend without an API token.':''}`);
    return response.json();
  }
  async results(progress=()=>{}){
    const job=await this.get(this.path);
    if(job.status!=='ready')throw Error(`Job ${this.job} is ${job.status}: ${job.error||job.phase||'not ready'}.`);
    const groups=[];let total=null;
    do{
      const page=await this.get(`${this.path}/incidents?limit=200&offset=${groups.length}&include_dismissed=true`);
      if(!Array.isArray(page.items)||!Number.isSafeInteger(page.total)||page.total<0)throw Error('Unexpected incident page format.');
      if(page.total>10000)throw Error('This job exceeds the 10,000-event browser limit. Use a smaller scenario.');
      if(total!==null&&total!==page.total)throw Error('The queue changed during loading. Please reconnect.');
      total=page.total;
      if(!page.items.length&&groups.length<total)throw Error('Backend returned an incomplete incident page.');
      groups.push(...page.items);progress(groups.length,total);
    }while(groups.length<total);
    if(groups.length!==total)throw Error('Incident total does not match the returned records.');
    return {schema_version:1,mode:'results',dataset:{name:`Blue Team · ${this.job}`,description:`${total.toLocaleString()} events · real backend results${job.summary?.partial_input?' · PARTIAL INPUT':''} · local explanations`},incidents:groups.map(adaptIncident)};
  }
  async detail(id){const payload=await this.get(`${this.path}/incidents/${encodeURIComponent(id)}`);if(payload.incident?.id!==id)throw Error('Backend returned a mismatched incident ID.');return adaptDetail(payload,this);}
  evidenceURL(id){return this.base+this.path+`/incidents/${encodeURIComponent(id)}/evidence?limit=200&offset=0`;}
}

export function adaptIncident(g){
  return {id:g.id,title:g.title,priority:g.priority_band,score:g.priority,entity:g.anchor?.slice(1).join(' / ')||g.hosts?.join(', ')||'Unknown',start:g.start,end:g.end,alert_count:g.count,sources:g.sensors,summary:'Select this event to load its explanation and representative original evidence.',reasons:[],benign_explanations:[],missing_context:[],next_steps:[],evidence:[],backend:{loaded:false,review_status:g.review?.status||'new',rule_score:g.score,priority_components:g.priority_components,score_components:g.score_components,ml:g.ml}};
}
export function adaptDetail(payload,client){
  const c=adaptIncident(payload.incident),ex=payload.explanation;
  if(!ex||typeof ex.answer!=='string'||!Array.isArray(ex.claims)||!Array.isArray(payload.representative_evidence))throw Error('Unexpected incident detail format.');
  c.summary=ex.answer;
  c.reasons=ex.claims.map(claim=>`${claim.text} [Evidence: ${claim.evidence_ids.join(', ')}]`);
  c.missing_context=ex.caveats||[];c.next_steps=ex.next_steps||[];
  c.evidence=payload.representative_evidence.map(e=>({id:String(e.alert_id),timestamp:new Date(e.normalized.time*1000).toISOString(),title:e.normalized.description,description:`${e.normalized.source||'Unknown file'} · line ${e.normalized.line??'unknown'} · ${e.normalized.sensor||'Unknown detector'}`,source:e.normalized.sensor||'Unknown',raw:e.original_record}));
  const available=new Set(c.evidence.map(e=>e.id));
  if(ex.claims.some(claim=>claim.evidence_ids.some(id=>!available.has(String(id)))))throw Error('An explanation cites evidence absent from the detail response.');
  c.backend={...c.backend,loaded:true,explanation_mode:ex.mode,evidence_url:client.evidenceURL(c.id)};
  return c;
}
