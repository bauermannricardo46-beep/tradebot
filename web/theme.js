(() => {
  const KEY = 'tradenex_visual_settings_v1';
  const defaults = {
    accent: '#55e7ff',
    background: 'grid',
    motion: true,
    glow: 12,
    panel: 88,
    logoBrightness: 100,
    logoGlow: 100,
  };

  const $ = (s, root = document) => root.querySelector(s);
  const load = () => {
    try { return { ...defaults, ...(JSON.parse(localStorage.getItem(KEY) || '{}')) }; }
    catch { return { ...defaults }; }
  };
  const save = s => localStorage.setItem(KEY, JSON.stringify(s));
  let state = load();

  function hexToHsl(hex) {
    const raw = hex.replace('#','');
    const r = parseInt(raw.slice(0,2),16)/255, g = parseInt(raw.slice(2,4),16)/255, b = parseInt(raw.slice(4,6),16)/255;
    const max = Math.max(r,g,b), min = Math.min(r,g,b); let h=0,s=0; const l=(max+min)/2;
    if (max !== min) {
      const d=max-min; s=l>0.5?d/(2-max-min):d/(max+min);
      switch(max){case r:h=(g-b)/d+(g<b?6:0);break;case g:h=(b-r)/d+2;break;default:h=(r-g)/d+4;}
      h/=6;
    }
    return [h*360,s*100,l*100];
  }
  const hsl = (h,s,l) => `hsl(${Math.round((h+360)%360)} ${Math.round(Math.max(0,Math.min(100,s)))}% ${Math.round(Math.max(0,Math.min(100,l)))}%)`;

  function apply() {
    const root = document.documentElement.style;
    const [h,s,l] = hexToHsl(state.accent);
    root.setProperty('--theme-accent', state.accent);
    root.setProperty('--theme-accent-2', hsl(h+55, Math.max(55,s), Math.min(72,l+6)));
    root.setProperty('--theme-accent-3', hsl(h-42, Math.max(52,s), Math.min(68,l+5)));
    root.setProperty('--theme-glow', String(state.glow/100));
    root.setProperty('--theme-panel-alpha', String(state.panel/100));
    document.body.classList.remove('theme-clean','theme-grid','theme-matrix','theme-particles','theme-aurora','theme-off');
    document.body.classList.add(`theme-${state.background}`);
    document.body.classList.toggle('motion-off', !state.motion);
    const logo = document.querySelector('.brand-mark img');
    if (logo) {
      logo.style.filter = `brightness(${state.logoBrightness/100}) drop-shadow(0 0 ${Math.max(6,18*state.logoGlow/100)}px color-mix(in srgb,var(--theme-accent) 35%,transparent))`;
    }
    const color = $('#themeAccent'); if (color) color.value = state.accent;
    const glow = $('#themeGlow'); if (glow) { glow.value = state.glow; const v=$('#themeGlowValue'); if(v)v.textContent=`${state.glow}%`; }
    const panel = $('#themePanel'); if (panel) { panel.value = state.panel; const v=$('#themePanelValue'); if(v)v.textContent=`${state.panel}%`; }
    const motion = $('#themeMotion'); if (motion) motion.checked = !!state.motion;
    const bg = $('#themeBackground'); if (bg) bg.value = state.background;
    const lb = $('#themeLogoBrightness'); if(lb){lb.value=state.logoBrightness;$('#themeLogoBrightnessValue').textContent=`${state.logoBrightness}%`;}
    const lg = $('#themeLogoGlow'); if(lg){lg.value=state.logoGlow;$('#themeLogoGlowValue').textContent=`${state.logoGlow}%`;}
    const label=$('#themeStateLabel'); if(label) label.textContent=state.motion?'LIVE VISUALS':'STATIC VISUALS';
  }

  function mountLogo() {
    const mark = document.querySelector('.brand-mark');
    if (!mark) return;
    mark.classList.add('theme-logo');
    mark.innerHTML = `<img src="./tradenex-logo.png" alt="TRADENEX" onerror="this.style.display='none';this.parentElement.textContent='NX'">`;
    const brand = document.querySelector('.brand');
    if (brand) {
      const strong = brand.querySelector('strong'); if (strong) strong.textContent='TRADENEX';
      const span = brand.querySelector('span'); if (span) span.textContent='AI TRADING INTELLIGENCE';
    }
  }

  function mountSettings() {
    const root = $('#settings');
    if (!root || $('#tradenexVisualLab')) return;
    const wrap = document.createElement('div');
    wrap.id = 'tradenexVisualLab';
    wrap.className = 'tradenex-theme-grid';
    wrap.innerHTML = `
      <section class="glass tradenex-theme-card">
        <span class="eyebrow">TRADENEX VISUAL LAB</span>
        <h3>Akzent & Glow</h3>
        <p class="theme-help">Passe die sichtbare TRADENEX-Identität live an. Die Trading-Engine wird dadurch nicht verändert.</p>
        <div class="theme-control"><span>Akzentfarbe</span><input id="themeAccent" type="color" value="${state.accent}"></div>
        <div class="theme-control"><span>Presets</span><div class="theme-presets">
          <button class="theme-swatch" data-accent="#55e7ff" style="background:#55e7ff;color:#55e7ff" title="TRADENEX Cyan"></button>
          <button class="theme-swatch" data-accent="#5d8bff" style="background:#5d8bff;color:#5d8bff" title="Electric Blue"></button>
          <button class="theme-swatch" data-accent="#8c5cff" style="background:#8c5cff;color:#8c5cff" title="Violet"></button>
          <button class="theme-swatch" data-accent="#ff39d1" style="background:#ff39d1;color:#ff39d1" title="Magenta"></button>
          <button class="theme-swatch" data-accent="#42f5a7" style="background:#42f5a7;color:#42f5a7" title="Emerald"></button>
          <button class="theme-swatch" data-accent="#ffb84d" style="background:#ffb84d;color:#ffb84d" title="Amber"></button>
        </div></div>
        <div class="theme-control"><span>Glow-Stärke</span><div><input id="themeGlow" type="range" min="0" max="30" step="1" value="${state.glow}"><div id="themeGlowValue" class="theme-range-value">${state.glow}%</div></div></div>
        <div class="theme-control"><span>Glass / Panel</span><div><input id="themePanel" type="range" min="55" max="98" step="1" value="${state.panel}"><div id="themePanelValue" class="theme-range-value">${state.panel}%</div></div></div>
      </section>
      <section class="glass tradenex-theme-card">
        <span class="eyebrow">AMBIENCE ENGINE</span>
        <h3>Interaktiver Hintergrund</h3>
        <p class="theme-help">Der Hintergrund läuft unabhängig vom Scanner und kann jederzeit geändert werden.</p>
        <div class="theme-control"><span>Style</span><select id="themeBackground"><option value="grid">Cyber Grid</option><option value="matrix">Matrix Flow</option><option value="particles">Floating Particles</option><option value="aurora">Aurora Field</option><option value="clean">Clean</option><option value="off">Static Dark</option></select></div>
        <div class="theme-control"><span>Animationen</span><input id="themeMotion" type="checkbox" ${state.motion?'checked':''}></div>
        <div class="theme-control"><span>Logo-Helligkeit</span><div><input id="themeLogoBrightness" type="range" min="60" max="140" step="1" value="${state.logoBrightness}"><div id="themeLogoBrightnessValue" class="theme-range-value">${state.logoBrightness}%</div></div></div>
        <div class="theme-control"><span>Logo-Glow</span><div><input id="themeLogoGlow" type="range" min="0" max="160" step="1" value="${state.logoGlow}"><div id="themeLogoGlowValue" class="theme-range-value">${state.logoGlow}%</div></div></div>
        <div class="theme-state"><span>Status</span><strong id="themeStateLabel">${state.motion?'LIVE VISUALS':'STATIC VISUALS'}</strong></div>
      </section>`;
    root.appendChild(wrap);

    $('#themeAccent').addEventListener('input',e=>{state.accent=e.target.value;save(state);apply();});
    $$('.theme-swatch').forEach(b=>b.addEventListener('click',()=>{state.accent=b.dataset.accent;save(state);apply();}));
    $('#themeBackground').addEventListener('change',e=>{state.background=e.target.value;save(state);apply();});
    $('#themeMotion').addEventListener('change',e=>{state.motion=e.target.checked;save(state);apply();});
    $('#themeGlow').addEventListener('input',e=>{state.glow=Number(e.target.value);save(state);apply();});
    $('#themePanel').addEventListener('input',e=>{state.panel=Number(e.target.value);save(state);apply();});
    $('#themeLogoBrightness').addEventListener('input',e=>{state.logoBrightness=Number(e.target.value);save(state);apply();});
    $('#themeLogoGlow').addEventListener('input',e=>{state.logoGlow=Number(e.target.value);save(state);apply();});
  }

  function loadCss() {
    if (document.querySelector('link[data-tradenex-theme]')) return;
    const link=document.createElement('link'); link.rel='stylesheet'; link.href='./theme.css'; link.dataset.tradenexTheme='1'; document.head.appendChild(link);
  }

  function init() {
    loadCss();
    mountLogo();
    mountSettings();
    apply();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init,{once:true}); else init();
})();