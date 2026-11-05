import json,re,sys
S='/tmp/claude-0/-home-user-cames-lp/d255b67e-5213-527c-9cc9-aa92091d8f96/scratchpad'
R='/home/user/cames-lp/room-simulation'
tpl=open(S+'/work2/room_template.html').read()
three=open(S+'/vendor/node_modules/three/build/three.module.js').read()
orbit=open(S+'/vendor/node_modules/three/examples/jsm/controls/OrbitControls.js').read()
# strip import block and export line
orbit=re.sub(r"^import \{[\s\S]*?\} from 'three';\n","",orbit,flags=re.M)
orbit=re.sub(r"^export \{ OrbitControls \};\s*$","",orbit,flags=re.M)
assert 'import' not in orbit.split('\n')[0]
spec=json.load(open(S+'/work2/sofa_spec.json'))
orbit='const OrbitControls=(()=>{\n'+orbit+'\nreturn OrbitControls;})();'
out=tpl.replace('/*THREE_INLINE*/',three).replace('/*ORBIT_INLINE*/',orbit).replace('/*SOFA_SPEC*/',json.dumps(spec,ensure_ascii=False))
open(R+'/index.html','w').write(out); print('built',len(out))
