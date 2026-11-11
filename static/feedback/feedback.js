'use strict';
function gardenSummary(){const p=S.progression;if(!p)return '';return '<div class="panel" style="margin:6px 0"><b>🌿 정원 레벨 '+p.level+' · 수확 '+p.total_completed+'그루</b><div class="sub">'+(p.is_max_level?'최고 레벨! 성과 도감에 수확 기록을 모아 보세요.':p.required_tier_label+' 식물 수확 '+p.progress_count+'/'+p.required_count+'그루 → 레벨 '+p.next_level)+'</div></div>';}
function harvestArchive(){const entries=(S.collection||[]).filter(x=>x.harvested_count>0);return '<div class="panel">'+(entries.length?entries.map(x=>{const m=TY[x.seed_type__key]||{};return '<div class="row2"><span>'+esc(m.emoji||'🌱')+' '+esc(m.name||x.seed_type__key)+'</span><b>'+x.harvested_count+'그루 수확</b></div>';}).join(''):'아직 수확 기록이 없어요. 성장 완료 식물의 ✨ 수확 버튼을 눌러 보세요.')+'</div>';}
let harvestBusy=false;
async function harvestPlant(){if(harvestBusy)return;harvestBusy=true;try{const d=await api('/api/garden/'+S.sel+'/harvest/',{method:'POST'});applyGarden(d);await loadSpecies();T(d.detail);bump();R();}catch(e){T(e.message||'수확하지 못했어요');}finally{harvestBusy=false;}}
function gardenThemePicker(){const owned=new Set(S.progression?.owned_themes||[]),items=[['spring','🌷','봄'],['summer','🌿','여름'],['autumn','🍁','가을'],['winter','❄️','겨울']];return '<b style="font-size:18px">🎨 정원 계절 변경</b><div class="season-choice-grid">'+items.map(([key,icon,name])=>'<button class="f '+(S.theme===key?'on':'')+'" onclick="setGardenTheme(\''+key+'\')">'+icon+' '+name+(owned.has(key)?'':' · 40P')+'</button>').join('')+'</div>';}
async function setGardenTheme(theme){try{const d=await api('/api/garden/style/',{json:{theme,action:'apply'}});applyGarden(d);T(d.detail);bump();R();if($('ov').classList.contains('show'))op(gardenThemePicker());}catch(e){T(e.message||'배경을 바꾸지 못했어요');}}
async function buyGardenTheme(theme){if(needLogin())return;try{const d=await api('/api/garden/style/',{json:{theme,action:'buy'}});applyGarden(d);T(d.detail);bump();R();}catch(e){T(e.message||'꾸미기를 구매하지 못했어요');}}
function learningHtml(card){if(!card)return '';return '<section class="panel" style="margin:12px 0"><b>🌏 '+esc(card.title)+'</b><p style="line-height:1.8">'+esc(card.text)+'</p><div class="sub">🌱 다음 작은 실천: '+esc(card.action)+'</div></section>';}
function showLearning(card){if(card)op(learningHtml(card)+'<button class="btn" onclick="cl()">확인했어요</button>');}
function appendQuizLearning(card){const el=$('qz');if(el&&card){const confirm=el.querySelector('.btn.y');if(confirm)confirm.insertAdjacentHTML('beforebegin',learningHtml(card));else el.insertAdjacentHTML('beforeend',learningHtml(card));}}
let weeklyLoading=false;
async function loadWeekly(){if(S.guest||weeklyLoading)return;weeklyLoading=true;const userId=S.me?.id;try{const d=await api('/api/missions/weekly/');if(S.guest||S.me?.id!==userId)return;S.weekly=d;if(S.tab==='mission')R();}catch(e){}finally{weeklyLoading=false;}}
function weeklyView(){const w=S.weekly;if(!w)return '<div class="panel sub">주간 목표를 불러오는 중이에요.</div>';return '<section class="panel"><b>📅 주간 목표</b><div class="sub" style="margin-top:8px">이번 주 일일 미션 '+w.completed+'/'+w.required+'개 완료</div><button class="btn" style="margin-top:10px" '+(!w.eligible||w.claimed?'disabled':'')+' onclick="claimWeekly()">'+(w.claimed?'이번 주 보상 완료':'두 목표 달성 보상 받기 · +'+w.reward+'P')+'</button></section>';}
async function claimWeekly(){try{const d=await api('/api/missions/weekly/',{method:'POST'});S.weekly=d;S.pt=d.points;T(d.detail);bump();R();}catch(e){T(e.message||'주간 보상을 받지 못했어요');}}
async function openFinalPractice(){try{const d=await api('/api/missions/final-practice/'),entry=d.entry||{};op(`<b style="font-size:18px">🌎 LEVEL 10 · 최종 실천 미션</b><p class="sub">계획하고 직접 실천한 뒤, 경험을 돌아봐요.</p><label class="sub" for="fp-plan">1. 계획하기</label><textarea id="fp-plan" class="fld" rows="2" maxlength="300" placeholder="내가 실천할 생태계 보호 행동">${esc(entry.planned_action||'')}</textarea><label class="sub" for="fp-action">2. 실천하기 · 실제로 한 내용을 적어 주세요</label><textarea id="fp-action" class="fld" rows="3" maxlength="500" placeholder="언제, 무엇을 실천했나요?">${esc(entry.action_taken||'')}</textarea><label class="sub" for="fp-reflection">3. 돌아보기 · 느낀 점</label><textarea id="fp-reflection" class="fld" rows="3" maxlength="800" placeholder="실천 후 알게 된 점이나 느낀 점을 적어 주세요">${esc(entry.reflection||'')}</textarea><button class="btn y" onclick="saveFinalPractice()">기록 저장하기</button>${entry.completed_at?`<div class="sub">마지막 저장 · ${esc(entry.completed_at.slice(0,10))}</div>`:''}`)}catch(e){T(e.message||'최종 미션을 불러오지 못했어요')}}
async function saveFinalPractice(){try{const d=await api('/api/missions/final-practice/',{method:'POST',json:{planned_action:$('fp-plan').value,action_taken:$('fp-action').value,reflection:$('fp-reflection').value}});T(d.detail);cl()}catch(e){T(e.message||'기록을 저장하지 못했어요')}}
function installFeedbackViews(){const previous=V.mission;V.mission=()=>S.guest?previous():'<h3>☀️ 일일 미션</h3>'+previous()+(S.gardenLevel>=10?'<section class="panel"><b>🌎 LEVEL 10 · 최종 실천 미션</b><div class="sub" style="margin-top:6px">생태계 보호 행동을 계획하고 실천한 뒤, 느낀 점을 기록해요.</div><button class="btn" style="margin-top:10px" onclick="openFinalPractice()">실천 미션 열기</button></section>':'')+(S.fl==='전체'?'<h3>📅 주간 미션</h3>'+weeklyView():'');}

