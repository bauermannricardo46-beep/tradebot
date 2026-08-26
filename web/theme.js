(() => {
  const KEY = 'tradenex_visual_settings_v3';
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
    ['grid','Cyber Grid','Tech grid mit sanftem Scan'],['matrix','Matrix Flow','Vertikaler Digitalfluss'],['particles','Floating Particles','Schwebende Lichtpunkte'],['aurora','Aurora Field','Langsam wandernde Lichtwolken'],['scanlines','Scanline Field','Kinematische Scanlinien'],['stars','Starfield','Dichte Cyber-Sterne'],['neon','Neon Pulse','Pulsierende Neonfelder'],['plasma','Plasma Field','Organische Energie-Wolken'],['vortex','Quantum Vortex','Rotierender Energie-Wirbel'],['circuit','Circuit Board','Animierte Leiterbahnen'],['synthwave','Synthwave Horizon','Cyberpunk-Horizon Grid'],['ocean','Ocean Depth','Tiefe Flüssigkeitsbewegung'],['inferno','Inferno','Warme Energie-Wellen'],['rain','Digital Rain','Dichter Datenregen'],['hex','Hex Mesh','Sechseckiges Holo-Mesh'],['radar','Radar Sweep','Radar-Scan um die Oberfläche'],['storm','Electric Storm','Elektrische Lichtblitze'],['nebula','Deep Nebula','Kosmischer Nebel'],['holo','Holographic Scan','Mehrschichtiger Holo-Scan'],['clean','Clean','Minimal ohne Effekt'],['off','Static Dark','Komplett statisch']
  ];
  const defaults={preset:'tradenex',accent:'#55e7ff',accent2:'#8c5cff',accent3:'#ff39d1',metal:'#c8d0df',background:'grid',motion:true,glow:12,panel:88,logoBrightness:100,logoGlow:100,effectStrength:65};
  const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const load=()=>{try{return {...defaults,...JSON.parse(localStorage.getItem(KEY)||'{}')}}catch{return {...defaults}}};
  let state=load();
  const save=()=>localStorage.setItem(KEY,JSON.stringify(state));

  function ensureAmbience(){
    let layer=$('#tradenexAmbience');
    if(!layer){layer=document.createElement('div');layer.id='tradenexAmbience';document.body.prepend(layer);}
    layer.innerHTML='<div class="ambience-base"></div><div class="fx fx-grid"></div><div class="fx fx-matrix"></div><div class="fx fx-particles"></div><div class="fx fx-stars"></div><div class="fx fx-glow glow-a"></div><div class="fx fx-glow glow-b"></div><div class="fx fx-scan"></div><div class="fx fx-circuit"></div><div class="fx fx-hex"></div><div class="fx fx-wave"></div><div class="fx fx-radar"></div><div class="fx fx-vortex"></div><div class="fx fx-storm"></div><div class="fx fx-nebula"></div>';
    return layer;
  }

  function setPalette(id){const p=palettes[id]||palettes.tradenex;state={...state,preset:id,accent:p.accent,accent2:p.accent2,accent3:p.accent3,metal:p.metal};save();apply();}

  function apply(){
    const root=document.documentElement.style;
    root.setProperty('--theme-accent',state.accent);root.setProperty('--theme-accent-2',state.accent2);root.setProperty('--theme-accent-3',state.accent3);root.setProperty('--theme-metal',state.metal);root.setProperty('--theme-bg',palettes[state.preset]?.bg||'#02040a');root.setProperty('--theme-glow',state.glow/100);root.setProperty('--theme-panel-alpha',state.panel/100);root.setProperty('--theme-effect-strength',state.effectStrength/100);
    root.setProperty('--cyan',state.accent);root.setProperty('--blue',state.accent2);root.setProperty('--violet',state.accent2);root.setProperty('--magenta',state.accent3);root.setProperty('--silver',state.metal);
    document.body.dataset.themePreset=state.preset;document.body.dataset.ambience=state.background;document.body.classList.toggle('motion-off',!state.motion);
    const layer=ensureAmbience();layer.dataset.effect=state.background;layer.dataset.motion=String(state.motion);
    const logo=document.querySelector('.brand-mark img');if(logo)logo.style.filter=`brightness(${state.logoBrightness/100}) drop-shadow(0 0 ${Math.max(4,24*state.logoGlow/100)}px ${state.accent})`;
    const controls={themePreset:state.preset,themeBackground:state.background,themeMotion:state.motion,themeGlow:state.glow,themePanel:state.panel,themeEffectStrength:state.effectStrength,themeLogoBrightness:state.logoBrightness,themeLogoGlow:state.logoGlow};
    Object.entries(controls).forEach(([id,val])=>{const el=$('#'+id);if(el){if(el.type==='checkbox')el.checked=!!val;else el.value=val;}});
    const names={themePresetName:palettes[state.preset]?.name||'Custom',themeEffectName:(effects.find(x=>x[0]===state.background)||effects[0])[1],themeGlowValue:state.glow+'%',themePanelValue:state.panel+'%',themeEffectStrengthValue:state.effectStrength+'%',themeLogoBrightnessValue:state.logoBrightness+'%',themeLogoGlowValue:state.logoGlow+'%'};Object.entries(names).forEach(([id,val])=>{const el=$('#'+id);if(el)el.textContent=val;});
    $$('.theme-preset-card').forEach(b=>b.classList.toggle('active',b.dataset.preset===state.preset));
    $$('.effect-card').forEach(b=>b.classList.toggle('active',b.dataset.effect===state.background));
  }

  function mountLogo(){const mark=$('.brand-mark');if(!mark)return;mark.classList.add('theme-logo');mark.innerHTML='<img src="./tradenex-logo.png" alt="TRADENEX" onerror="this.style.display=\'none\';this.parentElement.textContent=\'NX\'">';const brand=$('.brand');if(brand){const strong=brand.querySelector('strong');if(strong)strong.textContent='TRADENEX';const span=brand.querySelector('span');if(span)span.textContent='AI TRADING INTELLIGENCE';}}

  function activateView(id){$$('.view').forEach(v=>v.classList.toggle('active',v.id===id));$$('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.view===id));const title=$('#pageTitle');if(title)title.textContent=id==='design'?'Design Lab':id[0].toUpperCase()+id.slice(1);}

  function mountDesign(){
    if($('#design'))return;
    const nav=document.querySelector('.sidebar nav');if(!nav)return;
    const item=document.createElement('button');item.className='nav-item';item.dataset.view='design';item.innerHTML='✦ <span>Design Lab</span>';item.addEventListener('click',()=>activateView('design'));nav.appendChild(item);
    document.getElementById('tradenexVisualLab')?.remove();
    const main=document.querySelector('.main');const section=document.createElement('section');section.id='design';section.className='view';section.innerHTML=`
      <div class="design-hero glass"><div><span class="eyebrow">TRADENEX DESIGN LAB</span><h2>Visual Command Center</h2><p>Komplette Themes, Farbwelten, Effekte und Logo-Look — getrennt von allen Trading-Settings.</p></div><div class="design-current"><span>AKTIVES THEME</span><strong id="themePresetName">TRADENEX Core</strong><small id="themeEffectName">Cyber Grid</small></div></div>
      <div class="section-head"><div><span class="eyebrow">COLOR ARCHITECTURE</span><h2>Farbwelten</h2></div></div>
      <div class="theme-preset-grid design-palette-grid">${Object.entries(palettes).map(([id,p])=>`<button class="theme-preset-card" data-preset="${id}"><i style="--p1:${p.accent};--p2:${p.accent2};--p3:${p.accent3}"></i><b>${p.name}</b></button>`).join('')}</div>
      <div class="section-head"><div><span class="eyebrow">CUSTOM PALETTE</span><h2>Eigene Identität</h2></div></div>
      <div class="design-controls-grid"><section class="glass tradenex-theme-card"><div class="theme-control"><span>Akzent</span><input id="themeAccent" type="color" value="${state.accent}"></div><div class="theme-control"><span>Zweitfarbe</span><input id="themeAccent2" type="color" value="${state.accent2}"></div><div class="theme-control"><span>Highlight</span><input id="themeAccent3" type="color" value="${state.accent3}"></div><div class="theme-control"><span>Glow</span><div><input id="themeGlow" type="range" min="0" max="30" value="${state.glow}"><div id="themeGlowValue" class="theme-range-value">${state.glow}%</div></div></div><div class="theme-control"><span>Glass / Panel</span><div><input id="themePanel" type="range" min="55" max="98" value="${state.panel}"><div id="themePanelValue" class="theme-range-value">${state.panel}%</div></div></div></section>
      <section class="glass tradenex-theme-card"><div class="theme-control"><span>Animationen</span><input id="themeMotion" type="checkbox" ${state.motion?'checked':''}></div><div class="theme-control"><span>Effekt-Stärke</span><div><input id="themeEffectStrength" type="range" min="0" max="100" value="${state.effectStrength}"><div id="themeEffectStrengthValue" class="theme-range-value">${state.effectStrength}%</div></div></div><div class="theme-control"><span>Logo-Helligkeit</span><div><input id="themeLogoBrightness" type="range" min="60" max="140" value="${state.logoBrightness}"><div id="themeLogoBrightnessValue" class="theme-range-value">${state.logoBrightness}%</div></div></div><div class="theme-control"><span>Logo-Glow</span><div><input id="themeLogoGlow" type="range" min="0" max="160" value="${state.logoGlow}"><div id="themeLogoGlowValue" class="theme-range-value">${state.logoGlow}%</div></div></div></section></div>
      <div class="section-head"><div><span class="eyebrow">AMBIENCE LIBRARY</span><h2>Interaktive Hintergründe</h2></div></div>
      <div class="effect-grid">${effects.map(([id,name,desc])=>`<button class="effect-card" data-effect="${id}"><div class="effect-preview effect-${id}"><i></i></div><strong>${name}</strong><small>${desc}</small></button>`).join('')}</div>`;
    main.appendChild(section);

    $$('.theme-preset-card',section).forEach(b=>b.addEventListener('click',()=>setPalette(b.dataset.preset)));
    $('#themeAccent',section).addEventListener('input',e=>{state.preset='custom';state.accent=e.target.value;save();apply()});
    $('#themeAccent2',section).addEventListener('input',e=>{state.preset='custom';state.accent2=e.target.value;save();apply()});
    $('#themeAccent3',section).addEventListener('input',e=>{state.preset='custom';state.accent3=e.target.value;save();apply()});
    $('#themeMotion',section).addEventListener('change',e=>{state.motion=e.target.checked;save();apply()});
    $('#themeEffectStrength',section).addEventListener('input',e=>{state.effectStrength=Number(e.target.value);save();apply()});
    $('#themeGlow',section).addEventListener('input',e=>{state.glow=Number(e.target.value);save();apply()});
    $('#themePanel',section).addEventListener('input',e=>{state.panel=Number(e.target.value);save();apply()});
    $('#themeLogoBrightness',section).addEventListener('input',e=>{state.logoBrightness=Number(e.target.value);save();apply()});
    $('#themeLogoGlow',section).addEventListener('input',e=>{state.logoGlow=Number(e.target.value);save();apply()});
    $$('.effect-card',section).forEach(b=>b.addEventListener('click',()=>{state.background=b.dataset.effect;save();apply()}));
    apply();
  }

  function init(){mountLogo();mountDesign();apply();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();