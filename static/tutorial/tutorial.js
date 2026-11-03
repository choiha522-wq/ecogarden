'use strict';
const Tutorial={active:false,index:0,returnTab:'home',focus:null,target:null,observer:null,frame:0,timer:0};
const tutorialSteps=[
 ['home','garden','정원 버튼을 눌러 보세요','실제 버튼을 누르면 정원으로 이동해요. 식물을 돌보고, 다 자란 식물을 수확하면 20P와 수확 기록을 얻어요.'],
 ['garden','mission','미션으로 이동해 보세요','미션 버튼을 눌러 환경 실천을 둘러보세요. 미션 후 생태 지식을 읽고, 주간 미션 7개와 미션 보상 150P를 달성하면 80P를 받아요.'],
 ['mission','shop','상점을 열어 보세요','상점 버튼을 누르세요. 씨앗은 정원 레벨로 해금돼요. 이 안내에서는 구매하거나 포인트를 사용하지 않아요.'],
 ['shop','encyclopedia','식물 도감을 열어 보세요','도감 버튼을 누르세요. 레벨 1 식물은 기본 공개되고, 나머지는 수집하면 상세 정보가 열려요.'],
 ['encyclopedia','my','마이페이지로 이동해 보세요','마이페이지 버튼을 누르세요. 수확 성과와 친구 코드, 튜토리얼 다시 보기를 확인할 수 있어요.'],
 ['my','friends','친구 버튼을 눌러 보세요','마이페이지 안의 친구 버튼을 누르세요. 친구를 추가하거나 응원하는 동작은 지금 실행하지 않아요.'],
 ['friends','my','마이페이지로 돌아가세요','강조된 마이페이지 버튼을 누르면 다음으로 미니게임 메뉴를 찾아볼게요.'],
 ['my','game','미니게임 메뉴를 열어 보세요','미니게임 버튼을 누르세요. 쓰레기 피하기와 테트리스 안내를 볼 수 있어요. 게임 시작이나 티켓 사용은 하지 않아요.'],
 ['game','my','마이페이지로 돌아오면 완료예요','마이페이지에서 「이용 방법 · 튜토리얼 다시 보기」를 누르면 언제든 다시 시작할 수 있어요. 그 외에는 자동으로 다시 뜨지 않아요.']
];
async function maybeStartTutorial(){try{const r=await api('/api/auth/tutorial/start/',{method:'POST'});if(r.show_tutorial){startTutorial(true);return true;}}catch(e){T('이용 안내를 불러오지 못했어요. 마이페이지에서 다시 볼 수 있어요.');}return false;}
function startTutorial(automatic){
 if(S.guest||Tutorial.active)return;
 Tutorial.active=true;Tutorial.index=0;Tutorial.returnTab=automatic?'home':S.tab;Tutorial.focus=document.activeElement;
 if($('ov').classList.contains('show'))cl();
 const layer=document.createElement('div');layer.id='tutorial-layer';
 layer.innerHTML='<div class="tutorial-shade" id="tutorial-shade-top"></div><div class="tutorial-shade" id="tutorial-shade-left"></div><div class="tutorial-shade" id="tutorial-shade-right"></div><div class="tutorial-shade" id="tutorial-shade-bottom"></div><div id="tutorial-ring"></div><section class="tutorial-card" role="dialog" aria-label="버튼을 누르며 진행하는 이용 안내" tabindex="-1"><div class="tutorial-top"><span id="tutorial-count"></span><button type="button" onclick="finishTutorial()" aria-label="튜토리얼 닫기">✕</button></div><div class="tutorial-progress"><i id="tutorial-progress"></i></div><div aria-live="polite"><h2 id="tutorial-title"></h2><p id="tutorial-text"></p><b id="tutorial-hint">아래 강조된 실제 버튼을 눌러 주세요.</b></div><div class="tutorial-actions"><button id="tutorial-prev" onclick="moveTutorial(-1)">이전</button><button id="tutorial-retry" onclick="go(tutorialSteps[Tutorial.index][0]);tutorialLocate(true)" hidden>버튼 다시 찾기</button></div><button class="tutorial-skip" onclick="finishTutorial()">안내 종료 · 자동으로 다시 표시하지 않기</button></section>';
 document.body.appendChild(layer);document.addEventListener('click',tutorialClick,true);document.addEventListener('keydown',tutorialKeys,true);window.addEventListener('resize',tutorialSchedule);document.addEventListener('scroll',tutorialSchedule,true);
 Tutorial.observer=new MutationObserver(tutorialSchedule);Tutorial.observer.observe($('scr'),{childList:true,subtree:true});
 go('home');drawTutorial();
}
function drawTutorial(){const s=tutorialSteps[Tutorial.index];$('tutorial-count').textContent=(Tutorial.index+1)+' / '+tutorialSteps.length;$('tutorial-title').textContent=s[2];$('tutorial-text').textContent=s[3];$('tutorial-progress').style.width=((Tutorial.index+1)/tutorialSteps.length*100)+'%';$('tutorial-prev').disabled=Tutorial.index===0;tutorialLocate(true);}
function tutorialSchedule(){if(!Tutorial.active||Tutorial.frame)return;Tutorial.frame=requestAnimationFrame(()=>{Tutorial.frame=0;tutorialLocate(false);});}
function tutorialLocate(scroll){
 if(!Tutorial.active)return;
 const step=tutorialSteps[Tutorial.index],selector='button[onclick="go(\''+step[1]+'\')"]';
 const candidates=[...document.querySelectorAll(selector)];
 Tutorial.target=candidates.find(e=>e.getClientRects().length&&e.closest(step[0]==='my'?'#scr':'#nav'))||candidates.find(e=>e.getClientRects().length);
 const card=document.querySelector('.tutorial-card'),ring=$('tutorial-ring');
 if(!Tutorial.target){ring.hidden=true;$('tutorial-retry').hidden=false;$('tutorial-hint').textContent='화면이 바뀌었어요. 버튼 다시 찾기를 눌러 주세요.';tutorialShade(0,0,0,0);card.style.top='20px';card.style.bottom='auto';return;}
 $('tutorial-retry').hidden=true;$('tutorial-hint').textContent='빛나는 실제 버튼을 눌러 다음으로 진행하세요.';ring.hidden=false;
 if(scroll)Tutorial.target.scrollIntoView({block:'nearest',inline:'nearest',behavior:'instant'});
 const r=Tutorial.target.getBoundingClientRect(),w=window.innerWidth,h=window.innerHeight;
 const x=Math.max(0,r.left-5),y=Math.max(0,r.top-5),right=Math.min(w,r.right+5),bottom=Math.min(h,r.bottom+5);
 Object.assign(ring.style,{left:x+'px',top:y+'px',width:(right-x)+'px',height:(bottom-y)+'px'});tutorialShade(x,y,right,bottom);
 card.style.top='auto';card.style.bottom='auto';card.style.maxHeight=Math.max(110,Math.max(y,h-bottom)-24)+'px';
 if(y>=h-bottom)card.style.bottom=(h-y+12)+'px';else card.style.top=(bottom+12)+'px';
}
function tutorialShade(x,y,right,bottom){const w=innerWidth,h=innerHeight;const boxes={top:[0,0,w,y],left:[0,y,x,bottom-y],right:[right,y,w-right,bottom-y],bottom:[0,bottom,w,h-bottom]};for(const [k,b] of Object.entries(boxes))Object.assign($('tutorial-shade-'+k).style,{left:b[0]+'px',top:b[1]+'px',width:b[2]+'px',height:b[3]+'px'});}
function tutorialClick(e){
 if(!Tutorial.active||e.target.closest('.tutorial-card'))return;
 if(Tutorial.target&&Tutorial.target.contains(e.target)){
  if(Tutorial.timer){e.preventDefault();e.stopImmediatePropagation();return;}
  Tutorial.timer=setTimeout(()=>{Tutorial.timer=0;if(!Tutorial.active)return;if(S.tab!==tutorialSteps[Tutorial.index][1]){tutorialLocate(false);return;}moveTutorial(1);},80);return;
 }
 e.preventDefault();e.stopImmediatePropagation();
}
function moveTutorial(delta){if(!Tutorial.active)return;const n=Tutorial.index+delta;if(n>=tutorialSteps.length){finishTutorial(false);T('이용 안내를 마쳤어요. 마이페이지에서 다시 볼 수 있어요.');return;}Tutorial.index=Math.max(0,n);if(delta<0)go(tutorialSteps[Tutorial.index][0]);drawTutorial();if(Tutorial.target)Tutorial.target.focus();}
function finishTutorial(restore=true){if(!Tutorial.active)return;Tutorial.active=false;clearTimeout(Tutorial.timer);Tutorial.timer=0;cancelAnimationFrame(Tutorial.frame);Tutorial.frame=0;if(Tutorial.observer)Tutorial.observer.disconnect();document.removeEventListener('click',tutorialClick,true);document.removeEventListener('keydown',tutorialKeys,true);window.removeEventListener('resize',tutorialSchedule);document.removeEventListener('scroll',tutorialSchedule,true);$('tutorial-layer')?.remove();Tutorial.target=null;if(restore){go(Tutorial.returnTab);if(Tutorial.focus?.isConnected)Tutorial.focus.focus();}}
function tutorialKeys(e){if(!Tutorial.active)return;if(e.key==='Escape'){e.preventDefault();finishTutorial();return;}if(e.key==='Tab'){const items=[Tutorial.target,...document.querySelectorAll('#tutorial-layer button:not([disabled]):not([hidden])')].filter(e=>e&&e.getClientRects().length);const i=items.indexOf(document.activeElement);e.preventDefault();items[(i+(e.shiftKey?-1:1)+items.length)%items.length]?.focus();}else if((e.key==='Enter'||e.key===' ')&&!e.target.closest('.tutorial-card')&&e.target!==Tutorial.target){e.preventDefault();e.stopImmediatePropagation();}}
