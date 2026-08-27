const $=s=>document.querySelector(s);
const money=v=>new Intl.NumberFormat('de-DE',{style:'currency',currency:'EUR',minimumFractionDigits:2,maximumFractionDigits:2}).format(Number(v||0));
const esc=v=>String(v??'').replace(/[&<>'\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','\"':'&quot;'}[c]));
async function json(url,options={}){const r=await fetch(url,{cache:'no-store',...options});if(!r.ok)throw Error(`${url}: ${r.status}`);return r.json()}

let lastMarketAt=0;
let lastMarket=[];
let scannerFilter='ALL';

function setAuto(enabled){const b=$('#autoScanBtn');if(!b)return;b.textContent=enabled?'⚡ AUTO SCAN · AN':'⏸ AUTO SCAN · AUS';b.className=enabled?'primary-btn':'ghost-btn';b.dataset.enabled=String(enabled)}

async function engines(){try{const s=await json('/notifications/settings');if(s.scalp_enabled&&s.swing_enabled)return;await json('/notifications/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...s,scalp_enabled:true,swing_enabled:true})})}catch{}}

function statusBar(){if($('#autoStatusBar'))return;const top=document.querySelector('.topbar');if(!top)return;const x=document.createElement('section');x.id='autoStatusBar';x.className='glass auto-status';x.innerHTML='<div><strong>🟢 AUTO TRADING AKTIV</strong><br><small>SCALP + SWING · Scanner · Auto-Execution · Position Monitoring</small></div><div class="status-right"><strong id="autoOpenCount">0 offene Trades</strong><br><small id="autoScanTime">Live-Daten werden überwacht</small></div>';top.after(x)}

function mark(positions,market){const prices=new Map((market||[]).map(x=>[x.symbol,Number(x.price)]));let u=0;const out=(positions||[]).map(p=>{const e=Number(p.entry||0),q=Number(p.quantity||0),c=prices.has(p.symbol)?prices.get(p.symbol):e,v=(p.side==='LONG'?(c-e):(e-c))*q;u+=v;return {...p,current_price:c,unrealized_pnl:v}});return {positions:out,unrealized:u}}

function renderPositions(items){const box=$('#positionsGrid');if(!box)return;box.innerHTML=items.length?items.map(p=>{const v=Number(p.unrealized_pnl||0);return `<article class="glass position-card"><div class="position-top"><strong>${esc(p.symbol)}</strong><span class="${p.side==='LONG'?'side-long':'side-short'}">${esc(p.side)} · ${esc(p.mode)}</span></div><div class="position-pnl">${Number(p.entry||0).toLocaleString('de-DE',{maximumFractionDigits:8})} → ${Number(p.current_price||p.entry||0).toLocaleString('de-DE',{maximumFractionDigits:8})}</div><div class="position-pnl ${v>=0?'positive':'negative'}">${v>=0?'+':''}${money(v)}</div><p style="color:var(--muted);font-size:11px">SL ${Number(p.stop_loss||0).toLocaleString('de-DE',{maximumFractionDigits:8)} · TP ${Number(p.tp2||p.tp1||0).toLocaleString('de-DE',{maximumFractionDigits:8)} · Trail ${Number(p.trailing_stop||0).toLocaleString('de-DE',{maximumFractionDigits:8)}</p></article>`}).join(''):'<div class="empty-state">Keine offenen Trades.</div>'}

function renderHistory(items,s){const box=$('#historyGrid');if(!box)return;const gp=$('#historyProfit'),gl=$('#historyLoss'),net=$('#historyNet'),wr=$('#historyWinrate'),cnt=$('#historyCount');if(gp)gp.textContent='+'+money(s.gross_profit);if(gl)gl.textContent=money(s.gross_loss);if(net)net.textContent=(Number(s.net_pnl)>=0?'+':'')+money(s.net_pnl);if(wr)wr.textContent=s.trades?Number(s.win_rate).toFixed(1)+'%':'—';if(cnt)cnt.textContent=`${s.trades||0} Trades · ${s.wins||0} W / ${s.losses||0} L`;const closed=(items||[]).filter(x=>x.status==='CLOSED');box.innerHTML=closed.length?`<div class="trade-history-list"><div class="trade-history-row header"><span>SYMBOL</span><span>SEITE</span><span>MODE</span><span>ENTRY</span><span>EXIT</span><span>BRUTTO</span><span>GEBÜHREN</span><span>NETTO-P&L</span><span>STATUS</span></div>${closed.map(x=>{const p=Number(x.pnl||0),fees=Number(x.total_fees||0);return `<div class="trade-history-row ${p>0?'trade-win':'trade-loss'}"><strong>${esc(x.symbol)}</strong><span>${esc(x.side)}</span><span>${esc(x.mode)}</span><span>${Number(x.entry||0).toLocaleString('de-DE',{maximumFractionDigits:8})}</span><span>${Number(x.exit_price||0).toLocaleString('de-DE',{maximumFractionDigits:8})}</span><span>${(Number(x.gross_pnl||0)>=0?'+':'')+money(x.gross_pnl||0)}</span><span class="fee-cell" title="Gesamtgebühren für Entry + Exit">${money(fees)}</span><strong class="pnl-cell">${p>=0?'+':''}${money(p)}</strong><span class="result-pill">${p>0?'WIN':'LOSS'}</span></div>`}).join('')}</div>`:'<div class="empty-state">Noch keine geschlossenen Demo-Trades.</div>'}

function filteredSetups(items){return (items||[]).filter(x=>scannerFilter==='ALL'||scannerFilter===x.side||scannerFilter===x.mode)}

function renderScanner(items){const list=filteredSetups(items);const box=$('#scannerTable');if(!box)return;box.innerHTML=list.length?'<div class="scanner-row header"><span>SYMBOL</span><span>SEITE</span><span>MODE</span><span>WAHRSCHEINLICHKEIT</span><span>ENTRY</span><span>STATUS</span></div>'+list.map(x=>`<div class="scanner-row"><strong>${esc(x.symbol)}</strong><span class="${x.side==='LONG'?'side-long':'side-short'}">${esc(x.side)}</span><span>${esc(x.mode)}</span><strong>${(Number(x.probability||0)*100).toFixed(1)}%</strong><span>${Number(x.entry||0).toLocaleString('de-DE',{maximumFractionDigits:8})}</span><span class="result-pill">AUTO</span></div>`).join(''):'<div class="empty-state">Aktuell keine handelbaren Chancen.</div>';if($('#scannerSummary'))$('#scannerSummary').textContent=`${list.length} qualifizierte Chancen · Filter ${scannerFilter}`}

function renderDashboardSetups(items){
  if(typeof state!=='undefined'){
    state.setups=items||[];
    if(typeof renderSetups==='function')renderSetups();
  }
}

function updateFeeLabels(){const cards=[...document.querySelectorAll('#settings .setting-card')];const card=cards.find(x=>x.textContent.includes('Hyperliquid Demo'));if(!card)return;const rows=card.querySelectorAll('.toggle-row b');if(rows[0])rows[0].textContent='0,015 %';if(rows[1])rows[1].textContent='0,045 %';if(rows[2])rows[2].textContent='TAKER · PERPS TIER 0'}

async function syncDemo(){
  try{
    const s=await json('/demo/status');
    setAuto(!!s.enabled);
    statusBar();
    if(s.enabled)await engines();

    const now=Date.now();
    if(now-lastMarketAt>2000){
      try{const m=await json('/market/overview');lastMarket=m.items||[];lastMarketAt=now}catch{}
    }

    const [p,t]=await Promise.all([json('/demo/positions'),json('/demo/trades?limit=100')]);
    const live=mark(p.items||[],lastMarket);
    const real=Number(s.net_pnl||0);
    const unreal=live.unrealized;
    const total=real+unreal;
    const open=Number(s.open_positions??live.positions.length);
    const setups=s.setups||[];

    if($('#equity'))$('#equity').textContent=money(Number(s.equity||s.budget||500)+unreal);
    if($('#pnl'))$('#pnl').innerHTML=`${total>=0?'+':''}${money(total)} <span>${total>=0?'+':''}${((Number(s.budget||500)?total/Number(s.budget||500):0)*100).toFixed(2)}%</span>`;
    if($('#dailyPnl'))$('#dailyPnl').textContent=money(total);
    if($('#openTrades'))$('#openTrades').textContent=open;
    if($('#autoOpenCount'))$('#autoOpenCount').textContent=`${open} offene Trades`;
    if($('#scalpSignals'))$('#scalpSignals').textContent=live.positions.filter(x=>x.mode==='SCALP').length;
    if($('#swingSignals'))$('#swingSignals').textContent=live.positions.filter(x=>x.mode==='SWING').length;
    if($('#setupCount'))$('#setupCount').textContent=setups.length;
    if($('#scanSummary'))$('#scanSummary').textContent=`${setups.length} Chancen · Scanner aktiv`;
    if($('#autoScanTime'))$('#autoScanTime').textContent=s.updated_at?`Letztes Update ${new Date(s.updated_at).toLocaleTimeString('de-DE')}`:'Scanner läuft…';
    renderPositions(live.positions);
    renderHistory(t.items||[],s);
    renderDashboardSetups(setups);
    renderScanner(setups);
    updateFeeLabels();
  }catch{}
}

async function refresh(){await syncDemo()}

async function toggle(){const b=$('#autoScanBtn'),on=b?.dataset.enabled==='true';try{const d=await json('/demo/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:!on})});setAuto(!!d.enabled);await syncDemo()}catch{}}

function styles(){if($('#tradenex-history-fix'))return;const s=document.createElement('style');s.id='tradenex-history-fix';s.textContent=`
.trade-history-list{width:100%;overflow-x:auto;padding:4px 0 8px}
.trade-history-row{display:grid!important;grid-template-columns:minmax(150px,1.25fr) minmax(75px,.7fr) minmax(80px,.7fr) minmax(135px,1.1fr) minmax(135px,1.1fr) minmax(105px,.9fr) minmax(105px,.9fr) minmax(125px,1.05fr) minmax(80px,.7fr)!important;gap:16px!important;align-items:center!important;padding:13px 16px!important;min-width:1180px!important;box-sizing:border-box!important;white-space:nowrap!important;font-size:13px!important;line-height:1.35!important}
.trade-history-row>span,.trade-history-row>strong{min-width:0!important;overflow:hidden!important;text-overflow:ellipsis!important}
.trade-history-row.header{color:var(--muted)!important;background:transparent!important;font-size:11px!important;letter-spacing:.08em!important;font-weight:700!important;border-bottom:1px solid var(--line)!important}
.trade-history-row.trade-win{background:rgba(66,245,167,.045)!important;border-left:3px solid var(--green)!important}
.trade-history-row.trade-loss{background:rgba(255,92,120,.045)!important;border-left:3px solid var(--red)!important}
.trade-history-row.trade-win .pnl-cell{color:var(--green)!important}.trade-history-row.trade-loss .pnl-cell{color:var(--red)!important}
.trade-history-row .pnl-cell{font-weight:900!important;font-size:14px!important}.trade-history-row .fee-cell{color:var(--muted)!important;font-variant-numeric:tabular-nums!important}.trade-history-row .result-pill{justify-self:start!important}
.trade-history-row.trade-win .result-pill{color:var(--green)!important;background:rgba(66,245,167,.08)!important}.trade-history-row.trade-loss .result-pill{color:var(--red)!important;background:rgba(255,92,120,.08)!important}
`;document.head.appendChild(s)}

function bindFilters(){document.querySelectorAll('.filter').forEach(b=>{b.onclick=()=>{document.querySelectorAll('.filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');scannerFilter=b.dataset.filter||'ALL';if(typeof state!=='undefined')state.filter=scannerFilter;syncDemo()}})}

function init(){styles();bindFilters();if($('#autoScanBtn'))$('#autoScanBtn').onclick=toggle;statusBar();updateFeeLabels();refresh();setInterval(refresh,1000)}
document.addEventListener('DOMContentLoaded',init);
