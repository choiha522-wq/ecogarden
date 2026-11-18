/* 초록정원 · 3D 정원 장면(three.js) 그리기
   (index.html에서 분리한 파일 · 로드 순서 7/13 — 순서를 바꾸면 안 돼요) */

let G=null;const K={};const W3={};
(function(){
const recoveredForestKeys=level=>{
  const cells=[];
  for(let row=0;row<15;row++)for(let col=0;col<15;col++){
    const garden=row>=4&&row<=10&&col>=4&&col<=10;
    if(!garden&&row+col<=14)cells.push({row,col,distance:Math.min(row,col,14-row-col)});
  }
  const target=Math.ceil(cells.length*Math.max(1,Math.min(7,level))/7),bands=new Map();
  cells.forEach(cell=>{if(!bands.has(cell.distance))bands.set(cell.distance,[]);bands.get(cell.distance).push(cell)});
  const selected=new Set();let count=0;
  for(const distance of [...bands.keys()].sort((a,b)=>a-b)){
    const band=bands.get(distance),include=count===0||Math.abs(count+band.length-target)<Math.abs(count-target);
    if(!include)break;
    band.forEach(cell=>selected.add(`${cell.row},${cell.col}`));count+=band.length;
  }
  return selected;
};
const fallbackMount=()=>{
  const b=$('gbox');if(!b)return;
  const meadow=({spring:'#75B96A',summer:'#63B878',autumn:'#809253',winter:'#B6C6C4'}[S.theme||'spring']||'#75B96A'),parts=[`<polygon points="-2,320 250,184 502,320 250,456" fill="${meadow}"/>`],level=Math.max(1,Math.min(7,S.progression?.level||S.gardenLevel||1)),treeColors={spring:['#356F46','#3F8651','#55A066'],summer:['#246B3D','#2D874A','#48A85D'],autumn:['#865136','#B86B3A','#D38B4D'],winter:['#789D9A','#9CBFBA','#C6DFD8']}[S.theme||'spring']||['#356F46','#3F8651','#55A066'];const recoveredTrees=recoveredForestKeys(level);
  for(let row=0;row<15;row++)for(let col=0;col<15;col++){
    const x=250+(col-row)*14,y=62+(col+row)*7.6;
    const garden=row>=4&&row<=10&&col>=4&&col<=10;
    if(garden){
      const k=(row-4)*7+(col-4),open=S.unlockedPlots.has(k),plant=S.plots[k]!=null;
      const fill=open?(S.theme==='winter'?'#C4DCE1':'#74AF64'):'#352A42';
      const icon=open?(plant?(TY[S.types[k]]||{}).e||ST[S.plots[k]]:'🌱'):'🔒';
      parts.push(`<g onclick="toggleGardenPlot(${k})" style="cursor:pointer"><polygon points="${x},${y-8} ${x+14},${y} ${x},${y+8} ${x-14},${y}" fill="${fill}" stroke="#79D889" stroke-width="1.5"/><text x="${x}" y="${y+4}" text-anchor="middle" font-size="9">${icon}</text></g>`);
    }else{
      const tree=row+col<=14;
      const fill=tree?'#57944E':'#75B96A';
      parts.push(`<polygon points="${x},${y-8} ${x+14},${y} ${x},${y+8} ${x-14},${y}" fill="${fill}" stroke="#5A9A55" stroke-width=".5"/>`);
      if(tree){const recovered=recoveredTrees.has(`${row},${col}`),leaves=recovered?treeColors:['#443448','#514056','#604967'];parts.push(`<g stroke-linejoin="round"><path d="M${x-1.5} ${y+3}h3v7h-3z" fill="#76513A"/><path d="M${x} ${y-25}l-9 11h5l-7 8h7l-5 7h18l-5-7h7l-7-8h5z" fill="${leaves[0]}"/><path d="M${x} ${y-25}l-9 11h5l-7 8h7l-5 7h18l-5-7h7l-7-8h5z" fill="none" stroke="${leaves[1]}" stroke-width="1"/><path d="M${x} ${y-18}l-6 7h4l-5 6h14l-5-6h4z" fill="${leaves[2]}" opacity=".9"/></g>`)}
      else if(!tree&&(row+col)%4===0)parts.push(`<g stroke="#39844A" stroke-width="1.5" stroke-linecap="round"><path d="M${x-2} ${y+4}l-2-5m2 5 1-7m0 7 4-5"/></g>`);
    }
  }
  b.innerHTML=`<svg viewBox="165 70 170 210" preserveAspectRatio="none" aria-label="숲과 정원" style="position:relative;z-index:1;width:100%;height:100%;display:block">${parts.join('')}</svg>`;
  mountSeason(b);
};
try{
if(!window.THREE){W3.mount=fallbackMount;return}
const h=THREE,cv=document.createElement('canvas'),sc=new h.Scene(),cm=new h.OrthographicCamera(-1,1,1,-1,.1,60),wr=new h.Group(),pg=new h.Group(),fr=new h.Group(),forest=new h.Group(),mt={},tiles=[],baseTiles=[],P3=[],forestTrees=[],grassTufts=[],activeCritters=[];let r,forestTreeMeshes=[];
try{r=new h.WebGLRenderer({canvas:cv,antialias:false,alpha:true})}catch(error){console.error('정원 WebGL 초기화 실패',error);W3.mount=fallbackMount;return}
let renderedGardenLevel=null,animalEventTimer=null,animalEventSessionStarted=false;
cm.position.set(9,14,9);cm.lookAt(0,1.6,0);sc.add(wr,forest);wr.add(pg,fr);wr.position.set(0,0,0);
sc.add(new h.AmbientLight(0xffffff,.8));const dl=new h.DirectionalLight(0xffffff,.55);dl.position.set(4,9,3);sc.add(dl);
const bx=(g,w,ht,d,x,y,z,c)=>{const m=new h.Mesh(new h.BoxGeometry(w,ht,d),mt[c]||(mt[c]=new h.MeshLambertMaterial({color:c})));m.position.set(x,y,z);g.add(m);return m};
const UNIT=.9,GRID=15,GROUND_GRID=25,forestGround=bx(forest,GRID*UNIT,.2,GRID*UNIT,0,-.005,0,0x4B8B48);
bx(forest,18*UNIT,.2,18*UNIT,10*UNIT,-.004,10*UNIT,0x4B8B48);
for(let row=0;row<7;row++)for(let col=0;col<7;col++){const x=(col-3)*UNIT,z=(row-3)*UNIT;baseTiles.push(bx(wr,UNIT*.94,.42,UNIT*.94,x,-.115,z,(row+col)%2?0x5CBF74:0x4FB068))}
for(let row=0;row<7;row++)for(let col=0;col<7;col++){const k=row*7+col,x=(col-3)*UNIT,z=(row-3)*UNIT,t=bx(wr,UNIT*.87,.1,UNIT*.87,x,.05,z,0x8B5E3C);t.userData.k=k;tiles.push(t);P3.push({x,z})}
for(let row=0;row<GRID;row++)for(let col=0;col<GRID;col++){
  const gardenCell=row>=4&&row<=10&&col>=4&&col<=10;if(gardenCell)continue;
  const x=(col-7)*UNIT,z=(row-7)*UNIT;
  if(row+col<=14){
    const edge=row+col>7,height=edge?.88+(row+col)%3*.08:1.55+(7-row-col)*.07+(col%3)*.08;
    forestTrees.push({x,z,height,scale:.88+(col%3)*.06,index:forestTrees.length,row,col});
  }else{
    const j=grassTufts.length,height=.18+(j%3)*.045;
    for(let n=0;n<8;n++)grassTufts.push({x:x+((n%4)-1.5)*.18,z:z+(Math.floor(n/4)-.5)*.2,height,color:n%4,lean:((n%2)*2-1)*.12});
  }
}
for(let row=0;row<GROUND_GRID;row++)for(let col=0;col<GROUND_GRID;col++){
  const sourceRow=row-5,sourceCol=col-5;
  if(sourceRow>=0&&sourceRow<GRID&&sourceCol>=0&&sourceCol<GRID)continue;
  if(row+col<=GROUND_GRID+5)continue;
  const x=(col-(GROUND_GRID-1)/2)*UNIT,z=(row-(GROUND_GRID-1)/2)*UNIT,j=grassTufts.length;
  for(let n=0;n<8;n++)grassTufts.push({x:x+((n%4)-1.5)*.18,z:z+(Math.floor(n/4)-.5)*.2,height:.18+(j+n)%3*.045,color:n%4,lean:((n%2)*2-1)*.12});
}
const instanceGeometry=new h.BoxGeometry(1,1,1),treeDummy=new h.Object3D(),barkMat=new h.MeshLambertMaterial({color:0x76503C}),leafMat=new h.MeshLambertMaterial({color:0xFFFFFF});
const trunkMesh=new h.InstancedMesh(instanceGeometry,barkMat,forestTrees.length),leafMeshes=[0,1,2].map(()=>new h.InstancedMesh(instanceGeometry,leafMat.clone(),forestTrees.length));
forestTrees.forEach((tree,i)=>{const hgt=tree.height,s=tree.scale;treeDummy.position.set(tree.x,.1+hgt*.28,tree.z);treeDummy.scale.set(.14*s,hgt*.56,.14*s);treeDummy.updateMatrix();trunkMesh.setMatrixAt(i,treeDummy.matrix);
  [[.82,.46,.82,hgt*.58],[.66,.46,.66,hgt*.9],[.48,.42,.48,hgt*1.18]].forEach(([w,hh,d,y],tier)=>{treeDummy.position.set(tree.x,.1+y,tree.z);treeDummy.scale.set(w*s,hh,d*s);treeDummy.updateMatrix();leafMeshes[tier].setMatrixAt(i,treeDummy.matrix)})
});
trunkMesh.instanceMatrix.needsUpdate=true;forest.add(trunkMesh);leafMeshes.forEach(mesh=>{mesh.instanceMatrix.needsUpdate=true;forest.add(mesh)});forestTreeMeshes=leafMeshes;
const grassColors=[0x39844A,0x4DAB5C,0x70C46B,0x31814C],grassGeometry=new h.BoxGeometry(.045,1,.045),grassDummy=new h.Object3D();
grassColors.forEach((color,index)=>{const items=grassTufts.filter(item=>item.color===index);if(!items.length)return;const mesh=new h.InstancedMesh(grassGeometry,new h.MeshLambertMaterial({color}),items.length);items.forEach((item,n)=>{grassDummy.position.set(item.x,.095+item.height/2,item.z);grassDummy.scale.set(1,item.height,1);grassDummy.rotation.set(item.lean,0,-item.lean);grassDummy.updateMatrix();mesh.setMatrixAt(n,grassDummy.matrix)});mesh.instanceMatrix.needsUpdate=true;forest.add(mesh)});
[[1.18,.06,.08,0,.12,.59],[1.18,.06,.08,0,.12,-.59],[.08,.06,1.18,.59,.12,0],[.08,.06,1.18,-.59,.12,0]].forEach(a=>bx(fr,...a,0xFFC94D));
const cls=[0,1].map(n=>{const g=new h.Group();bx(g,2,.5,1,0,0,0,0xFFFFFF);bx(g,1.2,.5,.8,.4,.4,0,0xFFFFFF);g.position.set(0,5+n*1.2,-3+n*5);sc.add(g);return g});
const hx=v=>parseInt(v,16);
const pt3=k=>S.tx[k]||(S.tx[k]=(t=>{t.magFilter=t.minFilter=h.NearestFilter;t.generateMipmaps=false;return t})(new h.CanvasTexture(S.pc[k])));
const mkF=(g,s,M)=>{const L=0x6CD07E,S3=0x3E9B4F,hg=M.stem_height||1,n=Math.min(5,M.stem_count||3),ac=hx(M.accent||'FF7AA8'),ct=hx(M.center||'FFC107'),pos=[[0,0],[.45,.3],[-.4,.35],[.3,-.45],[-.35,-.4]];
if(s==0){bx(g,.3,.2,.3,0,.15,0,0x6B4A2B);return g}
if(s==1){bx(g,.1,.4,.1,0,.25,0,S3);bx(g,.36,.1,.18,0,.5,0,L);return g}
for(let i=0;i<n;i++){const x=pos[i][0],z=pos[i][1],H=(s==2?.6:s==3?.9:1)*hg+.3;
bx(g,.1,H,.1,x,H/2,z,S3);bx(g,.4,.1,.18,x+.15,H*.4,z,L);
if(s==3)bx(g,.2,.22,.2,x,H+.08,z,ac);
if(s==4){bx(g,.56,.1,.22,x,H+.05,z,ac);bx(g,.22,.1,.56,x,H+.05,z,ac);bx(g,.22,.14,.22,x,H+.08,z,ct)}}
return g};
const mkP=(s,ty,k)=>{const M=TY[ty]||TY.apple||{},g=new h.Group(),L=0x6CD07E,S3=0x3E9B4F,c=(M.palette||['2E9E52','3FB765','5CD07A']).map(hx),tr=hx(M.trunk||'8B5A2B'),ac=M.accent?hx(M.accent):0,sh=M.shape||'round',w=M.width||1;
if(ty=='photo'){bx(g,.14,1.4,.14,0,.7,0,0x8B5A2B);const f=new h.Group();f.rotation.y=Math.PI/4;f.position.y=1.75;bx(f,1.75,1.75,.08,0,0,-.06,0x8B5A2B);f.add(new h.Mesh(new h.PlaneGeometry(1.5,1.5),new h.MeshBasicMaterial({map:pt3(k)})));g.add(f);return g}
if(S.pd&&S.pd[k]&&S.pd[k].is_dead&&curPlots()===S.plots){const t=.5+s*.35;bx(g,.3,t,.3,0,t/2,0,0x6B5B4B);bx(g,.7,.12,.12,.25,t*.8,0,0x5A4A3B);bx(g,.12,.12,.6,0,t*.6,-.2,0x5A4A3B);if(s>=2)bx(g,.5,.1,.1,-.3,t*.95,0,0x5A4A3B);return g}
if(M.kind=='flower')return mkF(g,s,M);
if(s==0)bx(g,.3,.2,.3,0,.15,0,0x6B4A2B);
else if(s==1){bx(g,.12,.5,.12,0,.3,0,S3);bx(g,.42,.12,.2,0,.62,0,L)}
else if(s==2){bx(g,.16,1,.16,0,.5,0,S3);bx(g,.5,.12,.22,.3,.5,0,L);bx(g,.5,.12,.22,-.3,.75,0,L);bx(g,.22,.12,.5,0,.8,.3,L)}
else if(s==3){bx(g,.16,.9,.16,0,.45,0,tr);if(sh=='conifer'){bx(g,.9,.35,.9,0,.75,0,c[0]);bx(g,.55,.35,.55,0,1.1,0,c[1])}else bx(g,.8*w,.5,.8*w,0,1.1,0,c[1])}
else if(sh=='conifer'){bx(g,.3,1,.3,0,.5,0,tr);[[1.6,.9,0],[1.3,1.3,1],[1,1.7,0],[.65,2.1,1],[.3,2.5,0]].forEach(a=>bx(g,a[0]*w,.42,a[0]*w,0,a[1],0,c[a[2]]))}
else{const th=sh=='tall'?1.8:1.3;bx(g,.34,th,.34,0,th/2,0,tr);bx(g,1.3*w,.6,1.3*w,0,th+.3,0,c[0]);bx(g,1*w,.6,1*w,0,th+.85,0,c[1]);bx(g,.6*w,.4,.6*w,0,th+1.3,0,c[2]);
if(sh=='willow')[[.7,.2],[-.7,.3],[.2,-.7],[-.3,.7],[.75,-.5],[-.75,-.5]].forEach(a=>bx(g,.1,.9,.1,a[0]*w,th-.1,a[1]*w,c[2]));
if(ac)[[.7,th+.1,.3],[-.4,th+.5,.66],[.2,th+.35,-.66],[-.7,th+.2,-.3]].forEach(a=>bx(g,.2,.2,.2,a[0]*w,a[1],a[2]*w,ac))}
return g};
const makeCritter=kind=>{const g=new h.Group(),movers=[];const part=(w,ht,d,x,y,z,c,move=false)=>{const o=bx(g,w,ht,d,x,y,z,c);if(move)movers.push(o);return o};
if(kind==='bird'){part(.42,.28,.62,0,0,0,0x4D78A8);part(.28,.25,.28,0,.14,.34,0x6EA4D8);part(.2,.1,.16,0,.1,.54,0xF0A33A);part(.34,.08,.42,-.3,.04,0,0x8FC8E8,true);part(.34,.08,.42,.3,.04,0,0x8FC8E8,true);part(.09,.2,.1,-.12,-.2,.08,0xD18B38);part(.09,.2,.1,.12,-.2,.08,0xD18B38)}
else if(kind==='rabbit'){part(.55,.38,.76,0,.28,-.02,0xE8DED0);part(.37,.36,.38,0,.52,.32,0xF1E8DC);part(.11,.42,.13,-.12,.88,.3,0xD9949A);part(.11,.42,.13,.12,.88,.3,0xD9949A);part(.22,.18,.2,0,.16,-.42,0xF7F4ED);part(.08,.18,.12,-.2,.08,.2,0xD1C5B8,true);part(.08,.18,.12,.2,.08,.2,0xD1C5B8,true)}
else if(kind==='deer'){part(.72,.48,1.0,0,.55,0,0xA76B3E);part(.25,.7,.25,0,.94,.34,0xB87945);part(.38,.34,.42,0,1.27,.47,0xC78A50);part(.12,.42,.12,-.2,1.55,.45,0x795432);part(.12,.42,.12,.2,1.55,.45,0x795432);for(const x of [-.25,.25])for(const z of [-.3,.3])part(.12,.48,.13,x,.22,z,0x76513A,true)}
else if(kind==='squirrel'){part(.4,.6,.42,0,.36,0,0xB86E36);part(.3,.3,.3,0,.76,.17,0xD9904F);part(.2,.18,.18,0,.78,.34,0xE6BE7A);part(.26,.5,.25,-.38,.52,-.05,0xC97938,true);part(.26,.5,.25,.38,.52,-.05,0xC97938,true);part(.11,.14,.1,-.12,.94,.18,0x9C552E);part(.11,.14,.1,.12,.94,.18,0x9C552E)}
else if(kind==='fox'){part(.52,.4,.9,0,.34,0,0xC86D32);part(.34,.34,.4,0,.56,.48,0xE08A49);part(.12,.26,.12,-.14,.83,.54,0x9C4E2E);part(.12,.26,.12,.14,.83,.54,0x9C4E2E);part(.32,.36,.34,0,.14,-.58,0xD97837,true);part(.12,.32,.12,-.17,.12,.27,0x874A2D,true);part(.12,.32,.12,.17,.12,.27,0x874A2D,true)}
else if(kind==='butterfly'){part(.12,.44,.12,0,0,0,0x3D6555);for(const x of [-.22,.22])for(const z of [-.1,.18])part(.32,.28,.08,x,.14,z,x<0?0xF28CB6:0xF4C6DC,true)}
else if(kind==='turtle'){part(.5,.22,.7,0,.28,0,0x6FAE58);part(.58,.42,.56,0,.47,0,0x527C45);part(.34,.25,.38,0,.43,.31,0x78B95B);part(.08,.1,.06,-.08,.48,.49,0x17251B);part(.08,.1,.06,.08,.48,.49,0x17251B);for(const x of [-.24,.24])for(const z of [-.22,.22])part(.15,.18,.18,x,.15,z,0x6FAE58,true)}
else if(kind==='owl'){part(.56,.66,.48,0,.44,0,0x806044);part(.56,.4,.5,0,.85,.02,0x9B7954);for(const x of [-.14,.14]){part(.18,.18,.08,x,.9,.25,0xF5E7C8);part(.07,.1,.05,x,.9,.31,0x222A2B)}part(.1,.12,.12,0,.76,.31,0xE5A73D);part(.22,.48,.18,-.34,.45,-.02,0x604832,true);part(.22,.48,.18,.34,.45,-.02,0x604832,true);part(.12,.18,.12,-.13,.1,.04,0xDCA83F);part(.12,.18,.12,.13,.1,.04,0xDCA83F)}
else if(kind==='hedgehog'){part(.58,.48,.72,0,.34,0,0x8B6045);part(.38,.34,.36,0,.4,.38,0xD9B58B);part(.2,.16,.18,0,.35,.58,0x49362C);part(.06,.3,.06,0,.72,-.22,0x4C3A31);for(let i=0;i<7;i++){const x=(i-3)*.13;part(.055,.23,.055,x,.65,-.05-Math.abs(i-3)*.025,0x4C3A31)}for(const x of [-.21,.21])for(const z of [-.2,.22])part(.13,.2,.13,x,.13,z,0x76513A,true)}
else{part(.12,.44,.12,0,0,0,0x3D6555)}
return{group:g,kind,movers}};
const FOREST_ANIMALS=['bird','rabbit','deer','squirrel','fox','butterfly','turtle','owl','hedgehog'];
function clearActiveCritters(){activeCritters.forEach(c=>{sc.remove(c.group);c.group.traverse(o=>{if(o.geometry)o.geometry.dispose()})});activeCritters.length=0}
function spawnForestAnimal(kind){clearActiveCritters();const animal=makeCritter(kind),slot=0;sc.add(animal.group);activeCritters.push({...animal,start:performance.now(),duration:5000,offset:Math.random()*Math.PI*2,slot});const emojis={bird:'🐦',rabbit:'🐇',deer:'🦌',squirrel:'🐿️',fox:'🦊',butterfly:'🦋',turtle:'🐢',owl:'🦉',hedgehog:'🦔'};T(`${emojis[kind]||'🌿'} ${kind==='bird'?'새':kind==='rabbit'?'토끼':kind==='deer'?'사슴':kind==='squirrel'?'다람쥐':kind==='fox'?'여우':kind==='butterfly'?'나비':kind==='turtle'?'거북이':kind==='owl'?'부엉이':'고슴도치'}가 숲에서 놀러 왔어요!`)}
function unlockedForestAnimals(level){return FOREST_ANIMALS.slice(0,Math.max(1,Math.min(FOREST_ANIMALS.length,level-1)))}
function scheduleForestVisit(delay,initial=false){clearTimeout(animalEventTimer);animalEventTimer=setTimeout(()=>{if(S.guest){animalEventSessionStarted=false;animalEventTimer=null;return}if(!cv.isConnected||!['home','garden'].includes(S.tab)){scheduleForestVisit(initial?1200:15000,initial);return}const choices=unlockedForestAnimals(S.progression?.level||S.gardenLevel||1);spawnForestAnimal(choices[Math.floor(Math.random()*choices.length)]);scheduleForestVisit(300000+Math.random()*300000,false)},delay)}
function ensureForestVisitSchedule(){if(S.guest){clearTimeout(animalEventTimer);animalEventTimer=null;animalEventSessionStarted=false;return}if(!animalEventSessionStarted){animalEventSessionStarted=true;scheduleForestVisit(1000+Math.random()*9000,true)}}
function spawnLevelAnimal(level){const kind=FOREST_ANIMALS[level-2];if(kind)spawnForestAnimal(kind)}
function setForestLevel(level){const recovered=recoveredForestKeys(level),green={spring:[0x356F46,0x3F8651,0x55A066],summer:[0x246B3D,0x2D874A,0x48A85D],autumn:[0x865136,0xB86B3A,0xD38B4D],winter:[0x789D9A,0x9CBFBA,0xC6DFD8]}[S.theme||'spring'];forestTreeMeshes.forEach((mesh,tier)=>{forestTrees.forEach((tree,index)=>mesh.setColorAt(index,new h.Color(recovered.has(`${tree.row},${tree.col}`)?green[tier]:0x443448)));if(mesh.instanceColor)mesh.instanceColor.needsUpdate=true})}
function updateCritters(now){for(let i=activeCritters.length-1;i>=0;i--){const c=activeCritters[i],p=(now-c.start)/c.duration;if(p>=1){sc.remove(c.group);c.group.traverse(o=>{if(o.geometry)o.geometry.dispose()});activeCritters.splice(i,1);continue}const angle=p*Math.PI*2+c.offset,hide=Math.max(0,(p-.82)/.18),radius=4.15+hide*.75;c.group.position.set(Math.cos(angle)*radius,c.kind==='bird'?1.8+Math.sin(p*12+c.slot)*.22:.1+Math.abs(Math.sin(p*20+c.slot))*.05,Math.sin(angle)*radius);c.group.rotation.y=-angle;c.group.scale.setScalar((c.kind==='deer'?1.15:.85)*(1-hide*.94));c.movers.forEach((m,j)=>{if(c.kind==='bird'||c.kind==='butterfly')m.rotation.z=Math.sin(p*40+j)*.45;else m.rotation.x=Math.sin(p*40+j)*.28})}}
W3.size=()=>{const p=cv.parentNode;if(!p||!p.clientWidth)return;const w=p.clientWidth,ht=p.clientHeight,a=w/ht,f=Math.max(5.2,4.2/a);r.setSize(Math.max(1,w/3|0),Math.max(1,ht/3|0),false);cm.left=-f*a;cm.right=f*a;cm.top=f;cm.bottom=-f;cm.updateProjectionMatrix()};
const curGrid=()=>S.tab=='friends'&&S.vf!=null?Math.round(Math.sqrt(FR[S.vf].plot_count||9)):S.gridSize;
W3.mount=()=>{
  const b=$('gbox');if(!b)return;b.appendChild(cv);mountSeason(b);while(pg.children.length)pg.remove(pg.children[0]);
  ensureForestVisitSchedule();
  const gardenLevel=Math.max(1,Math.min(10,S.progression?.level||S.gardenLevel||1)),forestLevel=Math.min(7,gardenLevel);
  setForestLevel(forestLevel);
  forestGround.material.color.setHex(({spring:0x5F9B53,summer:0x378C52,autumn:0x71834F,winter:0xC6D8D9}[S.theme]||0x5F9B53));
  if(renderedGardenLevel!==null&&gardenLevel>renderedGardenLevel)spawnLevelAnimal(gardenLevel);
  renderedGardenLevel=gardenLevel;
  const terrain={spring:[0x5CBF74,0x4FB068],summer:[0x3FAD67,0x32965A],autumn:[0xDCA252,0xC78443],winter:[0xE4EEF0,0xC7DCE1]}[S.theme||'spring']||[0x5CBF74,0x4FB068];
  baseTiles.forEach((m,i)=>{const c=terrain[i%2];m.material=mt[c]||(mt[c]=new h.MeshLambertMaterial({color:c}))});
  tiles.forEach((t,k)=>{const open=S.tab=='friends'&&S.vf!=null?(FR[S.vf].unlocked_slots||[]).includes(k):S.unlockedPlots.has(k);const key=(S.theme||'spring')+(open?'open':'closed');const color=open?({spring:0x83AA68,summer:0x52996A,autumn:0xBD8051,winter:0xB9D2D8}[S.theme]||0x83AA68):0x352A42;t.material=mt[key]||(mt[key]=new h.MeshLambertMaterial({color}))});
  curPlots().forEach((s,k)=>{if(s==null||k>=49)return;const g=mkP(s,curTypes()[k],k);g.position.set(P3[k].x,.1,P3[k].z);g.userData.k=k;pg.add(g)});
  fr.visible=S.tab=='garden';fr.position.set(P3[S.sel].x,0,P3[S.sel].z);W3.size()
};
const mount3d=W3.mount;W3.mount=()=>{if(S.guest){clearTimeout(animalEventTimer);animalEventTimer=null;animalEventSessionStarted=false;clearActiveCritters()}try{mount3d()}catch(error){console.error('정원 장면 구성 실패',error);W3.mount=fallbackMount;fallbackMount()}};
addEventListener('resize',W3.size);
cv.addEventListener('pointerdown',e=>{if(S.tab!='garden')return;const b=cv.getBoundingClientRect(),rc=new h.Raycaster();rc.setFromCamera(new h.Vector2((e.clientX-b.left)/b.width*2-1,-(e.clientY-b.top)/b.height*2+1),cm);const o=rc.intersectObjects([...tiles,pg],true)[0];if(o){let p=o.object;while(p&&p.userData.k==null)p=p.parent;if(p){if(S.tab=='garden'){const k=p.userData.k,opened=toggleGardenPlot(k);if(opened&&S.plots[k]>=4&&!S.pd[k]?.is_dead)T('✨ 성장 완료! 아래 수확 버튼을 눌러요');}}}});
const ck=new h.Clock();(function lp(){requestAnimationFrame(lp);if(!cv.isConnected)return;const t=ck.getElapsedTime();wr.rotation.y=0;updateCritters(performance.now());
cls.forEach((c,i)=>c.position.x=((t*.4+i*7)%16)-8);pg.children.forEach((g,i)=>g.scale.y=1+Math.sin(t*2+i)*.04);try{r.render(sc,cm)}catch(error){console.error('정원 그리기 실패',error);W3.mount=fallbackMount;fallbackMount()}})();
}catch(error){console.error('정원 장면 초기화 실패',error);W3.mount=fallbackMount}
})();
