'use strict';
const Tutorial={active:false,index:0,returnTab:'home',focus:null};
const tutorialSteps=[
 ['home','🏡 초록정원에 오신 걸 환영해요','홈에서 내 정원과 오늘의 미션을 확인해요. 정원으로 가기에서 식물을 돌보고, 미션하러 가기에서 환경 실천을 시작할 수 있어요.'],
 ['garden','💧 식물을 돌봐요','정원에서 열린 땅을 선택해 씨앗을 심어요. 식물을 선택하면 물·햇빛·영양 상태를 확인하고 돌볼 수 있어요. 잠긴 땅은 정원 레벨을 올리며 열어 가요.'],
 ['garden','🌱 정원의 상태를 살펴봐요','정원 탄소 농도와 식물 상태를 확인해 주세요. 표시되는 탄소 농도는 게임 속 정원 상태이며 실제 대기 측정값은 아니에요. 성장 완료 식물은 수확 버튼으로 기록하고 20P를 받아요. 수확 성과에 따라 정원 레벨이 오르며 9칸에서 최대 25칸까지 7단계로 넓어져요.'],
 ['mission','🗺️ 미션으로 환경 실천을 시작해요','사진 미션, 퀴즈, 현실에서 키우는 식물의 관찰기록에 참여해 보세요. 각 미션의 조건과 보상을 확인해요. 완료 후 생태 지식 카드도 읽어 보세요. 주간 목표인 미션 7개와 미션 보상 150P를 모두 달성하면 80P를 한 번 받을 수 있어요. 관찰일지에는 실제 식물의 이름과 변화를 기록해요.'],
 ['shop','🛍️ 모은 포인트로 구매해요','상점에서 씨앗과 관리 아이템의 가격을 확인해요. 씨앗은 정원 레벨에 따라 열려요. 정원의 계절 꾸미기에서는 봄 외 배경을 각각 40P로 구매하고, 구매한 배경은 무료로 바꿀 수 있어요.'],
 ['encyclopedia','📚 식물 도감을 둘러봐요','식물 도감에서 식물 정보를 살펴봐요. 열려 있는 식물을 선택해 자세한 내용을 확인해 보세요. 레벨 1 식물은 기본 공개되고, 나머지는 해당 씨앗을 수집하면 상세 정보가 열려요. 수확 횟수는 마이페이지의 수확 성과 도감에서 확인해요.'],
 ['friends','🤝 친구와 함께해요','마이페이지에서 내 친구 코드를 확인할 수 있어요. 친구 메뉴에서 친구를 등록하고 정원 방문과 응원 기능을 이용해 보세요.'],
 ['game','🎮 미니게임도 즐겨요','마이페이지의 미니게임 메뉴에서 보유 티켓과 쓰레기 피하기·테트리스의 안내를 확인해요. 튜토리얼은 마이페이지의 「이용 방법 · 튜토리얼 다시 보기」 버튼으로 언제든 다시 볼 수 있어요.']
];
async function maybeStartTutorial(){
 try{const result=await api('/api/auth/tutorial/start/',{method:'POST'});if(result.show_tutorial){startTutorial(true);return true;}}
 catch(error){console.warn('튜토리얼 확인 실패');T('이용 안내를 불러오지 못했어요. 마이페이지에서 다시 볼 수 있어요.');}
 return false;
}
function startTutorial(automatic){
 if(S.guest||Tutorial.active)return;
 Tutorial.active=true;Tutorial.index=0;Tutorial.returnTab=automatic?'home':S.tab;Tutorial.focus=document.activeElement;
 if($('ov').classList.contains('show'))cl();
 const layer=document.createElement('div');layer.id='tutorial-layer';
 layer.innerHTML='<section class="tutorial-card" role="dialog" aria-modal="true" aria-labelledby="tutorial-title" aria-describedby="tutorial-text" tabindex="-1"><div class="tutorial-top"><span id="tutorial-count"></span><button type="button" onclick="finishTutorial()" aria-label="튜토리얼 닫기">✕</button></div><div class="tutorial-progress" aria-hidden="true"><i id="tutorial-progress"></i></div><h2 id="tutorial-title"></h2><p id="tutorial-text"></p><div class="tutorial-actions"><button type="button" id="tutorial-prev" onclick="moveTutorial(-1)">이전</button><button type="button" id="tutorial-next" onclick="moveTutorial(1)">다음</button></div><button class="tutorial-skip" type="button" onclick="finishTutorial()">건너뛰기 · 다시 자동으로 표시하지 않기</button></section>';
 document.body.appendChild(layer);document.addEventListener('keydown',tutorialKeys);drawTutorial();
}
function drawTutorial(){
 const step=tutorialSteps[Tutorial.index];go(step[0]);
 $('tutorial-count').textContent=(Tutorial.index+1)+' / '+tutorialSteps.length;
 $('tutorial-title').textContent=step[1];$('tutorial-text').textContent=step[2];
 $('tutorial-progress').style.width=((Tutorial.index+1)/tutorialSteps.length*100)+'%';
 $('tutorial-prev').disabled=Tutorial.index===0;
 $('tutorial-next').textContent=Tutorial.index===tutorialSteps.length-1?'완료':'다음';
 document.querySelector('.tutorial-card').focus();
}
function moveTutorial(delta){if(!Tutorial.active)return;const n=Tutorial.index+delta;if(n>=tutorialSteps.length){finishTutorial();return;}Tutorial.index=Math.max(0,n);drawTutorial();}
function finishTutorial(restore=true){
 if(!Tutorial.active)return;Tutorial.active=false;document.removeEventListener('keydown',tutorialKeys);
 const el=$('tutorial-layer');if(el)el.remove();
 if(restore){go(Tutorial.returnTab);if(Tutorial.focus&&Tutorial.focus.isConnected)Tutorial.focus.focus();}
}
function tutorialKeys(event){
 if(!Tutorial.active)return;
 if(event.key==='Escape'){event.preventDefault();finishTutorial();return;}
 if(event.key==='Tab'){
  const items=Array.from(document.querySelectorAll('#tutorial-layer button:not([disabled])'));const first=items[0],last=items[items.length-1];
  if(event.shiftKey&&(document.activeElement===first||!items.includes(document.activeElement))){event.preventDefault();last.focus();}
  else if(!event.shiftKey&&(document.activeElement===last||!items.includes(document.activeElement))){event.preventDefault();first.focus();}
 }
}
