import sys,json; sys.path.insert(0,'.')
import numpy as np, cv2
from cam import Cam
S='/tmp/claude-0/-home-user-cames-lp/d255b67e-5213-527c-9cc9-aa92091d8f96/scratchpad'
p=json.load(open('cam_fit.json'))
c=Cam(f=p['f'],yaw=p['yaw'],pitch=p['pitch'],roll=p['roll'],X=p['X'],Y=p['Y'],Z=p['Z'])
im=cv2.imread(S+'/room_main.jpg'); H,W=im.shape[:2]
# ---------- table / foreground mask ----------
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
bb=np.zeros((H,W),np.uint8); cv2.rectangle(bb,(1300,1550),(2200,2200),255,-1)
Bc,Gc,Rc=[im[:,:,i].astype(int) for i in range(3)]
light=(Rc>150)&(Gc>125)&(Bc>85)&(Rc-Bc<110)&(hsv[:,:,1]<120)
tmask=(light&(bb>0)).astype(np.uint8)*255
tmask=cv2.morphologyEx(tmask,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
tmask=cv2.morphologyEx(tmask,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(tmask); keep=np.zeros_like(tmask)
for i in range(1,n):
    if st[i,cv2.CC_STAT_AREA]>1500: keep[lab==i]=255
tmask=keep
add=[np.array([(1420,1640),(1470,1590),(1560,1570),(1640,1600),(1700,1640),(1760,1700),(1760,1760),(1600,1770),(1560,1900),(1500,1930),(1440,1900),(1420,1800)],np.int32),
     np.array([(1760,1700),(1800,1690),(1950,1700),(1960,1800),(1800,1780)],np.int32),
     np.array([(1594,1850),(1634,1850),(1640,1985),(1598,1985)],np.int32)]
for a in add: cv2.fillPoly(tmask,[a],255)
heater=np.array([(470,2250),(470,2200),(495,2150),(540,2122),(600,2118),(645,2140),(668,2185),(672,2250)],np.int32)
fgmask=tmask.copy(); cv2.fillPoly(fgmask,[heater],255)
rgba=cv2.cvtColor(im,cv2.COLOR_BGR2BGRA); rgba[:,:,3]=fgmask
cv2.imwrite(S+'/work/foreground.png',rgba); cv2.imwrite(S+'/work/foreground_mask.png',fgmask)
# ---------- sofa mask ----------
poly=np.array([(596,2250),(596,1500),(640,1470),(650,1400),(700,1360),(790,1390),(830,1410),(880,1380),(960,1360),(1040,1370),(1070,1420),(1180,1440),(1230,1480),(1250,1560),(1290,1680),(1350,1720),(1385,1760),(1390,1960),(1385,2060),(1375,2250)],np.int32)
mask=np.zeros((H,W),np.uint8); cv2.fillPoly(mask,[poly],255); mask=cv2.dilate(mask,np.ones((9,9),np.uint8))
ys,xs=np.where(mask>0); cols=np.unique(xs)
# floor line per column (far wall base at X=2 for u>=627, left wall base for u<627)
Xs=np.linspace(0,300,1200); Pl=np.stack([Xs,np.zeros_like(Xs),np.zeros_like(Xs)],1); prl=c.proj(Pl)
Ys=np.linspace(0,320,1200); Pf=np.stack([np.full_like(Ys,2.0),Ys,np.zeros_like(Ys)],1); prf=c.proj(Pf)
vfloor=np.zeros(W)
for u in cols:
    pr=prl if u<627 else prf; i=np.argmin(np.abs(pr[:,0]-u)); vfloor[u]=pr[i,1]
top=np.full(W,0)
for u in cols: top[u]=np.where(mask[:,u]>0)[0].min()
out=im.copy()
# --- wall/curtain: vertical stretch of the 220px band above the mask down to the floor line
wu=xs; wv=ys; sel=wv<vfloor[wu]; wu=wu[sel]; wv=wv[sel]
t=top[wu]; span=np.maximum(vfloor[wu]-t,1); band=220
src=(t-1-(wv-t)/span*band); src=np.clip(src,0,H-1)
s0=np.floor(src).astype(int); fr=(src-s0)[:,None]; s1=np.minimum(s0+1,H-1)
val=im[s0,wu].astype(np.float32)*(1-fr)+im[s1,wu].astype(np.float32)*fr
# darken toward floor (ambient occlusion) and hem shadow
frac=(wv-t)/span; val*= (1-0.18*frac**2)[:,None]
out[wv,wu]=np.clip(val,0,255).astype(np.uint8)
# --- floor: perspective clone along plank direction (Y shift), fallback inpaint
fu=xs[~sel]; fv=ys[~sel]
blocked=(mask>0)|(fgmask>0)
cv2.rectangle(blocked.view(np.uint8),(2050,1850),(2700,2250),1,-1)
cv2.rectangle(blocked.view(np.uint8),(0,0),(W,1880),1,-1)
res=out.copy(); filled=np.zeros(len(fu),bool)
# world floor coords of each pixel
dirs=c.fwd[None,:]+((fu-c.cx)/c.f)[:,None]*c.right[None,:]-((fv-c.cy)/c.f)[:,None]*c.up[None,:]
tt=(0-c.pos[2])/dirs[:,2]; Pw=c.pos[None,:]+tt[:,None]*dirs
def try_src(Ps):
    global filled
    pr=c.proj(Ps); su=np.round(pr[:,0]).astype(int); sv=np.round(pr[:,1]).astype(int)
    ok=(~filled)&(su>=0)&(su<W)&(sv>=0)&(sv<H)
    ok[ok]&=~blocked[sv[ok],su[ok]]
    res[fv[ok],fu[ok]]=im[sv[ok],su[ok]]; filled|=ok
# 1) same X, Y compressed into visible strip Y' in [90,132]
Ps=Pw.copy(); Ps[:,1]=90+np.clip(Pw[:,1],0,90)*(42/90.0); Ps[:,0]=np.clip(Pw[:,0],0,105); try_src(Ps)
# 2) shift X back toward window for near region
for dx in (40,70,100):
    Ps=Pw.copy(); Ps[:,1]=90+np.clip(Pw[:,1],0,90)*(42/90.0); Ps[:,0]=np.clip(Pw[:,0]-dx,0,105); try_src(Ps)
rem=np.zeros((H,W),np.uint8); rem[fv[~filled],fu[~filled]]=255
if rem.any():
    small=cv2.resize(res,(W//4,H//4),interpolation=cv2.INTER_AREA); smask=cv2.resize(rem,(W//4,H//4),interpolation=cv2.INTER_NEAREST)
    inp=cv2.resize(cv2.inpaint(small,smask,7,cv2.INPAINT_TELEA),(W,H),interpolation=cv2.INTER_CUBIC); res[rem>0]=inp[rem>0]
print('floor pixels',len(fu),'cloned',filled.sum())
# feather seams
blur=cv2.GaussianBlur(res,(0,0),2.5)
edge=cv2.dilate(mask,np.ones((11,11),np.uint8))-cv2.erode(mask,np.ones((11,11),np.uint8))
res[edge>0]=blur[edge>0]
cv2.imwrite(S+'/work/clean_plate.jpg',res,[cv2.IMWRITE_JPEG_QUALITY,95]); cv2.imwrite(S+'/work/sofa_mask.png',mask)
vis=im.copy(); vis[mask>0]=(vis[mask>0]*0.4+np.array([0,0,255])*0.6).astype(np.uint8); vis[fgmask>0]=(vis[fgmask>0]*0.4+np.array([0,255,0])*0.6).astype(np.uint8)
cv2.imwrite(S+'/crops/mask_vis.jpg',cv2.resize(vis[1300:2250,400:2300],(1900,950)))
cv2.imwrite(S+'/crops/clean_vis.jpg',cv2.resize(res[1200:2250,300:2400],(2100,1050)))
# table legs floor coords
for name,(u,v) in {'legA':(1355,2161),'legC':(1615,1978),'legD':(2178,2122),'legFarRight':(1935,1967),'ball':(1450,1960),'heater_top':(560,2120)}.items():
    print(name,np.round(c.floor_from_pixel(u,v),0))
