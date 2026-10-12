export const phases={queued:'Waiting to start',validating:'Checking file format',ingesting:'Reading log records',correlating:'Grouping related alerts',training_ml:'Ranking events',complete:'Ready'};
export function checkUpload(file,maxBytes,name,year){
 if(!file||!file.size)throw Error('Choose a non-empty log file.');
 if(!/\.(json|jsonl|ndjson|zip)$/i.test(file.name))throw Error('Choose a .json, .jsonl, .ndjson, or .zip file.');
 if(file.size>maxBytes)throw Error(`This deployment accepts files up to ${Math.floor(maxBytes/1024/1024)} MB.`);
 if(name.length>80)throw Error('Dataset names must be at most 80 characters.');
 if(!Number.isInteger(year)||year<1970||year>2100)throw Error('Enter a valid log year between 1970 and 2100.');
}
export function jobLabel(job){return job.parameters?.dataset_name|| (job.id==='demo'?'russellmitchell (default)':job.parameters?.scenario||`Dataset ${job.id.slice(0,8)}`);}
export async function listJobs(fetcher=fetch){
 const response=await fetcher('/api/v1/jobs',{credentials:'same-origin',cache:'no-store'});
 if(!response.ok)throw Error('Could not load datasets. Please try again.');
 const data=await response.json();
 if(!Array.isArray(data.items))throw Error('Unexpected dataset list.');
 return data.items;
}
export async function uploadDataset(file,options,fetcher=fetch){
 checkUpload(file,options.maxBytes,options.name,options.year);
 const body=new FormData();body.append('file',file);body.append('dataset_name',options.name.trim()||file.name.slice(0,80));
 body.append('syslog_year',String(options.year));body.append('allow_llm',String(options.allowLLM));
 const response=await fetcher('/api/v1/jobs',{method:'POST',credentials:'same-origin',body});
 const result=await response.json().catch(()=>null);
 if(!response.ok)throw Error(typeof result?.detail==='string'?result.detail:`Upload failed (HTTP ${response.status}). Check the file and try again.`);
 if(!result?.id)throw Error('Upload response did not include a dataset ID.');
 return result;
}
