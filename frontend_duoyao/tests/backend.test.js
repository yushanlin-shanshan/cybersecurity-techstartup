import test from 'node:test';
import assert from 'node:assert/strict';
import {BlueTeamBackend,adaptDetail} from '../dist/backend.js';
import {validateResults} from '../dist/schema.js';

const incident={id:'event-1',title:'Test event',priority_band:'medium',priority:58,score:65,anchor:['source','192.0.2.1'],hosts:['sensor-1'],start:'2022-01-21T00:00:00Z',end:'2022-01-21T00:01:00Z',count:20,sensors:['Wazuh'],review:{status:'investigating'}};
const response=value=>({ok:true,json:async()=>value});
test('reads every API page and preserves final priority rather than rule score',async()=>{
 const paths=[];
 const client=new BlueTeamBackend('http://localhost:8000','demo',async url=>{
  paths.push(url);
  if(url.endsWith('/demo'))return response({status:'ready',summary:{}});
  if(url.includes('offset=0'))return response({items:[incident],total:2});
  return response({items:[{...incident,id:'event-2'}],total:2});
 });
 const data=validateResults(await client.results());
 assert.equal(data.incidents.length,2);assert.equal(data.incidents[0].score,58);assert.equal(data.incidents[0].priority,'medium');assert.equal(data.incidents[0].entity,'192.0.2.1');assert.equal(paths.length,3);assert.match(paths[2],/offset=1/);
});
test('rejects incomplete pages and unfinished jobs instead of displaying partial success',async()=>{
 const client=new BlueTeamBackend('http://localhost:8000','demo',async url=>response(url.endsWith('/demo')?{status:'ready',summary:{}}:{items:[],total:2}));
 await assert.rejects(()=>client.results(),/incomplete/);
 const waiting=new BlueTeamBackend('http://localhost:8000','demo',async()=>response({status:'running',phase:'training_ml'}));
 await assert.rejects(()=>waiting.results(),/running/);
});
test('preserves original evidence and rejects unsupported citations',()=>{
 const client=new BlueTeamBackend('http://localhost:8000');
 const raw={full_log:'<script>untrusted evidence</script>'};
 const payload={incident,explanation:{answer:'Observed activity.',mode:'local',claims:[{text:'Reported activity.',evidence_ids:[7]}],caveats:['Not confirmed.'],next_steps:[]},representative_evidence:[{alert_id:7,normalized:{time:1642723200,source:'input.json',line:9,description:'Observed activity',sensor:'Wazuh'},original_record:raw}]};
 const detail=adaptDetail(payload,client);
 assert.deepEqual(detail.evidence[0].raw,raw);assert.equal(detail.evidence[0].timestamp,'2022-01-21T00:00:00.000Z');assert.match(detail.evidence[0].description,/line 9/);assert.equal(detail.backend.review_status,'investigating');
 payload.explanation.claims[0].evidence_ids=[999];assert.throws(()=>adaptDetail(payload,client),/absent/);
});
test('propagates authentication failure without replacing data',async()=>{
 const client=new BlueTeamBackend('http://localhost:8000','demo',async()=>({ok:false,status:401}));
 await assert.rejects(()=>client.results(),/authentication required/);
});
