import {validateReview} from '../../dist/review.js';
import {checkUpload} from '../../dist/datasets.js';
// Netlify replacement for serve.py. Credentials remain in function environment variables.
const json = (value, status=200) => new Response(JSON.stringify(value), {
  status, headers: {'Content-Type':'application/json', 'Cache-Control':'no-store'},
});

export function createGateway(env, fetcher=fetch) {
  return async request => {
    if(!['GET','PATCH','POST'].includes(request.method))return json({detail:'Method not allowed.'},405);
    const job=env.SIGNALDESK_JOB_ID||'demo';
    if(!/^[A-Za-z0-9-]{1,64}$/.test(job))return json({detail:'The deployment has an invalid dataset ID.'},503);
    // Preserve the bundled static demo until a live deployment is explicitly configured.
    if(!env.BACKEND_URL&&!env.BACKEND_API_TOKEN&&env.ENABLE_DATASET_UPLOADS!=='true'&&env.ENABLE_REVIEW_WRITES!=='true'&&job==='demo'&&new URL(request.url).pathname==='/app-config.json'){
      return request.method==='GET'?json({job_id:'demo',results_url:'/api-static/results.json',can_upload:false,can_review:false}):json({detail:'Method not allowed.'},405);
    }
    let upstream;
    try {
      upstream=new URL(env.BACKEND_URL);
      if(upstream.protocol!=='https:'||upstream.username||upstream.password||upstream.search||upstream.hash||upstream.origin===new URL(request.url).origin)throw Error();
    } catch {
      return json({detail:'Deployment setup is incomplete: configure the hosted Python BACKEND_URL in Netlify.'},503);
    }
    if(!env.BACKEND_API_TOKEN)return json({detail:'Deployment setup is incomplete: configure BACKEND_API_TOKEN in Netlify and the matching API_TOKEN on the backend.'},503);
    const url=new URL(request.url);
    const canReview=env.ENABLE_REVIEW_WRITES==='true';
    const canUpload=env.ENABLE_DATASET_UPLOADS==='true';
    const maxBytes=4*1024*1024;
    if(url.pathname==='/app-config.json')return request.method==='GET'?json({job_id:job,can_review:canReview,can_upload:canUpload,max_upload_bytes:maxBytes}):json({detail:'Method not allowed.'},405);
    // Upload-enabled deployments share all datasets on this backend with their users.
    const requestedJob=/^\/api\/v1\/jobs\/([A-Za-z0-9-]{1,64})(?:\/|$)/.exec(url.pathname)?.[1];
    const base=`/api/v1/jobs/${canUpload&&requestedJob?requestedJob:job}`;
    const suffix=url.pathname.startsWith(base)?url.pathname.slice(base.length):null;
    const validRoute=request.method==='GET'?/^($|\/incidents(?:\/[A-Za-z0-9_-]{1,128}(?:\/evidence)?)?)$/:/^\/incidents\/[A-Za-z0-9_-]{1,128}\/feedback$/;
    const collection=url.pathname==='/api/v1/jobs';
    if(request.method==='POST'&&!collection)return json({detail:'Method not allowed.'},405);
    if(!collection&&(suffix===null||!validRoute.test(suffix)))return json({detail:'Route not available.'},404);
    if(collection&&request.method==='PATCH')return json({detail:'Method not allowed.'},405);
    let body;
    if(request.method!=='GET'){
      const origin=request.headers.get('origin');
      if(origin&&origin!==url.origin)return json({detail:'Cross-origin writes are not allowed.'},403);
    }
    if(request.method==='POST'){
      if(!canUpload)return json({detail:'Dataset uploads are disabled for this deployment.'},403);
      try{
        const bytes=await request.arrayBuffer();
        if(bytes.byteLength>maxBytes+65536)return json({detail:'Netlify uploads are limited to 4 MB. Use a smaller file or the local app for larger datasets.'},413);
        const form=await new Request(request.url,{method:'POST',headers:{'Content-Type':request.headers.get('content-type')||''},body:bytes}).formData();
        const file=form.get('file'),name=String(form.get('dataset_name')||''),year=Number(form.get('syslog_year'));
        checkUpload(file,maxBytes,name,year);
        body=new FormData();body.append('file',file);body.append('dataset_name',name.trim()||file.name.slice(0,80));
        body.append('syslog_year',String(year));body.append('allow_llm',form.get('allow_llm')==='true'?'true':'false');
      }catch(error){return json({detail:`Invalid upload: ${error.message}`},400);}
    }
    if(request.method==='PATCH'){
      if(!canReview)return json({detail:'Review editing is disabled for this deployment.'},403);
      const origin=request.headers.get('origin');
      if(origin&&origin!==url.origin)return json({detail:'Cross-origin review updates are not allowed.'},403);
      try{
        if(!request.headers.get('content-type')?.startsWith('application/json'))throw Error('Expected a JSON review.');
        const raw=await request.text();
        if(raw.length>16384)throw Error('The review is too large.');
        body=JSON.stringify(validateReview(JSON.parse(raw)));
      }catch{return json({detail:'Invalid review. Choose a valid status and assessment, and limit notes to 2,000 characters.'},400);}
    }
    try {
      const target=upstream.href.replace(/\/$/,'')+url.pathname+url.search;
      const response=await fetcher(target, {
        method:request.method,body,
        headers:{Accept:'application/json',Authorization:`Bearer ${env.BACKEND_API_TOKEN}`,...(request.method==='PATCH'?{'Content-Type':'application/json'}:{})},
        signal:AbortSignal.timeout(50000), redirect:'error',
      });
      if(!response.ok) {
        const detail=response.status===401?'Backend authentication failed. Check the deployment token settings.':
          response.status===404?'The configured dataset or event was not found on the hosted backend.':
          response.status===413?'The file exceeds the hosted backend upload limit.':
          response.status===429?'The analysis queue is full. Please wait for a dataset to finish.':
          response.status===400||response.status===415||response.status===422?'The backend rejected this file or its analysis options. Check the format and log year.':
          'The investigation service could not complete this request.';
        return json({detail},response.status);
      }
      if(!response.headers.get('content-type')?.includes('application/json'))return json({detail:'The hosted backend returned an unexpected response.'},502);
      const result=await response.json();
      if(collection&&request.method==='GET'&&!canUpload)result.items=(result.items||[]).filter(item=>item.id===job);
      return json(result,response.status);
    } catch {
      return json({detail:'The hosted investigation service is unavailable or took too long. Please try again.'},502);
    }
  };
}

export default request => createGateway(process.env)(request);
export const config = {path:['/app-config.json','/api/v1/jobs','/api/v1/jobs/*']};
