/* 초록정원 · 정원 화면(V.garden)
   (index.html에서 분리한 파일 · 로드 순서 10/13 — 순서를 바꾸면 안 돼요) */

function toggleGardenProgress(){const box=$('garden-level-detail'),button=$('garden-level-toggle');if(!box)return;box.hidden=!box.hidden;button?.setAttribute('aria-expanded',String(!box.hidden))}
function closeGardenPlot(){S.gardenPlotOpen=false;R()}
function toggleGardenPlot(i){if(S.gardenPlotOpen&&S.sel===i){closeGardenPlot();return false}selP(i);return true}
function mountGardenPlotPanel(){
  const stage=document.querySelector('.garden-stage'),footer=document.querySelector('.garden-footer');
  if(!stage||!footer)return;
  stage.querySelector('.garden-carbon-info')?.remove();
  footer.querySelector('.garden-resources')?.remove();
  const panel=footer.querySelector('.garden-plot-panel');footer.remove();
  if(panel&&S.gardenPlotOpen){
    const shade=document.createElement('div');shade.className='garden-plot-shade';shade.setAttribute('aria-hidden','true');
    panel.classList.add('garden-plot-popover');stage.append(shade,panel);
  }
  W3.size?.();
}
function openGardenSeedPicker(){const seeds=Object.keys(S.seeds||{}).filter(t=>S.seeds[t]>0);op('<b>🌱 심을 씨앗 선택</b><div class="garden-seed-picker">'+seeds.map(t=>`<button class="sd" onclick="plant('${t}');cl()"><span>${TY[t]?.e||'🌱'}</span>${esc(TY[t]?.n||t)}<em>×${S.seeds[t]}</em></button>`).join('')+'</div>')}

