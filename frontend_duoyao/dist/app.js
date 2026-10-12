import {demoData} from './data.js';
import {validateResults} from './schema.js';
import {BlueTeamBackend} from './backend.js';

const $=s=>document.querySelector(s);
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=v=>new Date(v).toLocaleString('en-GB',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',timeZone:'UTC'});
const time=v=>new Date(v).toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',second:'2-digit',timeZone:'UTC'});
let data=structuredClone(demoData),selected=data.incidents[0].id,activeTab='timeline',reviewed=new Set();
let backend=null, queuePage=0;
const pageSize=50, pendingDetails=new WeakSet(), detailErrors=new WeakMap();

function notify(message,error=false){const n=$('#notice');n.textContent=message;n.hidden=false;n.className=error?'error':'';}
function filtered(){const term=$('#search').value.trim().toLowerCase();return data.incidents.filter(c=>(!term||[c.title,c.entity,c.id,...c.sources,...c.evidence.map(e=>e.id+' '+e.title)].join(' ').toLowerCase().includes(term))&&($('#priority-filter').value==='all'||c.priority===$('#priority-filter').value)&&($('#status-filter').value==='all'||reviewed.has(c.id)===($('#status-filter').value==='reviewed'))).sort((a,b)=>({high:0,medium:1,low:2}[a.priority]-{high:0,medium:1,low:2}[b.priority])||b.score-a.score||a.id.localeCompare(b.id));}
function render(){
  $('#mode-tag').textContent=data.mode==='demo'?'DEMO DATA':backend?'BACKEND CONNECTED':'IMPORTED RESULTS';$('#mode-tag').className='pill '+(data.mode==='demo'?'demo':'live');
  $('#dataset-name').textContent=data.dataset.name;$('#dataset-description').textContent=data.dataset.description||'Supplied by your analysis pipeline';
  $('#metric-alerts').textContent=data.incidents.reduce((n,c)=>n+c.alert_count,0).toLocaleString();$('#metric-groups').textContent=data.incidents.length;$('#metric-high').textContent=data.incidents.filter(c=>c.priority==='high').length;$('#metric-reviewed').textContent=reviewed.size;
  const matches=filtered();queuePage=Math.min(queuePage,Math.max(0,Math.ceil(matches.length/pageSize)-1));
  const cases=matches.slice(queuePage*pageSize,(queuePage+1)*pageSize);if(!cases.some(c=>c.id===selected))selected=cases[0]?.id??null;
  $('#queue-count').textContent=matches.length;
  const pagination=$('#pagination');pagination.hidden=matches.length<=pageSize;
  pagination.innerHTML=`<button class="button" id="prev-page" ${queuePage===0?'disabled':''}>← Previous</button><span>${queuePage*pageSize+1}–${Math.min((queuePage+1)*pageSize,matches.length)} of ${matches.length}</span><button class="button" id="next-page" ${(queuePage+1)*pageSize>=matches.length?'disabled':''}>Next →</button>`;
  $('#prev-page').onclick=()=>{queuePage--;render();$('#queue-list').scrollTop=0;};$('#next-page').onclick=()=>{queuePage++;render();$('#queue-list').scrollTop=0;};
  $('#queue-list').innerHTML=cases.length?cases.map(c=>`<button class="case ${c.priority} ${c.id===selected?'selected':''}" data-case="${escapeHTML(c.id)}" aria-pressed="${c.id===selected}"><div class="case-top"><span class="priority ${c.priority}">${c.priority} priority</span><span class="case-time">${date(c.start)} UTC</span></div><h3>${escapeHTML(c.title)}</h3><div class="case-meta"><code>${escapeHTML(c.entity)}</code><span>·</span><span>${c.alert_count} alerts</span><span class="case-arrow">${reviewed.has(c.id)?'<span class="reviewed-label">✓ Reviewed</span>':'↗'}</span></div></button>`).join(''):'<div class="empty"><strong>No matching investigations</strong>Try a different search or clear your filters.</div>';
  document.querySelectorAll('[data-case]').forEach(el=>el.addEventListener('click',()=>{selected=el.dataset.case;activeTab='timeline';render();}));renderDetail();
}
function renderDetail(){
 const c=data.incidents.find(c=>c.id===selected);if(!c){$('#detail').innerHTML='<div class="empty"><strong>A little less noise.</strong>No investigations match this view.</div>';return;}
 if(backend&&c.backend&&!c.backend.loaded){
  const error=detailErrors.get(c);
  $('#detail').innerHTML=`<h2>${escapeHTML(c.title)}</h2><div class="empty" role="status"><strong>${error?'Unable to load this event':'Loading original evidence…'}</strong>${error?escapeHTML(error):'Retrieving the backend explanation and representative records.'}${error?'<p><button id="retry-detail" class="button">Retry</button></p>':''}</div>`;
  if(error)$('#retry-detail').onclick=()=>{detailErrors.delete(c);renderDetail();};else ensureDetail(c);return;
 }
 $('#detail').innerHTML=`<div class="detail-top"><span class="priority ${c.priority}">${c.priority} priority</span><span class="score-label">Review score <strong>${c.score}</strong><span>/100</span></span><span class="detail-id">${escapeHTML(c.id)}</span></div><h2>${escapeHTML(c.title)}</h2><div class="detail-meta"><code>${escapeHTML(c.entity)}</code><span>${escapeHTML(c.sources.join(' + '))}</span><span>·</span><span>${date(c.start)} – ${date(c.end)} UTC</span></div><div class="detail-actions"><button id="review" class="button primary">${reviewed.has(c.id)?'✓ Reviewed · Undo':'✓ Mark reviewed (local)'}</button><button id="export" class="button">↓ Export case</button></div><div class="summary-box"><div class="section-label"> ${data.mode==='demo'?'DEMO SUMMARY':'WHAT HAPPENED'}</div><p>${escapeHTML(c.summary)}</p></div><div class="tabs" role="tablist" aria-label="Investigation details">${[['timeline','Timeline'],['reasoning','Why this matters'],['evidence','Evidence']].map(([id,label])=>`<button class="tab ${activeTab===id?'active':''}" id="tab-${id}" data-tab="${id}" role="tab" aria-selected="${activeTab===id}" aria-controls="tab-panel">${label}${id==='evidence'?` <span>${c.evidence.length}</span>`:''}</button>`).join('')}</div><div class="tab-panel" id="tab-panel" role="tabpanel" aria-labelledby="tab-${activeTab}" tabindex="0"></div><div class="note">${data.mode==='demo'?'Demo only: all cases, scores, and evidence shown here are fictional. No model has analyzed the AIT data in this interface.':'This page displays results provided by your pipeline. Priorities and explanations are not independently verified.'}</div>`;
 $('#review').onclick=()=>{reviewed.has(c.id)?reviewed.delete(c.id):reviewed.add(c.id);render();if(backend)notify('Review mark saved for this page session only. Backend review status was not changed.');};
 $('#export').onclick=()=>{const blob=new Blob([JSON.stringify({schema_version:1,mode:data.mode,dataset:data.dataset,incidents:[c],review_status:reviewed.has(c.id)?'reviewed':'open'},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`signaldesk-${c.id.replace(/[^a-z0-9_-]/gi,'_')}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notify('Case exported with evidence and current review status.');};
 document.querySelectorAll('[data-tab]').forEach(el=>{el.onclick=()=>{activeTab=el.dataset.tab;renderDetail();$(`#tab-${activeTab}`).focus();};el.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const keys=['timeline','reasoning','evidence'];activeTab=e.key==='Home'?keys[0]:e.key==='End'?keys[2]:keys[(keys.indexOf(activeTab)+(e.key==='ArrowRight'?1:2))%3];renderDetail();$(`#tab-${activeTab}`).focus();};});
 const panel=$('#tab-panel');
 if(backend&&c.backend){
  const info=document.createElement('div');info.className='backend-context';
  info.textContent=`Backend status: ${c.backend.review_status}. Explanation: ${c.backend.explanation_mode}. Showing ${c.evidence.length} representative records of ${c.alert_count.toLocaleString()} alerts; this is not the complete timeline.`;
  $('.tabs').before(info);
 }
 if(activeTab==='timeline'){
  panel.innerHTML=c.evidence.length?`<ol class="timeline">${[...c.evidence].sort((a,b)=>Date.parse(a.timestamp)-Date.parse(b.timestamp)).map(e=>`<li><div class="timeline-head"><span>${date(e.timestamp)}:${time(e.timestamp).slice(-2)} UTC</span><button class="evidence-link" data-evidence="${escapeHTML(e.id)}">${escapeHTML(e.id)} ↗</button></div><strong>${escapeHTML(e.title)}</strong><p>${escapeHTML(e.description||'')}</p></li>`).join('')}</ol>`:'<p>No evidence supplied for this group.</p>';
  document.querySelectorAll('[data-evidence]').forEach(el=>el.onclick=()=>{activeTab='evidence';renderDetail();const target=[...document.querySelectorAll('.evidence')].find(d=>d.dataset.id===el.dataset.evidence);if(target){target.open=true;target.querySelector('summary').focus();}});
 }else if(activeTab==='reasoning')panel.innerHTML=[['Why review this',c.reasons],['Possible normal explanations',c.benign_explanations],['What is still unknown',c.missing_context],['Suggested next steps',c.next_steps]].map(([title,items])=>`<section class="reason-block"><h3>${title}</h3>${items.length?`<ul>${items.map(v=>`<li>${escapeHTML(v)}</li>`).join('')}</ul>`:'<p>Not supplied.</p>'}</section>`).join('');
 else panel.innerHTML=c.evidence.length?c.evidence.map(e=>`<details class="evidence" data-id="${escapeHTML(e.id)}"><summary><strong>${escapeHTML(e.id)}</strong> &nbsp; ${escapeHTML(e.title)}</summary><pre>${escapeHTML(JSON.stringify(e.raw,null,2))}</pre></details>`).join(''):'<p>No evidence supplied for this group.</p>';
 if(backend&&c.backend&&activeTab==='reasoning'){
  const section=document.createElement('section');section.className='reason-block';
  section.innerHTML='<h3>Backend score breakdown</h3><pre class="score-breakdown"></pre>';
  section.querySelector('pre').textContent=JSON.stringify({priority_components:c.backend.priority_components,rule_components:c.backend.score_components,ml:c.backend.ml},null,2);panel.append(section);
 }
}
async function ensureDetail(c){
 if(pendingDetails.has(c))return;pendingDetails.add(c);const client=backend, dataset=data;
 try{const detail=await client.detail(c.id);validateResults({schema_version:1,mode:'results',dataset:data.dataset,incidents:[detail]});if(data!==dataset||backend!==client)return;Object.assign(c,detail);}
 catch(err){if(data===dataset&&backend===client)detailErrors.set(c,err.message);}
 finally{pendingDetails.delete(c);if(data===dataset&&backend===client&&selected===c.id)renderDetail();}
}
function loadResults(value,client=null){const checked=validateResults(value);data=checked;backend=client;queuePage=0;selected=null;reviewed=new Set();activeTab='timeline';$('#search').value='';$('#priority-filter').value='all';$('#status-filter').value='all';render();}
function filtersChanged(){queuePage=0;render();}
$('#search').addEventListener('input',filtersChanged);$('#priority-filter').onchange=filtersChanged;$('#status-filter').onchange=filtersChanged;
$('#import').onclick=()=>$('#file-input').click();$('#file-input').onchange=async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>10*1024*1024)throw Error('File is over 10 MB. Import grouped results, not the raw dataset.');loadResults(JSON.parse(await file.text()));notify(`Loaded ${data.incidents.length} groups from ${file.name}.`);}catch(err){notify(`Import failed: ${err.message}`,true);}finally{e.target.value='';}};
$('#reset').onclick=()=>{loadResults(structuredClone(demoData));notify('Demo restored. Review progress has been reset.');};
$('#connect').onclick=()=>$('#backend-dialog').showModal();$('#close-dialog').onclick=()=>$('#backend-dialog').close();
$('#connection-type').onchange=()=>{const blue=$('#connection-type').value==='blue-team';$('#job-field').hidden=!blue;$('#job-id').required=blue;$('#endpoint').value=blue?'http://127.0.0.1:8000':'';};
$('#backend-form').onsubmit=async e=>{
 e.preventDefault();const button=$('#fetch-button');$('#connection-error').textContent='';button.disabled=true;button.textContent='Loading…';
 try{
  if($('#connection-type').value==='blue-team'){
   const client=new BlueTeamBackend($('#endpoint').value,$('#job-id').value);
   const result=await client.results((loaded,total)=>{button.textContent=`Loading ${loaded}/${total}…`;});loadResults(result,client);
  }else{
   const url=new URL($('#endpoint').value);if(!['http:','https:'].includes(url.protocol))throw Error('Use an http:// or https:// endpoint.');
   const response=await fetch(url,{signal:AbortSignal.timeout(15000),credentials:'omit'});if(!response.ok)throw Error(`Server returned HTTP ${response.status}.`);
   const body=await response.text();if(body.length>10*1024*1024)throw Error('Response is too large. Return grouped results under 10 MB.');loadResults(JSON.parse(body));
  }
  $('#backend-dialog').close();notify(`Loaded ${data.incidents.length.toLocaleString()} events. ${backend?'Original evidence loads when you select an event. Review marks are local only.':'Results supplied by your backend.'}`);
 }catch(err){$('#connection-error').textContent=`Could not load results: ${err.message} Check the URL, job ID, server, and CORS origins.`;}
 finally{button.disabled=false;button.textContent='Load results';}
};
document.addEventListener('keydown',e=>{if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)&&!$('#backend-dialog').open){e.preventDefault();$('#search').focus();}});
render();
