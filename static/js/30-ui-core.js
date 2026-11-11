/* 초록정원 · 공통 화면 틀: 미션 카드, 홈/미션/게임 뷰(V), 렌더(R), 이동(go), 토스트, 시트(op/cl)
   (index.html에서 분리한 파일 · 로드 순서 4/13 — 순서를 바꾸면 안 돼요) */

/* ---- 서버 연동 끝 ---- */

const mc=m=>`<button class="mc ${m.completed?'dn':''}" style="--c:var(${CC[m.category]})" onclick="openM(${m.id})"><div class="ic">${m.emoji}</div><div><span class="tag">${CL[m.category]}${m.mission_type=='quiz'?' · 퀴즈':m.mission_type=='record'?' · 관찰기록':' · 사진'}${m.ai_assisted?' · AI 확인':''}</span><b>${m.title}</b></div><span class="rw">${m.completed?'완료 ✓':'⭐ +'+m.reward_points}</span></button>`;
function weeklyMissionCard(){const w=S.weekly;if(!w)return '<section class="panel weekly-goal"><b>📅 주간 미션</b><div class="sub">이번 주 목표를 불러오는 중이에요…</div></section>';const pct=Math.min(100,Math.round((w.completed||0)/Math.max(1,w.required||7)*100)),label=w.claimed?'이번 주 보상 완료':w.eligible?'⭐ +80P 받기':'목표 달성 후 +80P 받기';return `<section class="panel weekly-goal"><b>📅 주간 미션</b><div class="sub">이번 주 완료 ${w.completed}/${w.required}</div><div class="bar"><i style="width:${pct}%"></i></div><div class="sub">주간 목표를 달성하면 별 포인트 +80P</div><button class="btn y" ${w.eligible&&!w.claimed?'':'disabled'} onclick="claimWeeklyGoal()">${label}</button></section>`}
const V={
home(){if(S.guest)return guestHome();return `<div class="home-layout"><section class="scene home-scene"><div class="gb home" id="gbox"></div></section>
<div class="tri home-actions"><button onclick="go('garden')">🌱<span>정원으로 가기</span></button><button onclick="go('mission')">🗺️<span>미션하러 가기</span></button></div>
<section class="home-mission"><h3>오늘의 미션 <small>🌿</small></h3>${S.missions[0]?mc(S.missions[0]):'<div class="sub">미션을 불러오는 중이에요…</div>'}</section></div>`},
mission(){const l=S.missions.filter(m=>S.fl=='전체'||CL[m.category]==S.fl);
return `${S.fl=='전체'?weeklyMissionCard():''}<div class="chipsrow">${['전체','관찰','미생물','생물'].map(f=>`<button class="f ${S.fl==f?'on':''}" onclick="S.fl='${f}';R()">${f}</button>`).join('')}</div>${l.map(mc).join('')}`},
game(){const g=[['🗑️','쓰레기 피하기','🌱 식물이 쓰레기를 피해요'],['🧱','테트리스','줄을 채워 지워요']];
return `${backMy()}<div class="sub" style="margin:4px 2px 10px">미션을 완료하면 티켓을 받아요 · 보유 🎟️ ${S.tk}</div>${g.map(([e,n,d])=>`<div class="gm"><div class="ic">${e}</div><div><b>${n}</b><span class="sub">${d}</span></div><button class="btn y" onclick="play('${n}')">🎟️ 1 플레이</button></div>`).join('')}<div class="gm soon"><div class="ic">🐞</div><b>같은 생물 찾기</b><span class="sub" style="margin-left:auto">준비 중</span></div>`}};
function R(){const g=S.guest;
  [['pt','⭐ '+S.pt],['tk','🎟️ '+S.tk],['ab',S.attDone?'✅ 출석':'🎁 출석']].forEach(([id,t])=>{const e=$(id);e.textContent=g?'':t;e.style.display=g?'none':''});
  $('ab').classList.toggle('new',!S.attDone);$('scr').innerHTML=V[S.tab]();$('scr').classList.toggle('home-screen',!g&&S.tab=='home');$('scr').classList.toggle('garden-screen',!g&&S.tab=='garden');W3.mount&&W3.mount();if(S.tab=='garden'&&typeof mountGardenPlotPanel=='function')mountGardenPlotPanel();
  const tabs=g?[['home','🏡','홈'],['mission','🗺️','미션'],['encyclopedia','📚','도감'],['shop','🛍️','상점'],['my','👤','로그인']]:[['home','🏡','홈'],['garden','🌱','정원'],['mission','🗺️','미션'],['encyclopedia','📚','도감'],['shop','🛍️','상점'],['my','👤','마이']];
  $('nav').innerHTML=tabs.map(([k,e,n])=>`<button class="${S.tab==k||(k=='my'&&(S.tab=='friends'||S.tab=='game'))?'on':''}" onclick="go('${k}')"><span>${e}</span>${n}</button>`).join('')}
const backMy=()=>'<button class="f" style="margin-bottom:10px" onclick="go(\'my\')">← 마이페이지</button>';
const rewardStr=m=>`⭐ ${m.reward_points} + 🎟️ ${m.reward_tickets}${m.reward_water?` + 💧 ${m.reward_water}`:''}${m.reward_sunlight?` + ☀️ ${m.reward_sunlight}`:''}`;
const sn=(ty,v)=>(TY[ty]&&TY[ty].kind=='flower'?['씨앗','새싹','줄기','봉오리','개화']:SN)[v];
function go(t){S.tab=t;S.vf=null;if(t!=='garden')S.gardenPlotOpen=false;R();$('scr').scrollTop=0;if(t=='home'||t=='mission')dayCheck();if(t=='mission')loadWeekly();if(t=='my'&&!S.guest&&S.myView=='gallery')loadPhotoGallery();if(t=='friends'&&!S.guest)loadFriends()}
function T(m){const t=$('toast');t.textContent=m;t.classList.add('show');clearTimeout(T.h);T.h=setTimeout(()=>t.classList.remove('show'),1600)}
function bump(){['pt','tk'].forEach(i=>{const e=$(i);e.classList.remove('bump');void e.offsetWidth;e.classList.add('bump')})}
function selP(i){if(!S.unlockedPlots.has(i))return T(`🔒 정원 레벨 ${S.gardenLevel+1}에서 열려요`);S.sel=i;S.gardenPlotOpen=true;R()}
function plant(){if(S.seed&&S.plots[S.sel]==null){S.seed--;S.plots[S.sel]=0;T('🌰 씨앗을 심었어요');R()}}
function buy(k,p){if(S.pt<p)return T('포인트가 부족해요');S.pt-=p;S[k]++;T('구매했어요');bump();R()}
function cl(){stopG();S.photoMissionId=null;$('ov').classList.remove('show')}
function op(h){$('sh').innerHTML='<i class="grab"></i>'+h;$('ov').classList.add('show')}
