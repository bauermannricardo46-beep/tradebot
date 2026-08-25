async function refreshExecution(){const r=await fetch('/notifications/execution');const e=await r.json();document.querySelector('#executionLabel').textContent=e.mode==='LIVE'?'LIVE MODE':'DEMO MODE';document.querySelector('#demoModeBtn').textContent=e.mode==='LIVE'?'Demo wählen':'Aktiv';document.querySelector('#liveModeBtn').textContent=e.mode==='LIVE'?'Aktiv':'Live wählen';document.querySelector('#liveStatus').textContent=e.mode==='LIVE'?'LIVE ausgewählt – Echtgeld-Execution bleibt gesperrt.':'DEMO aktiv – virtuelle Trades.'}
async function setExecution(mode){const r=await fetch('/notifications/execution',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode})});const d=await r.json();if(!r.ok)throw Error(d.detail||'Modusfehler');await refreshExecution()}
async function loadSettings(){const s=await (await fetch('/notifications/settings')).json();for(const [k,id] of Object.entries({scalp_enabled:'scalpEnabled',swing_enabled:'swingEnabled',new_setups:'newSetups',new_trades:'newTrades'})){const e=document.querySelector('#'+id);if(e)e.checked=!!s[k]}document.querySelector('#riskInput').value=(s.risk_per_trade*100).toFixed(2);document.querySelector('#dailyLossInput').value=(s.max_daily_loss*100).toFixed(2)}
async function saveSettings(){await fetch('/notifications/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scalp_enabled:document.querySelector('#scalpEnabled').checked,swing_enabled:document.querySelector('#swingEnabled').checked,new_setups:document.querySelector('#newSetups').checked,new_trades:document.querySelector('#newTrades').checked,risk_per_trade:Number(document.querySelector('#riskInput').value)/100,max_daily_loss:Number(document.querySelector('#dailyLossInput').value)/100})})}
async function loadHistoryTotals(){const s=await (await fetch('/notifications/history/summary')).json();document.querySelector('#historyProfit').textContent=money(s.gross_profit);document.querySelector('#historyLoss').textContent=money(s.gross_loss);document.querySelector('#historyNet').textContent=money(s.net_pnl);document.querySelector('#historyWinrate').textContent=s.trades?(s.win_rate.toFixed(1)+'%'):'—';document.querySelector('#historyCount').textContent=`${s.trades} Trades · ${s.wins} W / ${s.losses} L`}
async function loadHistoryRows(){const d=await (await fetch('/data/analyses?limit=50')).json();const g=document.querySelector('#historyGrid');g.innerHTML=d.items?.length?`<div class="scanner-list"><div class="scanner-row header"><span>SYMBOL</span><span>SEITE</span><span>MODE</span><span>PROB.</span><span>EV</span><span>STATUS</span><span>DATUM / UHRZEIT</span></div>${d.items.map(x=>`<div class="scanner-row"><strong>${x.symbol}</strong><span>${x.side}</span><span>${x.mode}</span><span>${(x.probability*100).toFixed(1)}%</span><span>${Number(x.expected_value_r).toFixed(2)}R</span><span>${x.model_version}</span><span>${new Date(x.analyzed_at).toLocaleString('de-DE')}</span></div>`).join('')}</div>`:'<div class="empty-state">Noch keine Analysen.</div>'}

function addAutoScanToggle(){
  if(document.querySelector('#tradenexAutoScan'))return;
  const btn=document.createElement('button');
  btn.id='tradenexAutoScan';
  btn.type='button';
  btn.title='Automatischen Live-Scan ein- oder ausschalten';
  btn.style.cssText='position:fixed;right:24px;top:74px;z-index:9999;border:1px solid rgba(94,225,255,.35);border-radius:12px;padding:10px 14px;background:rgba(9,15,30,.92);backdrop-filter:blur(14px);color:#dff9ff;font:600 12px/1 system-ui;box-shadow:0 8px 30px rgba(0,0,0,.28);cursor:pointer';
  const stored=localStorage.getItem('tradenex_auto_scan');
  let enabled=stored===null?true:stored==='1';
  let busy=false;
  let timer=null;
  const paint=()=>{btn.textContent=enabled?'⚡ AUTO SCAN · AN':'⏸ AUTO SCAN · AUS';btn.style.borderColor=enabled?'rgba(94,225,255,.65)':'rgba(255,90,130,.45)';btn.style.color=enabled?'#dff9ff':'#ffdbe5'};
  const tick=async()=>{
    if(!enabled||busy)return;
    busy=true;
    try{
      if(typeof window.scanAll==='function')await window.scanAll();
      if(typeof window.loadMarket==='function')await window.loadMarket();
      if(typeof window.loadPositions==='function')await window.loadPositions();
      if(typeof window.loadHealth==='function')await window.loadHealth();
    }catch{}
    finally{busy=false}
  };
  const start=()=>{if(timer)clearInterval(timer);timer=setInterval(tick,2000);tick()};
  const stop=()=>{if(timer)clearInterval(timer);timer=null};
  btn.onclick=()=>{enabled=!enabled;localStorage.setItem('tradenex_auto_scan',enabled?'1':'0');paint();enabled?start():stop()};
  paint();document.body.appendChild(btn);enabled?start():stop();
}

(function wire(){document.querySelector('#demoModeBtn')?.addEventListener('click',()=>setExecution('DEMO'));document.querySelector('#liveModeBtn')?.addEventListener('click',()=>setExecution('LIVE'));['scalpEnabled','swingEnabled','newSetups','newTrades','riskInput','dailyLossInput'].forEach(id=>document.querySelector('#'+id)?.addEventListener('change',saveSettings));document.querySelector('[data-view="history"]')?.addEventListener('click',()=>{loadHistoryTotals();loadHistoryRows()});loadSettings();refreshExecution();loadHistoryTotals();setInterval(refreshExecution,10000);addAutoScanToggle()})();