/* 초록정원 · 로딩 화면(loadUp)과 앱 시작
   (index.html에서 분리한 파일 · 로드 순서 13/13 — 순서를 바꾸면 안 돼요) */

function loadUp(){const ld=$('ld'),x=ld.querySelector('canvas').getContext('2d'),bar=$('lb'),tx=$('lt'),tp=$('lp');
const C={g:'#3E9B4F',l:'#6CD07E',b:'#8B5A2B',p:'#FF8FB1',y:'#FFC94D',d:'#8B5E3C'},E='..........',D='dddddddddd';
const F=[[E,E,E,E,E,E,E,'....bb....',D,D],[E,E,E,E,E,'..ll..ll..','...llll...','....gg....',D,D],
[E,E,E,'..ll..ll..','...llll...','....gg....','.ll.gg.ll.','..lggggl..',D,D],
[E,'....pp....','...pyyp...','....pp....','....gg....','.ll.gg.ll.','..lggggl..','....gg....',D,D]];
const tips=['미션을 하면 식물이 자라요','도감을 채워 새 미션을 열어요','친구의 정원도 구경해요'];
const draw=s=>{x.clearRect(0,0,80,80);F[s].forEach((r,j)=>[...r].forEach((c,i)=>{if(c!='.'){x.fillStyle=C[c];x.fillRect(i*8,j*8,8,8)}}))};
let n=0;draw(0);tp.textContent=tips[0];
const t=setInterval(()=>{n++;if(n<=10)bar.children[n-1].className='on';draw(Math.min(3,n*4/10|0));tx.textContent='LOADING'+'.'.repeat(n%4);tp.textContent=tips[Math.min(2,n/4|0)];
if(n>=12){clearInterval(t);ld.classList.add('out');setTimeout(()=>{ld.remove();setTimeout(()=>{if(!S.attDone)att()},1400)},450)}},220)}
$('ld').classList.add('out');
installFeedbackViews();
if(localStorage.getItem('eg_access')){bootstrap()}else{enterGuest()}
