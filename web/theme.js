(() => {
  const KEY = 'tradenex_visual_settings_v2';
  const palettes = {
    tradenex: { name:'TRADENEX', accent:'#55e7ff', accent2:'#8c5cff', accent3:'#ff39d1', metal:'#c8d0df', bg:'#02040a' },
    cyan: { name:'Cyber Cyan', accent:'#55e7ff', accent2:'#4f7cff', accent3:'#8c5cff', metal:'#d8f9ff', bg:'#02040a' },
    silver: { name:'Silver / Black', accent:'#d7e2ef', accent2:'#8fa3bd', accent3:'#f4f7fb', metal:'#ffffff', bg:'#030507' },
    gold: { name:'Gold / Black', accent:'#f5c451', accent2:'#d89b2b', accent3:'#fff1a8', metal:'#f9e3a1', bg:'#050402' },
    platinum: { name:'Platinum / Black', accent:'#e7eef7', accent2:'#9eb0c2', accent3:'#ffffff', metal:'#d6e0ea', bg:'#040607' },
    blackgold: { name:'Black / Gold', accent:'#ffca4a', accent2:'#a87514', accent3:'#ffe6a3', metal:'#f0cf72', bg:'#050403' },
    blackplatinum: { name:'Black / Platinum', accent:'#eaf0f6', accent2:'#aab8c6', accent3:'#ffffff', metal:'#d9e2ea', bg:'#020304' },
    obsidian: { name:'Obsidian / Ruby', accent:'#ff5c78', accent2:'#a92749', accent3:'#ff9daf', metal:'#e7c5cc', bg:'#050205' },
    emerald: { name:'Emerald / Black', accent:'#42f5a7', accent2:'#159b6a', accent3:'#a9ffd8', metal:'#c9f7e4', bg:'#020604' },
  };
  const defaults = { preset:'tradenex', accent:'#55e7ff', accent2:'#8c5cff', accent3:'#ff39d1', metal:'#c8d0df', background:'grid', motion:true, glow:12, panel:88, logoBrightness:100, logoGlow:100, effectStrength:65 };
  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => [...root.querySelectorAll(s)];
  const load = () => { try { return { ...defaults, ...(JSON.parse(localStorage.getItem(KEY) || '{}')) }; } catch { return { ...defaults }; } };
  const save = s => localStorage.setItem(KEY, JSON.stringify(s));
  let state = load();

  function hexToRgb(hex){ const h=hex.replace('#',''); return {r:parseInt(h.slice(0,2),16),g:parseInt(h.slice(2,4),16),b:parseInt(h.slice(4,6),16)}; }
  function rgba(hex,a){ const {r,g,b}=hexToRgb(hex); return `rgba(${r},${g},${b},${a})`; }
  function applyPalette(id){ const p=palettes[id] || palettes.tradenex; state.preset=id; state.accent=p.accent; state.accent2=p.accent2; state.accent3=p.accent3; state.metal=p.metal; save(state); apply(); }

  function ensureAmbience(){
    let layer=$('#tradenexAmbience');
    if(!layer){
      layer=document.createElement('div');
      layer.id='tradenexAmbience';
      layer.innerHTML='<div class="ambience-grid"></div><div class="ambience-noise"></div><div class="ambience-glow a1"></div><div class="ambience-glow a2"></div><div class="ambience-particles"></div><div class="ambience-scanlines"></div>';
      document.body.prepend(layer);
    }
    return layer;
  }

  function apply(){
    const root=document.documentElement.style;
    root.setProperty('--theme-accent',state.accent);
    root.setProperty('--theme-accent-2',state.accent2);
    root.setProperty('--theme-accent-3',state.accent3);
    root.setProperty('--theme-metal',state.metal);
    root.setProperty('--theme-bg',state.background==='clean'?'#03050b':(palettes[state.preset]?.bg || '#03050b'));
    root.setProperty('--theme-glow',String(state.glow/100));
    root.setProperty('--theme-panel-alpha',String(state.panel/100));
    root.setProperty('--theme-effect-strength',String(state.effectStrength/100));
    root.setProperty('--cyan',state.accent);
    root.setProperty('--blue',state.accent2);
    root.setProperty('--violet',state.accent2);
    root.setProperty('--magenta',state.accent3);
    root.setProperty('--silver',state.metal);
    document.body.dataset.themePreset=state.preset;
    document.body.dataset.ambience=state.background;
    document.body.classList.toggle('motion-off',!state.motion);
    const layer=ensureAmbience(); layer.className=''; layer.id='tradenexAmbience'; layer.dataset.effect=state.background; layer.dataset.motion=String(state.motion);
    const logo=document.querySelector('.brand-mark img');
    if(logo) logo.style.filter=`brightness(${state.logoBrightness/100}) drop-shadow(0 0 ${Math.max(4,24*state.logoGlow/100)}px ${rgba(state.accent,state.logoGlow/100*.28)})`;
    const fields={themePreset:state.preset,themeAccent:state.accent,themeBackground:state.background,themeMotion:state.motion,themeGlow:state.glow,themePanel:state.panel,themeEffectStrength:state.effectStrength,themeLogoBrightness:state.logoBrightness,themeLogoGlow:state.logoGlow};
    Object.entries(fields).forEach(([id,val])=>{const el=$('#'+id);if(!el)return;if(el.type==='checkbox')el.checked=!!val;else el.value=val;});
    const vals={themeGlowValue:state.glow+'%',themePanelValue:state.panel+'%',themeEffectStrengthValue:state.effectStrength+'%',themeLogoBrightnessValue:state.logoBrightness+'%',themeLogoGlowValue:state.logoGlow+'%',themePresetName:palettes[state.preset]?.name||'TRADENEX'};
    Object.entries(vals).forEach(([id,val])=>{const el=$('#'+id);if(el)el.textContent=val;});
  }

  function mountLogo(){
    const mark=document.querySelector('.brand-mark'); if(!mark)return;
    mark.classList.add('theme-logo');
    mark.innerHTML='<img src="./tradenex-logo.png" alt="TRADENEX" onerror="this.style.display=\'none\';this.parentElement.textContent=\'NX\'">';
    const brand=document.querySelector('.brand'); if(brand){const strong=brand.querySelector('strong');if(strong)strong.textContent='TRADENEX';const span=brand.querySelector('span');if(span)span.textContent='AI TRADING INTELLIGENCE';}
  }

  function mountSettings(){
    const root=$('#settings'); if(!root||$('#tradenexVisualLab'))return;
    const wrap=document.createElement('div'); wrap.id='tradenexVisualLab'; wrap.className='tradenex-theme-grid';
    const buttons=Object.entries(palettes).map(([id,p])=>`<button class="theme-preset-card" data-preset="${id}"><i style="--p1:${p.accent};--p2:${p.accent2};--p3:${p.accent3}"></i><b>${p.name}</b></button>`).join('');
    wrap.innerHTML=`<section class="glass tradenex-theme-card theme-full"><span class="eyebrow">TRADENEX VISUAL LAB</span><h3>Farbwelten & Identität</h3><p class="theme-help">Komplette UI-Paletten statt nur einer einzelnen Akzentfarbe.</p><div class="theme-control"><span>Preset</span><div><select id="themePreset"><option value="">Custom</option>${Object.entries(palettes).map(([id,p])=>`<option value="${id}">${p.name}</option>`).join('')}</select><div id="themePresetName" class="theme-range-value"></div></div></div><div class="theme-preset-grid">${buttons}</div><div class="theme-control"><span>Custom Akzent</span><input id="themeAccent" type="color" value="${state.accent}"></div><div class="theme-control"><span>Custom Zweitfarbe</span><input id="themeAccent2" type="color" value="${state.accent2}"></div><div class="theme-control"><span>Custom Highlight</span><input id="themeAccent3" type="color" value="${state.accent3}"></div></section><section class="glass tradenex-theme-card"><span class="eyebrow">AMBIENCE ENGINE</span><h3>Interaktive Hintergründe</h3><p class="theme-help">Die Effekte laufen auf einer eigenen Layer hinter der gesamten Oberfläche.</p><div class="theme-control"><span>Style</span><select id="themeBackground"><option value="grid">Cyber Grid</option><option value="matrix">Matrix Flow</option><option value="particles">Floating Particles</option><option value="aurora">Aurora Field</option><option value="scanlines">Scanline Field</option><option value="stars">Starfield</option><option value="clean">Clean</option><option value="off">Static Dark</option></select></div><div class="theme-control"><span>Animationen</span><input id="themeMotion" type="checkbox" ${state.motion?'checked':''}></div><div class="theme-control"><span>Effekt-Stärke</span><div><input id="themeEffectStrength" type="range" min="0" max="100" value="${state.effectStrength}"><div id="themeEffectStrengthValue" class="theme-range-value">${state.effectStrength}%</div></div></div><div class="theme-control"><span>Glow-Stärke</span><div><input id="themeGlow" type="range" min="0" max="30" value="${state.glow}"><div id="themeGlowValue" class="theme-range-value">${state.glow}%</div></div></div><div class="theme-control"><span>Glass / Panel</span><div><input id="themePanel" type="range" min="55" max="98" value="${state.panel}"><div id="themePanelValue" class="theme-range-value">${state.panel}%</div></div></div></section><section class="glass tradenex-theme-card"><span class="eyebrow">LOGO IDENTITY</span><h3>TRADENEX Bull</h3><p class="theme-help">Dasselbe Logo wie Splash und EXE-Branding.</p><div class="theme-control"><span>Logo-Helligkeit</span><div><input id="themeLogoBrightness" type="range" min="60" max="140" value="${state.logoBrightness}"><div id="themeLogoBrightnessValue" class="theme-range-value">${state.logoBrightness}%</div></div></div><div class="theme-control"><span>Logo-Glow</span><div><input id="themeLogoGlow" type="range" min="0" max="160" value="${state.logoGlow}"><div id="themeLogoGlowValue" class="theme-range-value">${state.logoGlow}%</div></div></div></section>`;
    root.appendChild(wrap);
    $('#themePreset').addEventListener('change',e=>{if(e.target.value)applyPalette(e.target.value);else{state.preset='custom';save(state);apply();}});
    $$('.theme-preset-card').forEach(b=>b.addEventListener('click',()=>applyPalette(b.dataset.preset)));
    $('#themeAccent').addEventListener('input',e=>{state.preset='custom';state.accent=e.target.value;save(state);apply()});
    $('#themeAccent2').addEventListener('input',e=>{state.preset='custom';state.accent2=e.target.value;save(state);apply()});
    $('#themeAccent3').addEventListener('input',e=>{state.preset='custom';state.accent3=e.target.value;save(state);apply()});
    $('#themeBackground').addEventListener('change',e=>{state.background=e.target.value;save(state);apply()});
    $('#themeMotion').addEventListener('change',e=>{state.motion=e.target.checked;save(state);apply()});
    $('#themeEffectStrength').addEventListener('input',e=>{state.effectStrength=Number(e.target.value);save(state);apply()});
    $('#themeGlow').addEventListener('input',e=>{state.glow=Number(e.target.value);save(state);apply()});
    $('#themePanel').addEventListener('input',e=>{state.panel=Number(e.target.value);save(state);apply()});
    $('#themeLogoBrightness').addEventListener('input',e=>{state.logoBrightness=Number(e.target.value);save(state);apply()});
    $('#themeLogoGlow').addEventListener('input',e=>{state.logoGlow=Number(e.target.value);save(state);apply()});
  }

  function loadCss(){if(document.querySelector('link[data-tradenex-theme]'))return;const link=document.createElement('link');link.rel='stylesheet';link.href='./theme.css?v=2';link.dataset.tradenexTheme='1';document.head.appendChild(link)}
  function init(){loadCss();mountLogo();mountSettings();apply()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true}); else init();
})();