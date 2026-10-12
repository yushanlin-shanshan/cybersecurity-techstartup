// Render the small Markdown subset used by incident summaries. Never accept HTML.
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function inline(text) {
  return text.split(/(`[^`\n]+`|\*\*[^*\n]+\*\*)/g).map(part => {
    if (part.startsWith('**') && part.endsWith('**')) return `<strong>${escape(part.slice(2,-2))}</strong>`;
    if (part.startsWith('`') && part.endsWith('`')) return `<code>${escape(part.slice(1,-1))}</code>`;
    return escape(part);
  }).join('');
}
const marker = line => /^(\s*)([-+*]|\d+[.)])\s+(.*)$/.exec(line);
const heading = line => /^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$/.exec(line);

function blocks(lines) {
  const html=[];
  let i=0;
  while(i<lines.length) {
    if(!lines[i].trim()){i++;continue;}
    const title=heading(lines[i]);
    if(title){html.push(`<h3>${inline(title[1])}</h3>`);i++;continue;}
    const first=marker(lines[i]);
    if(first){
      const indent=first[1].length, ordered=/^\d/.test(first[2]), tag=ordered?'ol':'ul';
      const start=ordered?Number.parseInt(first[2],10):1;
      const items=[];
      while(i<lines.length){
        const current=marker(lines[i]);
        if(!current||current[1].length!==indent||/^\d/.test(current[2])!==ordered)break;
        const item=[current[3]];i++;
        while(i<lines.length){
          if(!lines[i].trim()){i++;continue;}
          const next=marker(lines[i]);
          if(next&&next[1].length<=indent)break;
          const leading=/^\s*/.exec(lines[i])[0].length;
          if(leading<=indent)break;
          item.push(lines[i].slice(indent+2));i++;
        }
        items.push(`<li>${blocks(item).join('')}</li>`);
      }
      html.push(`<${tag}${ordered&&start!==1?` start="${start}"`:''}>${items.join('')}</${tag}>`);
      continue;
    }
    const paragraph=[];
    while(i<lines.length&&lines[i].trim()&&!heading(lines[i])&&!marker(lines[i]))paragraph.push(lines[i++].trim());
    html.push(`<p>${inline(paragraph.join(' '))}</p>`);
  }
  return html;
}

export function formatSummary(text) {
  const content=blocks(String(text??'').replace(/\r\n?/g,'\n').split('\n'));
  if(String(text??'').length>1200&&content.length>1&&content[0].startsWith('<p>')) {
    return `${content[0]}<details class="summary-more"><summary><span class="summary-expand">Read detailed explanation</span><span class="summary-collapse">Hide detailed explanation</span></summary><div class="summary-breakdown">${content.slice(1).join('')}</div></details>`;
  }
  return content.join('');
}
