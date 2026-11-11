/* 초록정원 · 서버 통신(api), 로그인·회원가입·마이페이지·게스트 화면
   (index.html에서 분리한 파일 · 로드 순서 2/13 — 순서를 바꾸면 안 돼요) */


/* ---- 서버 연동: 여기서부터가 index.html을 실제 Django API에 연결하는 부분 ---- */
async function api(path,opts={}){
  opts=Object.assign({},opts);opts.headers=Object.assign({},opts.headers);
  const ac=localStorage.getItem('eg_access');if(ac)opts.headers['Authorization']='Bearer '+ac;
  if(opts.json!==undefined){opts.method=opts.method||'POST';opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(opts.json)}
  let r=await fetch(path,opts);
  if(r.status==401){
    const rf=localStorage.getItem('eg_refresh');
    if(rf){const rr=await fetch('/api/auth/login/refresh/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({refresh:rf})});
      if(rr.ok){const d=await rr.json();localStorage.setItem('eg_access',d.access);opts.headers['Authorization']='Bearer '+d.access;r=await fetch(path,opts)}
      else{logout();throw new Error('로그인이 만료됐어요. 다시 로그인해주세요')}}
  }
  if(!r.ok){let m='요청에 실패했어요';try{const e=await r.json();m=e.detail||Object.values(e).flat()[0]||m}catch(_){}throw new Error(m)}
  const ct=r.headers.get('content-type')||'';return ct.includes('application/json')?r.json():null;
}
function logout(){if(Tutorial.active)finishTutorial(false);clearInterval(S.pollId);localStorage.removeItem('eg_access');localStorage.removeItem('eg_refresh');S.gallery=[];S.galleryLoaded=false;S.galleryLoading=false;S.tab='my';S.authMode='login';enterGuest()}
const esc=x=>String(x==null?'':x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function loadSpecies(){const sp=await api('/api/garden/species/');sp.forEach(x=>{TY[x.key]=Object.assign({n:x.name,e:x.emoji,p:x.price,d:x.description},x)})}
const today=()=>new Date().toLocaleDateString('sv-SE');
async function dayCheck(){if(S.missionDay===today())return;S.missionDay=today();try{S.missions=await api('/api/missions/');if(!S.guest){const me=await api('/api/auth/me/');S.att=me.attendance_streak;S.attDone=me.attendance_claimed_today}R()}catch(e){}}
async function enterGuest(mode){S.guest=true;S.me=null;S.weekly=null;S.collection=[];S.speciesInfo={};delete document.documentElement.dataset.gardenTheme;if(mode)S.authMode=mode;
  try{S.missions=await api('/api/missions/');S.missionDay=today();S.shopItems=await api('/api/shop/');await loadSpecies()}catch(e){}
  if(!['home','mission','shop','encyclopedia','my'].includes(S.tab))S.tab='home';go(S.tab)}
const needLogin=()=>{if(!S.guest)return false;cl();T('로그인이 필요해요');S.authMode='login';go('my');return true};
const SIDO=['서울','부산','대구','인천','광주','대전','울산','세종','경기','강원','충북','충남','전북','전남','경북','경남','제주'],SCHOOL={elementary:'초등학생',middle:'중학생',high:'고등학생'};
const SEASONS={spring:'🌷 봄',summer:'🌿 여름',autumn:'🍁 가을',winter:'❄️ 겨울'};
const sidoOpts=sel=>'<option value="">시·도 선택</option>'+SIDO.map(x=>`<option ${x==sel?'selected':''}>${x}</option>`).join('');
const schoolOpts=sel=>'<option value="">학교급 (선택)</option>'+Object.entries(SCHOOL).map(([k,v])=>`<option value="${k}" ${k==sel?'selected':''}>${v}</option>`).join('');
const seasonOpts=sel=>'<option value="">좋아하는 계절 선택</option>'+Object.entries(SEASONS).map(([k,v])=>`<option value="${k}" ${k==sel?'selected':''}>${v}</option>`).join('');
const errMsg=e=>{if(e?.detail)return e.detail;const L={username:'아이디',password:'비밀번호',consent:'동의',favorite_season:'좋아하는 계절',region_sido:'사는 지역'},k=Object.keys(e||{})[0],v=k?[].concat(e[k])[0]:'요청을 처리하지 못했어요';return (L[k]?L[k]+': ':'')+v};
async function authError(r,fallback){const ct=r.headers.get('content-type')||'';if(ct.includes('application/json')){try{return errMsg(await r.json())}catch(_){}}if(r.status>=500)return '회원가입 서버 오류예요. PyCharm 터미널에서 python manage.py migrate를 실행한 뒤 서버를 다시 시작해 주세요.';return fallback}
const guestHome=()=>`<section class="scene"><div class="in" style="text-align:center;padding:26px 16px"><div style="font-size:54px">🌱</div><b style="font-size:19px">초록정원에 오신 걸 환영해요</b><div class="sub" style="margin:8px 0 4px">미션을 하고 나만의 정원을 가꾸며<br>육상생태계를 배워요</div><button class="btn" onclick="S.authMode='login';go('my')">로그인</button><button class="btn y" onclick="S.authMode='register';go('my')">회원가입</button></div></section><h3>미션 미리보기</h3>${S.missions.slice(0,3).map(mc).join('')}`;
function authView(){const reg=S.authMode=='register';
  return `<div class="panel" style="margin-top:6px"><b style="font-size:20px">🌿 ${reg?'회원가입':'로그인'}</b><div style="margin-top:14px"><input id="au" class="fld" placeholder="아이디" autocomplete="username" autocapitalize="none" autocorrect="off" spellcheck="false"><input id="ap" class="fld" placeholder="비밀번호" type="password" autocomplete="${reg?'new-password':'current-password'}">${reg?`<input id="ap2" class="fld" placeholder="비밀번호 확인" type="password" autocomplete="new-password"><select id="al" class="fld">${schoolOpts('')}</select><select id="afs" class="fld">${seasonOpts('')}</select><label style="display:flex;gap:8px;align-items:flex-start;font-size:13px;margin:4px 2px 8px"><input id="ac" type="checkbox" style="margin-top:3px"><span>선택한 학교급 정보와 AI 확인을 통과한 미션 사진을 내 개인 갤러리에 저장하는 데 동의해요.<br><span class="sub">만 14세 미만은 보호자와 함께 확인해 주세요.</span></span></label>`:''}</div><button class="btn" onclick="submitAuth('${S.authMode}')">${reg?'가입하고 시작하기':'로그인'}</button><button class="btn" style="background:var(--line);color:var(--tx);margin-top:8px" onclick="S.authMode='${reg?'login':'register'}';R()">${reg?'이미 계정이 있어요? 로그인':'계정이 없어요? 회원가입'}</button></div>`}
function photoGalleryView(){if(!S.galleryLoaded||S.galleryLoading)return '<div class="panel sub">사진을 불러오는 중이에요…</div>';if(!S.gallery.length)return '<div class="panel sub">아직 저장된 사진이 없어요. 사진 미션을 완료하면 여기에 모여요.</div>';return `<div class="photo-gallery" style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px">${S.gallery.map(p=>`<article class="panel" style="padding:6px;margin:0"><img src="${p.image}" alt="${esc(p.mission)} 사진" loading="lazy" style="width:100%;aspect-ratio:1;object-fit:cover;border-radius:10px"><div class="sub" style="margin:4px 1px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(p.date)} · ${esc(p.mission)}</div></article>`).join('')}</div>${S.galleryNext!==null?'<button class="btn" style="margin-top:10px" onclick="loadPhotoGallery(false)">더 보기</button>':''}`}
function profileEditView(m){const titles=m.profile_title_options||[],avatars=m.profile_avatar_options||[];return `<button class="f" onclick="S.myView='profile';R()">← 마이페이지</button><h3>✏️ 회원 정보 수정</h3><div class="panel"><label class="sub" for="profile-username">아이디</label><input id="profile-username" class="fld" maxlength="150" value="${esc(m.username||'')}"><label class="sub" for="profile-season">좋아하는 계절</label><select id="profile-season" class="fld">${Object.entries(SEASONS).map(([key,label])=>`<option value="${key}" ${key===m.favorite_season?'selected':''}>${label}</option>`).join('')}</select><label class="sub" for="profile-title">칭호</label><select id="profile-title" class="fld">${titles.map(x=>`<option value="${esc(x.title)}" ${x.title===m.profile_title?'selected':''} ${x.unlocked?'':'disabled'}>${esc(x.title)}${x.unlocked?'':' · 레벨 '+x.unlock_level+' 해금'}</option>`).join('')}</select><label class="sub" for="profile-avatar">프로필 이미지</label><select id="profile-avatar" class="fld">${avatars.map(x=>`<option value="${esc(x.key)}" ${x.key===m.profile_avatar?'selected':''} ${x.unlocked?'':'disabled'}>${x.emoji} ${esc(x.name)}${x.unlocked?'':' · 레벨 '+x.unlock_level+' 해금'}</option>`).join('')}</select><div class="sub">정원 레벨이 오르면 새로운 칭호와 숲 동물 이미지가 열려요.</div><button class="btn y" onclick="saveProfile()">변경 사항 저장</button></div>`}
function profileView(){const m=S.me||{};if(S.myView=='gallery')return `<button class="f" onclick="S.myView='profile';R()">← 마이페이지</button><h3>📷 내 사진 갤러리</h3>${photoGalleryView()}`;if(S.myView=='edit-profile')return profileEditView(m);return `<div class="panel" style="margin-top:6px"><div style="display:flex;align-items:center;gap:12px"><div class="ic" style="--c:var(--g);width:56px;height:56px;font-size:34px">${esc(m.profile_avatar_emoji||'🧑‍🌾')}</div><div style="flex:1;min-width:0"><b style="font-size:18px">${esc(m.username)}</b><div class="sub">${esc(m.profile_title||'초록정원 탐험가')}</div></div><button class="f" aria-label="회원 정보 수정" title="회원 정보 수정" onclick="S.myView='edit-profile';R()">✏️</button></div></div>
<h3>나의 정보</h3><div class="panel" style="margin-top:0"><div class="row2"><span class="sub">🤝 친구 코드</span><b>${esc(m.friend_code||'-')}</b></div><div class="row2" style="margin-top:8px"><span class="sub">📅 가입일</span><b>${esc((m.date_joined||'').slice(0,10))}</b></div><div class="row2" style="margin-top:8px"><span class="sub">🌦️ 좋아하는 계절</span><b>${esc(SEASONS[m.favorite_season]||'🌷 봄')}</b></div><div class="row2" style="margin-top:8px"><span class="sub">🌿 정원 레벨</span><b>${S.gardenLevel}</b></div></div>
<button class="btn" style="margin-top:12px" onclick="S.myView='gallery';S.galleryLoaded=false;go('my')">📷 사진 갤러리</button>
<h3>이용 안내</h3><button class="btn" style="background:var(--line);color:var(--tx)" onclick="startTutorial(false)">❔ 이용 방법 · 튜토리얼 다시 보기</button>
<h3>더 보기</h3><div class="tri" style="margin-top:0"><button onclick="go('friends')">👥<span>친구</span></button><button onclick="go('game')">🎮<span>미니게임</span></button></div>
<button class="btn" style="background:var(--line);color:var(--tx);margin-top:14px" onclick="logout()">🚪 로그아웃</button>`}
async function saveProfile(){try{const d=await api('/api/auth/me/',{method:'PATCH',json:{username:$('profile-username').value.trim(),favorite_season:$('profile-season').value,profile_title:$('profile-title').value,profile_avatar:$('profile-avatar').value}});S.me=d;const garden=await api('/api/garden/');applyGarden(garden);S.myView='profile';R();T('회원 정보를 저장했어요. 선택한 계절은 꾸미기에서 무료로 이용할 수 있어요.')}catch(e){T(e.message||'회원 정보를 저장하지 못했어요')}}
async function submitAuth(mode){const v=id=>($(id)||{}).value||'',username=v('au').trim(),password=v('ap');
  if(!username||!password)return T('아이디/비밀번호를 입력해주세요');
  try{
    if(mode=='register'){
      if(password!==v('ap2'))return T('비밀번호가 서로 달라요');
      if(!v('afs'))return T('좋아하는 계절을 골라 주세요');
      if(!$('ac').checked)return T('개인정보 수집·이용에 동의해 주세요');
      const r=await fetch('/api/auth/register/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password,school_level:v('al'),favorite_season:v('afs'),consent:true})});
      if(!r.ok)throw new Error(await authError(r,'회원가입 요청을 처리하지 못했어요. 입력 정보를 확인해 주세요.'))}
    const r=await fetch('/api/auth/login/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})});
    if(!r.ok)throw new Error('아이디 또는 비밀번호가 올바르지 않아요');
    const d=await r.json();localStorage.setItem('eg_access',d.access);localStorage.setItem('eg_refresh',d.refresh);S.tab='home';await bootstrap()
  }catch(e){T(e.message)}}
