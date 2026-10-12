import {validateResults} from './schema.js';
import {BlueTeamBackend} from './backend.js';

const $=s=>document.querySelector(s);
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=v=>new Date(v).toLocaleString('en-GB',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',timeZone:'UTC'});
const time=v=>new Date(v).toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',second:'2-digit',timeZone:'UTC'});
let data={schema_version:1,mode:'results',dataset:{name:'Investigation data'},incidents:[]},selected=null,activeTab='timeline';
let backend=null, queuePage=0;
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
  $('#queue-list').innerHTML=cases.length?cases.map(c=>`<button class="case ${c.priority} ${c.id===selected?'selected':''}" data-case="${escapeHTML(c.id)}" aria-pressed="${c.id===selected}"><div class="case-top"><span class="priority ${c.priority}">${c.priority} priority</span><span class="case-time">${date(c.start)} UTC</span></div><h3>${escapeHTML(c.title)}</h3><div class="case-meta"><code>${escapeHTML(c.entity)}</code><span>·</span><span>${c.alert_count} alerts</span><span class="case-arrow">${c.backend?.review_status&&c.backend.review_status!=='new'?`<span class="reviewed-label">${escapeHTML(c.backend.review_status)}</span>`:'↗'}</span></div></button>`).join(''):'<div class="empty"><strong>No matching investigations</strong>Try a different search or clear your filters.</div>';
  document.querySelectorAll('[data-case]').forEach(el=>el.addEventListener('click',()=>{selected=el.dataset.case;activeTab='timeline';render();}));renderDetail();
}
function renderDetail(){
 const c=data.incidents.find(c=>c.id===selected);if(!c){$('#detail').innerHTML='<div class="empty"><strong>A little less noise.</strong>No investigations match this view.</div>';return;}
 if(backend&&c.backend&&!c.backend.loaded){
  const error=detailErrors.get(c);
  $('#detail').innerHTML=`<h2>${escapeHTML(c.title)}</h2><div class="empty" role="status"><strong>${error?'Unable to load this event':'Loading original evidence…'}</strong>${error?'Please try again in a moment.':'Retrieving the explanation and representative records.'}${error?'<p><button id="retry-detail" class="button">Retry</button></p>':''}</div>`;
  if(error)$('#retry-detail').onclick=()=>{detailErrors.delete(c);renderDetail();};else ensureDetail(c);return;
 }
 $('#detail').innerHTML=`<div class="detail-top"><span class="priority ${c.priority}">${c.priority} priority</span><span class="score-label">Review score <strong>${c.score}</strong><span>/100</span></span><span class="detail-id">${escapeHTML(c.id)}</span></div><h2>${escapeHTML(c.title)}</h2><div class="detail-meta"><code>${escapeHTML(c.entity)}</code><span>${escapeHTML(c.sources.join(' + '))}</span><span>·</span><span>${date(c.start)} – ${date(c.end)} UTC</span></div><div class="detail-actions"><span class="review-status">Status: ${escapeHTML(c.backend?.review_status||'Unknown')}</span><button id="export" class="button">↓ Export case</button></div><div class="summary-box"><div class="section-label"> WHAT HAPPENED</div><p>${escapeHTML(c.summary)}</p></div><div class="tabs" role="tablist" aria-label="Investigation details">${[['timeline','Timeline'],['reasoning','Why this matters'],['evidence','Evidence']].map(([id,label])=>`<button class="tab ${activeTab===id?'active':''}" id="tab-${id}" data-tab="${id}" role="tab" aria-selected="${activeTab===id}" aria-controls="tab-panel">${label}${id==='evidence'?` <span>${c.evidence.length}</span>`:''}</button>`).join('')}</div><div class="tab-panel" id="tab-panel" role="tabpanel" aria-labelledby="tab-${activeTab}" tabindex="0"></div><div class="note">Priorities help guide investigation. They do not establish that an attack occurred.</div>`;
 $('#export').onclick=()=>{const blob=new Blob([JSON.stringify({schema_version:1,mode:data.mode,dataset:data.dataset,incidents:[c],review_status:c.backend?.review_status||'unknown'},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`signaldesk-${c.id.replace(/[^a-z0-9_-]/gi,'_')}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notify('Case exported with evidence and current review status.');};
 document.querySelectorAll('[data-tab]').forEach(el=>{el.onclick=()=>{activeTab=el.dataset.tab;renderDetail();$(`#tab-${activeTab}`).focus();};el.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const keys=['timeline','reasoning','evidence'];activeTab=e.key==='Home'?keys[0]:e.key==='End'?keys[2]:keys[(keys.indexOf(activeTab)+(e.key==='ArrowRight'?1:2))%3];renderDetail();$(`#tab-${activeTab}`).focus();};});
 const panel=$('#tab-panel');
 if(backend&&c.backend){
  const info=document.createElement('div');info.className='backend-context';
  info.textContent=`Showing ${c.evidence.length} representative records of ${c.alert_count.toLocaleString()} alerts; this is not the complete timeline.`;
  $('.tabs').before(info);
 }
 if(activeTab==='timeline'){
  panel.innerHTML=c.evidence.length?`<ol class="timeline">${[...c.evidence].sort((a,b)=>Date.parse(a.timestamp)-Date.parse(b.timestamp)).map(e=>`<li><div class="timeline-head"><span>${date(e.timestamp)}:${time(e.timestamp).slice(-2)} UTC</span><button class="evidence-link" data-evidence="${escapeHTML(e.id)}">${escapeHTML(e.id)} ↗</button></div><strong>${escapeHTML(e.title)}</strong><p>${escapeHTML(e.description||'')}</p></li>`).join('')}</ol>`:'<p>No evidence supplied for this group.</p>';
  document.querySelectorAll('[data-evidence]').forEach(el=>el.onclick=()=>{activeTab='evidence';renderDetail();const target=[...document.querySelectorAll('.evidence')].find(d=>d.dataset.id===el.dataset.evidence);if(target){target.open=true;target.querySelector('summary').focus();}});
 }else if(activeTab==='reasoning')panel.innerHTML=[['Why review this',c.reasons],['Possible normal explanations',c.benign_explanations],['What is still unknown',c.missing_context],['Suggested next steps',c.next_steps]].map(([title,items])=>`<section class="reason-block"><h3>${title}</h3>${items.length?`<ul>${items.map(v=>`<li>${escapeHTML(v)}</li>`).join('')}</ul>`:'<p>Not supplied.</p>'}</section>`).join('');
 else panel.innerHTML=c.evidence.length?c.evidence.map(e=>`<details class="evidence" data-id="${escapeHTML(e.id)}"><summary><strong>${escapeHTML(e.id)}</strong> &nbsp; ${escapeHTML(e.title)}</summary><pre>${escapeHTML(JSON.stringify(e.raw,null,2))}</pre></details>`).join(''):'<p>No evidence supplied for this group.</p>';
 if(backend&&c.backend&&activeTab==='reasoning'){
  const section=document.createElement('section');section.className='reason-block';
  section.innerHTML='<h3>Score breakdown</h3><pre class="score-breakdown"></pre>';
  section.querySelector('pre').textContent=JSON.stringify({priority_components:c.backend.priority_components,rule_components:c.backend.score_components,ml:c.backend.ml},null,2);panel.append(section);
 }
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
async function start(){
 $('#notice').hidden=true;
 $('#mode-tag').textContent='Loading';$('#mode-tag').className='pill';
 $('#dataset-name').textContent='Investigation data';$('#dataset-description').textContent='';
 for(const id of ['metric-alerts','metric-groups','metric-high','metric-reviewed'])$('#'+id).textContent='—';
 for(const el of [$('#search'),$('#priority-filter'),$('#status-filter')])el.disabled=true;
 $('#queue-count').textContent='';$('#pagination').hidden=true;
 $('#queue-list').innerHTML='<div class="empty" role="status"><strong>Loading events…</strong>Preparing your investigation queue.</div>';
 $('#detail').innerHTML='<div class="empty"><strong>Your evidence workspace</strong>Select an event once the investigation data is ready.</div>';
 try{
  const response=await fetch('/app-config.json',{cache:'no-store',signal:AbortSignal.timeout(10000)});
  if(!response.ok)throw Error('Application configuration unavailable.');
  const config=await response.json();
  if(typeof config.job_id!=='string'||!config.job_id.trim())throw Error('No dataset configured.');
  const client=new BlueTeamBackend(location.origin,config.job_id);
  const results=await client.results((loaded,total)=>{$('#dataset-description').textContent=`Loading ${loaded.toLocaleString()} of ${total.toLocaleString()} events…`;});
  loadResults(results,client);
  for(const el of [$('#search'),$('#priority-filter'),$('#status-filter')])el.disabled=false;
 }catch(err){
  console.error('Unable to load investigation data:',err.message);
  $('#mode-tag').textContent='Unavailable';$('#dataset-description').textContent='';
  $('#queue-list').innerHTML='<div class="empty"><strong>Events are temporarily unavailable</strong>Please try again in a moment.<p><button id="retry-load" class="button primary">Try again</button></p></div>';
  $('#detail').innerHTML='<div class="empty"><strong>No event data loaded</strong>Your events will appear here when the service is available.</div>';
  $('#retry-load').onclick=start;
 }
}
document.addEventListener('keydown',e=>{if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();$('#search').focus();}});
start();
