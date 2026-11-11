/* 초록정원 · 친구 목록·응원, 식물 종 정보(TY)
   (index.html에서 분리한 파일 · 로드 순서 9/13 — 순서를 바꾸면 안 돼요) */

S.vf=null;
let FR=[];
const pc=f=>f.plots.filter((x,i)=>x!=null&&i<49).length;
const myCode=()=>S.me&&S.me.friend_code?S.me.friend_code:'친구 코드 로딩 중';
const curPlots=()=>S.tab=='friends'&&S.vf!=null?FR[S.vf].plots:S.plots;
async function loadFriends(){try{FR=await api('/api/auth/friends/');R()}catch(e){T(e.message||'친구 목록을 불러오지 못했어요')}}
V.my=()=>S.guest?authView():profileView();
V.friends=()=>{if(S.vf!=null){const f=FR[S.vf];return `<button class="f" onclick="S.vf=null;R()">← 친구 목록</button><div class="sub" style="margin:10px 2px">${esc(f.n)}의 정원 · 레벨 ${f.garden_level||1} · 식물 ${pc(f)}/${f.plot_count||9}</div><div class="gb tall" id="gbox"></div><button class="btn y" ${f.ch?'disabled':''} onclick="cheer()">${f.ch?'오늘 응원 완료 ⭐':'💚 응원하기 (+5P)'}</button>`}
return `${backMy()}<div class="panel" style="margin:0 0 12px;display:flex;align-items:center;gap:10px"><div><div class="sub">내 친구 코드</div><b style="font-size:20px;font-family:Jua,sans-serif">${esc(myCode())}</b></div><button class="f" style="margin-left:auto" onclick="copyC()">복사</button></div>
<div class="add"><input id="fi" placeholder="친구 코드 입력" maxlength="12"><button class="btn y" onclick="addF()">친구 추가</button></div>
<h3>내 친구 ${FR.length}명</h3>${FR.length?FR.map((f,i)=>`<button class="mc" style="--c:var(--g)" onclick="S.vf=${i};R()"><div class="ic">${f.e||'🌱'}</div><div><b>${esc(f.n)}</b><span class="sub">🌱 식물 ${pc(f)}종</span></div><span class="rw">정원 구경 ›</span></button>`).join(''):'<div class="sub">아직 친구가 없어요. 친구 코드를 입력해 추가해 보세요.</div>'}`};
async function addF(){const c=$('fi').value.trim().toUpperCase();if(!c)return T('친구 코드를 입력해 주세요');try{const d=await api('/api/auth/friends/',{json:{friend_code:c}});S.pt=d.points;await loadFriends();bump();T(d.detail)}catch(e){T(e.message||'친구를 추가하지 못했어요')}}
async function cheer(){const f=FR[S.vf];if(!f||f.ch)return;try{const d=await api(`/api/auth/friends/${f.id}/cheer/`,{method:'POST'});S.pt=d.points;f.ch=true;bump();T('⭐ 응원했어요! 나와 친구 모두 +5P');R()}catch(e){T(e.message||'응원 포인트를 적립하지 못했어요')}}
function copyC(){try{navigator.clipboard.writeText(myCode())}catch(e){}T('친구 코드를 복사했어요')}
const TY={};  // 씨앗 종류 정보는 서버(/api/garden/species/)에서 불러와요
const curTypes=()=>S.tab=='friends'&&S.vf!=null?FR[S.vf].types||[]:S.types;
