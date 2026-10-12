import {validateReview} from '../../dist/review.js';
// Netlify replacement for serve.py. Credentials remain in function environment variables.
const json = (value, status=200) => new Response(JSON.stringify(value), {
  status, headers: {'Content-Type':'application/json', 'Cache-Control':'no-store'},
});

export function createGateway(env, fetcher=fetch) {
  return async request => {
    if(!['GET','PATCH'].includes(request.method))return json({detail:'Method not allowed.'},405);
    const job=env.SIGNALDESK_JOB_ID||'demo';
    if(!/^[A-Za-z0-9-]{1,64}$/.test(job))return json({detail:'The deployment has an invalid dataset ID.'},503);
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
    if(url.pathname==='/app-config.json')return request.method==='GET'?json({job_id:job,can_review:canReview}):json({detail:'Method not allowed.'},405);
    // Only expose this dataset's reads and opt-in review updates. No uploads or Q&A.
    const base=`/api/v1/jobs/${job}`;
    const suffix=url.pathname.startsWith(base)?url.pathname.slice(base.length):null;
    const validRoute=request.method==='GET'?/^($|\/incidents(?:\/[A-Za-z0-9_-]{1,128}(?:\/evidence)?)?)$/:/^\/incidents\/[A-Za-z0-9_-]{1,128}\/feedback$/;
    if(suffix===null||!validRoute.test(suffix))return json({detail:'Route not available.'},404);
    let body;
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
        headers:{Accept:'application/json',Authorization:`Bearer ${env.BACKEND_API_TOKEN}`,...(body?{'Content-Type':'application/json'}:{})},
        signal:AbortSignal.timeout(50000), redirect:'error',
      });
      if(!response.ok) {
        const detail=response.status===401?'Backend authentication failed. Check the deployment token settings.':
          response.status===404?'The configured dataset or event was not found on the hosted backend.':
          'The investigation service could not complete this request.';
        return json({detail},response.status);
      }
      if(!response.headers.get('content-type')?.includes('application/json'))return json({detail:'The hosted backend returned an unexpected response.'},502);
      return json(await response.json());
    } catch {
      return json({detail:'The hosted investigation service is unavailable or took too long. Please try again.'},502);
    }
  };
}

export default request => createGateway(process.env)(request);
export const config = {path:['/app-config.json','/api/v1/jobs/*']};
