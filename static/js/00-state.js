/* 초록정원 · 기본 상수와 전역 상태(S) 정의
   (index.html에서 분리한 파일 · 로드 순서 1/13 — 순서를 바꾸면 안 돼요) */

const ST=['🌰','🌱','🌿','🌸','🌳'],SN=['씨앗','새싹','줄기','묘목','나무'];
const S={pt:0,tk:0,seed:0,nutri:0,plots:Array(49).fill(null),sel:24,gardenPlotOpen:false,att:0,attDone:false,tab:'home',myView:'profile',fl:'전체',done:{},missions:[],missionDay:'',shopItems:[],mic:0,pd:{},co2:null,co2base:432.7,co2max:500,wd:0,sl:0,waterCap:10,waterNext:null,guest:true,speciesInfo:{},me:null,authMode:'login',sf:'전체',div:0,poll:0,photoMissionId:null,gallery:[],galleryNext:null,galleryLoaded:false,galleryLoading:false,gardenLevel:1,progression:null,plotCount:9,gridSize:3,unlockedPlots:new Set(),co2Info:false,ef:'전체'};
const $=id=>document.getElementById(id);
const CL={observation:'관찰',microbe:'미생물',biology:'생물'},CC={observation:'--g',microbe:'--pu',biology:'--tl'};
