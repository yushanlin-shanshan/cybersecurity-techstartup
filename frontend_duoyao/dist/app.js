import {validateResults} from './schema.js';
import {BlueTeamBackend} from './backend.js';
import {formatSummary} from './summary.js';
import {reviewStatuses,reviewAssessments} from './review.js';
import {listJobs,uploadDataset,jobLabel,phases} from './datasets.js';

const $=s=>document.querySelector(s);
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=v=>new Date(v).toLocaleString('en-GB',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',timeZone:'UTC'});
const time=v=>new Date(v).toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',second:'2-digit',timeZone:'UTC'});
let data={schema_version:1,mode:'results',dataset:{name:'Investigation data'},incidents:[]},selected=null,activeTab='timeline';
let backend=null, queuePage=0, canReview=false;
const reviewDrafts=new WeakMap();
let appConfig=null,loadVersion=0,uploadBusy=false;
const pageSize=50, pendingDetails=new WeakSet(), detailErrors=new WeakMap();

function notify(message,error=false){const n=$('#notice');n.textContent=message;n.hidden=false;n.className=error?'error':'';}
function filtered(){const term=$('#search').value.trim().toLowerCase();return data.incidents.filter(c=>(!term||[c.title,c.entity,c.id,...c.sources,...c.evidence.map(e=>e.id+' '+e.title)].join(' ').toLowerCase().includes(term))&&($('#priority-filter').value==='all'||c.priority===$('#priority-filter').value)&&($('#status-filter').value==='all'||c.backend?.review_status===$('#status-filter').value)).sort((a,b)=>({high:0,medium:1,low:2}[a.priority]-{high:0,medium:1,low:2}[b.priority])||b.score-a.score||a.id.localeCompare(b.id));}
function render(){
  $('#mode-tag').textContent='Ready';$('#mode-tag').className='pill live';
  $('#dataset-name').textContent=data.dataset.name;$('#dataset-description').textContent=data.dataset.description||'Supplied by your analysis pipeline';
  $('#metric-alerts').textContent=data.incidents.reduce((n,c)=>n+c.alert_count,0).toLocaleString();$('#metric-groups').textContent=data.incidents.length;$('#metric-high').textContent=data.incidents.filter(c=>c.priority==='high').length;$('#metric-reviewed').textContent=data.incidents.filter(c=>['resolved','dismissed'].includes(c.backend?.review_status)).length;
  const matches=filtered();queuePage=Math.min(queuePage,Math.max(0,Math.ceil(matches.length/pageSize)-1));
  const cases=matches.slice(queuePage*pageSize,(queuePage+1)*pageSize);if(!cases.some(c=>c.id===selected))selected=cases[0]?.id??null;
  $('#queue-count').textContent=matches.length;
  const pagination=$('#pagination');pagination.hidden=matches.length<=pageSize;
  pagination.innerHTML=`<button class="button" id="prev-page" ${queuePage===0?'disabled':''}>← Previous</button><span>${queuePage*pageSize+1}–${Math.min((queuePage+1)*pageSize,matches.length)} of ${matches.length}</span><button class="button" id="next-page" ${(queuePage+1)*pageSize>=matches.length?'disabled':''}>Next →</button>`;
  $('#prev-page').onclick=()=>{queuePage--;render();$('#queue-list').scrollTop=0;};$('#next-page').onclick=()=>{queuePage++;render();$('#queue-list').scrollTop=0;};
  $('#queue-list').innerHTML=cases.length?cases.map(c=>`<button class="case ${c.priority} ${c.id===selected?'selected':''}" data-case="${escapeHTML(c.id)}" aria-pressed="${c.id===selected}"><div class="case-top"><span class="priority ${c.priority}">${c.priority} priority</span><span class="case-time">${date(c.start)} UTC</span></div><h3>${escapeHTML(c.title)}</h3><div class="case-meta"><code>${escapeHTML(c.entity)}</code><span>·</span><span>${c.alert_count} alerts</span><span class="case-arrow">${c.backend?.review_status&&c.backend.review_status!=='new'?`<span class="status-badge status-${escapeHTML(c.backend.review_status)}">${escapeHTML(reviewStatuses[c.backend.review_status]?.[0]||c.backend.review_status)}</span>`:'↗'}</span></div></button>`).join(''):'<div class="empty"><strong>No matching investigations</strong>Try a different search or clear your filters.</div>';
  document.querySelectorAll('[data-case]').forEach(el=>el.addEventListener('click',()=>{selected=el.dataset.case;activeTab='timeline';render();}));renderDetail();
}
function renderDetail(){
 const c=data.incidents.find(c=>c.id===selected);if(!c){$('#detail').innerHTML='<div class="empty"><strong>A little less noise.</strong>No investigations match this view.</div>';return;}
 if(backend&&c.backend&&!c.backend.loaded){
  const error=detailErrors.get(c);
  $('#detail').innerHTML=`<h2>${escapeHTML(c.title)}</h2><div class="empty" role="status"><strong>${error?'Unable to load this event':'Loading original evidence…'}</strong>${error?'Please try again in a moment.':'Analyzing this event and retrieving evidence. AI analysis may take a moment.'}${error?'<p><button id="retry-detail" class="button">Retry</button></p>':''}</div>`;
  if(error)$('#retry-detail').onclick=()=>{detailErrors.delete(c);renderDetail();};else ensureDetail(c);return;
 }
 $('#detail').innerHTML=`<div class="detail-top"><span class="priority ${c.priority}">${c.priority} priority</span><span class="score-label">Review score <strong>${c.score}</strong><span>/100</span></span><span class="detail-id">${escapeHTML(c.id)}</span></div><h2>${escapeHTML(c.title)}</h2><div class="detail-meta"><code>${escapeHTML(c.entity)}</code><span>${escapeHTML(c.sources.join(' + '))}</span><span>·</span><span>${date(c.start)} – ${date(c.end)} UTC</span></div><div class="detail-actions"><span class="review-status">Status: <strong class="status-badge status-${escapeHTML(c.backend?.review_status)}">${escapeHTML(reviewStatuses[c.backend?.review_status]?.[0]||'Unknown')}</strong></span>${canReview?'<button id="edit-review" class="button">Update status</button>':''}<button id="export" class="button">↓ Export case</button></div>${renderReview(c)}<div class="summary-box"><div class="section-label"> WHAT HAPPENED</div><div class="summary-content">${formatSummary(c.summary)}</div></div><div class="tabs" role="tablist" aria-label="Investigation details">${[['timeline','Timeline'],['reasoning','Why this matters'],['evidence','Evidence']].map(([id,label])=>`<button class="tab ${activeTab===id?'active':''}" id="tab-${id}" data-tab="${id}" role="tab" aria-selected="${activeTab===id}" aria-controls="tab-panel">${label}${id==='evidence'?` <span>${c.evidence.length}</span>`:''}</button>`).join('')}</div><div class="tab-panel" id="tab-panel" role="tabpanel" aria-labelledby="tab-${activeTab}" tabindex="0"></div><div class="note">Priorities help guide investigation. They do not establish that an attack occurred.</div>`;
 bindReview(c);
 $('#export').onclick=()=>{const blob=new Blob([JSON.stringify({schema_version:1,mode:data.mode,dataset:data.dataset,incidents:[c],review_status:c.backend?.review_status||'unknown'},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`sigsig-${c.id.replace(/[^a-z0-9_-]/gi,'_')}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notify('Case exported with evidence and current review status.');};
 document.querySelectorAll('[data-tab]').forEach(el=>{el.onclick=()=>{activeTab=el.dataset.tab;renderDetail();$(`#tab-${activeTab}`).focus();};el.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const keys=['timeline','reasoning','evidence'];activeTab=e.key==='Home'?keys[0]:e.key==='End'?keys[2]:keys[(keys.indexOf(activeTab)+(e.key==='ArrowRight'?1:2))%3];renderDetail();$(`#tab-${activeTab}`).focus();};});
 const panel=$('#tab-panel');
 if(backend&&c.backend){
  const info=document.createElement('div');info.className='backend-context';
  info.textContent=`Showing ${c.evidence.length} representative records of ${c.alert_count.toLocaleString()} alerts; this is not the complete timeline.`;
  $('.tabs').before(info);
 }
 if(activeTab==='timeline'){
  panel.innerHTML=c.evidence.length?`<ol class="timeline">${[...c.evidence].sort((a,b)=>Date.parse(a.timestamp)-Date.parse(b.timestamp)).map(e=>`<li><div class="timeline-head"><span>${date(e.timestamp)}:${time(e.timestamp).slice(-2)} UTC</span><button class="evidence-link" data-evidence="${escapeHTML(e.id)}">${escapeHTML(e.id)} ↗</button></div><strong>${escapeHTML(e.title)}</strong><p>${escapeHTML(e.description||'')}</p></li>`).join('')}</ol>`:'<p>No evidence supplied for this group.</p>';

 }else if(activeTab==='reasoning')panel.innerHTML=[['Why review this',c.reasons],['Possible normal explanations',null],['What is still unknown',c.missing_context],['Suggested next steps',c.next_steps]].map(([title,items])=>items===null?renderBenign(c):`<section class="reason-block"><h3>${title}</h3>${items.length?`<ul>${items.map(v=>`<li>${escapeHTML(v)}</li>`).join('')}</ul>`:'<p>Not supplied.</p>'}</section>`).join('');
 else panel.innerHTML=c.evidence.length?c.evidence.map(e=>`<details class="evidence" data-id="${escapeHTML(e.id)}"><summary><strong>${escapeHTML(e.id)}</strong> &nbsp; ${escapeHTML(e.title)}</summary><pre>${escapeHTML(JSON.stringify(e.raw,null,2))}</pre></details>`).join(''):'<p>No evidence supplied for this group.</p>';
  document.querySelectorAll('[data-evidence]').forEach(el=>el.onclick=()=>{activeTab='evidence';renderDetail();const target=[...document.querySelectorAll('.evidence')].find(d=>d.dataset.id===el.dataset.evidence);if(target){target.open=true;target.querySelector('summary').focus();}});
 if(backend&&c.backend&&activeTab==='reasoning'){
  const section=document.createElement('section');section.className='reason-block';
  section.innerHTML='<h3>Score breakdown</h3><pre class="score-breakdown"></pre>';
  section.querySelector('pre').textContent=JSON.stringify({priority_components:c.backend.priority_components,rule_components:c.backend.score_components,ml:c.backend.ml},null,2);panel.append(section);
 }
}
function draftFor(c){
 if(!reviewDrafts.has(c))reviewDrafts.set(c,{open:false,saving:false,error:'',status:c.backend.review_status,disposition:c.backend.review_disposition,note:c.backend.review_note});
 return reviewDrafts.get(c);
}
function renderReview(c){
 const d=draftFor(c);
 if(!canReview||!d.open){
  return `<div class="review-summary"><span>Assessment: ${escapeHTML(reviewAssessments[c.backend.review_disposition]||'Not assessed')}</span>${c.backend.review_note?`<p><strong>Review note</strong> ${escapeHTML(c.backend.review_note)}</p>`:''}${!canReview?'<p>Status editing is disabled for this deployment.</p>':''}</div>`;
 }
 return `<form id="review-form" class="review-form"><h3>Update review</h3><p>Status tracks the work. Assessment records your conclusion about the activity.</p><fieldset ${d.saving?'disabled':''}><div class="review-fields"><label for="review-status-input">Status<select id="review-status-input" aria-label="Review status" aria-describedby="review-status-help">${Object.entries(reviewStatuses).map(([value,[label]])=>`<option value="${value}" ${d.status===value?'selected':''}>${label}</option>`).join('')}</select></label><label for="review-assessment">Assessment<select id="review-assessment" aria-label="Review assessment">${Object.entries(reviewAssessments).map(([value,label])=>`<option value="${value}" ${d.disposition===value?'selected':''}>${label}</option>`).join('')}</select></label></div><p id="review-status-help">${escapeHTML(reviewStatuses[d.status]?.[1])}</p><label class="review-note-label" for="review-note">Review note <span>(optional)</span><textarea id="review-note" aria-label="Review note" maxlength="2000" rows="3" placeholder="What did you check, and why did you choose this status?">${escapeHTML(d.note)}</textarea></label><div class="review-buttons"><button type="submit" class="button primary">${d.saving?'Saving…':'Save review'}</button><button type="button" class="button" id="cancel-review">Cancel</button></div></fieldset><p class="review-error" role="alert">${escapeHTML(d.error)}</p><p class="review-sharing">Saved to the backend and shared with everyone using this dataset. You can change the status again later.</p></form>`;
}
function bindReview(c){
 const d=draftFor(c);
 if($('#edit-review')){
  $('#edit-review').disabled=d.saving;
  $('#edit-review').onclick=()=>{d.open=true;renderDetail();$('#review-status-input').focus();};
 }
 const form=$('#review-form');if(!form)return;
 $('#review-status-input').onchange=e=>{d.status=e.target.value;$('#review-status-help').textContent=reviewStatuses[d.status][1];};
 $('#review-assessment').onchange=e=>{d.disposition=e.target.value;};
 $('#review-note').oninput=e=>{d.note=e.target.value;};
 $('#cancel-review').onclick=()=>{reviewDrafts.delete(c);renderDetail();$('#edit-review')?.focus();};
 form.onsubmit=async e=>{
  e.preventDefault();if(d.saving)return;
  d.saving=true;d.error='';renderDetail();
  const dataset=data,client=backend;
  try{
   const saved=await client.updateReview(c.id,{status:d.status,disposition:d.disposition,note:d.note});
   if(data!==dataset||backend!==client)return;
   c.backend.review_status=saved.status;c.backend.review_disposition=saved.disposition;c.backend.review_note=saved.note;
   reviewDrafts.delete(c);
   const hidden=!filtered().some(item=>item.id===c.id);
   notify(`Review saved: ${reviewStatuses[saved.status][0]}.${hidden?' This event no longer matches the current filters.':''}`);
   render();
   if(selected===c.id)$('#edit-review')?.focus();
  }catch(error){
   d.error=error.message;d.saving=false;
   if(data===dataset&&backend===client){if(selected===c.id)renderDetail();else notify(`Review was not saved: ${error.message}`,true);}
  }
 };
}
function renderBenign(c){
 const hypotheses=c.backend?.benign_hypotheses||[];
 const ai=c.backend?.explanation_mode==='llm';
 return `<section class="reason-block benign-section"><div class="benign-heading"><h3>Possible normal explanations</h3><span class="analysis-label">${ai?'AI-generated hypotheses':'AI analysis unavailable'}</span></div><p>${escapeHTML(c.backend?.benign_assessment||'No alternative-cause assessment is available.')}</p>${hypotheses.map(h=>`<article class="benign-card"><p>${escapeHTML(h.text)}</p><p class="verification"><strong>How to verify</strong> ${escapeHTML(h.verification)}</p><div class="hypothesis-evidence"><span>Related evidence</span>${h.evidence_ids.map(id=>`<button class="evidence-link" data-evidence="${escapeHTML(id)}" aria-label="View evidence ${escapeHTML(id)}">${escapeHTML(id)} ↗</button>`).join('')}</div></article>`).join('')}${hypotheses.length?'<p class="hypothesis-note">These are possible causes, not confirmed findings. Verify before dismissing an event.</p>':''}</section>`;
}
async function ensureDetail(c){
 if(pendingDetails.has(c))return;pendingDetails.add(c);const client=backend, dataset=data;
 try{const detail=await client.detail(c.id);validateResults({schema_version:1,mode:'results',dataset:data.dataset,incidents:[detail]});if(data!==dataset||backend!==client)return;Object.assign(c,detail);}
 catch(err){if(data===dataset&&backend===client)detailErrors.set(c,err.message);}
 finally{pendingDetails.delete(c);if(data===dataset&&backend===client&&selected===c.id)renderDetail();}
}
function loadResults(value,client=null){const checked=validateResults(value);data=checked;backend=client;queuePage=0;selected=null;activeTab='timeline';$('#search').value='';$('#priority-filter').value='all';$('#status-filter').value='all';render();}
function filtersChanged(){queuePage=0;render();}
$('#search').addEventListener('input',filtersChanged);$('#priority-filter').onchange=filtersChanged;$('#status-filter').onchange=filtersChanged;
async function start(requestedJob=null){
 const version=++loadVersion;
 const current=()=>version===loadVersion;
 backend=null;data={schema_version:1,mode:'results',dataset:{name:'Investigation data'},incidents:[]};
 $('#notice').hidden=true;
 $('#mode-tag').textContent='Loading';$('#mode-tag').className='pill';
 $('#dataset-name').textContent='Investigation data';$('#dataset-description').textContent='';
 for(const id of ['metric-alerts','metric-groups','metric-high','metric-reviewed'])$('#'+id).textContent='—';
 for(const el of [$('#search'),$('#priority-filter'),$('#status-filter')])el.disabled=true;
 $('#queue-count').textContent='';$('#pagination').hidden=true;
 $('#queue-list').innerHTML='<div class="empty" role="status"><strong>Loading events…</strong>Preparing your investigation queue.</div>';
 $('#detail').innerHTML='<div class="empty"><strong>Your evidence workspace</strong>Select an event once the investigation data is ready.</div>';
 try{
  if(!appConfig){
   const response=await fetch('/app-config.json',{cache:'no-store',signal:AbortSignal.timeout(10000)});
   if(!response.ok){const failure=await response.json().catch(()=>null);throw Error(failure?.detail||'Deployment setup is incomplete: application configuration is unavailable.');}
   appConfig=await response.json();
   if(typeof appConfig.job_id!=='string'||!appConfig.job_id.trim())throw Error('No default dataset configured.');
  }
  if(!current())return;
  canReview=appConfig.can_review===true;
  $('#open-upload').hidden=!appConfig.can_upload;
  $('#upload-limit').textContent=`Maximum file size: ${Math.floor((appConfig.max_upload_bytes||4194304)/1024/1024)} MB.`;
  // Preserve the team's published read-only snapshot when no live API is configured.
  if(typeof appConfig.results_url==='string'&&appConfig.results_url.startsWith('/')&&!appConfig.results_url.startsWith('//')){
   canReview=false;$('#open-upload').hidden=true;
   const response=await fetch(appConfig.results_url,{cache:'no-store',signal:AbortSignal.timeout(60000)});
   if(!response.ok)throw Error('Published event snapshot unavailable.');
   const snapshot=await response.json();if(!current())return;
   loadResults(snapshot);
   $('#dataset-select').innerHTML=`<option>${escapeHTML(snapshot.dataset.name)} · published snapshot</option>`;$('#dataset-select').disabled=true;
   for(const el of [$('#search'),$('#priority-filter'),$('#status-filter')])el.disabled=false;
   return;
  }
  const jobs=await listJobs();if(!current())return;
  let remembered;try{remembered=localStorage.getItem('sigsig-active-job');}catch{}
  const chosen=requestedJob||remembered||appConfig.job_id;
  let job=jobs.find(j=>j.id===chosen)||jobs.find(j=>j.id===appConfig.job_id)||jobs.find(j=>j.status==='ready')||jobs[0];
  $('#dataset-select').innerHTML=jobs.length?jobs.map(j=>`<option value="${escapeHTML(j.id)}" ${j.id===job.id?'selected':''}>${escapeHTML(jobLabel(j))} · ${escapeHTML(j.status)}</option>`).join(''):'<option>No datasets yet</option>';
  $('#dataset-select').disabled=!jobs.length;
  if(!job){$('#mode-tag').textContent='No data';$('#queue-list').innerHTML='<div class="empty"><strong>No datasets yet</strong>Upload a log file to begin an investigation.</div>';return;}
  try{localStorage.setItem('sigsig-active-job',job.id);}catch{}
  $('#dataset-name').textContent=jobLabel(job);
  const client=new BlueTeamBackend(location.origin,job.id);
  while(job.status==='queued'||job.status==='running'){
   const phase=phases[job.phase]||'Processing dataset';
   const count=job.summary?.counts?.accepted;
   $('#mode-tag').textContent='Analyzing';
   $('#queue-list').innerHTML=`<div class="empty" role="status"><strong>${escapeHTML(phase)}</strong><progress aria-label="Dataset analysis in progress"></progress><p>${count===undefined?'Analysis continues on the server. You may switch datasets or return later.':`${Number(count).toLocaleString()} records accepted so far.`}</p></div>`;
   await new Promise(resolve=>setTimeout(resolve,1500));if(!current())return;
   job=await client.get(client.path);if(!current())return;
  }
  if(job.status!=='ready')throw Error(`Dataset analysis failed: ${job.error||'Check the file format and log year, then upload a corrected file.'}`);
  const results=await client.results((loaded,total)=>{if(current())$('#dataset-description').textContent=`Loading ${loaded.toLocaleString()} of ${total.toLocaleString()} events…`;});
  if(!current())return;
  if(job.parameters?.dataset_name)results.dataset.name=job.parameters.dataset_name;
  loadResults(results,client);
  $('#dataset-select').selectedOptions[0].textContent=`${jobLabel(job)} · ready`;
  const rejected=job.summary?.counts?.rejected||0;
  if(rejected)notify(`${rejected.toLocaleString()} records were rejected. The displayed events use accepted records only.`,true);
  for(const el of [$('#search'),$('#priority-filter'),$('#status-filter')])el.disabled=false;
 }catch(err){
  if(!current())return;
  console.error('Unable to load investigation data:',err.message);
  $('#mode-tag').textContent='Unavailable';$('#dataset-description').textContent='';
  notify(err.message,true);
  $('#queue-list').innerHTML='<div class="empty"><strong>Events are temporarily unavailable</strong>Please try again in a moment.<p><button id="retry-load" class="button primary">Try again</button></p></div>';
  $('#detail').innerHTML='<div class="empty"><strong>No event data loaded</strong>Your events will appear here when the service is available.</div>';
  $('#retry-load').onclick=()=>start($('#dataset-select').value||null);
 }
}
$('#dataset-select').onchange=e=>start(e.target.value);
$('#open-upload').onclick=()=>{if(uploadBusy)return;$('#upload-form').reset();$('#log-year').value=new Date().getFullYear();$('#upload-error').textContent='';$('#upload-state').textContent='';$('#upload-dialog').showModal();};
$('#close-upload').onclick=()=>$('#upload-dialog').close();
$('#upload-dialog').addEventListener('cancel',e=>{if(uploadBusy)e.preventDefault();});
$('#dataset-file').onchange=e=>{if(!$('#dataset-title').value)$('#dataset-title').value=(e.target.files[0]?.name||'').slice(0,80);};
$('#upload-form').onsubmit=async e=>{
 e.preventDefault();if(uploadBusy)return;
 uploadBusy=true;$('#upload-fields').disabled=true;$('#upload-error').textContent='';$('#upload-state').textContent='Uploading file… Please keep this page open.';
 try{
  const job=await uploadDataset($('#dataset-file').files[0],{name:$('#dataset-title').value,year:Number($('#log-year').value),allowLLM:$('#upload-ai').checked,maxBytes:appConfig.max_upload_bytes||4194304});
  $('#upload-dialog').close();start(job.id);
 }catch(error){$('#upload-error').textContent=error.message;}
 finally{uploadBusy=false;$('#upload-fields').disabled=false;$('#upload-state').textContent='';}
};
document.addEventListener('keydown',e=>{if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();$('#search').focus();}});
start();
