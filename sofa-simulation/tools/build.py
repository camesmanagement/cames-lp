import json,re
S='/tmp/claude-0/-home-user-cames-lp/d255b67e-5213-527c-9cc9-aa92091d8f96/scratchpad'
R='/home/user/cames-lp/sofa-simulation'
tpl=open(S+'/work/app_template.html').read()
three=open(S+'/vendor/node_modules/three/build/three.module.js').read()
cam=json.load(open(R+'/assets/camera_fit.json')); fg=json.load(open(R+'/assets/foreground_table.json'))
out=tpl.replace('/*THREE_INLINE*/',three).replace('/*CAMERA_JSON*/',json.dumps(cam)).replace('/*FG_JSON*/',json.dumps(fg))
open(R+'/index.html','w').write(out)
print('built',len(out))
