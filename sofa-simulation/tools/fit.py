import sys; sys.path.insert(0,'.')
import numpy as np
from scipy.optimize import least_squares
from cam import Cam
Hc=240.0
obs_pts=[ # (world fn of params, pixel)
 (lambda p:(0,0,Hc),(545,355)),
 (lambda p:(0,3,p['Hw']),(565,702)),
 (lambda p:(0,p['Yw2'],p['Hw']),(2213,722)),
 (lambda p:(0,p['Wr'],Hc),(2470,472)),
 (lambda p:(25,p['Yac'],232),(1490,470)),
 (lambda p:(25,p['Yac']+80,203),(1990,680)),
 (lambda p:(3,p['Ycb'],0),(1550,1940)),
]
obs_lines=[ # 3D line (P0,P1 fns), observed endpoints
 (lambda p:((100,p['Wr']-p['bd'],Hc),(400,p['Wr']-p['bd'],Hc)),((3715,92),(2645,404))),
 (lambda p:((100,p['Wr']-p['bd'],p['Hb']),(400,p['Wr']-p['bd'],p['Hb'])),((3714,291),(2747,510))),
 (lambda p:((0,0,p['Hw']),(0,250,p['Hw'])),((565,702),(1958,720))),
 (lambda p:((0,0,Hc),(0,250,Hc)),((869,375),(1785,428))),
]
names=['f','yaw','pitch','roll','X','Y','Z','Hw','Wr','Yac','Yw2','bd','Hb','Ycb']
x0=np.array([2805,25.5,3.3,1.45,423,13.5,155.5,195,305,122,251,18,200,139])
def unpack(x): return dict(zip(names,x))
def resid(x):
    p=unpack(x); c=Cam(f=p['f'],yaw=p['yaw'],pitch=p['pitch'],roll=p['roll'],X=p['X'],Y=p['Y'],Z=p['Z'])
    r=[]
    for fn,(u,v) in obs_pts:
        q=c.proj(fn(p))[0]; r+= [q[0]-u, q[1]-v]
    for fn,(e1,e2) in obs_lines:
        P0,P1=fn(p); a=c.proj(P0)[0][:2]; b=c.proj(P1)[0][:2]; d=b-a; n=np.array([-d[1],d[0]])/np.linalg.norm(d)
        for e in (e1,e2): r.append(float(np.dot(np.array(e)-a,n)))
    # vertical tilt at door frame (175,0): observed dx/dy=0.0548
    a=c.proj((175,0,100))[0]; b=c.proj((175,0,220))[0]; r.append(((b[0]-a[0])/(b[1]-a[1])-0.0548)*2000)
    # tilt at right edge vertical x~3712: assume a vertical at (Xv, Wr, z) with Xv such that u~3712 -> use jamb line 93 instead (2215,721)-(2224,1105): dx/dy=0.0234
    a=c.proj((0,p['Yw2'],100))[0]; b=c.proj((0,p['Yw2'],190))[0]; r.append(((b[0]-a[0])/(b[1]-a[1])-0.0234)*2000)
    # priors
    r.append((p['f']-2805)/300*5); r.append((p['Z']-150)/25*5); r.append((p['Hb']-200)/15*5); r.append((p['bd']-18)/8*5)
    return np.array(r)
res=least_squares(resid,x0,x_scale='jac')
p=unpack(res.x)
for k in names: print(f"{k}: {p[k]:.2f}")
r=resid(res.x); print('rms px (pts+lines):',np.sqrt(np.mean(r[:-6]**2)), np.round(r,1))
import json; json.dump(p,open('cam_fit.json','w'),indent=1)
