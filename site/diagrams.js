const figures=[...document.querySelectorAll('.diagram')];
const root=document.documentElement, en=root.lang==='en';
const sources=figures.map(figure=>figure.querySelector('code').textContent);
const dark=()=>root.dataset.theme?root.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
let version=0, queue=Promise.resolve();
for(const figure of figures) {
  const button=figure.querySelector('button');
  button.addEventListener('click',()=>{
    const expanded=figure.classList.toggle('diagram-expanded');
    button.setAttribute('aria-pressed',String(expanded));
    button.textContent=expanded?(en?'Fit to page':'适应页面'):(en?'Enlarge diagram':'放大图表');
  });
}
function refresh() {
  const ticket=++version;
  queue=queue.then(async()=>{
    if(ticket!==version)return;
    try {
      const {default:mermaid}=await import('./mermaid/mermaid.esm.min.mjs');
      await document.fonts.ready;
      const night=dark();
      mermaid.initialize({startOnLoad:false,securityLevel:'strict',suppressErrorRendering:true,theme:'base',fontFamily:'system-ui, sans-serif',flowchart:{htmlLabels:false},themeVariables:{darkMode:night,background:night?'#202123':'#f6f2e9',primaryColor:night?'#28292c':'#eee9df',primaryTextColor:night?'#e6e2da':'#292a2c',primaryBorderColor:night?'#b3c5dd':'#344d67',lineColor:night?'#b3c5dd':'#344d67',secondaryColor:night?'#28292c':'#eee9df',tertiaryColor:night?'#202123':'#f6f2e9',edgeLabelBackground:night?'#202123':'#f6f2e9'}});
      for(const [i,figure] of figures.entries()) {
        // Stack left-to-right lifecycles to keep labels readable in a book column.
        const {svg}=await mermaid.render(`diagram-${ticket}-${i}`,sources[i].replace(/^flowchart LR\b/m,'flowchart TB'));
        if(ticket!==version)return;
        const view=figure.querySelector('.diagram-view');
        view.innerHTML=svg;
        const drawing=view.querySelector('svg');
        drawing.setAttribute('role','img');
        drawing.setAttribute('aria-label',en?'Course flowchart; text available in diagram source':'课程流程图；文字说明见图表源文');
        drawing.style.setProperty('--diagram-width',`${drawing.viewBox.baseVal.width}px`);
        figure.querySelector('details').open=false;
        figure.querySelector('button').hidden=false;
        figure.querySelector('.diagram-error')?.remove();
      }
    } catch(error) {
      console.error('Diagram rendering failed',error);
      for(const figure of figures) {
        if(!figure.querySelector('.diagram-error')) {
          const message=document.createElement('p');message.className='diagram-error';
          message.setAttribute('role','status');message.textContent=en?'Diagram unavailable. The full source is below.':'图表暂时无法显示，完整源文见下方。';
          figure.prepend(message);
        }
        figure.querySelector('details').open=true;
      }
    }
  });
}
new MutationObserver(refresh).observe(root,{attributes:true,attributeFilter:['data-theme']});
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',refresh);
refresh();
