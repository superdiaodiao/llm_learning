#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成每一课的两版封面：2.35:1 首图 + 1:1 方图。

两版分别构图，不能靠裁——中心裁 2.35:1 那张会把标题从中间切断。

    python3 wechat/build-cover.py 1
    python3 wechat/build-cover.py 2        # 不带参数则全部重出
"""
import io
import sys

CJK  = "Noto Sans CJK SC, PingFang SC, Microsoft YaHei, sans-serif"
MONO = "JetBrains Mono, DejaVu Sans Mono, Menlo, monospace"
INK, MUTED, SEAM, SEAM_SOFT, SURFACE, LINE = \
    '#1f2937', '#6b7280', '#be123c', '#ffe4e6', '#f3f4f6', '#9ca3af'

# 每课只需配这一段：标题怎么断行、底部用什么视觉签名。
LESSONS = {
    1: {
        'slug':  'wx1',
        'wide':  [('它能写代码，', INK, 62), ('却数不清 |三个 r|', INK, 62)],
        'square': [('它能写代码，', INK, 44), ('却数不清', INK, 44), ('三个 r', SEAM, 54)],
        'motif': ('tiles', 'strawberry', {2, 7, 8}),
        'caption': '它看不见这三个 r',
    },
    2: {
        'slug':  'wx2',
        'wide':  [('国王 − 男人 + 女人', INK, 58), ('|= ？|', SEAM, 76)],
        'square': [('国王 − 男人', INK, 44), ('+ 女人', INK, 44), ('= ？', SEAM, 62)],
        'motif': ('strip', '0.21  −0.88  0.34  …', None),
        'caption': '每个词，都是一串数字',
    },
}


def line(x, y, s, fill, size):
    """竖线包住的片段上强调色：'却数不清 |三个 r|'。"""
    if '|' in s:
        a, mid, b = s.split('|')[0], s.split('|')[1], s.split('|')[2]
        inner = '%s<tspan dx="%g" fill="%s">%s</tspan>%s' % (a, 7 if a else 0, SEAM, mid, b)
        fill = INK if a else fill
    else:
        inner = s
    return ('<text x="%g" y="%g" font-family="%s" font-size="%g" font-weight="700" '
            'fill="%s">%s</text>' % (x, y, CJK, size, fill, inner))


def motif(kind, data, hi, x0, y, cw, step, tw):
    """底部视觉签名：字母方块，或一条数字带。"""
    out = []
    if kind == 'tiles':
        for i, c in enumerate(data):
            h = i in hi
            out.append('<rect x="%g" y="%g" width="%g" height="%g" rx="6" fill="%s" stroke="%s" '
                       'stroke-width="1.5"/>' % (x0 + i * step, y, cw, cw, SEAM_SOFT if h else SURFACE,
                                                 SEAM if h else LINE))
            out.append('<text x="%g" y="%g" text-anchor="middle" font-family="%s" font-size="%g" '
                       'font-weight="%s" fill="%s">%s</text>'
                       % (x0 + i * step + cw / 2, y + cw / 2 + 6, MONO, cw * 0.46,
                          '600' if h else '400', SEAM if h else INK, c))
    else:
        out.append('<rect x="%g" y="%g" width="%g" height="%g" rx="8" fill="%s" stroke="%s" '
                   'stroke-width="1.6"/>' % (x0, y, tw, cw, SEAM_SOFT, SEAM))
        out.append('<text x="%g" y="%g" text-anchor="middle" font-family="%s" font-size="%g" '
                   'font-weight="600" fill="%s">%s</text>'
                   % (x0 + tw / 2, y + cw / 2 + 7, MONO, cw * 0.5, SEAM, data))
    return out


def build(n):
    L = LESSONS[n]
    kind, data, hi = L['motif']

    # ---------- 2.35:1 首图 ----------
    W, H = 900, 383
    p = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
         'role="img" aria-label="封面：从零看懂大模型 第 %d 课">' % (W, H, W * 2, H * 2, n),
         '<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H),
         '<line x1="46" y1="64" x2="46" y2="319" stroke="%s" stroke-width="3" stroke-dasharray="7 6"/>' % SEAM,
         '<text x="76" y="92" font-family="%s" font-size="17" font-weight="600" letter-spacing="3.2" '
         'fill="%s">从零看懂大模型 · 第 %d 课</text>' % (MONO, SEAM, n)]
    y = 186
    for (s, fill, size) in L['wide']:
        p.append(line(76, y, s, fill, size))
        y += size + 14
    if kind == 'tiles':
        p += motif(kind, data, hi, 76, 296, 32, 36, 0)
        cx = 76 + 10 * 36 + 14
        p.append('<text x="%g" y="319" font-family="%s" font-size="16" fill="%s">← %s</text>'
                 % (cx, CJK, MUTED, L['caption']))
    else:
        p += motif(kind, data, hi, 76, 292, 40, 0, 300)
        p.append('<text x="392" y="319" font-family="%s" font-size="16" fill="%s">← %s</text>'
                 % (CJK, MUTED, L['caption']))
    p.append('</svg>')
    io.open('images/%s_cover.svg' % L['slug'], 'w', encoding='utf-8').write(''.join(p))

    # ---------- 1:1 方图（单独构图） ----------
    S = 383
    q = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
         'role="img" aria-label="方形封面：从零看懂大模型 第 %d 课">' % (S, S, S * 2, S * 2, n),
         '<rect width="%d" height="%d" fill="#ffffff"/>' % (S, S),
         '<line x1="22" y1="44" x2="22" y2="340" stroke="%s" stroke-width="2.5" stroke-dasharray="6 5"/>' % SEAM,
         '<text x="44" y="58" font-family="%s" font-size="13" font-weight="600" letter-spacing="2.4" '
         'fill="%s">从零看懂大模型 · 第 %d 课</text>' % (MONO, SEAM, n)]
    y = 142
    for (s, fill, size) in L['square']:
        q.append(line(44, y, s, fill, size))
        y += size + 14
    if kind == 'tiles':
        q += motif(kind, data, hi, 44, 288, 27, 30, 0)
    else:
        q += motif(kind, data, hi, 44, 284, 34, 0, 295)
    q.append('<text x="44" y="338" font-family="%s" font-size="14" fill="%s">%s</text>'
             % (CJK, MUTED, L['caption']))
    q.append('</svg>')
    io.open('images/%s_cover_square.svg' % L['slug'], 'w', encoding='utf-8').write(''.join(q))
    print('images/%s_cover.svg  900x383 (2.35:1)\nimages/%s_cover_square.svg  383x383 (1:1)'
          % (L['slug'], L['slug']))


if __name__ == '__main__':
    for n in ([int(a) for a in sys.argv[1:]] or sorted(LESSONS)):
        build(n)