V.garden=()=>{
  const k=S.sel,v=S.plots[k],ty=S.types[k]||'apple',pd=S.pd[k]||{},inv=Object.keys(S.seeds||{}).filter(t=>S.seeds[t]>0);
  const pg=S.progression||{level:1,total_completed:0,next_level:2,required_tier_label:'쉬움',progress_count:0,required_count:3,is_max_level:false};
  const name=esc(S.me?.username||'정원사'),avatar=esc(S.me?.profile_avatar_emoji||'🧑‍🌾'),pct=Math.min(100,pg.progress_count/Math.max(1,pg.required_count)*100);
  const nextSpecies=Object.values(TY).filter(x=>x.unlock_level===pg.next_level).slice(0,3);
  const unlockLine=nextSpecies.length?`다음 도감 해금 · ${nextSpecies.map(x=>esc(x.name)).join(' · ')}`:'';
  const levelDetails=pg.is_max_level?'최고 레벨이에요. 식물을 끝까지 키우고 수확해 성과를 쌓아 보세요.':`${pg.required_tier_label} 식물을 ${pg.required_count}그루 수확하면 레벨 ${pg.next_level}로 올라요. 현재 ${pg.progress_count}/${pg.required_count}그루를 채웠어요.`;
  const danger=S.co2!=null&&S.co2>S.co2max,co2Text=S.co2==null?'--':`${S.co2.toFixed(0)} ppm`;
  let panel='';
  if(!S.unlockedPlots.has(k))panel=`<div class="garden-plot-title"><b>🔒 오염된 땅</b><span>레벨 ${S.gardenLevel+1}에서 회복돼요</span></div>`;
  else if(v==null){
    const quick=inv.slice(0,3).map(t=>`<button class="garden-seed" onclick="plant('${t}')"><span>${TY[t]?.e||'🌱'}</span><b>${esc(TY[t]?.n||t)}</b><small>×${S.seeds[t]}</small></button>`).join('');
    panel=`<div class="garden-plot-title"><b>🪴 빈 땅</b><span>심을 씨앗을 골라요</span></div><div class="garden-empty-actions">${quick}${inv.length>3?'<button class="garden-seed-more" onclick="openGardenSeedPicker()">씨앗 더 보기</button>':''}${!inv.length?'<button class="garden-seed-more" onclick="go(\'shop\')">🌱 상점에서 씨앗 고르기</button>':''}</div>`;
  }else if(ty==='photo')panel=`<div class="garden-plot-title"><b>🖼️ 사진 식물</b><button class="garden-dig-btn" onclick="askDig()">뽑기</button></div><div class="garden-subline">사진을 분석해 심은 식물이에요.</div>`;
  else{
    const plant=TY[ty]||{},water=Math.round(pd.water||0),sun=Math.round(pd.sun||0),nutrients=Math.round(pd.nutrients||0),microbes=Math.round(pd.microbes||0),sunTarget=(plant.sun_need||3)*6;
    const condition=(label,value,target,amount)=>`<div class="garden-condition"><b>${label}</b><strong class="${value<target?'low':'good'}">${value}/100 · ${value<target?'보충 추천':'양호'}</strong><small>1회 사용 시 +${amount}</small></div>`;
    const conditionBox=`<div class="garden-condition-grid">${condition('💧 수분',water,30,50)}<div class="garden-condition"><b>☀️ 햇빛</b><strong class="${sun<sunTarget?'low':'good'}">${sun}/100 · ${sun<sunTarget?'필요량 미달':'양호'}</strong><small>필요 ${sunTarget} · 조각 1개 +50</small></div>${condition('🧪 영양',nutrients,30,40)}<div class="garden-condition"><b>🦠 미생물</b><strong class="${microbes<20?'low':'good'}">${microbes}/100 · ${microbes<20?'성장 도움 적음':'성장 도움 중'}</strong><small>미생물제 1개 +40</small></div></div>`;
    const heading=`<div class="garden-plot-title"><b>${pd.is_dead?'💀 시든':esc(plant.e||'🌱')+' '+esc(plant.n||ty)}${pd.is_dead?' '+esc(plant.n||'식물'):' · '+esc(sn(ty,v))}</b><button class="garden-dig-btn" onclick="askDig()">${pd.is_dead?'정리':'뽑기'}</button></div>`;
    panel=`${heading}${pd.is_dead?`<div class="garden-subline garden-warning">${esc(WARN[pd.death_reason]||'돌봄이 필요해요.')}</div>`:`<div class="bar garden-growth"><i style="width:${Math.min(100,(v+(pd.growth_progress||0))/4*100)}%"></i></div>${pd.stress>0?`<div class="garden-subline garden-warning">⚠️ ${esc(WARN[pd.stress_reason]||'식물이 스트레스를 받아요.')}</div>`:''}`}${conditionBox}${pd.is_dead?'':`<div class="garden-care-row"><button class="garden-care-btn" ${S.wd?'':'disabled'} onclick="careAct('water')">💧 물 ${S.wd}</button><button class="garden-care-btn" ${S.sl?'':'disabled'} onclick="careAct('sunlight')">☀️ 빛 ${S.sl}</button><button class="garden-care-btn" ${S.nutri?'':'disabled'} onclick="careAct('feed')">🧪 영양 ${S.nutri}</button><button class="garden-care-btn" ${S.mic?'':'disabled'} onclick="careAct('microbes')">🦠 미생물 ${S.mic}</button>${v>=4?'<button class="garden-harvest-btn" onclick="harvestPlant()">✨ 수확</button>':''}</div>`}`;
  }
  return `<div class="garden-layout"><aside id="garden-level-detail" class="garden-level-detail" hidden><b>🌿 다음 레벨 조건</b><span>${levelDetails}</span>${unlockLine?`<span>${unlockLine}</span>`:''}<span>레벨업하면 새 땅과 숲의 동식물이 돌아와요.</span></aside><section class="garden-stage"><div class="gb garden-scene" id="gbox"></div><button id="garden-level-toggle" class="garden-profile-chip" aria-expanded="false" onclick="toggleGardenProgress()"><span class="garden-avatar">${avatar}</span><span class="garden-profile-copy"><b>${name}</b><span>정원 레벨 ${pg.level}${pg.is_max_level?' · MAX':''}</span><i class="garden-level-track"><i style="width:${pg.is_max_level?100:pct}%"></i></i></span><span class="garden-level-value">${pg.is_max_level?'완료':`${pg.progress_count}/${pg.required_count}`}</span></button><button class="garden-style-btn" aria-label="정원 계절 변경" onclick="op(gardenThemePicker())">🎨</button><div class="garden-carbon-info">${S.co2Info?'<span class="garden-carbon-pop">게임 속 수치이며 실제 대기 측정값은 아니에요.</span>':''}<button class="garden-co2-chip ${danger?'danger':''}" onclick="S.co2Info=!S.co2Info;R()">🌫️ ${co2Text} ⓘ</button></div></section><footer class="garden-footer"><div class="garden-resources"><span>💧 ${S.wd}/${S.waterCap}</span><span>☀️ ${S.sl}</span><span>🧪 ${S.nutri}</span><span>🦠 ${S.mic}</span></div><section class="garden-plot-panel">${panel}</section></footer></div>`;
};
