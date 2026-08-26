(()=>{
  const KEY='tradenex_visual_settings_v3';
  const EXTRA=[
    ['quantum-web','Quantum Web','Leuchtende Netzwerkverbindungen mit Tiefenstaffelung'],
    ['energy-tunnel','Energy Tunnel','Perspektivischer Energie-Tunnel mit Warp-Effekt'],
    ['singularity','Singularity Core','Schwarzes Zentrum mit umlaufender Energie'],
    ['galaxy-drift','Galaxy Drift','Tiefer Sternenstrom mit Nebel und Parallax'],
    ['cyber-city','Cyber City','Futuristische Skyline aus Lichtlinien'],
    ['ai-neural','AI Neural','Neuronales Netz mit wandernden Datenimpulsen'],
    ['data-core','Data Core','Rotierender holografischer Datenkern'],
    ['holo-rings','Holo Rings','Mehrere räumliche Hologramm-Ringe'],
    ['electric-vortex','Electric Vortex','Elektrischer Wirbel mit Energieblitzen'],
    ['deep-space','Deep Space','Kosmischer Raum mit farbigem Partikelnebel'],
    ['digital-ocean','Digital Ocean','Wellenfeld aus leuchtenden Datenpunkten'],
    ['particle-storm','Particle Storm','Dynamischer Partikelsturm mit Windrichtung'],
    ['hex-flux','Hex Flux','Tiefes Hexagon-Mesh mit Energiefluss'],
    ['reactor','Reactor Core','Kinetischer Reaktorkern mit Puls und Strahlen']
  ];
  const $=s=>document.querySelector(s);
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  let state={}; let canvas,ctx,W=0,H=0,dpr=1,last=0,raf=0;
  let particles=[],stars=[],rain=[],nodes=[],rings=[];

  function load(){try{state=JSON.parse(localStorage.getItem(KEY)||'{}')}catch{state={}}}
  function colors(){const cs=getComputedStyle(document.documentElement);return [cs.getPropertyValue('--theme-accent').trim()||'#55e7ff',cs.getPropertyValue('--theme-accent-2').trim()||'#8c5cff',cs.getPropertyValue('--theme-accent-3').trim()||'#ff39d1',cs.getPropertyValue('--theme-metal').trim()||'#c8d0df'];}
  function rgb(hex){const h=hex.replace('#','');if(h.length!==6)return [120,180,255];return [parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)]}
  function rgba(hex,a){const [r,g,b]=rgb(hex);return `rgba(${r},${g},${b},${a})`}
  function hexmix(a,b,t){const A=rgb(a),B=rgb(b);return '#'+[0,1,2].map(i=>Math.round(A[i]+(B[i]-A[i])*t).toString(16).padStart(2,'0')).join('')}
  function resize(){
    if(!canvas)return; dpr=Math.min(window.devicePixelRatio||1,1.5); W=innerWidth;H=innerHeight; canvas.width=Math.floor(W*dpr);canvas.height=Math.floor(H*dpr);canvas.style.width='100%';canvas.style.height='100%';ctx.setTransform(dpr,0,0,dpr,0,0);seed();
  }
  function seed(){
    const count=clamp(Math.floor(W*H/17000),80,250);
    particles=Array.from({length:count},()=>({x:Math.random()*W,y:Math.random()*H,z:.2+Math.random()*.8,vx:(Math.random()-.5)*.15,vy:(Math.random()-.5)*.15,s:.6+Math.random()*2.2,a:.2+Math.random()*.55}));
    stars=Array.from({length:Math.max(70,Math.floor(W*H/12000))},()=>({x:Math.random()*W,y:Math.random()*H,z:.15+Math.random()*.85,r:.4+Math.random()*1.7,v:.05+Math.random()*.32}));
    rain=Array.from({length:Math.max(36,Math.floor(W/24))},()=>({x:Math.random()*W,y:Math.random()*H,l:12+Math.random()*40,v:2+Math.random()*8,a:.12+Math.random()*.45}));
    nodes=Array.from({length:Math.max(28,Math.floor(W*H/25000))},()=>({x:Math.random()*W,y:Math.random()*H,vx:(Math.random()-.5)*.35,vy:(Math.random()-.5)*.35,p:Math.random()*Math.PI*2}));
    rings=Array.from({length:7},(_,i)=>({r:40+i*54,a:Math.random()*Math.PI*2,v:(.0015+i*.00035)*(i%2?-1:1),w:1+i*.4}));
  }
  function clear(){ctx.fillStyle='rgba(1,3,9,.28)';ctx.fillRect(0,0,W,H)}
  function glowDot(x,y,r,c,a){const g=ctx.createRadialGradient(x,y,0,x,y,r*5);g.addColorStop(0,rgba(c,a));g.addColorStop(.18,rgba(c,a*.7));g.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=g;ctx.beginPath();ctx.arc(x,y,r*5,0,Math.PI*2);ctx.fill();ctx.fillStyle=rgba(c,a);ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill()}
  function drawParticles(c1,c2,c3,t){for(const p of particles){p.x+=p.vx*(1+p.z*2);p.y+=p.vy*(1+p.z*2);if(p.x<0)p.x=W;if(p.x>W)p.x=0;if(p.y<0)p.y=H;if(p.y>H)p.y=0;const c=p.z>.66?c1:(p.z>.42?c2:c3);glowDot(p.x,p.y,p.s*p.z,c,.15+p.a*.25)}}
  function drawStars(c1,c4,t,warp=false){for(const s of stars){s.y+=s.v*(warp?7:1);s.x+=(warp?(s.x-W/2)*.0007:0);if(s.y>H+4)s.y=-4;ctx.fillStyle=rgba(s.z>.6?c4:c1,.2+s.z*.55);ctx.beginPath();ctx.arc(s.x,s.y,s.r*s.z,0,Math.PI*2);ctx.fill();if(warp&&s.z>.72){ctx.strokeStyle=rgba(c1,.16);ctx.beginPath();ctx.moveTo(s.x,s.y);ctx.lineTo(s.x-(s.x-W/2)*.025,s.y-18*s.z);ctx.stroke()}}}
  function drawRain(c1,c2,t){ctx.font='10px monospace';for(const r of rain){r.y+=r.v*2;if(r.y>H+r.l*8){r.y=-r.l*8;r.x=Math.random()*W}for(let i=0;i<r.l;i++){const a=r.a*(1-i/r.l);ctx.fillStyle=rgba(i%7===0?c2:c1,a);ctx.fillText(String.fromCharCode(0x30a0+Math.floor(Math.random()*96)),r.x,r.y-i*9)}}}
  function drawGrid(c1,c2,t){const horizon=H*.58;const step=44;ctx.lineWidth=1;ctx.strokeStyle=rgba(c1,.17);for(let x=-W;x<W*2;x+=step){ctx.beginPath();ctx.moveTo(W/2+(x-W/2)*.05,horizon);ctx.lineTo(x,H);ctx.stroke()}for(let i=1;i<18;i++){const y=horizon+Math.pow(i/18,1.65)*(H-horizon);ctx.strokeStyle=rgba(c2,.08+i*.004);ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke()}ctx.fillStyle='rgba(0,0,0,.15)';ctx.fillRect(0,horizon,W,H-horizon)}
  function drawAurora(c1,c2,c3,t){for(let i=0;i<5;i++){const x=W*(.15+i*.18)+Math.sin(t*.00035+i)*W*.12;const y=H*(.18+i*.12)+Math.cos(t*.00028+i*1.4)*H*.11;const g=ctx.createRadialGradient(x,y,0,x,y,Math.max(W,H)*.32);g.addColorStop(0,rgba(i%2?c2:c1,.11));g.addColorStop(.55,rgba(i%2?c3:c2,.045));g.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=g;ctx.fillRect(0,0,W,H)}}
  function drawVortex(c1,c2,t){const cx=W*.5,cy=H*.52;ctx.save();ctx.translate(cx,cy);for(let i=0;i<900;i++){const a=i*.21+t*.00055*(i%3?1:-1);const r=(i/900)*Math.min(W,H)*.47;const x=Math.cos(a)*r*(.4+.6*i/900),y=Math.sin(a)*r*.5;const c=i%2?c1:c2;ctx.fillStyle=rgba(c,.08);ctx.fillRect(x,y,1.6,1.6)}const g=ctx.createRadialGradient(0,0,0,0,0,Math.min(W,H)*.25);g.addColorStop(0,'rgba(0,0,0,.92)');g.addColorStop(.75,rgba(c1,.08));g.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=g;ctx.beginPath();ctx.arc(0,0,Math.min(W,H)*.28,0,Math.PI*2);ctx.fill();ctx.restore()}
  function drawRadar(c1,c2,t){const cx=W*.5,cy=H*.5,r=Math.min(W,H)*.42;ctx.save();ctx.translate(cx,cy);for(let i=1;i<=4;i++){ctx.strokeStyle=rgba(c1,.06);ctx.beginPath();ctx.arc(0,0,r*i/4,0,Math.PI*2);ctx.stroke()}for(let a=0;a<Math.PI*2;a+=Math.PI/4){ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(Math.cos(a)*r,Math.sin(a)*r);ctx.stroke()}const a=t*.0008;const g=ctx.createConicGradient(a,0,0);g.addColorStop(0,rgba(c1,0));g.addColorStop(.92,rgba(c1,0));g.addColorStop(.98,rgba(c1,.16));g.addColorStop(1,rgba(c1,0));ctx.fillStyle=g;ctx.beginPath();ctx.arc(0,0,r,0,Math.PI*2);ctx.fill();for(let i=0;i<9;i++){const ang=a-(i*.42);const rr=r*(.2+((i*37)%80)/100);glowDot(Math.cos(ang)*rr,Math.sin(ang)*rr,2.2,c2,.35)}ctx.restore()}
  function drawCircuit(c1,c2,t){const cols=18,rows=11;const cw=W/cols,ch=H/rows;ctx.lineWidth=1;for(let y=0;y<rows;y++){for(let x=0;x<cols;x++){const ox=x*cw+cw*.12,oy=y*ch+ch*.5;ctx.strokeStyle=rgba((x+y)%2?c1:c2,.12);ctx.beginPath();ctx.moveTo(ox,oy);ctx.lineTo(ox+cw*.55,oy);ctx.lineTo(ox+cw*.55,oy+ch*.32);ctx.lineTo(ox+cw*.85,oy+ch*.32);ctx.stroke();if(((x*13+y*7)%17)<2)glowDot(ox+cw*.85,oy+ch*.32,1.4,c1,.5)}}}
  function drawWaves(c1,c2,t){for(let k=0;k<7;k++){ctx.beginPath();for(let x=0;x<=W;x+=10){const y=H*.58+k*18+Math.sin(x*.01+k+t*.0012)*(12+k*1.8)+Math.sin(x*.003-t*.0007)*(18+k*2);if(x===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)}ctx.strokeStyle=rgba(k%2?c1:c2,.08+k*.008);ctx.stroke()}}
  function drawHex(c1,c2,t){const s=62;ctx.strokeStyle=rgba(c1,.10);for(let y=-s;y<H+s;y+=s*.86){for(let x=-s;x<W+s;x+=s*1.5){const xx=x+((Math.floor(y/(s*.86))%2)*s*.75);ctx.beginPath();for(let i=0;i<6;i++){const a=Math.PI/3*i;const px=xx+Math.cos(a)*s*.42,py=y+Math.sin(a)*s*.42;i?ctx.lineTo(px,py):ctx.moveTo(px,py)}ctx.closePath();ctx.stroke()}}for(let i=0;i<12;i++){const x=(i*137+t*.05)%W,y=(i*83+t*.03)%H;glowDot(x,y,2,c2,.4)}}
  function drawParticlesNetwork(c1,c2,c3,t){for(const n of nodes){n.x+=n.vx;n.y+=n.vy;n.p+=.02;if(n.x<0||n.x>W)n.vx*=-1;if(n.y<0||n.y>H)n.vy*=-1}for(let i=0;i<nodes.length;i++){for(let j=i+1;j<nodes.length;j++){const a=nodes[i],b=nodes[j];const dx=a.x-b.x,dy=a.y-b.y,d=Math.hypot(dx,dy);if(d<170){ctx.strokeStyle=rgba(d<90?c1:c2,(1-d/170)*.12);ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke()}}}nodes.forEach((n,i)=>{const c=i%3===0?c3:(i%2?c1:c2);glowDot(n.x,n.y,1.6,c,.35)})}
  function drawCore(c1,c2,c3,t){const cx=W*.5,cy=H*.5;ctx.save();ctx.translate(cx,cy);for(let i=0;i<9;i++){const r=42+i*28+Math.sin(t*.001+i)*4;ctx.strokeStyle=rgba(i%2?c1:c2,.09);ctx.lineWidth=1+i*.12;ctx.beginPath();ctx.arc(0,0,r, t*.0004*(i%2?-1:1),t*.0004*(i%2?-1:1)+Math.PI*(1.15+i*.08));ctx.stroke()}for(let i=0;i<14;i++){const a=t*.001*(i%2?-1:1)+i*.45,r=70+i*7;glowDot(Math.cos(a)*r,Math.sin(a)*r,c3,.34?2.1:2.1,c3,.35)}const g=ctx.createRadialGradient(0,0,4,0,0,90);g.addColorStop(0,rgba(c3,.4));g.addColorStop(.3,rgba(c1,.14));g.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=g;ctx.beginPath();ctx.arc(0,0,120,0,Math.PI*2);ctx.fill();ctx.restore()}
  function drawCity(c1,c2,t){const horizon=H*.72;ctx.fillStyle='rgba(0,0,0,.25)';ctx.fillRect(0,horizon,W,H-horizon);const count=22;for(let i=0;i<count;i++){const x=i*(W/count);const h=(.12+((i*17)%100)/100*.46)*H;const w=W/count*.65;ctx.fillStyle=rgba(i%2?c1:c2,.07);ctx.fillRect(x,horizon-h,w,h);for(let yy=horizon-h+10;yy<horizon-8;yy+=13){if(((i*31+yy)%47)<20){ctx.fillStyle=rgba(c1,.16);ctx.fillRect(x+4,yy,Math.max(2,w*.08),2)}}}for(let i=0;i<8;i++){const y=horizon-i*22+Math.sin(t*.0008+i)*5;ctx.strokeStyle=rgba(c1,.08);ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke()}}
  function render(t){
    if(!ctx)return; load(); const [c1,c2,c3,c4]=colors(); const eff=state.background||document.body.dataset.ambience||'grid'; const strength=clamp(Number(state.effectStrength??65)/100,0,1); const motion=state.motion!==false;
    ctx.clearRect(0,0,W,H); ctx.fillStyle=rgba(state.preset==='gold'?'#080501':'#01030a',.88);ctx.fillRect(0,0,W,H); ctx.globalAlpha=strength; ctx.globalCompositeOperation='lighter';
    if(eff==='grid'||eff==='synthwave')drawGrid(c1,c2,t);
    if(eff==='matrix'||eff==='rain')drawRain(c1,c2,t);
    if(eff==='particles'||eff==='digital-ocean'||eff==='particle-storm')drawParticles(c1,c2,c3,t);
    if(eff==='aurora'||eff==='nebula'||eff==='deep-space')drawAurora(c1,c2,c3,t);
    if(eff==='stars'||eff==='galaxy-drift'||eff==='deep-space')drawStars(c1,c4,t,eff==='galaxy-drift');
    if(eff==='vortex'||eff==='electric-vortex'||eff==='singularity')drawVortex(c1,c2,t);
    if(eff==='radar')drawRadar(c1,c2,t);
    if(eff==='circuit')drawCircuit(c1,c2,t);
    if(eff==='ocean'||eff==='digital-ocean')drawWaves(c1,c2,t);
    if(eff==='hex'||eff==='hex-flux')drawHex(c1,c2,t);
    if(eff==='quantum-web'||eff==='ai-neural')drawParticlesNetwork(c1,c2,c3,t);
    if(eff==='data-core'||eff==='holo-rings'||eff==='reactor'||eff==='holographic')drawCore(c1,c2,c3,t);
    if(eff==='cyber-city')drawCity(c1,c2,t);
    if(eff==='energy-tunnel'||eff==='warp')drawStars(c1,c4,t,true);
    if(eff==='neon'||eff==='plasma'||eff==='inferno'||eff==='storm'){
      drawAurora(c1,c2,c3,t);drawParticles(c1,c2,c3,t);
    }
    if(eff==='scanlines'||eff==='holo')drawRain(c1,c2,t*1.4);
    if(!motion){/* intentionally frozen background */}
    ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
    raf=requestAnimationFrame(render);
  }
  function addEffectsToLab(){
    const grid=$('#design .effect-grid');if(!grid||grid.dataset.engineAdded)return;grid.dataset.engineAdded='1';
    for(const [id,name,desc] of EXTRA){const b=document.createElement('button');b.className='effect-card premium-effect';b.dataset.effect=id;b.innerHTML=`<div class="effect-preview premium-preview"><i></i><b>${name}</b></div><strong>${name}</strong><small>${desc}</small>`;grid.appendChild(b);b.addEventListener('click',()=>{state.background=id;localStorage.setItem(KEY,JSON.stringify(state));document.body.dataset.ambience=id;document.querySelectorAll('.effect-card').forEach(x=>x.classList.toggle('active',x.dataset.effect===id));const el=$('#themeEffectName');if(el)el.textContent=name});}
  }
  function init(){
    const layer=$('#tradenexAmbience')||document.body.insertAdjacentHTML('afterbegin','<div id="tradenexAmbience"></div>')||$('#tradenexAmbience');
    canvas=document.createElement('canvas');canvas.className='tradenex-ambience-canvas';canvas.setAttribute('aria-hidden','true');
    const host=$('#tradenexAmbience');host&&host.appendChild(canvas);ctx=canvas.getContext('2d',{alpha:true});resize();addEffectsToLab();window.addEventListener('resize',resize,{passive:true});
    const watch=setInterval(()=>{addEffectsToLab();load()},400);
    requestAnimationFrame(render); return ()=>{clearInterval(watch);cancelAnimationFrame(raf)};
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,350),{once:true});else setTimeout(init,350);
})();