(() => {
  const KEY = 'tradenex_visual_settings_v4';
  const palettes = {
    tradenex:{name:'TRADENEX Core',accent:'#55e7ff',accent2:'#8c5cff',accent3:'#ff39d1',metal:'#c8d0df',bg:'#02040a'},
    cybercyan:{name:'Cyber Cyan',accent:'#35f4ff',accent2:'#3978ff',accent3:'#7b61ff',metal:'#dffcff',bg:'#02070b'},
    electricblue:{name:'Electric Blue',accent:'#4f8cff',accent2:'#23d5ff',accent3:'#7b5cff',metal:'#d9e8ff',bg:'#02050b'},
    violet:{name:'Violet Pulse',accent:'#9a63ff',accent2:'#5a74ff',accent3:'#ec4dff',metal:'#eee4ff',bg:'#05020a'},
    magenta:{name:'Magenta Core',accent:'#ff3fcb',accent2:'#8a5cff',accent3:'#ff789d',metal:'#ffe2f4',bg:'#09020a'},
    silver:{name:'Silver / Black',accent:'#d7e2ef',accent2:'#8fa3bd',accent3:'#f4f7fb',metal:'#ffffff',bg:'#030507'},
    platinum:{name:'Platinum / Black',accent:'#e7eef7',accent2:'#9eb0c2',accent3:'#ffffff',metal:'#d6e0ea',bg:'#040607'},
    blackgold:{name:'Black / Gold',accent:'#ffca4a',accent2:'#9f6d16',accent3:'#ffe6a3',metal:'#f0cf72',bg:'#050403'},
    gold:{name:'Gold / Black',accent:'#f5c451',accent2:'#d89b2b',accent3:'#fff1a8',metal:'#f9e3a1',bg:'#080501'},
    graphite:{name:'Graphite / Silver',accent:'#aeb8c7',accent2:'#66758b',accent3:'#f3f7ff',metal:'#d8dee7',bg:'#06080b'},
    obsidian:{name:'Obsidian / Ruby',accent:'#ff5c78',accent2:'#a92749',accent3:'#ff9daf',metal:'#e7c5cc',bg:'#050205'},
    emerald:{name:'Emerald / Black',accent:'#42f5a7',accent2:'#159b6a',accent3:'#a9ffd8',metal:'#c9f7e4',bg:'#020604'},
    toxic:{name:'Toxic Lime / Black',accent:'#baff31',accent2:'#4fae16',accent3:'#e6ff8b',metal:'#e5f6c6',bg:'#030601'},
    amber:{name:'Amber / Obsidian',accent:'#ffb64d',accent2:'#a86219',accent3:'#ffe0a1',metal:'#f5dbaf',bg:'#070402'},
    ice:{name:'Ice / Deep Navy',accent:'#9cf7ff',accent2:'#5ea6ff',accent3:'#d5fbff',metal:'#eefcff',bg:'#020610'},
    ocean:{name:'Ocean Depth',accent:'#32d7d1',accent2:'#1877ff',accent3:'#7ee8ff',metal:'#d6ffff',bg:'#011116'},
    plasma:{name:'Plasma / Black',accent:'#d24cff',accent2:'#6d5cff',accent3:'#ff6b9d',metal:'#f3d8ff',bg:'#06020b'},
    solar:{name:'Solar Gold / Violet',accent:'#ffd15c',accent2:'#ff8c42',accent3:'#9d64ff',metal:'#fff0b8',bg:'#090505'},
    crimson:{name:'Crimson / Platinum',accent:'#ff4a4a',accent2:'#8e1e35',accent3:'#e8eef7',metal:'#f4f6fb',bg:'#080203'},
    stealth:{name:'Stealth / Ice',accent:'#a9c7e8',accent2:'#5f7898',accent3:'#dff1ff',metal:'#e9f5ff',bg:'#030609'},
    holographic:{name:'Holographic',accent:'#62f3ff',accent2:'#b168ff',accent3:'#ff5fcf',metal:'#eefcff',bg:'#03050a'}
  };
  const effects = [
    ['grid','Cyber Grid','3D-Perspektivnetz mit Horizont'],['aurora','Aurora Veil','Volumetrische Lichtschleier'],['particles','Particle Field','Tiefenpartikel mit Parallax'],['stars','Deep Starfield','Tiefer Sternenraum'],
    ['nebula','Nebula Drift','Langsam wandernder Weltraumnebel'],['vortex','Quantum Vortex','Spiralenergie um ein dunkles Zentrum'],['radar','Radar Sweep','Holografischer Radar-Scan'],['circuit','Circuit Flux','Leuchtende Leiterbahnen'],
    ['synthwave','Synthwave Horizon','Perspektivischer Neon-Horizont'],['ocean','Digital Ocean','Lebendes Wellen-/Datenfeld'],['rain','Digital Rain','Dichter vertikaler Datenstrom'],['hex','Hex Mesh','Tiefes holografisches Hexmesh'],
    ['holo','Holographic Scan','Mehrschichtige Scanflächen'],['reactor','Reactor Core','Kinetischer Energiekern'],['singularity','Singularity','Schwarzes Zentrum mit Akkretionsring'],['ai-neural','AI Neural','Neuronales Netzwerk mit Datenimpulsen'],
    ['galaxy-drift','Galaxy Drift','Parallax-Sternenstrom und Nebel'],['energy-tunnel','Energy Tunnel','Perspektivischer Warp-Tunnel'],['cyber-city','Cyber City','Leuchtende Skyline'],['electric-vortex','Electric Vortex','Elektrischer Wirbel'],
    ['deep-space','Deep Space','Kosmischer Tiefenraum'],['digital-ocean','Digital Ocean+','Mehrschichtige Datenwellen'],['particle-storm','Particle Storm','Partikelsturm mit Windfeld'],['hex-flux','Hex Flux','Energiefluss durch Hexfelder'],
    ['holo-rings','Holo Rings','Räumliche Hologramm-Ringe'],['data-core','Data Core','Rotierender Datenkern'],['quantum-web','Quantum Web','Tiefengestaffeltes Quantennetz'],['reactor-pro','Reactor Pro','Mehrstufiger Reaktor mit Pulswellen'],
    ['clean','Clean Void','Minimaler Hintergrund'],['off','Static Dark','Komplett statisch']
  ];

  const defaults = {preset:'tradenex',accent:'#55e7ff',accent2:'#8c5cff',accent3:'#ff39d1',metal:'#c8d0df',background:'grid',motion:true,glow:12,panel:88,logoBrightness:100,logoGlow:100,effectStrength:65};
  const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const loadLocal=()=>{try{return {...defaults,...JSON.parse(localStorage.getItem(KEY)||'{}')}}catch{return {...defaults}}};
  const saveLocal=()=>localStorage.setItem(KEY,JSON.stringify(state));
  let state=loadLocal(); let saveTimer=null;

  function saveServerNow(){
    return fetch('/notifications/visual',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
      preset:state.preset,accent:state.accent,accent2:state.accent2,accent3:state.accent3,metal:state.metal,background:state.background,
      motion:state.motion,glow:Number(state.glow),panel:Number(state.panel),logo_brightness:Number(state.logoBrightness),logo_glow:Number(state.logoGlow),effect_strength:Number(state.effectStrength)
    })}).then(r=>{if(!r.ok)throw new Error('Visual settings konnten nicht gespeichert werden');return r.json()});
  }
  function queueServerSave(){clearTimeout(saveTimer);saveTimer=setTimeout(()=>saveServerNow().then(()=>setSaveState('GESPEICHERT')).catch(()=>setSaveState('LOKAL GESPEICHERT')),450);setSaveState('SPEICHERE...');}
  async function loadServer(){
    try{
      const r=await fetch('/notifications/visual',{cache:'no-store'}); if(!r.ok)throw new Error('visual api');
      const v=await r.json();
      state={...defaults,...v}; saveLocal();
    }catch{/* localStorage fallback */}
  }

  function setSaveState(text){const el=$('#designSaveState');if(el)el.textContent=text}
  function rgba(hex,a){const h=(hex||'#ffffff').replace('#','');const r=parseInt(h.slice(0,2),16)||255,g=parseInt(h.slice(2,4),16)||255,b=parseInt(h.slice(4,6),16)||255;return `rgba(${r},${g},${b},${a})`}

  function setBaseVariables(){
    const root=document.documentElement.style;
    const p=palettes[state.preset]||palettes.tradenex;
    const bg=p.bg;
    root.setProperty('--theme-accent',state.accent);root.setProperty('--theme-accent-2',state.accent2);root.setProperty('--theme-accent-3',state.accent3);root.setProperty('--theme-metal',state.metal);root.setProperty('--theme-bg',bg);
    root.setProperty('--cyan',state.accent);root.setProperty('--blue',state.accent2);root.setProperty('--violet',state.accent2);root.setProperty('--magenta',state.accent3);root.setProperty('--silver',state.metal);
    root.setProperty('--bg',bg);root.setProperty('--bg2',rgba(state.accent2,.055));root.setProperty('--panel',rgba(state.metal,.055));root.setProperty('--panel2',rgba(state.accent2,.075));
    root.setProperty('--line',rgba(state.accent,.15));root.setProperty('--line2',rgba(state.accent2,.22));root.setProperty('--muted','#8090a9');root.setProperty('--text','#f5f8ff');root.setProperty('--shadow','0 30px 100px rgba(0,0,0,.52)');
    root.setProperty('--theme-glow',Number(state.glow)/100);root.setProperty('--theme-panel-alpha',Number(state.panel)/100);root.setProperty('--theme-effect-strength',Number(state.effectStrength)/100);
    root.setProperty('--theme-primary-gradient',`linear-gradient(135deg,${state.accent} 0%,${state.accent2} 52%,${state.accent3} 100%)`);
    document.body.dataset.themePreset=state.preset;document.body.dataset.ambience=state.background;document.body.classList.toggle('motion-off',!state.motion);

    let style=$('#tradenex-theme-runtime');
    if(!style){style=document.createElement('style');style.id='tradenex-theme-runtime';document.head.appendChild(style)}
    style.textContent=`
      body{background:radial-gradient(circle at 80% -5%,${rgba(state.accent2,.18)},transparent 28%),radial-gradient(circle at 15% 20%,${rgba(state.accent,.09)},transparent 24%),linear-gradient(180deg,${bg},${bg} 55%,#010207)!important;color:var(--text)!important}
      .sidebar{background:linear-gradient(180deg,${rgba(state.metal,.035)},${rgba(state.accent2,.025)})!important;border-color:${rgba(state.accent,.14)}!important}
      .nav-item.active{background:linear-gradient(90deg,${rgba(state.accent,.12)},${rgba(state.accent2,.10)},${rgba(state.accent3,.05)})!important;border-color:${rgba(state.accent,.24)}!important;color:#fff!important}
      .primary-btn{background:var(--theme-primary-gradient)!important;box-shadow:0 14px 34px ${rgba(state.accent,.16)},inset 0 0 18px rgba(255,255,255,.18)!important}
      .mode.active,.filter.active{background:linear-gradient(90deg,${rgba(state.accent,.15)},${rgba(state.accent2,.12)})!important;border-color:${rgba(state.accent,.32)}!important;color:${state.accent}!important}
      .glass{border-color:${rgba(state.accent,.12)}!important;background:linear-gradient(180deg,${rgba(state.metal,.055)},${rgba(state.accent2,.045)})!important;box-shadow:0 30px 100px rgba(0,0,0,.48),inset 0 1px 0 ${rgba(state.metal,.05)}!important}
      .strategy-icon{background:linear-gradient(145deg,${rgba(state.accent,.14)},${rgba(state.accent2,.08)})!important;border-color:${rgba(state.accent,.18)}!important;color:${state.accent}!important}
      .position-bar i{background:linear-gradient(90deg,${state.accent},${state.accent2},${state.accent3})!important}
      .sidebar:after{background:linear-gradient(90deg,transparent,${state.accent},${state.accent3},transparent)!important}
      .theme-logo{border-color:${rgba(state.accent,.45)}!important;box-shadow:inset 0 0 20px ${rgba(state.accent,.14)},0 0 34px ${rgba(state.accent,.12)}!important}
    `;
  }

  function ensureAmbience(){
    let layer=$('#tradenexAmbience');
    if(!layer){layer=document.createElement('div');layer.id='tradenexAmbience';document.body.prepend(layer)}
    return layer;
  }

  function apply(){
    setBaseVariables();
    const layer=ensureAmbience(); layer.dataset.effect=state.background; layer.dataset.motion=String(state.motion); layer.dataset.strength=String(state.effectStrength);
    const logo=document.querySelector('.sidebar .brand-mark img');
    if(logo)logo.style.filter=`brightness(${state.logoBrightness/100}) drop-shadow(0 0 ${Math.max(4,24*state.logoGlow/100)}px ${rgba(state.accent,.30)})`;
    const controls={themeAccent:state.accent,themeAccent2:state.accent2,themeAccent3:state.accent3,themeMotion:state.motion,themeGlow:state.glow,themePanel:state.panel,themeEffectStrength:state.effectStrength,themeLogoBrightness:state.logoBrightness,themeLogoGlow:state.logoGlow};
    Object.entries(controls).forEach(([id,v])=>{const el=$('#'+id);if(!el)return;if(el.type==='checkbox')el.checked=!!v;else el.value=v});
    const preset=$('#themePreset');if(preset)preset.value=palettes[state.preset]?state.preset:'';
    const name=$('#themePresetName');if(name)name.textContent=palettes[state.preset]?.name||'Custom';
    const eff=$('#themeEffectName');if(eff)eff.textContent=(effects.find(x=>x[0]===state.background)||['','Custom Effect'])[1];
    const vals={themeGlowValue:state.glow+'%',themePanelValue:state.panel+'%',themeEffectStrengthValue:state.effectStrength+'%',themeLogoBrightnessValue:state.logoBrightness+'%',themeLogoGlowValue:state.logoGlow+'%'};
    Object.entries(vals).forEach(([id,v])=>{const el=$('#'+id);if(el)el.textContent=v});
    $$('.theme-preset-card').forEach(b=>b.classList.toggle('active',b.dataset.preset===state.preset));
    $$('.effect-card').forEach(b=>b.classList.toggle('active',b.dataset.effect===state.background));
  }

  function mutate(patch,{persist=true}={}){state={...state,...patch};saveLocal();apply();if(persist)queueServerSave()}

  function mountLogo(){
    const mark=document.querySelector('.brand-mark');if(!mark)return;
    mark.classList.add('theme-logo');
    mark.innerHTML='<img src="./tradenex-logo.png" alt="TRADENEX">';
    const brand=document.querySelector('.brand');if(brand){const strong=brand.querySelector('strong');if(strong)strong.textContent='TRADENEX';const span=brand.querySelector('span');if(span)span.textContent='AI TRADING INTELLIGENCE'}
  }

  function activateView(id){
    $$('.view').forEach(v=>v.classList.toggle('active',v.id===id));
    $$('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.view===id));
    const title=$('#pageTitle');if(title)title.textContent=id==='design'?'Design Lab':id[0].toUpperCase()+id.slice(1);
  }

  function mountDesign(){
    if($('#design'))return;
    const nav=document.querySelector('.sidebar nav');if(!nav)return;
    const item=document.createElement('button');item.className='nav-item';item.dataset.view='design';item.innerHTML='✦ <span>Design Lab</span>';item.addEventListener('click',()=>activateView('design'));nav.appendChild(item);
    document.getElementById('tradenexVisualLab')?.remove();
    const main=document.querySelector('.main');if(!main)return;
    const section=document.createElement('section');section.id='design';section.className='view';
    section.innerHTML=`
      <div class="design-hero glass"><div><span class="eyebrow">TRADENEX DESIGN LAB</span><h2>Visual Command Center</h2><p>Komplette Themes, Farbwelten, Effekte und Logo-Look — getrennt von allen Trading-Settings.</p></div><div class="design-current"><span>AKTIVES THEME</span><strong id="themePresetName">TRADENEX Core</strong><small id="themeEffectName">Cyber Grid</small></div></div>
      <div class="design-savebar glass"><div><strong>Design-Konfiguration</strong><small id="designSaveState">SERVER GESPEICHERT</small></div><div><button class="ghost-btn" id="designResetBtn">↺ Standard</button><button class="primary-btn" id="designSaveBtn">✓ Design speichern</button></div></div>
      <div class="section-head"><div><span class="eyebrow">COLOR ARCHITECTURE</span><h2>Farbwelten</h2></div></div>
      <div class="theme-preset-grid design-palette-grid">${Object.entries(palettes).map(([id,p])=>`<button class="theme-preset-card" data-preset="${id}"><i style="--p1:${p.accent};--p2:${p.accent2};--p3:${p.accent3}"></i><b>${p.name}</b></button>`).join('')}</div>
      <div class="section-head"><div><span class="eyebrow">CUSTOM PALETTE</span><h2>Eigene Identität</h2></div></div>
      <div class="design-controls-grid"><section class="glass tradenex-theme-card"><div class="theme-control"><span>Akzent</span><input id="themeAccent" type="color" value="${state.accent}"></div><div class="theme-control"><span>Zweitfarbe</span><input id="themeAccent2" type="color" value="${state.accent2}"></div><div class="theme-control"><span>Highlight</span><input id="themeAccent3" type="color" value="${state.accent3}"></div><div class="theme-control"><span>Glow</span><div><input id="themeGlow" type="range" min="0" max="30" value="${state.glow}"><div id="themeGlowValue" class="theme-range-value">${state.glow}%</div></div></div><div class="theme-control"><span>Glass / Panel</span><div><input id="themePanel" type="range" min="55" max="98" value="${state.panel}"><div id="themePanelValue" class="theme-range-value">${state.panel}%</div></div></div></section>
      <section class="glass tradenex-theme-card"><div class="theme-control"><span>Animationen</span><input id="themeMotion" type="checkbox" ${state.motion?'checked':''}></div><div class="theme-control"><span>Effekt-Stärke</span><div><input id="themeEffectStrength" type="range" min="0" max="100" value="${state.effectStrength}"><div id="themeEffectStrengthValue" class="theme-range-value">${state.effectStrength}%</div></div></div><div class="theme-control"><span>Logo-Helligkeit</span><div><input id="themeLogoBrightness" type="range" min="60" max="140" value="${state.logoBrightness}"><div id="themeLogoBrightnessValue" class="theme-range-value">${state.logoBrightness}%</div></div></div><div class="theme-control"><span>Logo-Glow</span><div><input id="themeLogoGlow" type="range" min="0" max="160" value="${state.logoGlow}"><div id="themeLogoGlowValue" class="theme-range-value">${state.logoGlow}%</div></div></div></section></div>
      <div class="section-head"><div><span class="eyebrow">AMBIENCE LIBRARY</span><h2>Interaktive Hintergründe</h2></div></div>
      <div class="effect-grid">${effects.map(([id,name,desc])=>`<button class="effect-card" data-effect="${id}"><div class="effect-preview effect-${id}"><i></i></div><strong>${name}</strong><small>${desc}</small></button>`).join('')}</div>`;
    main.appendChild(section);

    $$('.theme-preset-card',section).forEach(b=>b.addEventListener('click',()=>mutate((()=>{const p=palettes[b.dataset.preset];return {preset:b.dataset.preset,accent:p.accent,accent2:p.accent2,accent3:p.accent3,metal:p.metal}})())));
    $('#themeAccent',section).addEventListener('input',e=>mutate({preset:'custom',accent:e.target.value}));
    $('#themeAccent2',section).addEventListener('input',e=>mutate({preset:'custom',accent2:e.target.value}));
    $('#themeAccent3',section).addEventListener('input',e=>mutate({preset:'custom',accent3:e.target.value}));
    $('#themeMotion',section).addEventListener('change',e=>mutate({motion:e.target.checked}));
    $('#themeEffectStrength',section).addEventListener('input',e=>mutate({effectStrength:Number(e.target.value)}));
    $('#themeGlow',section).addEventListener('input',e=>mutate({glow:Number(e.target.value)}));
    $('#themePanel',section).addEventListener('input',e=>mutate({panel:Number(e.target.value)}));
    $('#themeLogoBrightness',section).addEventListener('input',e=>mutate({logoBrightness:Number(e.target.value)}));
    $('#themeLogoGlow',section).addEventListener('input',e=>mutate({logoGlow:Number(e.target.value)}));
    $$('.effect-card',section).forEach(b=>b.addEventListener('click',()=>mutate({background:b.dataset.effect})));
    $('#designSaveBtn').addEventListener('click',()=>saveServerNow().then(()=>setSaveState('GESPEICHERT')).catch(()=>setSaveState('LOKAL GESPEICHERT')));
    $('#designResetBtn').addEventListener('click',()=>{state={...defaults};saveLocal();apply();queueServerSave();});
    apply();
  }

  async function init(){
    mountLogo();
    mountDesign();
    await loadServer();
    apply();
    setSaveState('SERVER GESPEICHERT');
    window.__TRADENEX_THEME_STATE=state;
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true}); else init();
})();