(() => {
  const root=document.documentElement;
  root.classList.add('js');
  const en=root.lang==='en', t=(zh,enText)=>en?enText:zh;
  const themes=[...document.querySelectorAll('.theme-toggle')];
  const dark=()=>root.dataset.theme?root.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
  function updateTheme(){themes.forEach(button=>{button.textContent=dark()?t('白天模式','Day mode'):t('夜晚模式','Night mode');button.setAttribute('aria-label',dark()?t('切换到白天模式','Switch to day mode'):t('切换到夜晚模式','Switch to night mode'));button.setAttribute('aria-pressed',String(dark()));});}
  themes.forEach(theme=>{theme.hidden=false;theme.addEventListener('click',()=>{root.dataset.theme=dark()?'light':'dark';try{localStorage.setItem('quant-course-theme',root.dataset.theme)}catch{}updateTheme();});});
  updateTheme();matchMedia('(prefers-color-scheme: dark)').addEventListener('change',updateTheme);
  const toggle=document.querySelector('.menu-toggle'), nav=document.querySelector('#chapters');
  toggle.hidden=false;
  toggle.addEventListener('click',()=>{const open=nav.classList.toggle('open');toggle.setAttribute('aria-expanded',String(open));});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){nav.classList.remove('open');toggle.setAttribute('aria-expanded','false');}});
  for(const pre of document.querySelectorAll('pre')) {
    pre.tabIndex=0;
    const button=document.createElement('button');button.className='code-copy';button.textContent=t('复制代码','Copy code');
    button.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(pre.textContent);button.textContent=t('已复制','Copied')}catch{button.textContent=t('请选中代码手动复制','Select code to copy')}setTimeout(()=>button.textContent=t('复制代码','Copy code'),2500)});pre.after(button);
  }
  // Search index is fetched once on demand; page content remains readable without JavaScript.
  const dialog=document.querySelector('.search-dialog'),input=document.querySelector('#search-input'),results=document.querySelector('#search-results'),status=document.querySelector('#search-status'),search=document.querySelector('.search-toggle');
  let index,loading,sequence=0;
  const base=new URL(document.body.dataset.search,location.href);
  async function load(){if(index)return index;if(!loading){loading=fetch(base).then(r=>{if(!r.ok)throw Error('Search index unavailable');return r.json()}).then(data=>index=data).catch(error=>{loading=null;throw error})}return loading;}
  function open(){dialog.showModal();input.focus();}
  search.hidden=false;search.addEventListener('click',open);
  document.addEventListener('keydown',e=>{if(e.key==='/'&&!dialog.open&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)){e.preventDefault();open()}});
  dialog.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();dialog.close();}});
  dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close()}});
  let timer;
  input.addEventListener('input',()=>{clearTimeout(timer);const ticket=++sequence;timer=setTimeout(async()=>{
    const query=input.value.trim().toLocaleLowerCase();results.replaceChildren();if(!query){status.textContent=t('输入关键词开始搜索。','Enter a search term.');return}
    status.textContent=t('正在检索教材…','Searching the course…');
    try{const data=await load();if(ticket!==sequence)return;const words=query.split(/\s+/);const matches=data.filter(p=>words.every(w=>(p.title+' '+p.text).toLocaleLowerCase().includes(w))).sort((a,b)=>Number(b.title.toLocaleLowerCase().includes(query))-Number(a.title.toLocaleLowerCase().includes(query)));
      status.textContent=matches.length?t(`找到 ${matches.length} 页，显示前 20 项。`,`${matches.length} pages found. Showing the first 20.`):t('没有找到匹配内容，试试更短的关键词。','No matches. Try a shorter search term.');
      for(const p of matches.slice(0,20)){const li=document.createElement('li'),a=document.createElement('a'),text=document.createElement('p');a.textContent=p.title;a.href=new URL(p.url,new URL(en?'en/index.html':'zh/index.html',base)).href;const pos=Math.max(0,p.text.toLocaleLowerCase().indexOf(words[0])-50);text.textContent=(pos?'…':'')+p.text.slice(pos,pos+180)+'…';li.append(a,text);results.append(li)}
    }catch{if(ticket===sequence)status.textContent=t('搜索暂时不可用，请检查连接后重新输入，或使用章节目录。','Search is unavailable. Check your connection and retry, or use the chapter contents.');}
  },180)});
  const tocLinks=[...document.querySelectorAll('.page-toc a')];
  const observer=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting){for(const a of tocLinks)a.removeAttribute('aria-current');const a=tocLinks.find(a=>decodeURIComponent(a.hash.slice(1))===entry.target.id);if(a)a.setAttribute('aria-current','true')}},{rootMargin:'-10% 0px -70% 0px'});
  document.querySelectorAll('.prose h2,.prose h3').forEach(h=>observer.observe(h));
})();
