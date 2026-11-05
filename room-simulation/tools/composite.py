"""Photo-based compositing: real photo (cleaned) + 3D furniture pass + 3D room pass for reconstructed areas.
Plan coords: x 0..320 (TV wall -> right wall), y 0..430 (kitchen wall -> balcony), z up. Output 1920x1080."""
import sys, json, numpy as np, cv2
S='/tmp/claude-0/-home-user-cames-lp/d255b67e-5213-527c-9cc9-aa92091d8f96/scratchpad'
W,H=1920,1080; SC=W/4000.0
ROOM=dict(W=320,D=430,H=240)

class PlanCam:
    def __init__(s,pos,fwd,right,up,f): s.pos=np.array(pos,float); s.fwd=np.array(fwd,float); s.right=np.array(right,float); s.up=np.array(up,float); s.f=f
    @staticmethod
    def lookat(pos,look,f):
        fwd=np.array(look,float)-np.array(pos,float); fwd/=np.linalg.norm(fwd); upw=np.array([0,0,1.0])
        right=np.cross(upw,fwd); right/=np.linalg.norm(right); up=np.cross(fwd,right); return PlanCam(pos,fwd,right,up,f)
    def rays(s):
        v,u=np.mgrid[0:H,0:W]; d=s.fwd[None,None,:]+((u-W/2)/s.f)[:,:,None]*s.right[None,None,:]-((v-H/2)/s.f)[:,:,None]*s.up[None,None,:]
        return d
    def proj(s,P):
        d=np.asarray(P,float)-s.pos; dep=d@s.fwd; return np.array([W/2+s.f*(d@s.right)/dep, H/2-s.f*(d@s.up)/dep, dep])

def ray_box_t(o,d,b0,b1):
    """slab test, vectorized over rays d (H,W,3); returns t of entry (inf if miss)."""
    with np.errstate(divide='ignore',invalid='ignore'):
        t0=(b0-o)/d; t1=(b1-o)/d
    tmin=np.minimum(t0,t1).max(axis=2); tmax=np.maximum(t0,t1).min(axis=2)
    hit=(tmax>=np.maximum(tmin,0)); t=np.where(hit,np.maximum(tmin,0),np.inf); return t

def classify(cam,boxes):
    d=cam.rays(); o=cam.pos
    with np.errstate(divide='ignore',invalid='ignore'): tf=(0-o[2])/d[:,:,2]
    tf=np.where((tf>0),tf,np.inf); P=o[None,None,:]+tf[:,:,None]*d
    infl=(P[:,:,0]>=-14)&(P[:,:,0]<=ROOM['W']+14)&(P[:,:,1]>=-14)&(P[:,:,1]<=ROOM['D']+14)
    tbox=np.full((H,W),np.inf)
    for b0,b1 in boxes: tbox=np.minimum(tbox,ray_box_t(o,d,np.array(b0,float),np.array(b1,float)))
    cls=np.full((H,W),3,np.uint8)   # 0 floor, 1 far wall(y<=0 or y>=D depending), 2 box/3D, 3 other wall
    floor=infl&(tf<tbox); cls[floor]=0
    cls[(tbox<np.inf)&(tbox<=tf)]=2
    # far-wall classification: ray hits plane y=D (balcony wall) or y=0 (kitchen wall) before floor
    for yplane,code in ((ROOM['D'],1),(0,1)):
        if (yplane==0 and o[1]<=0) or (yplane==ROOM['D'] and o[1]>=ROOM['D']): continue
        with np.errstate(divide='ignore',invalid='ignore'): ty=(yplane-o[1])/d[:,:,1]
        ok=(ty>0)&(ty<tf)&(ty<tbox); Pw=o[None,None,:]+ty[:,:,None]*d
        ok&=(Pw[:,:,0]>=-5)&(Pw[:,:,0]<=ROOM['W']+5)&(Pw[:,:,2]>=0)&(Pw[:,:,2]<=ROOM['H'])
        cls[ok&(cls!=2)]=code
    return cls,P,tf

def load_tile():
    top=cv2.imread(S+'/work3/floor_topdown.jpg'); sc=4; X0,X1,Y0,Y1=40,100,108,134
    patch=top[X0*sc:X1*sc,Y0*sc:Y1*sc].astype(np.float32); blur=cv2.GaussianBlur(patch,(0,0),30); mean=patch.reshape(-1,3).mean(0)
    flat=np.clip(patch/np.maximum(blur,1)*mean,0,255); tile=np.concatenate([flat,flat[:,::-1]],1); tile=np.concatenate([tile,tile[::-1]],0)  # rows: X_old 120cm, cols: Y_old 52cm @4px/cm
    return tile, mean

