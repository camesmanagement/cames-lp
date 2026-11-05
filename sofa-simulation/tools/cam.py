import numpy as np, json
# World: origin = floor corner (left sofa wall meets window wall). X toward kitchen/camera, Y toward TV wall, Z up. Units cm.
# Camera: looks toward -X when yaw=0; yaw positive rotates view toward +Y (right). pitch positive = down. roll positive = clockwise image.
def rot(yaw, pitch, roll):
    cy,sy=np.cos(yaw),np.sin(yaw); cp,sp=np.cos(pitch),np.sin(pitch); cr,sr=np.cos(roll),np.sin(roll)
    fwd=np.array([-cy, sy, 0.0]); right=np.array([sy, cy, 0.0]); up=np.array([0,0,1.0])
    # pitch down: rotate fwd toward -up
    f2=fwd*cp - up*sp; u2=up*cp + fwd*sp
    # roll: rotate right/up about fwd
    r3=right*cr + u2*sr; u3=u2*cr - right*sr
    return f2, r3, u3
class Cam:
    def __init__(s, f=2805, cx=2000, cy=1125, yaw=25.5, pitch=3.3, roll=1.45, X=423, Y=13.5, Z=155.5):
        s.f,s.cx,s.cy=f,cx,cy; s.pos=np.array([X,Y,Z],float)
        s.fwd,s.right,s.up=rot(np.radians(yaw),np.radians(pitch),np.radians(roll))
    def proj(s,P):
        P=np.atleast_2d(np.asarray(P,float)); d=P-s.pos
        dep=d@s.fwd; lat=d@s.right; ver=d@s.up
        return np.stack([s.cx+s.f*lat/dep, s.cy-s.f*ver/dep, dep],1)
    def floor_from_pixel(s,u,v,Z=0.0):
        # ray direction
        dirc=s.fwd + ((u-s.cx)/s.f)*s.right - ((v-s.cy)/s.f)*s.up
        t=(Z-s.pos[2])/dirc[2]; return s.pos+t*dirc
