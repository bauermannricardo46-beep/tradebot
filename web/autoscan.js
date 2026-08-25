const AUTO_SCAN_KEY='tradenex_auto_scan';
const qs=(s)=>document.querySelector(s);

function setAutoScanButton(enabled){
  const b=qs('#autoScanBtn');
  if(!b) return;
  b.textContent=enabled?'⚡ AUTO SCAN · AN':'⏸ AUTO SCAN · AUS';
  b.className=enabled?'primary-btn':'ghost-btn';
  b.dataset.enabled=String(enabled);
  b.title=enabled?'Automatische Analyse aktiv':'Automatische Analyse pausiert';
}

async function refreshAutoScan(){
  try{
    const r=await fetch('/demo/status',{cache:'no-store'});
    const s=await r.json();
    const enabled=!!s.enabled;
    localStorage.setItem(AUTO_SCAN_KEY,String(enabled));
    setAutoScanButton(enabled);
  }catch{
    const saved=localStorage.getItem(AUTO_SCAN_KEY);
    setAutoScanButton(saved!=='false');
  }
}

async function toggleAutoScan(){
  const b=qs('#autoScanBtn');
  const current=b?.dataset.enabled==='true';
  try{
    const r=await fetch('/demo/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:!current})});
    const d=await r.json();
    if(!r.ok) throw Error(d.detail||'Auto Scan konnte nicht geändert werden');
    localStorage.setItem(AUTO_SCAN_KEY,String(!!d.enabled));
    setAutoScanButton(!!d.enabled);
    const t=qs('#toast'); if(t){t.textContent=d.enabled?'⚡ Auto Scan aktiviert':'⏸ Auto Scan pausiert';t.classList.add('show');setTimeout(()=>t.classList.remove('show'),1800)}
  }catch(e){
    const t=qs('#toast'); if(t){t.textContent=e.message;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2200)}
  }
}

function initAutoScan(){
  if(!qs('#autoScanBtn')) return;
  qs('#autoScanBtn').onclick=toggleAutoScan;
  refreshAutoScan();
  setInterval(refreshAutoScan,2000);
}

document.addEventListener('DOMContentLoaded',initAutoScan);