function mountSeason(box){
  box.querySelector('.season-particles')?.remove();
  if(S.tab!=='garden'&&!(S.tab==='home'&&!S.guest))return;
  const layer=document.createElement('div');
  layer.className='season-particles';
  layer.setAttribute('aria-hidden','true');
  layer.style.cssText='position:absolute;inset:0;overflow:hidden;pointer-events:none;z-index:0;';
  const icons={spring:['🌸','🌸','🌺'],summer:['🍃','🌿'],autumn:['🍁','🍂'],winter:['❄','❅','❆']}[S.theme||'spring'];
  const height=Math.max(box.clientHeight,300), reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  for(let i=0;i<12;i++){
    const leaf=document.createElement('span');
    leaf.textContent=icons[i%icons.length];
    leaf.style.cssText=`position:absolute;top:-28px;left:${(i*37)%100}%;font-size:${12+i%3*3}px;line-height:1;filter:drop-shadow(0 1px 2px #0006);`;
    if(reduced){leaf.style.top=`${12+(i*19)%72}%`;leaf.style.opacity='.85'}
    else if(leaf.animate){
      const duration=7000+(i%6)*1000;
      leaf.animate([{transform:'translate3d(0,-24px,0) rotate(0deg)',opacity:0},{transform:`translate3d(${20+(i%5)*9}px,${height+60}px,0) rotate(220deg)`,opacity:.95}],{duration,delay:-((i*730)%duration),iterations:Infinity,easing:'linear'});
    }else{
      leaf.style.animation=`season-fall ${7+i%6}s linear ${-i*.73}s infinite`;
    }
    layer.appendChild(leaf);
  }
  box.appendChild(layer);
}
