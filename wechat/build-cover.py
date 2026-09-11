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
    3: {
        'slug':  'wx3',
        'wide':  [('人咬狗和狗咬人，', INK, 58), ('|AI 怎么分得清|', SEAM, 58)],
        'square': [('人咬狗', INK, 46), ('和狗咬人，', INK, 46), ('AI 怎么分得清', SEAM, 42)],
        'motif': ('phrase', '同样三个字，意思相反', None),
        'caption': '顺序，也是信息',
    },
    4: {
        'slug':  'wx4',
        'wide':  [('AI 为什么', INK, 62), ('|每次回答都不一样|', SEAM, 56)],
        'square': [('AI 为什么', INK, 44), ('每次回答', INK, 44), ('都不一样', SEAM, 50)],
        'motif': ('phrase', '它在掷骰子', None),
        'caption': '模型给概率，挑词靠抽签',
    },
    5: {
        'slug':  'wx5',
        'wide':  [('发给 AI 的长文档，', INK, 54), ('|它为什么总忘了前面|', SEAM, 50)],
        'square': [('长文档', INK, 46), ('它为什么', INK, 46), ('总忘了前面', SEAM, 44)],
        'motif': ('phrase', '不是忘了，是没看见', None),
        'caption': '窗口之外，它一个字都看不到',
    },
    6: {
        'slug':  'wx6',
        'wide':  [('没人教它，', INK, 60), ('|AI 是怎么学会说话的|', SEAM, 52)],
        'square': [('没人教它，', INK, 46), ('AI 是怎么', INK, 44), ('学会说话的', SEAM, 46)],
        'motif': ('phrase', '猜下一个词，猜错就改', None),
        'caption': '几万亿次以后，它会了',
    },
    7: {
        'slug':  'wx7',
        'wide':  [('AI 怎么从只会接话，', INK, 52), ('|变成会聊天|', SEAM, 62)],
        'square': [('AI 怎么从', INK, 44), ('只会接话，', INK, 44), ('变成会聊天', SEAM, 46)],
        'motif': ('phrase', '先学格式，再学好坏', None),
        'caption': '它的性格，是这一步教出来的',
    },
    8: {
        'slug':  'wx8',
        'wide':  [('AI 的深度思考，', INK, 56), ('|是怎么练出来的|', SEAM, 56)],
        'square': [('AI 的', INK, 44), ('深度思考，', INK, 44), ('是怎么练出来的', SEAM, 40)],
        'motif': ('phrase', '不教它怎么想，只告诉它对没对', None),
        'caption': '答对的那种想法，就变多',
    },
}

# 合集二「动手用大模型」：同字体同骨架，强调色换蓝，左侧虚线换成勾选框，主图是等宽字体的指令片段。
ACC, ACC_SOFT = '#2563eb', '#dbeafe'
HANDS = {
    1: {
        'slug':  'hx1',
        'wide':  [('跟 AI 说话，', INK, 58), ('|为什么不能像跟人说话|', ACC, 50)],
        'square': [('跟 AI 说话，', INK, 44), ('为什么不能', INK, 44), ('像跟人说话', ACC, 46)],
        'motif': ('cmd', '任务 · 限制 · 材料 · 再说一遍', None),
        'caption': '它每轮从头读，读完就忘',
    },
}


def line(x, y, s, fill, size, accent=SEAM):
    """竖线包住的片段上强调色：'却数不清 |三个 r|'。"""
    if '|' in s:
        a, mid, b = s.split('|')[0], s.split('|')[1], s.split('|')[2]
        inner = '%s<tspan dx="%g" fill="%s">%s</tspan>%s' % (a, 7 if a else 0, accent, mid, b)
        fill = INK if a else fill
    else:
        inner = s
    return ('<text x="%g" y="%g" font-family="%s" font-size="%g" font-weight="700" '
            'fill="%s">%s</text>' % (x, y, CJK, size, fill, inner))


def motif(kind, data, hi, x0, y, cw, step, tw, accent=SEAM, soft=SEAM_SOFT):
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
        fam = CJK if kind == 'phrase' else MONO
        out.append('<rect x="%g" y="%g" width="%g" height="%g" rx="8" fill="%s" stroke="%s" '
                   'stroke-width="1.6"/>' % (x0, y, tw, cw, soft, accent))
        if kind == 'cmd':   # 指令片段：左对齐、带提示符
            out.append('<text x="%g" y="%g" font-family="%s" font-size="%g" font-weight="600" fill="%s">'
                       '<tspan fill="%s">&gt;</tspan> %s</text>'
                       % (x0 + 16, y + cw / 2 + 6, fam, cw * 0.42, INK, accent, data))
        else:
            out.append('<text x="%g" y="%g" text-anchor="middle" font-family="%s" font-size="%g" '
                       'font-weight="600" fill="%s">%s</text>'
                       % (x0 + tw / 2, y + cw / 2 + 7, fam, cw * 0.5, accent, data))
    return out


