import test from 'node:test';
import assert from 'node:assert/strict';
import {checkUpload,uploadDataset,jobLabel} from '../dist/datasets.js';
import {createGateway} from '../netlify/functions/backend-gateway.mjs';
const maxBytes=4*1024*1024;
const file=new File(['{"timestamp":"2026-10-12T00:00:00Z"}\n'],'company.jsonl');
const env={BACKEND_URL:'https://backend.example.com',BACKEND_API_TOKEN:'test-token',ENABLE_DATASET_UPLOADS:'true',ENABLE_REVIEW_WRITES:'true'};
const upload=(overrides={},origin='https://sigsquared.netlify.app')=>{
 const body=new FormData();
 for(const [k,v] of Object.entries({file,dataset_name:'Company logs',syslog_year:'2026',allow_llm:'false',...overrides}))body.append(k,v);
 return new Request('https://sigsquared.netlify.app/api/v1/jobs',{method:'POST',headers:{Origin:origin},body});
};
test('checks file format, size, name and year before upload',()=>{
 checkUpload(file,maxBytes,'Company',2026);
 for(const [f,name,year] of [[null,'',2026],[new File(['x'],'bad.csv'),'',2026],[new File([],'empty.json'),'',2026],[{name:'big.zip',size:maxBytes+1},'',2026],[file,'x'.repeat(81),2026],[file,'',1800]])assert.throws(()=>checkUpload(f,maxBytes,name,year));
 assert.equal(jobLabel({id:'demo'}),'russellmitchell (default)');
 assert.equal(jobLabel({id:'a',parameters:{dataset_name:'Company'}}),'Company');
});
test('uploads multipart data with explicit per-dataset AI consent',async()=>{
 const result=await uploadDataset(file,{name:'Company',year:2026,allowLLM:false,maxBytes},async(url,opts)=>{
  assert.equal(url,'/api/v1/jobs');assert.equal(opts.method,'POST');
  assert.equal(opts.body.get('file').name,file.name);assert.equal(opts.body.get('allow_llm'),'false');
  assert.equal(opts.body.get('dataset_name'),'Company');return Response.json({id:'new-job'},{status:202});
 });
 assert.equal(result.id,'new-job');
 await assert.rejects(uploadDataset(file,{name:'',year:2026,allowLLM:false,maxBytes},async()=>Response.json({detail:'Queue full'},{status:429})),/Queue full/);
});
test('Netlify uploads require enablement, same origin and valid file, then preserve 202',async()=>{
 const calls=[];
 const gateway=createGateway(env,async(url,options)=>{calls.push({url,options});return Response.json({id:'uploaded-job'},{status:202});});
 assert.equal((await createGateway({...env,ENABLE_DATASET_UPLOADS:'false'})(upload())).status,403);
 assert.equal((await gateway(upload({},'https://other.example'))).status,403);
 assert.equal((await gateway(upload({file:new File(['x'],'bad.csv')}))).status,400);
 assert.equal((await gateway(upload({file:new File([new Uint8Array(maxBytes+65536)],'big.zip')}))).status,413);
 assert.equal((await gateway(upload())).status,202);
 assert.equal(calls.length,1);
 assert.equal(calls[0].options.headers.Authorization,'Bearer test-token');
 assert.equal(calls[0].options.body.get('allow_llm'),'false');
 assert.equal(calls[0].options.body.get('file').name,file.name);
 await gateway(upload({allow_llm:'true'}));assert.equal(calls[1].options.body.get('allow_llm'),'true');
});
test('dataset catalog and uploaded job reads and reviews follow deployment permissions',async()=>{
 const fetcher=async()=>Response.json({items:[{id:'demo'},{id:'uploaded-job'}]});
 const req=path=>new Request('https://sigsquared.netlify.app'+path);
 const enabled=createGateway(env,fetcher),disabled=createGateway({...env,ENABLE_DATASET_UPLOADS:'false'},fetcher);
 assert.equal((await enabled(req('/api/v1/jobs/uploaded-job'))).status,200);
 assert.equal((await disabled(req('/api/v1/jobs/uploaded-job'))).status,404);
 assert.equal((await (await enabled(req('/api/v1/jobs'))).json()).items.length,2);
 assert.equal((await (await disabled(req('/api/v1/jobs'))).json()).items.length,1);
 const patch=new Request('https://sigsquared.netlify.app/api/v1/jobs/uploaded-job/incidents/a/feedback',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:'resolved',disposition:'benign',note:'Checked'})});
 assert.equal((await enabled(patch)).status,200);
});
