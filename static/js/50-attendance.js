/* 초록정원 · 출석 보상 팝업
   (index.html에서 분리한 파일 · 로드 순서 6/13 — 순서를 바꾸면 안 돼요) */

function att(){const r=[10,10,15,15,20,20,50];
op(`<b style="font-size:18px">🎁 출석 보상</b><div class="sub">월~일 주간 출석 ${S.att}/7일 · 빠진 날이 있어도 이어져요</div><div class="days">${r.map((x,i)=>`<div class="d ${i<S.att?'ok':i==S.att&&!S.attDone?'td':''}">${i+1}일<em>${i<S.att?'✓':i==6?'🎟️':'⭐'}</em>${x}</div>`).join('')}</div><button class="btn y" ${S.attDone?'disabled':''} onclick="claim()">${S.attDone?'오늘 출석 완료':'이번 주 보상 받기'}</button>`)}
async function claim(){try{const r=await api('/api/auth/attendance/',{method:'POST'});S.pt=r.points;S.tk=r.tickets;S.att=r.attendance_streak;S.attDone=r.attendance_claimed_today;cl();T(r.detail);bump();R()}catch(e){T(e.message||'출석에 실패했어요')}}