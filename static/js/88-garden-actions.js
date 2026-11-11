/* 초록정원 · 씨앗 심기·뽑기
   (index.html에서 분리한 파일 · 로드 순서 12/13 — 순서를 바꾸면 안 돼요) */

async function plant(t){const k=S.sel;if(S.plots[k]!=null)return;
try{const r=await api(`/api/garden/${k}/plant/`,{method:'POST',json:{seed_key:t}});applyGarden(r);S.seeds[t]=(S.seeds[t]||1)-1;T(TY[t].e+' '+TY[t].n+' 씨앗을 심었어요');R()}catch(e){T(e.message||'심기에 실패했어요')}}
function askDig(){op(`<b style="font-size:18px">이 식물을 뽑을까요?</b><p class="sub">뽑으면 다시 되돌릴 수 없어요.</p><button class="btn" onclick="dig()">뽑기</button><button class="btn" style="background:var(--line);color:var(--tx)" onclick="cl()">취소</button>`)}
async function dig(){const k=S.sel;try{const r=await api(`/api/garden/${k}/dig/`,{method:'POST'});delete S.tx[k];delete S.pc[k];applyGarden(r);cl();T('화분을 비웠어요');R()}catch(e){T(e.message||'실패했어요')}}
