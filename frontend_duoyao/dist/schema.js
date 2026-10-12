// Validation boundary for imported/backend data. No labels or raw dataset parsing here.
export function validateResults(value){
 const fail=message=>{throw new Error(message);};
 const obj=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
 const str=(v,path)=>{if(typeof v!=='string'||!v.trim())fail(`${path} must be a non-empty string.`);};
 const arr=(v,path)=>{if(!Array.isArray(v)||v.some(x=>typeof x!=='string'))fail(`${path} must be an array of strings.`);};
 const timestamp=(v,path)=>{if(typeof v!=='string'||!/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(v)||!Number.isFinite(Date.parse(v)))fail(`${path} must be an ISO timestamp with a timezone.`);};
 if(!obj(value)||value.schema_version!==1)fail('schema_version must be 1. See BACKEND_CONTRACT.md.');
 if(!['demo','results'].includes(value.mode))fail('mode must be "demo" or "results".');
 if(!obj(value.dataset))fail('dataset must be an object.');str(value.dataset.name,'dataset.name');
 if(value.dataset.description!==undefined&&typeof value.dataset.description!=='string')fail('dataset.description must be a string.');
 if(!Array.isArray(value.incidents)||value.incidents.length>10000)fail('incidents must be an array with at most 10,000 groups.');
 const ids=new Set();for(const [i,c] of value.incidents.entries()){
  const p=`incidents[${i}]`;if(!obj(c))fail(`${p} must be an object.`);
  for(const key of ['id','title','entity','summary'])str(c[key],`${p}.${key}`);
  if(ids.has(c.id))fail(`${p}.id is duplicated.`);ids.add(c.id);
  if(!['high','medium','low'].includes(c.priority))fail(`${p}.priority must be high, medium, or low.`);
  if(typeof c.score!=='number'||!Number.isFinite(c.score)||c.score<0||c.score>100)fail(`${p}.score must be between 0 and 100.`);
  if(!Number.isSafeInteger(c.alert_count)||c.alert_count<1)fail(`${p}.alert_count must be a positive integer.`);
  timestamp(c.start,`${p}.start`);timestamp(c.end,`${p}.end`);if(Date.parse(c.end)<Date.parse(c.start))fail(`${p}.end cannot precede start.`);
  for(const key of ['sources','reasons','benign_explanations','missing_context','next_steps'])arr(c[key],`${p}.${key}`);
  if(!Array.isArray(c.evidence)||c.evidence.length>200)fail(`${p}.evidence must be an array with at most 200 records.`);
  const evidenceIds=new Set();for(const [j,e] of c.evidence.entries()){
   const q=`${p}.evidence[${j}]`;if(!obj(e))fail(`${q} must be an object.`);str(e.id,`${q}.id`);str(e.title,`${q}.title`);timestamp(e.timestamp,`${q}.timestamp`);
   if(evidenceIds.has(e.id))fail(`${q}.id is duplicated within the group.`);evidenceIds.add(e.id);
   if(!obj(e.raw))fail(`${q}.raw must be an object containing the original evidence.`);
   for(const key of ['description','source'])if(e[key]!==undefined&&typeof e[key]!=='string')fail(`${q}.${key} must be a string.`);
  }
 }
 return structuredClone(value);
}