def marks(x, y0, y1, w, accent, soft, dash):
    """左侧标识：主线是一条红色虚线，合集二是一列蓝色勾选框。"""
    if dash:
        return ['<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="%g" stroke-dasharray="%s"/>'
                % (x, y0, x, y1, accent, w, dash)]
    out = []
    n = 6
    step = (y1 - y0) / n
    for i in range(n):
        yy = y0 + i * step
        s = step * 0.42
        checked = i < 3
        out.append('<rect x="%g" y="%g" width="%g" height="%g" rx="3" fill="%s" stroke="%s" stroke-width="1.8"/>'
                   % (x - s / 2, yy, s, s, soft if checked else '#ffffff', accent))
        if checked:
            out.append('<path d="M%g %g l%g %g l%g %g" stroke="%s" stroke-width="2.4" fill="none" '
                       'stroke-linecap="round" stroke-linejoin="round"/>'
                       % (x - s * 0.3, yy + s * 0.5, s * 0.22, s * 0.22, s * 0.4, -s * 0.44, accent))
    return out


def build(n, series='main'):
    hands = series == 'hands'
    L = (HANDS if hands else LESSONS)[n]
    kind, data, hi = L['motif']
    accent, soft = (ACC, ACC_SOFT) if hands else (SEAM, SEAM_SOFT)
    eyebrow = '动手用大模型' if hands else '从零看懂大模型 · 第 %d 课' % n

    # ---------- 2.35:1 首图 ----------
    W, H = 900, 383
    p = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
         'role="img" aria-label="封面：%s">' % (W, H, W * 2, H * 2, eyebrow),
         '<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H)]
    p += marks(46, 64, 319, 3, accent, soft, '' if hands else '7 6')
    p.append('<text x="76" y="92" font-family="%s" font-size="17" font-weight="600" letter-spacing="3.2" '
             'fill="%s">%s</text>' % (MONO, accent, eyebrow))
    y = 186
    for (s, fill, size) in L['wide']:
        p.append(line(76, y, s, fill, size, accent))
        y += size + 14
    if kind == 'tiles':
        p += motif(kind, data, hi, 76, 296, 32, 36, 0)
        cx = 76 + 10 * 36 + 14
        p.append('<text x="%g" y="319" font-family="%s" font-size="16" fill="%s">← %s</text>'
                 % (cx, CJK, MUTED, L['caption']))
    else:
        tw = 360 if kind == 'cmd' else 300
        p += motif(kind, data, hi, 76, 292, 40, 0, tw, accent, soft)
        p.append('<text x="%g" y="319" font-family="%s" font-size="16" fill="%s">← %s</text>'
                 % (76 + tw + 16, CJK, MUTED, L['caption']))
    p.append('</svg>')
    io.open('images/%s_cover.svg' % L['slug'], 'w', encoding='utf-8').write(''.join(p))

    # ---------- 1:1 方图（单独构图） ----------
    S = 383
    q = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
         'role="img" aria-label="方形封面：%s">' % (S, S, S * 2, S * 2, eyebrow),
         '<rect width="%d" height="%d" fill="#ffffff"/>' % (S, S)]
    q += marks(22, 44, 340, 2.5, accent, soft, '' if hands else '6 5')
    q.append('<text x="44" y="58" font-family="%s" font-size="13" font-weight="600" letter-spacing="2.4" '
             'fill="%s">%s</text>' % (MONO, accent, eyebrow))
    y = 142
    for (s, fill, size) in L['square']:
        q.append(line(44, y, s, fill, size, accent))
        y += size + 14
    if kind == 'tiles':
        q += motif(kind, data, hi, 44, 288, 27, 30, 0)
    else:
        q += motif(kind, data, hi, 44, 284, 34, 0, 295, accent, soft)
    q.append('<text x="44" y="338" font-family="%s" font-size="14" fill="%s">%s</text>'
             % (CJK, MUTED, L['caption']))
    q.append('</svg>')
    io.open('images/%s_cover_square.svg' % L['slug'], 'w', encoding='utf-8').write(''.join(q))
    print('images/%s_cover.svg  900x383 (2.35:1)\nimages/%s_cover_square.svg  383x383 (1:1)'
          % (L['slug'], L['slug']))


if __name__ == '__main__':
    # python3 wechat/build-cover.py 5        主线第 5 课
    # python3 wechat/build-cover.py h1       合集二第 1 篇
    args = sys.argv[1:] or [str(n) for n in sorted(LESSONS)] + ['h%d' % n for n in sorted(HANDS)]
    for a in args:
        if a.startswith('h'):
            build(int(a[1:]), 'hands')
        else:
            build(int(a))
