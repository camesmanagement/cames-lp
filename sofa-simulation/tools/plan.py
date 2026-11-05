# Top-view placement diagram (SVG). Units: cm -> px (scale), origin at window-wall/left-wall corner.
import json
S='/tmp/claude-0/-home-user-cames-lp/d255b67e-5213-527c-9cc9-aa92091d8f96/scratchpad'
def plan(model, W, sofa_d, chaise_w, chaise_d, color_fill, title, note):
    sc=2.2; mx,my=230,150            # margins (px)
    roomW=316; roomL=360             # drawn room: width Y (cm), length along wall X (cm) (room length beyond wall drawn as opening)
    wall=175; over=W-wall
    def X(x): return mx+x*sc          # x: along left wall (cm), window at 0 -> left side
    def Y(y): return my+y*sc          # y: from left wall into room
    w=mx*2+roomL*sc; h=my*2+roomW*sc+40
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" font-family="Hiragino Sans, Noto Sans JP, sans-serif">',
       '<rect width="100%" height="100%" fill="#fafaf7"/>',
       f'<text x="{w/2:.0f}" y="44" text-anchor="middle" font-size="26" font-weight="700" fill="#222">{title}</text>',
       f'<text x="{w/2:.0f}" y="72" text-anchor="middle" font-size="15" fill="#555">{note}</text>']
    # floor
    s.append(f'<rect x="{X(0)}" y="{Y(0)}" width="{roomL*sc}" height="{roomW*sc}" fill="#f1e4cf"/>')
    # window wall (X=0) thick line
    s.append(f'<rect x="{X(0)-14}" y="{Y(0)-14}" width="14" height="{roomW*sc+28}" fill="#444"/>')
    s.append(f'<rect x="{X(0)-10}" y="{Y(5)}" width="6" height="{255*sc}" fill="#9cc9e8"/>')  # window glass
    s.append(f'<text x="{X(0)-70}" y="{Y(roomW/2)}" font-size="16" fill="#333" transform="rotate(-90 {X(0)-70} {Y(roomW/2)})" text-anchor="middle">奥の窓・カーテン（窓側）</text>')
    # left wall 175cm (Y=0) from X=0 to 175
    s.append(f'<rect x="{X(0)}" y="{Y(0)-14}" width="{wall*sc}" height="14" fill="#444"/>')
    # door opening after wall end (sliding door) dashed
    s.append(f'<line x1="{X(wall)}" y1="{Y(0)-7}" x2="{X(roomL)}" y2="{Y(0)-7}" stroke="#888" stroke-width="3" stroke-dasharray="10 8"/>')
    s.append(f'<text x="{X(wall+(roomL-wall)/2)+30}" y="{Y(0)-46}" font-size="14" fill="#666" text-anchor="middle">引き戸開口（壁なし）→ キッチン側</text>')
    # right wall (TV)
    s.append(f'<rect x="{X(0)}" y="{Y(roomW)}" width="{roomL*sc}" height="14" fill="#444"/>')
    s.append(f'<rect x="{X(10)}" y="{Y(roomW-42)}" width="{130*sc}" height="{42*sc}" fill="#c9a97c" stroke="#8a6a3f"/><text x="{X(75)}" y="{Y(roomW-18)}" font-size="13" text-anchor="middle" fill="#333">テレビボード</text>')
    # wall label
    s.append(f'<text x="{X(wall/2)}" y="{Y(0)-46}" font-size="15" fill="#222" text-anchor="middle">左側の壁 175cm（ソファー背面）</text>')
    # existing table (approx from photo) dashed
    s.append(f'<polygon points="{X(23)},{Y(137)} {X(113)},{Y(186)} {X(93)},{Y(231)} {X(3)},{Y(182)}" fill="none" stroke="#b46" stroke-width="2" stroke-dasharray="6 5"/>')
    s.append(f'<text x="{X(58)}" y="{Y(250)}" font-size="12" fill="#b46" text-anchor="middle">現ローテーブル 100×50（写真から推定位置）</text>')
    s.append(f'<text x="{X(58)}" y="{Y(266)}" font-size="11" fill="#b46" text-anchor="middle">※カウチ前端(150cm)と約13cm重なる → 右へ15cm以上移動が必要</text>')
    # sofa: chaise at window side X 0..chaise_w, depth chaise_d ; body X chaise_w..W, depth sofa_d
    gap=2
    s.append(f'<rect x="{X(0)}" y="{Y(gap)}" width="{chaise_w*sc}" height="{chaise_d*sc}" fill="{color_fill}" stroke="#333" stroke-width="2" rx="6"/>')
    s.append(f'<rect x="{X(chaise_w)}" y="{Y(gap)}" width="{(W-chaise_w)*sc}" height="{sofa_d*sc}" fill="{color_fill}" stroke="#333" stroke-width="2" rx="6"/>')
    # back cushions band
    s.append(f'<rect x="{X(0)+3}" y="{Y(gap)+3}" width="{W*sc-6}" height="{18*sc}" fill="rgba(0,0,0,0.12)" rx="4"/>')
    s.append(f'<text x="{X(chaise_w/2)}" y="{Y(gap+chaise_d/2+30)}" font-size="14" text-anchor="middle" fill="#222">カウチ</text>')
    s.append(f'<text x="{X(chaise_w/2)}" y="{Y(gap+chaise_d/2+48)}" font-size="12" text-anchor="middle" fill="#222">{chaise_w}×{chaise_d}cm</text>')
    s.append(f'<text x="{X(chaise_w+(W-chaise_w)/2)}" y="{Y(gap+sofa_d/2+10)}" font-size="14" text-anchor="middle" fill="#222">{model}</text>')
    s.append(f'<text x="{X(chaise_w+(W-chaise_w)/2)}" y="{Y(gap+sofa_d/2+28)}" font-size="12" text-anchor="middle" fill="#222">{W-chaise_w}×{sofa_d}cm</text>')
    # overhang hatch
    s.append('<defs><pattern id="h" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="8" stroke="#d33" stroke-width="3"/></pattern></defs>')
    s.append(f'<rect x="{X(wall)}" y="{Y(gap)}" width="{over*sc}" height="{sofa_d*sc}" fill="url(#h)" opacity="0.55"/>')
    # dimension lines
    def dim(x1,x2,y,label,col='#111',above=True):
        yy=Y(y); 
        s.append(f'<line x1="{X(x1)}" y1="{yy}" x2="{X(x2)}" y2="{yy}" stroke="{col}" stroke-width="2"/>')
        for x in (x1,x2): s.append(f'<line x1="{X(x)}" y1="{yy-8}" x2="{X(x)}" y2="{yy+8}" stroke="{col}" stroke-width="2"/>')
        s.append(f'<text x="{X((x1+x2)/2)}" y="{yy-8 if above else yy+22}" font-size="15" font-weight="700" fill="{col}" text-anchor="middle">{label}</text>')
    dim(0,W,chaise_d+gap+26,f'ソファー全幅 {W}cm')
    dim(0,wall,chaise_d+gap+58,'壁 175cm')
    dim(wall,W,chaise_d+gap+58,f'はみ出し {over}cm','#d33',above=False)
    # vertical dims
    def vdim(x,y1,y2,label,col='#111'):
        xx=X(x); s.append(f'<line x1="{xx}" y1="{Y(y1)}" x2="{xx}" y2="{Y(y2)}" stroke="{col}" stroke-width="2"/>')
        for y in (y1,y2): s.append(f'<line x1="{xx-8}" y1="{Y(y)}" x2="{xx+8}" y2="{Y(y)}" stroke="{col}" stroke-width="2"/>')
        s.append(f'<text x="{xx+10}" y="{Y((y1+y2)/2)+5}" font-size="14" fill="{col}">{label}</text>')
    vdim(-24,gap,gap+chaise_d,f'カウチ奥行 {chaise_d}cm')
    vdim(W+16,gap,gap+sofa_d,f'奥行 {sofa_d}cm')
    # wall end marker
    s.append(f'<line x1="{X(wall)}" y1="{Y(0)-14}" x2="{X(wall)}" y2="{Y(chaise_d+gap+72)}" stroke="#d33" stroke-width="2" stroke-dasharray="5 4"/>')
    s.append(f'<text x="{X(wall)+6}" y="{Y(0)-22}" font-size="13" fill="#d33">壁の終端 (175cm)</text>')
    # north/direction labels
    s.append(f'<text x="{X(roomL)-10}" y="{Y(roomW/2)}" font-size="16" fill="#333" text-anchor="end">→ キッチン側（手前）</text>')
    s.append(f'<text x="{X(5)}" y="{Y(roomW)-10}" font-size="12" fill="#666">部屋幅 約{roomW}cm（写真から推定）</text>')
    s.append(f'<text x="{mx}" y="{h-18}" font-size="12" fill="#777">縮尺 1cm = {sc}px / 壁175cm基準。ソファー背面と壁の隙間 {gap}cm で作図。</text>')
    s.append('</svg>'); return '\n'.join(s)
specs={
 'manner': dict(model='マナー④ 2Pソファ', W=215, sofa_d=86.5, chaise_w=73, chaise_d=150, color_fill='#8b6a4f', title='上面配置図 A/B：マナー④（関家具 nora.）幅215cm', note='背面＝左側の壁(175cm)、カウチ＝奥の窓側、キッチン側へ40cmはみ出し'),
 'graciero': dict(model='グラシエーロⅡ 1.5P', W=222, sofa_d=94, chaise_w=100, chaise_d=150, color_fill='#8f8f8c', title='上面配置図 C/D：グラシエーロⅡ（RELAX FORM）幅222cm', note='背面＝左側の壁(175cm)、シェーズロング＝奥の窓側、キッチン側へ47cmはみ出し'),
}
for k,v in specs.items():
    open(S+f'/out/plan_{k}.svg','w').write(plan(**v))
print('ok')
