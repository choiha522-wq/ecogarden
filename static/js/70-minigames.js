/* 초록정원 · 미니게임(똥피하기·테트리스)과 키 입력
   (index.html에서 분리한 파일 · 로드 순서 8/13 — 순서를 바꾸면 안 돼요) */

const stopG=()=>{if(G){cancelAnimationFrame(G.raf);G=null}};
const press=k=>{K[k]=1;G&&G.act(k)};
const KM={ArrowLeft:'l',ArrowRight:'r',ArrowDown:'d',ArrowUp:'u'};
addEventListener('keydown',e=>{const m=KM[e.key];if(m&&G){e.preventDefault();press(m)}});
addEventListener('keyup',e=>{const m=KM[e.key];if(m)K[m]=0});
function run(me,tick){const lp=()=>{if(G!==me)return;tick();if(G===me)me.raf=requestAnimationFrame(lp)};lp()}
async function fin(s,k){stopG();let r=0;try{const d=await api('/api/auth/mini-game/finish/',{json:{game_round_id:S.gameRoundId,score:s,game:k=='d'?'dodge':'tetris'}});S.pt=d.points;r=d.earned;S.gameRoundId=null}catch(e){T(e.message||'게임 보상을 받지 못했어요')}bump();R();op(`<b style="font-size:20px">🎮 게임 끝!</b><p>점수 ${s}점 → ⭐ +${r}</p><button class="btn y" onclick="play('${k=='d'?'쓰레기 피하기':'테트리스'}')">🎟️ 1 다시 하기</button><button class="btn" style="background:var(--line);color:var(--tx)" onclick="cl()">닫기</button>`)}
function dodge(c){const x=c.getContext('2d'),W=240,H=300;let px=106,os=[],sc=0,t=0;const me=G={raf:0,act(){}};
c.onpointermove=e=>{const b=c.getBoundingClientRect();px=(e.clientX-b.left)/b.width*W-14};
run(me,()=>{if(K.l)px-=4;if(K.r)px+=4;px=Math.max(0,Math.min(W-28,px));
if(++t%Math.max(12,38-sc)==0)os.push({x:Math.random()*(W-22),y:-22,v:2.2+Math.random()+sc/50});
os.forEach(o=>o.y+=o.v);
if(os.some(o=>o.y+22>252&&o.y<276&&o.x+22>px+2&&o.x<px+26))return fin(sc,'d');
os=os.filter(o=>o.y<H||!++sc);
x.fillStyle='#DFF1F8';x.fillRect(0,0,W,H);x.fillStyle='#4FB068';x.fillRect(0,276,W,24);
x.font='22px serif';os.forEach(o=>x.fillText('🗑️',o.x,o.y+20));x.font='28px serif';x.fillText('🌱',px,276);
x.fillStyle='#23402F';x.font='bold 14px sans-serif';x.fillText('점수 '+sc,8,18)})}
const PC=[[[1,1,1,1]],[[1,1],[1,1]],[[0,1,0],[1,1,1]],[[1,0,0],[1,1,1]],[[0,0,1],[1,1,1]],[[0,1,1],[1,1,0]],[[1,1,0],[0,1,1]]],PL=['#7CC4E8','#FFC94D','#9B7FD1','#4C8FE0','#F08A4B','#4CAF7D','#E8655F'];
function tetris(c){const x=c.getContext('2d'),C=10,N=16,Z=18;let b=Array.from({length:N},()=>Array(C).fill(0)),sc=0,t=0,cur;const me=G={raf:0};
const hit=(m,px,py)=>m.some((r,j)=>r.some((v,i)=>v&&(px+i<0||px+i>=C||py+j>=N||b[py+j][px+i])));
const nw=()=>{const i=Math.random()*7|0;cur={m:PC[i],c:PL[i],x:3,y:0};if(hit(cur.m,3,0))fin(sc,'t')};
const lock=()=>{cur.m.forEach((r,j)=>r.forEach((v,i)=>v&&(b[cur.y+j][cur.x+i]=cur.c)));const nb=b.filter(r=>!r.every(v=>v)),n=N-nb.length;while(nb.length<N)nb.unshift(Array(C).fill(0));b=nb;sc+=[0,10,25,40,60][n];nw()};
me.act=k=>{if(k=='l'&&!hit(cur.m,cur.x-1,cur.y))cur.x--;else if(k=='r'&&!hit(cur.m,cur.x+1,cur.y))cur.x++;
else if(k=='u'){const m=cur.m[0].map((_,i)=>cur.m.map(r=>r[i]).reverse());if(!hit(m,cur.x,cur.y))cur.m=m}
else if(k=='d'){if(!hit(cur.m,cur.x,cur.y+1))cur.y++;else lock()}};
nw();run(me,()=>{if(++t%28==0)me.act('d');if(G!==me)return;
x.fillStyle='#DFF1F8';x.fillRect(0,0,C*Z,N*Z);const d=(i,j,col)=>{x.fillStyle=col;x.fillRect(i*Z+1,j*Z+1,Z-2,Z-2)};
b.forEach((r,j)=>r.forEach((v,i)=>v&&d(i,j,v)));cur.m.forEach((r,j)=>r.forEach((v,i)=>v&&d(cur.x+i,cur.y+j,cur.c)));
x.fillStyle='#23402F';x.font='bold 13px sans-serif';x.fillText('점수 '+sc,6,14)})}
async function play(n){if(S.tk<1){cl();return T('티켓이 없어요. 미션을 완료해 보세요')}
try{const d=await api('/api/auth/consume-ticket/',{method:'POST'});S.tk=d.tickets;S.gameRoundId=d.game_round_id}catch(e){return T(e.message)}
bump();R();const d2=n=='쓰레기 피하기',bt=(k,l)=>`<button onpointerdown="press('${k}')" onpointerup="K.${k}=0" onpointerleave="K.${k}=0">${l}</button>`;
op(`<b style="font-size:18px">${d2?'🗑️ 쓰레기 피하기':'🧱 테트리스'}</b> <span class="sub">${d2?'좌우로 움직여 피해요':'줄을 채우면 사라져요'}</span><canvas id="gc" class="gcv" width="${d2?240:180}" height="${d2?300:288}" style="${d2?'':'width:200px'}"></canvas><div class="ctl">${bt('l','◀')}${d2?'':bt('u','↻')+bt('d','▼')}${bt('r','▶')}</div>`);
(d2?dodge:tetris)($('gc'))}