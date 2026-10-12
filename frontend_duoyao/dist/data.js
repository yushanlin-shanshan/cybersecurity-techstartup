// Fictional UI fixtures. These are NOT findings derived from the AIT dataset.
const caseData = [
  ['INC-001','Repeated authentication failures followed by access','high',87,'mail-demo-01','2022-01-24T09:04:00Z',24,'Wazuh','Repeated failures and a later successful authentication warrant a closer look. These records alone do not establish account compromise.',
    ['Repeated authentication failures','Successful authentication reported','Additional session activity'],
    ['Several authentication attempts were rejected.','A later attempt for the same demo account succeeded.','Further activity was recorded after the successful login.'],
    ['Repeated failures followed by success in a short period.','The sequence is linked by the same demo account.'],
    ['The user may have forgotten a password.','A client may have retained an outdated password.'],
    ['Whether the account owner recognizes this session.','Whether the device and source are expected.'],
    ['Confirm the session with the account owner.','Inspect related activity before deciding on a response.']],
  ['INC-002','Unusual DNS queries from one reporting host','high',81,'dns-demo-01','2022-01-24T08:42:00Z',18,'AMiner','Unusually complex domain names appear repeatedly. Review the original queries and their source before drawing conclusions about data transfer.',
    ['Unusual domain pattern observed','Similar queries repeated','Frequency anomaly reported'],
    ['A detector flagged a complex domain string.','Additional requests shared the same pattern.','A separate frequency observation adds context.'],
    ['Repeated complex domain strings.','A related frequency signal from the same reporting host.'],
    ['An authorized application may encode identifiers in DNS queries.'],
    ['The application generating these queries.','Whether the destination is expected.'],
    ['Identify the originating process or device.','Compare destination domains with expected services.']],
  ['INC-003','Burst of web requests returning errors','medium',62,'web-demo-01','2022-01-24T08:18:00Z',42,'Wazuh','Many unsuccessful requests appear close together. This may be automated probing, a broken client, or an authorized test.',
    ['Web request errors begin','Repeated errors grouped','Activity slows'],
    ['The server returned several client-error responses.','Related responses continued in a short interval.','Fewer related responses were observed later.'],
    ['A concentrated burst of related errors.'],['A misconfigured application or authorized scanner could cause this pattern.'],['Request paths and an authorized testing schedule.'],['Review request paths and sources.','Check for scheduled testing.']],
  ['INC-004','TLS parser alerts need additional context','medium',45,'gateway-demo-01','2022-01-24T07:56:00Z',31,'Suricata','The detector reported difficulty interpreting TLS traffic. The alerts do not reveal the encrypted content or prove malicious communication.',
    ['TLS record warning','Handshake warning','Repeated parser warnings'],
    ['A protocol parser reported an unexpected record.','A related connection generated a handshake warning.','Similar warnings appeared again.'],
    ['Multiple related protocol warnings.'],['Unsupported traffic or packet capture issues may explain the warnings.'],['Capture quality and application context.'],['Check sensor health and packet loss.','Identify the destination application.']],
  ['INC-005','Routine update notifications grouped','low',18,'mail-demo-02','2022-01-24T07:30:00Z',12,'Wazuh','These example alerts describe antivirus database updates. They are grouped for review; no compromise is established by the supplied evidence.',
    ['Update process started','Update status reported','Follow-up update notification'],
    ['An antivirus update process started.','The service emitted an update status message.','A related update message followed.'],
    ['Repeated notifications from the same update service.'],['Scheduled antivirus maintenance.'],['Whether the update completed successfully.'],['Confirm expected update schedule and completion.']]
];
export const demoData = {schema_version:1,mode:'demo',dataset:{name:'russellmitchell · UI examples',description:'Fictional examples · not findings from AIT'},incidents:caseData.map((c,index)=>{
  const [id,title,priority,score,entity,start,count,source,summary,titles,descriptions,reasons,benign,missing,next]=c;
  const evidence=titles.map((eventTitle,i)=>({id:`DEMO-${index+1}-${i+1}`,timestamp:new Date(Date.parse(start)+i*60000).toISOString(),title:eventTitle,description:descriptions[i],source,raw:{synthetic:true,note:'Fictional UI example; not an original AIT record.',reporting_entity:entity,message:descriptions[i]}}));
  return {id,title,priority,score,entity,start,end:evidence.at(-1).timestamp,alert_count:count,sources:[source],summary,reasons,benign_explanations:benign,missing_context:missing,next_steps:next,evidence};
})};
