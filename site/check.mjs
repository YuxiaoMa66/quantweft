import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'..','dist');
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)])}
const files=walk(root), pages=files.filter(f=>f.endsWith('.html'));
const errors=[], missingAnchors=[];
const decode=s=>s.replace(/&amp;/g,'&');
const headingIds=new Map(pages.map(p=>[p,new Set([...fs.readFileSync(p,'utf8').matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]))]));
let localLinks=0,math=0;
for(const file of pages){
 const html=fs.readFileSync(file,'utf8');
 assert(!html.includes('class="math-error"'),file);
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
 assert.equal((html.match(/<h1[ >]/g)||[]).length,1,'Chapter needs one main heading');
}
for(const lang of ['zh','en']) {
 const overview=fs.readFileSync(path.join(root,'read',lang,'index.html'),'utf8');
 assert.equal((overview.match(/<h1[ >]/g)||[]).length,1,'Overview needs one main heading');
 const index=JSON.parse(fs.readFileSync(path.join(root,'read',`search-${lang}.json`),'utf8'));
 const chapter=index.find(p=>p.url==='ch08.html');
 assert(chapter.text.includes('import numpy'),'Search must include code');
}
assert(math>10000,'Expected full mathematical content');
console.log(`PASS: ${pages.length} pages, 45 bilingual chapter pairs (90 routes), ${localLinks} local links/assets, ${math} rendered equations, no missing anchors or math errors.`);