def synth_floor(photo,P,floor_mask,sample_mask):
    """photo floor synthesis from tile + fitted low-frequency shading (quadratic in x,y)."""
    tile,tmean=load_tile(); th,tw=tile.shape[:2]
    Xo=ROOM['D']-P[:,:,1]; Yo=ROOM['W']-P[:,:,0]           # old-frame coords
    r=((Xo*4)%th).astype(int); c=((Yo*4)%tw).astype(int)
    tex=tile[np.clip(r,0,th-1),np.clip(c,0,tw-1)]
    lum=photo.astype(np.float32).mean(2); tl=tmean.mean()
    ys,xs=np.where(sample_mask); idx=np.random.RandomState(0).choice(len(ys),min(30000,len(ys)),replace=False); ys,xs=ys[idx],xs[idx]
    x=P[ys,xs,0]; y=P[ys,xs,1]; A=np.stack([np.ones_like(x),x,y,x*y,x*x,y*y],1); b=lum[ys,xs]/tl
    coef,_,_,_=np.linalg.lstsq(A,b,rcond=None)
    xx=P[:,:,0]; yy=P[:,:,1]; shade=coef[0]+coef[1]*xx+coef[2]*yy+coef[3]*xx*yy+coef[4]*xx*xx+coef[5]*yy*yy
    shade=np.clip(shade,0.15,2.0)
    out=np.clip(tex*shade[:,:,None],0,255)
    # color match: scale per channel so that mean over sample pixels matches photo
    pm=photo[sample_mask].reshape(-1,3).mean(0); om=out[sample_mask].reshape(-1,3).mean(0); out=np.clip(out*(pm/np.maximum(om,1)),0,255)
    return out.astype(np.uint8)

def column_extend(img,mask):
    out=img.copy(); H_,W_=mask.shape
    cols=np.where(mask.any(0))[0]
    for u in cols:
        ys=np.where(mask[:,u])[0]; t=ys.min(); bnd=ys.max()
        band=min(220,t);
        if band<5: continue
        for v in ys:
            k=(v-t)%(2*band); src=t-1-(k if k<band else 2*band-1-k); out[v,u]=img[max(src,0),u]
    return out

def composite(cfg):
    photo=cv2.resize(cv2.imread(cfg['base']),(W,H),interpolation=cv2.INTER_AREA)
    cam=cfg['cam']; cls,P,tf=classify(cam,cfg['boxes'])
    hole=np.zeros((H,W),np.uint8)
    for poly in cfg['holes']: cv2.fillPoly(hole,[np.int32(np.array(poly)*SC)],255)
    hole=cv2.dilate(hole,np.ones((cfg.get('dilate',7),cfg.get('dilate',7)),np.uint8))>0
    room=cv2.imread(cfg['room_pass']); furn=cv2.imread(cfg['furn_pass'],cv2.IMREAD_UNCHANGED)
    # gain match 3D room pass to photo on a reference wall patch
    (x0,y0,x1,y1)=cfg['ref_wall']; g=photo[y0:y1,x0:x1].reshape(-1,3).mean(0)/np.maximum(room[y0:y1,x0:x1].reshape(-1,3).mean(0),1)
    room_m=np.clip(room.astype(np.float32)*g,0,255).astype(np.uint8)
    base=photo.copy()
    # fills
    floor_h=hole&(cls==0); sample=(~hole)&(cls==0)
    if cfg.get('extra_sample_exclude') is not None: sample&=~cfg['extra_sample_exclude']
    synth=synth_floor(photo,P,floor_h,sample); base[floor_h]=synth[floor_h]
    far_h=hole&(cls==1)
    if cfg.get('far_fill')=='column' and far_h.any(): base=column_extend(base,far_h)
    cv2.imwrite(cfg['room_pass'].replace('_room.png','_cls.png'),(np.stack([(cls==0)*200,(cls==1)*200+(cls==2)*120,(cls==3)*200],2)).astype(np.uint8))
    # 3D fill with locally matched gain: ratio photo/room over valid (non-hole, non-floor) pixels, smoothed by normalized convolution
    valid=((~hole)&(cls!=0)).astype(np.float32); sig=70
    num=cv2.GaussianBlur(photo.astype(np.float32)*valid[:,:,None],(0,0),sig); den=cv2.GaussianBlur(room.astype(np.float32)*valid[:,:,None],(0,0),sig)
    gmap=np.clip(num/np.maximum(den,1),0.2,2.5); room_m=np.clip(room.astype(np.float32)*gmap,0,255).astype(np.uint8)
    def smooth_fill(img,fillmask,validmask):
        # diffusion fill: init with large-scale normalized convolution, then iterative blur inside the hole (harmonic-like)
        out=img.astype(np.float32).copy(); v=validmask.astype(np.float32)
        num=cv2.GaussianBlur(img.astype(np.float32)*v[:,:,None],(0,0),200); den=cv2.GaussianBlur(v,(0,0),200)
        init=num/np.maximum(den,1e-3)[:,:,None]; out[fillmask]=init[fillmask]
        keep=~fillmask
        for sig in [40]*10+[16]*10+[6]*8:
            b=cv2.GaussianBlur(out,(0,0),sig); out[fillmask]=b[fillmask]
        rng=np.random.RandomState(5); out=out+rng.normal(0,1.6,out.shape); return np.clip(out,0,255).astype(np.uint8)
    lum=photo.astype(np.float32).mean(2)
    tvh=hole&(cls==2); wall_h=hole&(cls==3)
    if cfg.get('far_fill')!='column': wall_h|=far_h
    if cfg.get('box_fill','3d')=='3d': base[tvh]=room_m[tvh]
    else: wall_h|=tvh
    if wall_h.any():
        validw=(~hole)&((cls==1)|(cls==3))&(lum>70); sf=smooth_fill(base,wall_h.copy(),validw); base[wall_h]=sf[wall_h]
    for (x0,y0,x1,y1,col) in cfg.get('force_fill',[]): r=np.zeros((H,W),bool); r[int(y0*SC):int(y1*SC),int(x0*SC):int(x1*SC)]=True; r&=hole; base[r]=col
    wall_h=np.zeros((H,W),bool)
    if wall_h.any(): base[wall_h]=room_m[wall_h]
    # feather hole boundary
    hm=cv2.GaussianBlur(hole.astype(np.float32),(0,0),2.5)[:,:,None]
    base=(base.astype(np.float32)*hm+photo.astype(np.float32)*(1-hm))
    # furniture pass
    furn=cv2.GaussianBlur(furn,(0,0),0.7); a=(furn[:,:,3:4].astype(np.float32)/255.0); fg=furn[:,:,:3].astype(np.float32)*cfg.get('furn_gain',0.9)
    out=fg*a+base*(1-a)
    # mild film grain to blend render with photo noise
    rng=np.random.RandomState(1); noise=rng.normal(0,2.2,(H,W,1)); out=np.clip(out+noise*a,0,255).astype(np.uint8)
    return out, cls, hole

