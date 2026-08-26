(() => {
  if (window.__TRADENEX_STABLE_THEME__) return;
  window.__TRADENEX_STABLE_THEME__ = true;

  const KEY = 'tradenex_visual_settings_v4';
  const palettes = {
    tradenex:['TRADENEX Core','#55e7ff','#8c5cff','#ff39d1','#c8d0df','#02040a'],
    cyan:['Cyber Cyan','#35f4ff','#3978ff','#7b61ff','#dffcff','#02070b'],
    blue:['Electric Blue','#4f8cff','#23d5ff','#7b5cff','#d9e8ff','#02050b'],
    violet:['Violet Pulse','#9a63ff','#5a74ff','#ec4dff','#eee4ff','#05020a'],
    magenta:['Magenta Core','#ff3fcb','#8a5cff','#ff789d','#ffe2f4','#09020a'],
    silver:['Silver / Black','#d7e2ef','#8fa3bd','#f4f7fb','#ffffff','#030507'],
    platinum:['Platinum / Black','#e7eef7','#9eb0c2','#ffffff','#d6e0ea','#040607'],
    blackgold:['Black / Gold','#ffca4a','#9f6d16','#ffe6a3','#f0cf72','#050403'],
    gold:['Gold / Black','#f5c451','#d89b2b','#fff1a8','#f9e3a1','#080501'],
    graphite:['Graphite / Silver','#aeb8c7','#66758b','#f3f7ff','#d8dee7','#06080b'],
    ruby:['Obsidian / Ruby','#ff5c78','#a92749','#ff9daf','#e7c5cc','#050205'],
    emerald:['Emerald / Black','#42f5a7','#159b6a','#a9ffd8','#c9f7e4','#020604'],
    lime:['Toxic Lime / Black','#baff31','#4fae16','#e6ff8b','#e5f6c6','#030601'],
    amber:['Amber / Obsidian','#ffb64d','#a86219','#ffe0a1','#f5dbaf','#070402'],
    ice:['Ice / Deep Navy','#9cf7ff','#5ea6ff','#d5fbff','#eefcff','#020610'],
    ocean:['Ocean Depth','#32d7d1','#1877ff','#7ee8ff','#d6ffff','#011116'],
    plasma:['Plasma / Black','#d24cff','#6d5cff','#ff6b9d','#f3d8ff','#06020b'],
    solar:['Solar Gold / Violet','#ffd15c','#ff8c42','#9d64ff','#fff0b8','#090505'],
    crimson:['Crimson / Platinum','#ff4a4a','#8e1e35','#e8eef7','#f4f6fb','#080203'],
    stealth:['Stealth / Ice','#a9c7e8','#5f7898','#dff1ff','#e9f5ff','#030609'],
    holo:['Holographic','#62f3ff','#b168ff','#ff5fcf','#eefcff','#03050a']
  };
  const effects = [
    ['grid','Cyber Grid'],['matrix','Matrix Flow'],['particles','Particle Field'],['aurora','Aurora Veil'],
    ['stars','Deep Starfield'],['nebula','Nebula Drift'],['vortex','Quantum Vortex'],['radar','Radar Sweep'],
    ['circuit','Circuit Flux'],['synthwave','Synthwave Horizon'],['ocean','Digital Ocean'],['rain','Digital Rain'],
    ['hex','Hex Mesh'],['holo','Holographic Scan'],['reactor','Reactor Core'],['singularity','Singularity'],
    ['neural','AI Neural'],['galaxy','Galaxy Drift'],['storm','Electric Storm'],['clean','Clean Void']
  ];
  const defaults = {preset:'tradenex',accent:'#55e7ff',accent2:'#8c5cff',accent3:'#ff39d1',metal:'#c8d0df',background:'grid',motion:true,glow:12,panel:88,logoBrightness:100,logoGlow:90,effectStrength:60};
  const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const load=()=>{try{return {...defaults,...JSON.parse(localStorage.getItem(KEY)||'{}')}}catch{return {...defaults}}};
  let state=load();
  const save=()=>localStorage.setItem(KEY,JSON.stringify(state));

  function installStyle(){
    if ($('#tradenexStableDesignCSS')) return;
    const style=document.createElement('style');
    style.id='tradenexStableDesignCSS';
    style.textContent=`
      .brand-mark{width:44px!important;height:44px!important;min-width:44px!important;max-width:44px!important;min-height:44px!important;max-height:44px!important;overflow:hidden!important}
      .brand-mark img{width:100%!important;height:100%!important;display:block!important;object-fit:contain!important}
      .main img[src*="tradenex-logo"],#design img[src*="tradenex-logo"]{display:none!important}
      #tradenexStableBg{position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;background:#02040a;opacity:var(--tn-bg-opacity,.6)}
      #tradenexStableBg:before,#tradenexStableBg:after{content:"";position:absolute;inset:0;pointer-events:none}
      .app-shell{position:relative;z-index:2}.sidebar,.main{position:relative;z-index:3}
      body[data-tn-bg="grid"] #tradenexStableBg{background-image:linear-gradient(color-mix(in srgb,var(--theme-accent) 7%,transparent) 1px,transparent 1px),linear-gradient(90deg,color-mix(in srgb,var(--theme-accent-2) 5%,transparent) 1px,transparent 1px);background-size:48px 48px;animation:tnGrid 8s linear infinite}
      body[data-tn-bg="matrix"] #tradenexStableBg:before{background:repeating-linear-gradient(90deg,transparent 0 24px,color-mix(in srgb,var(--theme-accent) 7%,transparent) 25px 26px);animation:tnMatrix 5s linear infinite}
      body[data-tn-bg="particles"] #tradenexStableBg:before{background-image:radial-gradient(circle at 12% 18%,var(--theme-accent) 0 1px,transparent 2px),radial-gradient(circle at 31% 72%,var(--theme-accent-2) 0 1px,transparent 2px),radial-gradient(circle at 76% 26%,var(--theme-accent-3) 0 1px,transparent 2px),radial-gradient(circle at 88% 78%,var(--theme-metal) 0 1px,transparent 2px);background-size:180px 180px,230px 230px,270px 270px,320px 320px;animation:tnFloat 18s linear infinite}
      body[data-tn-bg="aurora"] #tradenexStableBg:before{background:radial-gradient(circle at 20% 28%,color-mix(in srgb,var(--theme-accent) 20%,transparent),transparent 32%),radial-gradient(circle at 80% 35%,color-mix(in srgb,var(--theme-accent-3) 18%,transparent),transparent 28%),radial-gradient(circle at 55% 80%,color-mix(in srgb,var(--theme-accent-2) 16%,transparent),transparent 34%);filter:blur(26px);animation:tnAurora 14s ease-in-out infinite alternate}
      body[data-tn-bg="stars"] #tradenexStableBg{background-image:radial-gradient(circle,var(--theme-metal) 0 1px,transparent 1.8px),radial-gradient(circle,var(--theme-accent) 0 1px,transparent 1.8px);background-size:86px 86px,139px 139px;animation:tnStars 32s linear infinite}
      body[data-tn-bg="nebula"] #tradenexStableBg{background:radial-gradient(circle at 22% 65%,color-mix(in srgb,var(--theme-accent-2) 18%,transparent),transparent 30%),radial-gradient(circle at 73% 25%,color-mix(in srgb,var(--theme-accent-3) 16%,transparent),transparent 26%),radial-gradient(circle at 52% 72%,color-mix(in srgb,var(--theme-accent) 12%,transparent),transparent 35%),#02030a;filter:blur(.1px);animation:tnNebula 18s ease-in-out infinite alternate}
      body[data-tn-bg="vortex"] #tradenexStableBg{background:conic-gradient(from 0deg at 50% 50%,transparent 0 18%,color-mix(in srgb,var(--theme-accent) 10%,transparent) 20%,transparent 31%,color-mix(in srgb,var(--theme-accent-3) 8%,transparent) 33%,transparent 47%);mask-image:radial-gradient(circle at center,black 0 26%,transparent 73%);animation:tnSpin 12s linear infinite}
      body[data-tn-bg="radar"] #tradenexStableBg{background:repeating-radial-gradient(circle at center,transparent 0 110px,color-mix(in srgb,var(--theme-accent) 5%,transparent) 112px 114px),conic-gradient(from 0deg at center,transparent 0 84%,color-mix(in srgb,var(--theme-accent) 16%,transparent) 86%,transparent 89%);animation:tnSpin 6s linear infinite}
      body[data-tn-bg="circuit"] #tradenexStableBg{background-image:linear-gradient(90deg,transparent 0 47%,color-mix(in srgb,var(--theme-accent) 8%,transparent) 48% 50%,transparent 51%),linear-gradient(0deg,transparent 0 47%,color-mix(in srgb,var(--theme-accent-2) 7%,transparent) 48% 50%,transparent 51%);background-size:120px 120px}
      body[data-tn-bg="synthwave"] #tradenexStableBg{background:linear-gradient(180deg,#04020a 0 52%,transparent 53%),repeating-linear-gradient(90deg,transparent 0 28px,color-mix(in srgb,var(--theme-accent-2) 12%,transparent) 29px 30px);transform:perspective(520px) rotateX(65deg) scale(1.8);transform-origin:center bottom;animation:tnWave 8s ease-in-out infinite alternate}
      body[data-tn-bg="ocean"] #tradenexStableBg{background:repeating-radial-gradient(ellipse at 50% 100%,color-mix(in srgb,var(--theme-accent) 10%,transparent) 0 2px,transparent 3px 24px);animation:tnOcean 9s ease-in-out infinite alternate}
      body[data-tn-bg="rain"] #tradenexStableBg:before{background:repeating-linear-gradient(180deg,transparent 0 8px,color-mix(in srgb,var(--theme-accent) 8%,transparent) 9px 11px),repeating-linear-gradient(90deg,transparent 0 20px,color-mix(in srgb,var(--theme-accent-2) 4%,transparent) 21px 22px);background-size:100% 150px,44px 100%;animation:tnRain 3s linear infinite}
      body[data-tn-bg="hex"] #tradenexStableBg{background-image:linear-gradient(30deg,color-mix(in srgb,var(--theme-accent) 7%,transparent) 12%,transparent 12.5%,transparent 87%,color-mix(in srgb,var(--theme-accent) 7%,transparent) 87.5%),linear-gradient(150deg,color-mix(in srgb,var(--theme-accent-2) 5%,transparent) 12%,transparent 12.5%,transparent 87%,color-mix(in srgb,var(--theme-accent-2) 5%,transparent) 87.5%);background-size:80px 46px}
      body[data-tn-bg="holo"] #tradenexStableBg{background:radial-gradient(circle at center,transparent 0 22%,color-mix(in srgb,var(--theme-accent) 9%,transparent) 24%,transparent 26%),repeating-conic-gradient(from 0deg,transparent 0 8deg,color-mix(in srgb,var(--theme-accent-3) 5%,transparent) 9deg 10deg);animation:tnSpin 18s linear infinite}
      body[data-tn-bg="reactor"] #tradenexStableBg{background:radial-gradient(circle at center,color-mix(in srgb,var(--theme-accent) 18%,transparent),transparent 12%),radial-gradient(circle at center,color-mix(in srgb,var(--theme-accent-2) 8%,transparent),transparent 42%);animation:tnReactor 5s ease-in-out infinite alternate}
      body[data-tn-bg="singularity"] #tradenexStableBg{background:radial-gradient(circle at center,#000 0 12%,color-mix(in srgb,var(--theme-accent) 15%,transparent) 15%,transparent 42%);animation:tnSingularity 8s ease-in-out infinite alternate}
      body[data-tn-bg="neural"] #tradenexStableBg{background-image:radial-gradient(circle at 16% 30%,var(--theme-accent) 0 1px,transparent 2px),radial-gradient(circle at 44% 58%,var(--theme-accent-2) 0 1px,transparent 2px),radial-gradient(circle at 76% 24%,var(--theme-accent-3) 0 1px,transparent 2px);background-size:180px 180px,220px 220px,260px 260px;animation:tnFloat 10s linear infinite}
      body[data-tn-bg="galaxy"] #tradenexStableBg{background:radial-gradient(circle at 20% 35%,color-mix(in srgb,var(--theme-accent) 14%,transparent),transparent 28%),radial-gradient(circle at 78% 62%,color-mix(in srgb,var(--theme-accent-3) 12%,transparent),transparent 24%),radial-gradient(circle at center,var(--theme-accent-2) 0 1px,transparent 1.8px);background-size:auto,auto,46px 46px;animation:tnGalaxy 18s linear infinite}
      body[data-tn-bg="storm"] #tradenexStableBg:before{background:linear-gradient(118deg,transparent 0 49%,color-mix(in srgb,var(--theme-metal) 20%,transparent) 50%,transparent 51%),linear-gradient(248deg,transparent 0 68%,color-mix(in srgb,var(--theme-accent) 16%,transparent) 69%,transparent 70%);background-size:180% 180%;animation:tnStorm 2.8s steps(2,end) infinite}
      body[data-tn-bg="clean"] #tradenexStableBg{opacity:.15;background:var(--theme-bg)}
      body[data-tn-bg="grid"] #tradenexStableBg,body[data-tn-bg="matrix"] #tradenexStableBg,body[data-tn-bg="particles"] #tradenexStableBg,body[data-tn-bg="aurora"] #tradenexStableBg,body[data-tn-bg="stars"] #tradenexStableBg,body[data-tn-bg="nebula"] #tradenexStableBg{background-color:var(--theme-bg)}
      body.motion-off #tradenexStableBg,body.motion-off #tradenexStableBg:before,body.motion-off #tradenexStableBg:after{animation:none!important}
      .tradenex-design{padding-bottom:28px}.tradenex-design .design-hero{display:flex;justify-content:space-between;gap:20px;align-items:center;padding:24px;margin-bottom:18px}.tradenex-design .design-current{min-width:190px;padding:14px;border:1px solid rgba(255,255,255,.08);border-radius:14px;background:rgba(255,255,255,.025)}.tradenex-design .design-current span,.tradenex-design .design-current small{display:block;color:var(--muted);font-size:8px;letter-spacing:.14em}.tradenex-design .design-current strong{display:block;margin:6px 0 4px;color:var(--theme-accent);font-size:14px}.tradenex-design .palette-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}.tradenex-design .palette{border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.025);color:#e7edf7;padding:10px;border-radius:12px;cursor:pointer;text-align:left}.tradenex-design .palette:hover,.tradenex-design .palette.active{border-color:color-mix(in srgb,var(--theme-accent) 45%,transparent);box-shadow:0 0 24px color-mix(in srgb,var(--theme-accent) 10%,transparent);transform:translateY(-1px)}.tradenex-design .swatches{height:22px;border-radius:7px;background:linear-gradient(90deg,var(--p1),var(--p2),var(--p3));margin-bottom:7px}.tradenex-design .palette b{font-size:9px}.tradenex-design .controls{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:18px 0}.tradenex-design .control-card{padding:18px}.tradenex-design .row{display:grid;grid-template-columns:1fr 190px;gap:15px;align-items:center;border-top:1px solid rgba(255,255,255,.05);padding:11px 0;color:#b9c2d2}.tradenex-design input[type=color]{width:100%;height:38px;padding:3px;border-radius:9px;border:1px solid color-mix(in srgb,var(--theme-accent) 22%,transparent);background:#070c16}.tradenex-design input[type=range]{width:100%;accent-color:var(--theme-accent)}.tradenex-design .value{margin-top:4px;text-align:right;color:var(--theme-accent);font-weight:800;font-size:10px}.tradenex-design .effects{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.tradenex-design .effect{padding:0;border:1px solid rgba(255,255,255,.08);border-radius:13px;overflow:hidden;background:rgba(255,255,255,.025);color:#e7edf7;text-align:left;cursor:pointer}.tradenex-design .effect:hover,.tradenex-design .effect.active{border-color:color-mix(in srgb,var(--theme-accent) 45%,transparent);box-shadow:0 0 24px color-mix(in srgb,var(--theme-accent) 10%,transparent)}.tradenex-design .preview{height:74px;background:var(--theme-bg);position:relative;overflow:hidden}.tradenex-design .preview:before{content:"";position:absolute;inset:0}.tradenex-design .effect-name{padding:9px 11px 3px;font-size:10px;font-weight:850}.tradenex-design .effect-note{padding:0 11px 10px;color:var(--muted);font-size:8px}.tradenex-design .preview.grid{background-image:linear-gradient(var(--theme-accent) 1px,transparent 1px),linear-gradient(90deg,var(--theme-accent-2) 1px,transparent 1px);background-size:18px 18px}.tradenex-design .preview.matrix{background:repeating-linear-gradient(90deg,transparent 0 8px,var(--theme-accent) 9px 10px);animation:tnMatrix 2.2s linear infinite}.tradenex-design .preview.particles{background-image:radial-gradient(circle,var(--theme-accent) 0 1px,transparent 2px);background-size:15px 15px;animation:tnFloat 4s linear infinite}.tradenex-design .preview.aurora{background:radial-gradient(circle at 22% 60%,var(--theme-accent),transparent 35%),radial-gradient(circle at 80% 28%,var(--theme-accent-3),transparent 30%)}.tradenex-design .preview.stars{background-image:radial-gradient(circle,var(--theme-metal) 0 1px,transparent 1.5px);background-size:14px 14px}.tradenex-design .preview.vortex{background:conic-gradient(from 0deg,transparent,var(--theme-accent),transparent,var(--theme-accent-3),transparent);animation:tnSpin 3s linear infinite}.tradenex-design .preview.radar{background:repeating-radial-gradient(circle at center,transparent 0 16px,var(--theme-accent) 17px 18px),conic-gradient(from 0deg,transparent 0 86%,var(--theme-accent) 87%,transparent 89%);animation:tnSpin 3s linear infinite}.tradenex-design .preview.nebula{background:radial-gradient(circle at 22% 60%,var(--theme-accent-2),transparent 35%),radial-gradient(circle at 78% 30%,var(--theme-accent-3),transparent 30%)}.tradenex-design .preview.reactor{background:radial-gradient(circle at center,var(--theme-accent) 0 3%,transparent 18%),radial-gradient(circle at center,var(--theme-accent-2),transparent 55%);animation:tnReactor 2s ease-in-out infinite alternate}.tradenex-design .preview.synthwave{background:linear-gradient(180deg,#02020a 0 52%,transparent 53%),repeating-linear-gradient(90deg,transparent 0 10px,var(--theme-accent-2) 11px 12px)}
      @keyframes tnGrid{to{background-position:0 48px,48px 0}}@keyframes tnMatrix{from{background-position:0 -100vh}to{background-position:0 100vh}}@keyframes tnFloat{from{background-position:0 0,0 0,0 0,0 0}to{background-position:70px -40px,-60px 55px,80px -30px,-40px 60px}}@keyframes tnAurora{from{transform:translate3d(-2%,-1%,0) scale(1)}to{transform:translate3d(4%,3%,0) scale(1.08)}}@keyframes tnStars{to{background-position:86px 86px,139px 139px}}@keyframes tnNebula{from{transform:scale(1)}to{transform:scale(1.08) translate3d(1%,-1%,0)}}@keyframes tnSpin{to{transform:rotate(360deg)}}@keyframes tnWave{from{transform:perspective(520px) rotateX(65deg) scale(1.72) translateY(2%)}to{transform:perspective(520px) rotateX(65deg) scale(1.84) translateY(-3%)}}@keyframes tnOcean{from{background-position:50% 100%}to{background-position:50% 92%}}@keyframes tnRain{to{background-position:0 150px,44px 0}}@keyframes tnReactor{from{transform:scale(.96);filter:blur(0)}to{transform:scale(1.04);filter:blur(1px)}}@keyframes tnSingularity{from{transform:scale(.98)}to{transform:scale(1.04)}}@keyframes tnGalaxy{to{background-position:40px 0,-40px 0,46px 46px}}@keyframes tnStorm{50%{opacity:.45}}
      @media(max-width:1100px){.tradenex-design .palette-grid{grid-template-columns:repeat(4,minmax(0,1fr))}.tradenex-design .effects{grid-template-columns:repeat(3,minmax(0,1fr))}}
      @media(max-width:820px){.tradenex-design .design-hero,.tradenex-design .controls{grid-template-columns:1fr;display:grid}.tradenex-design .palette-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.tradenex-design .effects{grid-template-columns:repeat(2,minmax(0,1fr))}.tradenex-design .row{grid-template-columns:1fr}}
    `;
    document.head.appendChild(style);
  }

  function apply(){
    const root=document.documentElement.style;
    root.setProperty('--theme-accent',state.accent);root.setProperty('--theme-accent-2',state.accent2);root.setProperty('--theme-accent-3',state.accent3);root.setProperty('--theme-metal',state.metal);root.setProperty('--theme-bg',palettes[state.preset]?.[5]||'#02040a');root.setProperty('--theme-glow',state.glow/100);root.setProperty('--theme-panel-alpha',state.panel/100);root.setProperty('--tn-bg-opacity',Math.max(.18,state.effectStrength/100));
    root.setProperty('--cyan',state.accent);root.setProperty('--blue',state.accent2);root.setProperty('--violet',state.accent2);root.setProperty('--magenta',state.accent3);root.setProperty('--silver',state.metal);
    document.body.dataset.themePreset=state.preset;document.body.dataset.tnBg=state.background;document.body.classList.toggle('motion-off',!state.motion);
    const bg=$('#tradenexStableBg');if(bg)bg.style.display=state.background==='clean'?'none':'block';
    const logo=document.querySelector('.brand-mark img');if(logo)logo.style.filter=`brightness(${state.logoBrightness/100}) drop-shadow(0 0 ${Math.max(3,18*state.logoGlow/100)}px ${state.accent})`;
    $$('.palette').forEach(b=>b.classList.toggle('active',b.dataset.preset===state.preset));
    $$('.effect').forEach(b=>b.classList.toggle('active',b.dataset.effect===state.background));
    const map={themeGlowValue:`${state.glow}%`,themePanelValue:`${state.panel}%`,themeEffectStrengthValue:`${state.effectStrength}%`,themeLogoBrightnessValue:`${state.logoBrightness}%`,themeLogoGlowValue:`${state.logoGlow}%`,themePresetName:palettes[state.preset]?.[0]||'Custom',themeEffectName:(effects.find(e=>e[0]===state.background)||effects[0])[1]};
    Object.entries(map).forEach(([id,val])=>{const e=$('#'+id);if(e)e.textContent=val});
  }

  function mountBrand(){
    const mark=document.querySelector('.brand-mark');
    if(mark){mark.innerHTML='<img src="./tradenex-logo.png" alt="TRADENEX">';mark.style.width='44px';mark.style.height='44px';}
    document.querySelectorAll('img[src*="tradenex-logo"]').forEach(img=>{if(!img.closest('.brand-mark'))img.remove()});
    const brand=document.querySelector('.brand');
    if(brand){const s=brand.querySelector('strong');const p=brand.querySelector('span');if(s)s.textContent='TRADENEX';if(p)p.textContent='AI TRADING INTELLIGENCE';}
  }

  function mountBackground(){if($('#tradenexStableBg'))return;const bg=document.createElement('div');bg.id='tradenexStableBg';bg.setAttribute('aria-hidden','true');document.body.prepend(bg)}

  function activate(id){$$('.view').forEach(v=>v.classList.toggle('active',v.id===id));$$('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.view===id));const t=$('#pageTitle');if(t)t.textContent=id==='design'?'Design Lab':id[0].toUpperCase()+id.slice(1)}

  function mountDesign(){
    document.querySelector('#tradenexVisualLab')?.remove();
    if($('#design'))return;
    const nav=document.querySelector('.sidebar nav');const main=document.querySelector('.main');if(!nav||!main)return;
    const item=document.createElement('button');item.className='nav-item';item.dataset.view='design';item.innerHTML='✦ <span>Design Lab</span>';item.addEventListener('click',()=>activate('design'));nav.appendChild(item);
    const section=document.createElement('section');section.id='design';section.className='view tradenex-design';
    const paletteHtml=Object.entries(palettes).map(([id,p])=>`<button class="palette" data-preset="${id}"><div class="swatches" style="--p1:${p[1]};--p2:${p[2]};--p3:${p[3]}"></div><b>${p[0]}</b></button>`).join('');
    const effectsHtml=effects.map(([id,name])=>`<button class="effect" data-effect="${id}"><div class="preview ${id}"></div><div class="effect-name">${name}</div><div class="effect-note">Live Hintergrund</div></button>`).join('');
    section.innerHTML=`<div class="design-hero glass"><div><span class="eyebrow">TRADENEX DESIGN LAB</span><h2>Visual Command Center</h2><p style="color:var(--muted);margin:6px 0 0">Farbwelten, Hintergründe, Glow und Logo-Look – komplett getrennt von den Trading-Einstellungen.</p></div><div class="design-current"><span>AKTIVES THEME</span><strong id="themePresetName">TRADENEX Core</strong><small id="themeEffectName">Cyber Grid</small></div></div><div class="section-head"><div><span class="eyebrow">COLOR ARCHITECTURE</span><h2>Farbwelten</h2></div></div><div class="palette-grid">${paletteHtml}</div><div class="controls"><section class="glass control-card"><span class="eyebrow">CUSTOM PALETTE</span><h3>Eigene Identität</h3><div class="row"><span>Akzent</span><input id="themeAccent" type="color" value="${state.accent}"></div><div class="row"><span>Zweitfarbe</span><input id="themeAccent2" type="color" value="${state.accent2}"></div><div class="row"><span>Highlight</span><input id="themeAccent3" type="color" value="${state.accent3}"></div><div class="row"><span>Glow</span><div><input id="themeGlow" type="range" min="0" max="30" value="${state.glow}"><div id="themeGlowValue" class="value">${state.glow}%</div></div></div><div class="row"><span>Glass / Panel</span><div><input id="themePanel" type="range" min="55" max="98" value="${state.panel}"><div id="themePanelValue" class="value">${state.panel}%</div></div></div></section><section class="glass control-card"><span class="eyebrow">MOTION & LOGO</span><h3>Feintuning</h3><div class="row"><span>Animationen</span><input id="themeMotion" type="checkbox" ${state.motion?'checked':''}></div><div class="row"><span>Effekt-Stärke</span><div><input id="themeEffectStrength" type="range" min="0" max="100" value="${state.effectStrength}"><div id="themeEffectStrengthValue" class="value">${state.effectStrength}%</div></div></div><div class="row"><span>Logo-Helligkeit</span><div><input id="themeLogoBrightness" type="range" min="60" max="140" value="${state.logoBrightness}"><div id="themeLogoBrightnessValue" class="value">${state.logoBrightness}%</div></div></div><div class="row"><span>Logo-Glow</span><div><input id="themeLogoGlow" type="range" min="0" max="160" value="${state.logoGlow}"><div id="themeLogoGlowValue" class="value">${state.logoGlow}%</div></div></div></section></div><div class="section-head"><div><span class="eyebrow">AMBIENCE LIBRARY</span><h2>Interaktive Hintergründe</h2></div></div><div class="effects">${effectsHtml}</div>`;
    main.appendChild(section);
    $$('.palette',section).forEach(b=>b.addEventListener('click',()=>{const p=palettes[b.dataset.preset];state={...state,preset:b.dataset.preset,accent:p[1],accent2:p[2],accent3:p[3],metal:p[4]};save();apply()}));
    $('#themeAccent',section).addEventListener('input',e=>{state.preset='custom';state.accent=e.target.value;save();apply()});
    $('#themeAccent2',section).addEventListener('input',e=>{state.preset='custom';state.accent2=e.target.value;save();apply()});
    $('#themeAccent3',section).addEventListener('input',e=>{state.preset='custom';state.accent3=e.target.value;save();apply()});
    $('#themeGlow',section).addEventListener('input',e=>{state.glow=Number(e.target.value);save();apply()});
    $('#themePanel',section).addEventListener('input',e=>{state.panel=Number(e.target.value);save();apply()});
    $('#themeMotion',section).addEventListener('change',e=>{state.motion=e.target.checked;save();apply()});
    $('#themeEffectStrength',section).addEventListener('input',e=>{state.effectStrength=Number(e.target.value);save();apply()});
    $('#themeLogoBrightness',section).addEventListener('input',e=>{state.logoBrightness=Number(e.target.value);save();apply()});
    $('#themeLogoGlow',section).addEventListener('input',e=>{state.logoGlow=Number(e.target.value);save();apply()});
    $$('.effect',section).forEach(b=>b.addEventListener('click',()=>{state.background=b.dataset.effect;save();apply()}));
  }

  function init(){installStyle();mountBrand();mountBackground();mountDesign();apply();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();