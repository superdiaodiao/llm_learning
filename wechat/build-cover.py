# -*- coding: utf-8 -*-
import io
CJK  = "Noto Sans CJK SC, PingFang SC, Microsoft YaHei, sans-serif"
MONO = "JetBrains Mono, DejaVu Sans Mono, Menlo, monospace"
INK, MUTED, SEAM, SEAM_SOFT, SURFACE, LINE = '#1f2937', '#6b7280', '#be123c', '#ffe4e6', '#f3f4f6', '#9ca3af'
W, H = 900, 383                     # 公众号首图 2.35:1

p = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
     'role="img" aria-label="封面：它能写代码，却数不清三个 r">' % (W, H, W*2, H*2),
     '<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H)]

# 左侧一道竖切缝，呼应正文里的母题
p.append('<line x1="46" y1="64" x2="46" y2="319" stroke="%s" stroke-width="3" stroke-dasharray="7 6"/>' % SEAM)

p.append('<text x="76" y="92" font-family="%s" font-size="17" font-weight="600" letter-spacing="3.2" fill="%s">从零看懂大模型 · 第 1 课</text>'
         % (MONO, SEAM))

# 主标题两行，"三个 r" 单独上强调色
p.append('<text x="76" y="186" font-family="%s" font-size="62" font-weight="700" fill="%s">它能写代码，</text>' % (CJK, INK))
p.append('<text x="76" y="262" font-family="%s" font-size="62" font-weight="700" fill="%s">却数不清<tspan dx="7" fill="%s">三个 r</tspan></text>'
         % (CJK, INK, SEAM))

# 底部字母带：缩略图下读作"一串方块 + 三点红"，是钩子也是签名
x0, step, cw = 76, 36, 32
for i, c in enumerate('strawberry'):
    hi = i in (2, 7, 8)
    p.append('<rect x="%d" y="296" width="%d" height="%d" rx="6" fill="%s" stroke="%s" stroke-width="1.5"/>'
             % (x0+i*step, cw, cw, SEAM_SOFT if hi else SURFACE, SEAM if hi else LINE))
    p.append('<text x="%d" y="318" text-anchor="middle" font-family="%s" font-size="17" font-weight="%s" fill="%s">%s</text>'
             % (x0+i*step+cw//2, MONO, '600' if hi else '400', SEAM if hi else INK, c))
p.append('<text x="%d" y="319" font-family="%s" font-size="16" fill="%s">← 它看不见这三个 r</text>'
         % (x0+10*step+14, CJK, MUTED))
p.append('</svg>')

io.open('images/wx1_cover.svg', 'w', encoding='utf-8').write(''.join(p))
print('images/wx1_cover.svg  %dx%d (2.35:1)' % (W, H))

# ---- 1:1 方图：单独构图，标题拆三行，不能靠裁 2.35:1 那张 ----
S = 383
q = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
     'role="img" aria-label="方形封面：它能写代码，却数不清三个 r">' % (S, S, S*2, S*2),
     '<rect width="%d" height="%d" fill="#ffffff"/>' % (S, S),
     '<line x1="22" y1="44" x2="22" y2="340" stroke="%s" stroke-width="2.5" stroke-dasharray="6 5"/>' % SEAM,
     '<text x="44" y="58" font-family="%s" font-size="13" font-weight="600" letter-spacing="2.4" fill="%s">从零看懂大模型 · 第 1 课</text>' % (MONO, SEAM),
     '<text x="44" y="142" font-family="%s" font-size="44" font-weight="700" fill="%s">它能写代码，</text>' % (CJK, INK),
     '<text x="44" y="198" font-family="%s" font-size="44" font-weight="700" fill="%s">却数不清</text>' % (CJK, INK),
     '<text x="44" y="260" font-family="%s" font-size="54" font-weight="700" fill="%s">三个 r</text>' % (CJK, SEAM)]
x0, step, cw = 44, 30, 27
for i, c in enumerate('strawberry'):
    hi = i in (2, 7, 8)
    q.append('<rect x="%d" y="288" width="%d" height="%d" rx="5" fill="%s" stroke="%s" stroke-width="1.4"/>'
             % (x0+i*step, cw, cw, SEAM_SOFT if hi else SURFACE, SEAM if hi else LINE))
    q.append('<text x="%d" y="307" text-anchor="middle" font-family="%s" font-size="15" font-weight="%s" fill="%s">%s</text>'
             % (x0+i*step+cw//2, MONO, '600' if hi else '400', SEAM if hi else INK, c))
q.append('<text x="44" y="338" font-family="%s" font-size="14" fill="%s">它看不见这三个 r</text>' % (CJK, MUTED))
q.append('</svg>')
io.open('images/wx1_cover_square.svg', 'w', encoding='utf-8').write(''.join(q))
print('images/wx1_cover_square.svg  %dx%d (1:1)' % (S, S))