if __name__=='__main__':
    which=sys.argv[1]; pat=sys.argv[2]; outp=sys.argv[3]
    B=json.load(open(S+'/work3/photo2_basis.json'))
    cab=([0,210,0],[40,270,105]); low=([0,270,0],[40,330,45]); tv=([17,254,51],[23,366,116])
    if which=='photo2':
        cam=PlanCam(B['pos'],B['fwd'],B['right'],B['up'],B['f1920'])
        cfg=dict(base='/home/user/cames-lp/room-simulation/assets/photo2_clean_plate.jpg',cam=cam,boxes=[cab,low,tv],
            holes=[[(2430,600),(2900,520),(3850,600),(3850,2250),(2430,2250)],
                   [(1400,1560),(1750,1560),(1750,1700),(2440,1690),(2440,2250),(1400,2250)],
                   [(460,2110),(680,2110),(680,2250),(460,2250)],[(1430,1930),(1480,1930),(1480,1985),(1430,1985)]],
            ref_wall=(1300,400,1600,600),far_fill='column',
            room_pass=S+f'/work3/L_{pat}_photo_room.png',furn_pass=S+f'/work3/L_{pat}_photo_furn.png',furn_gain=0.9)
    else:
        cam=PlanCam.lookat([262,404,118],[42,0,100],540/np.tan(np.radians(42.8/2)))
        cfg=dict(base=S+'/room_reverse.jpg',cam=cam,boxes=[cab,low,tv],
            holes=[[(1180,420),(1700,330),(2040,560),(2060,1400),(1980,1750),(1950,2250),(1150,2250),(1100,1700),(1130,900)],
                   [(2440,1370),(2910,1370),(2930,2170),(2430,2170)],[(2050,1730),(2380,1730),(2410,2110),(2030,2110)],
                   [(2820,1650),(3150,1650),(3180,2170),(2810,2170)],[(0,1940),(1520,1940),(1580,2250),(0,2250)]],
            ref_wall=(1010,340,1290,430),far_fill='smooth',box_fill='smooth',dilate=15,
            room_pass=S+f'/work3/L_{pat}_photo1_room.png',furn_pass=S+f'/work3/L_{pat}_photo1_furn.png',furn_gain=1.05,wall_fill='inpaint')
    out,cls,hole=composite(cfg); cv2.imwrite(outp,out,[cv2.IMWRITE_JPEG_QUALITY,93])
    dbg=out.copy(); dbg[hole]=(dbg[hole]*0.6+np.array([0,0,120])*0.4).astype(np.uint8)
    cv2.imwrite(outp.replace('.jpg','_debug.jpg'),cv2.resize(dbg,(1280,720)))
    print('ok',outp)
