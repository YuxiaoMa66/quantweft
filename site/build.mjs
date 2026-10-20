import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import MarkdownIt from 'markdown-it';
import container from 'markdown-it-container';
import {isPrintLayout,stripPrintLines} from './print-layout.mjs';
import texmath from 'markdown-it-texmath';
import katex from 'katex';
import hljs from 'highlight.js';

const root = path.resolve(import.meta.dirname, '..');
const out = path.join(root, 'dist');
const git = 'https://github.com/YuxiaoMa66/quantweft/blob/main/';
const files = execFileSync('git', ['ls-files'], { cwd: root, encoding: 'utf8' }).trim().split('\n');
const sources = files.filter(p => p.endsWith('.md') && !p.startsWith('third_party/'));
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const escape = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const slug = s => s.toLowerCase().replace(/[^\p{L}\p{N}_\s-]/gu, '').trim().replace(/\s/g, '-');
const language = p => p.startsWith('editions/en/') || p.startsWith('course/en/') || p === 'README.en.md' ? 'en' : 'zh';
const route = p => {
  const m = p.match(/^course\/(zh|en)\/chapters\/(ch\d+)\/content.md$/);
  return m ? `read/${m[1]}/${m[2]}.html` : `read/files/${p.replace(/\.md$/, '.html')}`;
};
const pages = new Map(sources.map(p => [p, { source: p, lang: language(p), route: route(p) }]));
const chapters = lang => Array.from({length:45}, (_, i) => pages.get(`course/${lang}/chapters/ch${String(i+1).padStart(2,'0')}/content.md`));
for (const [p, page] of pages) {
  page.title = read(p).split('\n').find(s => /^# /.test(s))?.slice(2).trim() || path.basename(p, '.md');
  // Existing course prose is preserved, including its original punctuation and terminology.
  page.heading = page.title;
}
function counterpart(page) {
  const p = page.source;
  if (p.startsWith('course/')) return pages.get(p.replace(p.includes('/en/') ? '/en/' : '/zh/', p.includes('/en/') ? '/zh/' : '/en/'));
  if (p.startsWith('editions/en/')) return pages.get(p.replace('editions/en/', 'editions/zh/')) || pages.get(p.replace('editions/en/', ''));
  if (p.startsWith('editions/zh/')) return pages.get(p.replace('editions/zh/', 'editions/en/'));
  return pages.get('editions/en/' + p);
}
// Relative URLs work under a repository subpath and when served at the domain root.
const relative = (from, to) => path.posix.relative(path.posix.dirname(from), to) || path.posix.basename(to);
function href(page, target) { return relative(page.route, typeof target === 'string' ? target : target.route); }
fs.rmSync(out, {recursive:true, force:true});
fs.mkdirSync(out, {recursive:true});
fs.cpSync(path.join(root, 'docs'), out, {recursive:true, filter:p => !p.endsWith('.md')});
fs.mkdirSync(path.join(out, '_reader'), {recursive:true});
for (const f of ['reader.css', 'reader.js', 'diagrams.js']) fs.copyFileSync(path.join(root, 'site', f), path.join(out, '_reader', f));
fs.cpSync(path.join(root, 'node_modules/katex/dist'), path.join(out, '_reader/katex'), {recursive:true, filter:p => !p.endsWith('.js') && !p.endsWith('.map')});
fs.copyFileSync(path.join(root, 'node_modules/katex/LICENSE'), path.join(out, '_reader/katex/LICENSE'));
fs.copyFileSync(path.join(root, 'node_modules/highlight.js/styles/github.css'), path.join(out, '_reader/highlight.css'));
fs.copyFileSync(path.join(root, 'node_modules/highlight.js/LICENSE'), path.join(out, '_reader/highlight-LICENSE'));
fs.cpSync(path.join(root, 'node_modules/mermaid/dist'), path.join(out, '_reader/mermaid'), {recursive:true, filter:p => fs.statSync(p).isDirectory() || p.endsWith('.mjs')});
fs.copyFileSync(path.join(root, 'node_modules/mermaid/LICENSE'), path.join(out, '_reader/mermaid/LICENSE'));
const copied = new Set();
const mathErrors = [];
let current;
const md = new MarkdownIt({html:true, linkify:false, highlight(code, lang) {
  return lang && hljs.getLanguage(lang) ? hljs.highlight(code, {language:lang}).value : escape(code);
}}).use(texmath, {engine:{renderToString(tex, options) {
  try { return katex.renderToString(tex, {...options, throwOnError:true, strict:'ignore', trust:false}); }
  catch (error) { mathErrors.push({source:current.source, tex, error:error.message}); return `<code class="math-error">${escape(tex)}</code>`; }
}}, delimiters:['brackets','dollars'], katexOptions:{strict:'ignore', trust:false}});
// Pandoc-style teaching boxes share the Markdown parser, including lists, code and math.
const boxInfo = /^\{\.(body-(?:definition|conditions|example|pitfall)) title="([\s\S]*)"\}$/;
md.use(container, 'teaching-box', {
  validate: info => boxInfo.test(info.trim()),
  render(tokens, i) {
    if (tokens[i].nesting === -1) return '</aside>\n';
    const [, type, title] = tokens[i].info.trim().match(boxInfo);
    return `<aside class="teaching-box ${type}"><p class="teaching-title">${escape(title)}</p>\n`;
  }
});
const fenceRule = md.renderer.rules.fence;
md.renderer.rules.fence = (tokens, i, options, env, renderer) => {
  if (tokens[i].info.trim() === '{=latex}' && isPrintLayout(tokens[i].content)) return '';
  if (tokens[i].info.trim() !== 'mermaid') return fenceRule(tokens,i,options,env,renderer);
  const en = env.page.lang === 'en';
  return `<figure class="diagram"><button class="diagram-zoom" hidden aria-pressed="false">${en?'Enlarge diagram':'放大图表'}</button><div class="diagram-view" tabindex="0" role="region" aria-label="${en?'Diagram (scroll when enlarged)':'流程图（放大后可滚动）'}"></div><details class="diagram-source" open><summary>${en?'Diagram source':'图表源文'}</summary><pre><code>${escape(tokens[i].content)}</code></pre></details></figure>\n`;
};
function resolveLink(page, url, image=false) {
  if (/^(?:https?:|mailto:|#)/.test(url)) return url;
  const [raw, hash] = url.split('#');
  const target = path.posix.normalize(path.posix.join(path.posix.dirname(page.source), decodeURIComponent(raw)));
  if (pages.has(target)) return href(page, pages.get(target)) + (hash ? '#' + hash : '');
  if (!fs.existsSync(path.join(root, target))) return url;
  if (image || /\.(?:pdf|png|jpe?g|svg|webp)$/i.test(target)) {
    const dest = '_content/' + target;
    if (!copied.has(dest)) { fs.mkdirSync(path.dirname(path.join(out,dest)),{recursive:true}); fs.copyFileSync(path.join(root,target),path.join(out,dest)); copied.add(dest); }
    return href(page, dest) + (hash ? '#' + hash : '');
  }
  return git + target + (hash ? '#' + hash : '');
}
md.renderer.rules.link_open = (tokens, i, options, env, renderer) => {
  tokens[i].attrSet('href', resolveLink(env.page, tokens[i].attrGet('href')));
  return renderer.renderToken(tokens,i,options);
};
function sourceHtml(tokens,i,options,env) {
  return tokens[i].content.replace(/<[^>]*>/g,tag=> {
    if (/^<p align="(?:right|center|left)">$/i.test(tag)) return tag;
    const link=tag.match(/^<a href="([^"]+)">$/i);
    if(link && md.validateLink(link[1])) return `<a href="${escape(resolveLink(env.page,link[1]))}">`;
    if (/^<a id="[A-Za-z0-9_-]+"><\/a>$/.test(tag)) return tag;
    if (/^<a id="[A-Za-z0-9_-]+">$/.test(tag) || /^<\/a>$/.test(tag)) return tag;
    if (/^<\/?(?:br|details|summary|strong|p)\s*\/?\s*>$/i.test(tag)) return tag;
    return escape(tag);
  });
}
md.renderer.rules.html_block=sourceHtml;
md.renderer.rules.html_inline=sourceHtml;
const imageRule = md.renderer.rules.image;
md.renderer.rules.image = (tokens, i, options, env, renderer) => {
  tokens[i].attrSet('src',resolveLink(env.page,tokens[i].attrGet('src'),true));
  tokens[i].attrSet('loading','lazy'); tokens[i].attrSet('decoding','async');
  return imageRule(tokens,i,options,env,renderer);
};
function compile(page) {
  current = page;
  // Normalize display delimiters only outside code, so escaped currency dollars stay inside math.
  const chunks = read(page.source).split(/(^```[^\n]*\n[\s\S]*?^```[^\n]*$|^~~~[^\n]*\n[\s\S]*?^~~~[^\n]*$)/m);
  const source = chunks.map((s,i)=>i%2?s:stripPrintLines(s)
    .replace(/\\color\{qink\}/g,'')
    .replace(/\\begin\{center\}\s*\\begin\{tikzpicture\}[\s\S]*?\\end\{tikzpicture\}\s*\\end\{center\}/g, `![${page.lang==='en'?'Three observed points, candidate lines, and OLS residuals':'三个观测点、候选直线与 OLS 残差'}](${path.posix.relative(path.posix.dirname(page.source),'site/regression.svg')})`)
    .replace(/\$\$([\s\S]*?)\$\$/g,(_,tex)=>'\\[\n'+tex+'\n\\]')
    .replace(/\\\[([\s\S]*?)\\\]/g,(_,tex)=>'\n\n\\[\n'+tex+'\n\\]\n\n')).join('');
  const tokens = md.parse(source, {page});
  const headings = []; const used = new Map();
  for (let i=0;i<tokens.length;i++) if (tokens[i].type==='heading_open') {
    const text = tokens[i+1].children?.filter(t=>!['html_inline'].includes(t.type)).map(t=>t.content).join('') || tokens[i+1].content;
    const base=slug(text); const n=used.get(base)||0;used.set(base,n+1);const id=base+(n?'-'+n:'');tokens[i].attrSet('id',id);
    if (tokens[i].tag==='h2' || tokens[i].tag==='h3') headings.push({text,id,level:tokens[i].tag});
  }
  page.headings = headings;
  page.html = md.renderer.render(tokens,md.options,{page});
  page.search = tokens.filter(t=>!(t.type==='fence' && t.info.trim()==='{=latex}' && isPrintLayout(t.content))).filter(t=>['inline','fence','code_block'].includes(t.type)||t.type.startsWith('math_')).map(t=>t.children?.filter(x=>['text','code_inline'].includes(x.type)||x.type.startsWith('math_')).map(x=>x.content).join(' ')||t.content).join(' ');
}
for (const p of pages.values()) compile(p);
if (mathErrors.length) {
  fs.writeFileSync(path.join(out,'math-errors.json'),JSON.stringify(mathErrors,null,2));
  console.error(`Math parsing failed: ${mathErrors.length} expressions. See dist/math-errors.json.`);
  process.exit(1);
}
function nav(page) {
  const en=page.lang==='en';
  const groups = [[1,3,en?'Getting started':'开始学习'],[4,9,en?'Mathematics and statistics':'数学与统计'],[10,15,en?'Finance and pricing':'金融与定价'],[16,21,en?'Time series and portfolios':'时间序列与组合'],[22,28,en?'Alpha and research design':'Alpha 与研究设计'],[29,36,en?'Validation and execution':'验证与执行'],[37,45,en?'Machine learning and engineering':'机器学习与工程']];
  let html='';
  for (const [lo,hi,label] of groups) {
    const active=chapters(page.lang).slice(lo-1,hi).some(p=>p.source===page.source);
    html+=`<details${active?' open':''}><summary>${label}</summary><ol start="${lo}">`+chapters(page.lang).slice(lo-1,hi).map(p=>`<li><a ${p.source===page.source?'aria-current="page"':''} href="${href(page,p)}">${escape(p.title.replace(/^(?:第\s*\d+\s*章\s*[—-]?\s*|Chapter\s+\d+\s*[—-]?\s*)/,''))}</a></li>`).join('')+'</ol></details>';
  }
  const projectBase=en?'editions/en/':'';
  html+=`<details${page.source.includes('/project')||page.source.startsWith('projects/')||page.source.includes('capstone/')?' open':''}><summary>${en?'Projects and Capstone':'项目与 Capstone'}</summary><ul>`;
  for (let n=1;n<=6;n++) { const p=pages.get(`${projectBase}projects/project0${n}/README.md`);html+=`<li><a href="${href(page,p)}">${en?'Project':'项目'} ${n} · ${escape(p.title.replace(/^.*?[:：]\s*/,''))}</a></li>`; }
  const cap=pages.get(projectBase+'capstone/README.md');html+=`<li><a href="${href(page,cap)}">Capstone</a></li></ul></details>`;
  return html;
}
function document(page) {
  const en=page.lang==='en', t=(a,b)=>en?b:a;
  const book=`_content/editions/${page.lang}/body/quantweft-textbook-${page.lang}.pdf`;
  // Copy only the four reader books, never private build or QA material.
  resolveLink(page,path.posix.relative(path.posix.dirname(page.source),book.replace('_content/','')));
  const other=page.counterpartRoute ? {route:page.counterpartRoute} : counterpart(page);
  const list=chapters(page.lang), index=list.indexOf(page);const prev=list[index-1],next=list[index+1];
  let article=page.html;
  if(index>=0) article=article.replace(/<h1([^>]*)>([\s\S]*?)<\/h1>/,(_,attrs,title)=>`<header class="chapter-heading"><p class="chapter-number">${t('第 '+(index+1)+' 章','CHAPTER '+String(index+1).padStart(2,'0'))}<span>/ 45</span></p><h1${attrs}>${title.replace(/^(?:第\s*\d+\s*章\s*[—-]?\s*|Chapter\s+\d+\s*[—-]?\s*)/,'')}</h1></header>`);
  return `<!doctype html><html lang="${en?'en':'zh-CN'}"><head><meta charset="utf-8"><script>document.documentElement.classList.add('js')</script><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(page.title)} | QuantWeft</title><meta name="description" content="${escape(t('QuantWeft 量化经纬双语课程在线阅读。','Read the QuantWeft bilingual course online.'))}"><link rel="icon" href="data:,"><link rel="stylesheet" href="${href(page,'_reader/highlight.css')}"><link rel="stylesheet" href="${href(page,'_reader/reader.css')}"><link rel="stylesheet" href="${href(page,'_reader/katex/katex.min.css')}"><script>try{const t=localStorage.getItem('quant-course-theme');if(t)document.documentElement.dataset.theme=t}catch{}</script><script defer src="${href(page,'_reader/reader.js')}"></script>${article.includes('class="diagram"')?`<script type="module" src="${href(page,'_reader/diagrams.js')}"></script>`:''}</head><body data-search="${href(page,`read/search-${page.lang}.json`)}"><a class="skip" href="#content">${t('跳到正文','Skip to content')}</a><header class="reader-header"><a class="brand" href="${href(page,'index.html')}?lang=${page.lang}"><span class="brand-mark" aria-hidden="true">QW</span><span>QuantWeft<small>${t('量化经纬','Yuxiao Ma')}</small></span></a><div class="header-actions"><button class="menu-toggle" aria-expanded="false" aria-controls="chapters" hidden>${t('目录','Contents')}</button><button class="search-toggle" hidden>${t('搜索','Search')} <kbd>/</kbd></button>${other?`<a class="language" href="${href(page,other)}" lang="${en?'zh-CN':'en'}">${t('English','中文')}</a>`:''}<button class="theme-toggle" hidden aria-label="${t('切换明暗主题','Toggle color theme')}">${t('主题','Theme')}</button></div></header><div class="reader-layout"><aside id="chapters" class="chapter-nav" aria-label="${t('课程目录','Course contents')}"><a class="reader-home" href="${href(page,`read/${page.lang}/index.html`)}">${t('课程概览','Course overview')}</a>${nav(page)}<div class="nav-resources"><button class="theme-toggle mobile-theme" hidden>${t('切换明暗主题','Toggle theme')}</button><a href="${href(page,pages.get(`editions/${page.lang}/NOTEBOOK_GUIDE.md`))}">${t('运行 Notebook','Run a Notebook')}</a><a href="${href(page,book)}">${t('下载完整 PDF','Download textbook PDF')}</a></div></aside><main id="content" tabindex="-1"><div class="reading-context"><a href="${href(page,`read/${page.lang}/index.html`)}">${t('在线教材','Online textbook')}</a><span>${t('中文','English')}</span></div><details class="mobile-toc"><summary>${t('本章小节','On this page')}</summary><ul>${page.headings.filter(h=>h.level==='h2').map(h=>`<li><a href="#${escape(h.id)}">${escape(h.text)}</a></li>`).join('')}</ul></details><article class="prose">${article}</article><nav class="page-turn" aria-label="${t('章节导航','Chapter navigation')}">${prev?`<a href="${href(page,prev)}"><small>${t('上一章','Previous chapter')}</small>${escape(prev.title)}</a>`:'<span></span>'}${next?`<a href="${href(page,next)}"><small>${t('下一章','Next chapter')}</small>${escape(next.title)}</a>`:''}</nav><footer><a href="${href(page,pages.get('LICENSE.md'))}">MIT / CC BY-SA 4.0</a><a href="${git+page.source}">${t('查看 Markdown 源文','View Markdown source')}</a><span>Yuxiao Ma</span></footer></main><aside class="page-toc" aria-label="${t('本章目录','On this page')}"><details open><summary>${t('本章目录','On this page')}</summary><ul>${page.headings.map(h=>`<li class="${h.level}"><a href="#${escape(h.id)}">${escape(h.text)}</a></li>`).join('')}</ul></details></aside></div><dialog class="search-dialog" aria-labelledby="search-title"><form method="dialog"><h2 id="search-title">${t('搜索教材','Search the course')}</h2><button aria-label="${t('关闭搜索','Close search')}">${t('关闭','Close')}</button></form><label for="search-input">${t('输入关键词，检索当前语言全文','Search the full text in this language')}</label><input id="search-input" type="search" autocomplete="off"><p id="search-status" role="status">${t('输入关键词开始搜索。','Enter a search term.')}</p><ol id="search-results"></ol></dialog></body></html>`;
}
for (const page of pages.values()) {
  const dest=path.join(out,page.route);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,document(page));
}
for (const lang of ['zh','en']) {
  const intro=pages.get(`editions/${lang}/README.md`);
  const overview={...intro,route:`read/${lang}/index.html`,title:lang==='zh'?'课程概览':'Course overview'};
  const first=chapters(lang)[0];
  compile(overview);
  const overviewBody=overview.html.replace(/<h1([^>]*)>([\s\S]*?)<\/h1>/,'<h2$1>$2</h2>');
  overview.html=`<header class="overview-heading"><h1>${lang==='zh'?'量化研究，<br>从理解开始。':'Quantitative research,<br>from first principles.'}</h1><p class="lead">${lang==='zh'?'一本连接数学、金融与代码的双语教材。沿着 45 章的路径，读懂模型，动手验证，完成自己的研究。':'A bilingual textbook connecting mathematics, finance, and code. Follow 45 chapters from understanding models to building your own research.'}</p><a class="start-link" href="${href(overview,first)}">${lang==='zh'?'开始阅读第一章':'Begin with Chapter 1'} ↗</a></header><nav class="course-index" aria-label="${lang==='zh'?'课程组成':'Course collection'}"><a href="${href(overview,first)}"><strong>45</strong>${lang==='zh'?'循序渐进的章节':'Chapters to work through'}</a><a href="${href(overview,pages.get((lang==='en'?'editions/en/':'')+'projects/project01/README.md'))}"><strong>06</strong>${lang==='zh'?'动手实践的项目':'Applied projects'}</a><a href="${href(overview,pages.get((lang==='en'?'editions/en/':'')+'capstone/README.md'))}"><strong>01</strong>${lang==='zh'?'完整研究 Capstone':'Research Capstone'}</a></nav><p class="edition-note">${lang==='zh'?'网页版完整呈现仓库 Markdown；PDF 是另行排版的阅读版本，内容组织可能不同。':'The web edition renders the repository Markdown in full. The separately typeset PDFs may organize content differently.'}</p>`+overviewBody;
  overview.counterpartRoute=`read/${lang==='zh'?'en':'zh'}/index.html`;
  fs.writeFileSync(path.join(out,overview.route),document(overview));
  const search=[...pages.values()].filter(p=>p.lang===lang).map(p=>({title:p.title,url:relative(`read/${lang}/index.html`,p.route),text:p.search}));
  fs.writeFileSync(path.join(out,`read/search-${lang}.json`),JSON.stringify(search));
}
let landing=fs.readFileSync(path.join(out,'index.html'),'utf8');
landing=landing.replace(/href="[^"]*" data-online-reader/g,'href="read/zh/index.html" data-reader-zh="read/zh/index.html" data-reader-en="read/en/index.html"');
landing=landing.replace(/href="https:\/\/github.com\/YuxiaoMa66\/quantweft\/blob\/main\/([^"#]+)([^"]*)"/g,(full,target,fragment)=>{
  if(pages.has(target))return `href="${pages.get(target).route}${fragment}"`;
  if(target.endsWith('.pdf')){
    const dummy={route:'index.html',source:'README.md'};
    return `href="${resolveLink(dummy,target)}${fragment}"`;
  }
  return full;
});
landing=landing.replace(/data-doc-(zh|en)="([^"]+)"/g,(full,lang,target)=>pages.has(target)?`data-reader-${lang}="${pages.get(target).route}"`:full);
fs.writeFileSync(path.join(out,'index.html'),landing);
fs.writeFileSync(path.join(out,'read/index.html'),'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=zh/index.html"><a href="zh/index.html">中文</a> <a href="en/index.html">English</a>');
console.log(`Built ${pages.size+2} static reader pages; 90 chapter texts; ${copied.size} book/image assets. No course source was modified.`);
