/* 초록정원 · 정원 상태 불러오기(applyGarden)·폴링·돌봄 액션·bootstrap
   (index.html에서 분리한 파일 · 로드 순서 3/13 — 순서를 바꾸면 안 돼요) */

function loadPhotoToCanvas(url){return new Promise(res=>{const im=new Image();im.onload=()=>{const c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;c.getContext('2d').drawImage(im,0,0);res(c)};im.onerror=()=>res(null);im.src=url})}
async function refreshSeeds(){const list=await api('/api/garden/seeds/');S.seeds={};list.forEach(x=>S.seeds[x.seed_type.key]=x.quantity)}
function applyGarden(d){S.collection=d.collection||[];if(d.points!=null)S.pt=d.points;S.theme=d.progression.theme||'spring';document.documentElement.dataset.gardenTheme=S.theme;const oldLevel=S.gardenLevel||1;S.gardenLevel=d.progression.level;S.progression=d.progression;S.plotCount=d.plot_count;S.gridSize=d.grid_size;S.unlockedPlots=new Set(d.plots.filter(p=>p.unlocked).map(p=>p.slot_index));if(S.gardenLevel>oldLevel){T(`🎉 정원 레벨 ${S.gardenLevel}! 새 땅과 상점 씨앗이 열렸어요`);api('/api/shop/').then(items=>S.shopItems=items).catch(()=>{});api('/api/auth/me/').then(profile=>{S.me=profile;if(S.tab==='my'||S.tab==='garden')R()}).catch(()=>{})};S.co2=d.co2_ppm;S.co2base=d.co2_baseline;S.co2max=d.co2_limit;S.nutri=d.nutrients;S.mic=d.microbes;S.wd=d.water_drops;S.sl=d.sunlight;S.waterCap=d.water_cap;S.waterNext=d.water_next_seconds;S.div=d.diversity;S.poll=d.pollination;S.pd={};
  d.plots.forEach(p=>{const k=p.slot_index;S.pd[k]=p;
    if(p.seed_type){S.plots[k]=p.growth_stage;S.types[k]=p.seed_type.key}
    else if(p.photo){S.plots[k]=p.growth_stage;S.types[k]='photo'}
    else{S.plots[k]=null;S.types[k]=undefined}})}
async function loadPhotos(plots){for(const p of plots){if(!p.seed_type&&p.photo&&p.pixel_photo&&!S.pc[p.slot_index]){const c=await loadPhotoToCanvas(p.pixel_photo);if(c)S.pc[p.slot_index]=c}}}
function startPolling(){clearInterval(S.pollId);S.pollId=setInterval(async()=>{
  if(S.guest||!localStorage.getItem('eg_access')||$('ov').classList.contains('show')||(S.tab!='garden'&&S.tab!='home'&&S.tab!='mission'))return;
  try{await dayCheck();const old=S.pd,d=await api('/api/garden/');applyGarden(d);await loadPhotos(d.plots);
    d.plots.forEach(p=>{const o=old[p.slot_index];if(o&&!o.is_dead&&p.is_dead)T('💀 '+(p.seed_type?p.seed_type.name:'나무')+'가 시들었어요')});R()}catch(e){}},30000)}
const WHY={sun:'☀️ 햇빛을 못 봐서 시들었어요. 주변에 다 자란 나무가 너무 많아 그늘이 졌어요.',water:'💧 물이 부족해서 시들었어요. 물을 자주 주세요.',nutrients:'🌱 영양분이 부족해서 시들었어요. 영양제나 미생물제를 주세요.',co2:'🌫️ 공기 중 탄소 농도가 너무 높아서 시들었어요. 나무를 더 키워 농도를 낮춰요.'};
const WARN={water:'💧 물이 말라가요!',nutrients:'🌱 영양분이 바닥나고 있어요!',sun:'☀️ 그늘이 져서 햇빛이 부족해요!',co2:'🌫️ 탄소 농도가 너무 높아요!'};
const stat=(ic,l,v)=>{v=v==null?0:v;const col=v<=15?'#D9534F':v<=35?'#F0AD4E':'var(--g)';return `<div style="display:flex;align-items:center;gap:8px;margin-top:6px"><span style="width:84px;font-size:13px;font-weight:700">${ic} ${l}</span><div class="bar" style="flex:1;margin:0"><i style="width:${v}%;background:${col}"></i></div><span class="sub" style="width:28px;text-align:right">${v}</span></div>`};
const co2Bar=()=>{if(S.co2==null)return'';const lo=350,hi=S.co2max+30,pct=Math.max(0,Math.min(100,(S.co2-lo)/(hi-lo)*100)),lim=(S.co2max-lo)/(hi-lo)*100,danger=S.co2>S.co2max,col=danger?'#C62828':S.co2>S.co2max-20?'#F0AD4E':'var(--g)',riskBg=`linear-gradient(90deg,var(--line) 0%,var(--line) ${lim}%,rgba(198,40,40,.25) ${lim}%,rgba(198,40,40,.25) 100%)`;return `<div class="panel co2 ${danger?'danger':''}" style="margin:0 0 10px"><div class="co2head"><b>🌫️ 정원 탄소 농도</b><span class="co2value">${S.co2.toFixed(1)} ppm</span><button class="co2info" aria-label="탄소 농도 설명" aria-expanded="${S.co2Info}" onclick="S.co2Info=!S.co2Info;R()">ⓘ</button></div><div class="co2track"><div class="bar" style="background:${riskBg}"><i style="width:${pct}%;background:${col}"></i><u style="left:${lim}%"></u></div></div>${danger?'<div class="co2alert" role="alert">⚠️ 위험</div>':''}${S.co2Info?`<div class="sub co2explain">게임 속 정원 상태를 계산한 값이며 실제 대기 측정값은 아니에요. 빨간 선(${S.co2max} ppm)을 넘으면 식물이 스트레스를 받아요.</div>`:''}</div>`};
async function careAct(kind){const k=S.sel;try{const r=await api(`/api/garden/${k}/${kind}/`,{method:'POST'});applyGarden(r);T(r.detail);bump();R()}catch(e){T(e.message||'실패했어요')}}
async function bootstrap(){
  try{
    S.guest=false;const me=await api('/api/auth/me/');S.me=me;S.att=me.attendance_streak;S.attDone=me.attendance_claimed_today;S.pt=me.points;S.tk=me.tickets;S.nutri=me.nutrients;S.mic=me.microbes;
    S.missions=await api('/api/missions/');S.missionDay=today();S.shopItems=await api('/api/shop/');await loadSpecies();await refreshSeeds();
    S.plots=Array(49).fill(null);S.types={};S.pc={};S.tx={};S.pd={};
    const gd=await api('/api/garden/');applyGarden(gd);await loadPhotos(gd.plots);
    go('home');startPolling();const tourShown=await maybeStartTutorial();if(!tourShown&&!S.attDone)setTimeout(()=>{if(!Tutorial.active&&!S.guest)att()},800)
  }catch(e){T(e.message);enterGuest('login')}
}
