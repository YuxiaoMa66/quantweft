import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {isPrintLayout,stripPrintLines} from './print-layout.mjs';
assert(isPrintLayout(String.raw`\needspace{28\baselineskip}`));
assert(isPrintLayout(String.raw`\par\smallskip`));
assert(!isPrintLayout(String.raw`\frac{1}{2}`));
assert(!isPrintLayout(String.raw`\clearpage and teaching text`));
assert.equal(stripPrintLines(String.raw`\Needspace{7\baselineskip}`),'');
assert.equal(stripPrintLines('    '+String.raw`\clearpage`),'    '+String.raw`\clearpage`,'Preserve indented code');
const root=path.resolve(import.meta.dirname,'..','dist');
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)])}
const files=walk(root), pages=files.filter(f=>f.endsWith('.html'));
const errors=[], missingAnchors=[];
const decode=s=>s.replace(/&amp;/g,'&');
const headingIds=new Map(pages.map(p=>[p,new Set([...fs.readFileSync(p,'utf8').matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]))]));
let localLinks=0,math=0,boxes=0,diagrams=0;
for(const file of pages){
 const html=fs.readFileSync(file,'utf8');
 assert(!html.includes('class="math-error"'),file);
 for(const block of html.matchAll(/<pre[^>]*><code class="language-\{=latex\}">([\s\S]*?)<\/code><\/pre>/g))assert(!isPrintLayout(block[1]),'Print-only code block: '+file);
 assert(!/<p>\\(?:[Nn]eedspace|clearpage|newpage)\b/.test(html),'Print-only paragraph: '+file);
 assert(!/:::\s*\{\.body-/.test(html),'Unrendered teaching box: '+file);
 boxes+=(html.match(/class="teaching-box /g)||[]).length;
 diagrams+=(html.match(/class="diagram"/g)||[]).length;
 if(html.includes('class="diagram"'))assert(html.includes('/diagrams.js"'),'Missing diagram module: '+file);
 math+=(html.match(/class="katex"/g)||[]).length;
 for(const m of html.matchAll(/\b(?:href|src)="([^"]+)"/g)){
  const value=decode(m[1]);if(/^(?:https?:|mailto:|data:)/.test(value))continue;
  const url=new URL(value,'https://reader.test/'+path.relative(root,file));
  const dest=path.join(root,decodeURIComponent(url.pathname));
  if(!fs.existsSync(dest)){errors.push([path.relative(root,file),value]);continue}
  localLinks++;
  if(url.hash&&dest.endsWith('.html')){
   const id=decodeURIComponent(url.hash.slice(1));
   if(!headingIds.get(dest)?.has(id))missingAnchors.push([path.relative(root,file),value]);
  }
 }
}
assert.deepEqual(errors,[],'Broken local targets');
assert.deepEqual(missingAnchors,[],'Broken local anchors');
for(const lang of ['zh','en'])for(let n=1;n<=45;n++){
 const name=`ch${String(n).padStart(2,'0')}.html`,html=fs.readFileSync(path.join(root,'read',lang,name),'utf8');
 assert(html.includes(`href="../${lang==='zh'?'en':'zh'}/${name}"`),'Same-chapter language switch '+name);
 assert(html.includes('<article class="prose">'),'Missing article');
 assert(html.includes('>MIT / CC BY-NC-SA 4.0</a>'),'Reader must show the current content license');
 assert.equal((html.match(/<h1[ >]/g)||[]).length,1,'Chapter needs one main heading');
 const definitions=html.match(/<h2[^>]*>5[.、\s][\s\S]*?(?=<h2|$)/)?.[0];
 assert(definitions,'Missing formal definitions: '+lang+'/'+name);
 const prose=definitions.replace(/<pre[\s\S]*?<\/pre>|<code[\s\S]*?<\/code>/g,'');
 assert(!prose.includes('**'),'Unrendered definition emphasis: '+lang+'/'+name);
 assert(!/\n\d+\. <strong>/.test(prose),'Definition list escaped its list item: '+lang+'/'+name);
 if(n===43)assert(/<li>\s*(?:<p>)?<strong>(?:Stable unit|稳定个体)/.test(definitions),'Fourth causal assumption must be a list item: '+lang);

}
for(const lang of ['zh','en']) {
 const overview=fs.readFileSync(path.join(root,'read',lang,'index.html'),'utf8');
 assert.equal((overview.match(/<h1[ >]/g)||[]).length,1,'Overview needs one main heading');
 const index=JSON.parse(fs.readFileSync(path.join(root,'read',`search-${lang}.json`),'utf8'));
 const chapter=index.find(p=>p.url==='ch08.html');
 assert(chapter.text.includes('import numpy'),'Search must include code');
}
const optionsChapter=fs.readFileSync(path.join(root,'read/zh/ch10.html'),'utf8');
assert(optionsChapter.includes('<strong>期权（option）</strong>'),'CJK punctuation must allow adjacent bold text');
const costsChapter=fs.readFileSync(path.join(root,'read/zh/ch35.html'),'utf8');
assert(/<strong>定义 5\.1[^<]*<\/strong>：<br>/.test(costsChapter),'Standalone definition label must retain its line break');
const landing=fs.readFileSync(path.join(root,'index.html'),'utf8');
for(const name of ['button primary','nav-reader']) {
 assert(landing.includes(`class="${name}" href="read/zh/index.html" data-reader-zh="read/zh/index.html" data-reader-en="read/en/index.html"`),'Online reader entry: '+name);
}
assert(!landing.includes('data-online-reader'),'All online entry markers must resolve');
assert(!/blob\/main\/[^"]+\.pdf/.test(landing),'Landing PDF links must download directly');
assert(landing.includes('property="og:image"'),'Landing needs a social preview image');
assert(/href="styles\.[a-f0-9]{12}\.css"/.test(landing),'Landing styles must change URL when content changes');
assert(/src="site\.[a-f0-9]{12}\.js"/.test(landing),'Landing script must change URL when content changes');
const sourceRoot=path.dirname(root);
const sources=execFileSync('git',['ls-files'],{cwd:sourceRoot,encoding:'utf8'}).trim().split('\n').filter(p=>p.endsWith('.md')&&!p.startsWith('third_party/'));
let expectedBoxes=0,expectedDiagrams=0;
for(const source of sources){const text=fs.readFileSync(path.join(sourceRoot,source),'utf8');expectedBoxes+=(text.match(/^(?:[ \t]*- )?[ \t]*:{3,} \{\.body-/gm)||[]).length;expectedDiagrams+=(text.match(/^```mermaid\s*$/gm)||[]).length;}
assert.equal(boxes,expectedBoxes,'All teaching boxes must render, including boxes nested in lists');
assert.equal(diagrams,expectedDiagrams,'All Mermaid fences must render as diagrams');
assert(fs.existsSync(path.join(root,'_reader/mermaid/mermaid.esm.min.mjs')),'Missing self-hosted Mermaid');
console.log(`PASS: ${boxes} teaching boxes and ${diagrams} diagram containers match the source corpus.`);
assert(!files.some(file=>file.endsWith('.pdf')),'PDF downloads belong on GitHub, outside the site payload');
for(const lang of ['zh','en']){const html=fs.readFileSync(path.join(root,'read',lang,'ch01.html'),'utf8');assert(html.includes(`https://github.com/YuxiaoMa66/quantweft/raw/main/editions/${lang}/body/quantweft-textbook-${lang}.pdf`),'Textbook link must point to GitHub');}
assert(math>10000,'Expected full mathematical content');
console.log(`PASS: ${pages.length} pages, 45 bilingual chapter pairs (90 routes), ${localLinks} local links/assets, ${math} rendered equations, no missing anchors or math errors.`);
