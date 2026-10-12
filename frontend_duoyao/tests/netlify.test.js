import test from 'node:test';
import assert from 'node:assert/strict';
import {createGateway} from '../netlify/functions/backend-gateway.mjs';
const env={BACKEND_URL:'https://backend.example.com',BACKEND_API_TOKEN:'test-only-token'};
const request=(path,method='GET')=>new Request('https://sigsquared.netlify.app'+path,{method});

test('returns app configuration without exposing backend credentials',async()=>{
 const response=await createGateway(env)(request('/app-config.json'));
 assert.equal(response.status,200);
 assert.deepEqual(await response.json(),{job_id:'demo',can_review:false});
});
test('rejects missing deployment settings with actionable errors',async()=>{
 for(const settings of [{},{...env,BACKEND_URL:'http://localhost:8000'},{...env,BACKEND_API_TOKEN:''}]) {
  assert.equal((await createGateway(settings)(request('/app-config.json'))).status,503);
 }
});
test('forwards only the configured job with server-side authentication',async()=>{
 const calls=[];
 const gateway=createGateway(env,async(url,options)=>{
  calls.push({url,options});return Response.json({items:[],total:0});
 });
 const response=await gateway(request('/api/v1/jobs/demo/incidents?limit=200&offset=0'));
 assert.equal(response.status,200);
 assert.equal(calls[0].url,'https://backend.example.com/api/v1/jobs/demo/incidents?limit=200&offset=0');
 assert.equal(calls[0].options.headers.Authorization,'Bearer test-only-token');
 for(const path of ['/api/v1/jobs/other','/api/v1/jobs/demo2','/api/v1/jobs/demo/incidents/a/ask','/api/v1/jobs/demo/incidents/a/feedback'])assert.equal((await gateway(request(path))).status,404);
 assert.equal((await gateway(request('/api/v1/jobs/demo','POST'))).status,405);
 assert.equal(calls.length,1);
});
test('preserves actionable failures without reflecting backend secrets',async()=>{
 const gateway=createGateway(env,async()=>new Response('private provider details',{status:401}));
 const response=await gateway(request('/api/v1/jobs/demo'));
 assert.equal(response.status,401);assert.match((await response.json()).detail,/authentication/);
 const offline=createGateway(env,async()=>{throw Error('private host details');});
 assert.equal((await offline(request('/api/v1/jobs/demo'))).status,502);
 const html=createGateway(env,async()=>new Response('<html>login</html>'));
 assert.equal((await html(request('/api/v1/jobs/demo'))).status,502);
});


test('allows validated review writes only when enabled and same-origin',async()=>{
 const payload={status:'dismissed',disposition:'unreviewed',note:'Duplicate incident; no harmlessness conclusion.'};
 const patch=(value=payload,origin='https://sigsquared.netlify.app',path='/api/v1/jobs/demo/incidents/a/feedback')=>new Request('https://sigsquared.netlify.app'+path,{method:'PATCH',headers:{'Content-Type':'application/json',Origin:origin},body:JSON.stringify(value)});
 const calls=[];
 const gateway=createGateway({...env,ENABLE_REVIEW_WRITES:'true'},async(url,options)=>{calls.push({url,options});return Response.json({id:'a',review:JSON.parse(options.body)});});
 assert.equal((await createGateway(env)(patch())).status,403);
 assert.equal((await gateway(patch(payload,'https://other.example'))).status,403);
 assert.equal((await gateway(patch({...payload,status:'invalid'}))).status,400);
 assert.equal((await gateway(patch({...payload,note:'x'.repeat(2001)}))).status,400);
 assert.equal((await gateway(patch(payload,'https://sigsquared.netlify.app','/api/v1/jobs/other/incidents/a/feedback'))).status,404);
 assert.equal((await gateway(patch())).status,200);
 assert.equal(calls.length,1);
 assert.equal(calls[0].options.method,'PATCH');
 assert.deepEqual(JSON.parse(calls[0].options.body),payload);
 assert.equal(calls[0].options.headers.Authorization,'Bearer test-only-token');
});
