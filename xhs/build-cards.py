#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成小红书图文笔记的 7 张卡片（3:4 竖版，1080x1440）。

小红书是翻图的场子：一张卡只讲一件事，字要大到扫一眼就懂。
配色和母题沿用公众号版，两边看起来是同一个系列。

    python3 xhs/build-cards.py 2 && for f in images/xhs2_*.svg; do
        rsvg-convert -w 1080 -o "${f%.svg}.png" "$f"; done

卡片内容按课号分支，加新课就在 LESSON 分支里再写一段。
"""
import io, os

CJK  = "Noto Sans CJK SC, PingFang SC, Microsoft YaHei, sans-serif"
MONO = "JetBrains Mono, DejaVu Sans Mono, Menlo, monospace"
INK, MUTED, SEAM, SEAM_SOFT, SURFACE, LINE, ACC_SOFT = \
    '#1f2937', '#6b7280', '#be123c', '#ffe4e6', '#f3f4f6', '#9ca3af', '#dbeafe'
W, H, M = 540, 720, 48          # viewBox；渲染时放大到 1080 宽
TOTAL = 7


def t(x, y, s, size=16, fill=MUTED, anchor='start', fam=CJK, wt='400', ls=None):
    a = ' letter-spacing="%s"' % ls if ls else ''
    return ('<text x="%g" y="%g" text-anchor="%s" font-family="%s" font-size="%g" '
            'font-weight="%s" fill="%s"%s>%s</text>' % (x, y, anchor, fam, size, wt, fill, a, s))


def tile(x, y, w, h, ch, hi=False, size=20, r=7, fam=MONO):
    return ('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" stroke="%s" stroke-width="1.6"/>'
            '<text x="%g" y="%g" text-anchor="middle" font-family="%s" font-size="%g" font-weight="%s" fill="%s">%s</text>'
            % (x, y, w, h, r, SEAM_SOFT if hi else SURFACE, SEAM if hi else LINE,
               x + w / 2.0, y + h / 2.0 + size * 0.35, fam, size, '600' if hi else '400',
               SEAM if hi else INK, ch))


def card(n, parts, eyebrow=True):
    """统一的卡片外框：切缝、眉标、页码。"""
    p = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
         'aria-label="从零看懂大模型 第 1 课 第 %d 张">' % (W, H, W * 2, H * 2, n),
         '<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H),
         '<line x1="26" y1="72" x2="26" y2="648" stroke="%s" stroke-width="2.5" stroke-dasharray="6 5"/>' % SEAM]
    if eyebrow:
        p.append(t(M, 84, '从零看懂大模型 · 第 %d 课' % LESSON, 14, SEAM, fam=MONO, wt='600', ls='1.8'))
    p += parts
    p.append(t(W - M, 686, '%d / %d' % (n, TOTAL), 13, LINE, anchor='end', fam=MONO))
    p.append('</svg>')
    return ''.join(p)


LET, HI = 'strawberry', {2, 7, 8}
LESSON = int(__import__('sys').argv[1]) if len(__import__('sys').argv) > 1 else 1
cards = []

if LESSON == 1:

    # ---- 1 封面：钩子 ----
    p = [t(M, 268, '它能写代码，', 46, INK, wt='700'),
         t(M, 332, '却数不清', 46, INK, wt='700'),
         t(M, 404, '三个 r', 56, SEAM, wt='700')]
    x0, step, cw = 53, 44, 38
    for i, c in enumerate(LET):
        p.append(tile(x0 + i * step, 470, cw, cw, c, i in HI, 18, 6))
    p.append(t(W / 2, 542, '它看不见这三个 r', 16, MUTED, anchor='middle'))
    cards.append(card(1, p))

    # ---- 2 问题与答案 ----
    p = [t(W / 2, 200, '单词', 24, MUTED, anchor='middle'),
         t(W / 2, 256, 'strawberry', 40, INK, anchor='middle', fam=MONO, wt='600'),
         t(W / 2, 312, '里有几个字母 r ？', 28, INK, anchor='middle'),
         t(W / 2, 470, '3', 130, SEAM, anchor='middle', fam=MONO, wt='600'),
         t(W / 2, 516, '正确答案', 20, MUTED, anchor='middle'),
         t(W / 2, 590, '这道题曾经是所有大模型的集体翻车现场', 17, MUTED, anchor='middle'),
         t(W / 2, 618, '它们几乎清一色地回答 2', 17, MUTED, anchor='middle')]
    cards.append(card(2, p))

    # ---- 3 核心反差：你看见的 vs 它看见的 ----
    p = [t(M, 150, '同一个单词，两种看法', 26, INK, wt='700'), t(M, 208, '你看见的', 16, MUTED)]
    for i, c in enumerate(LET):
        p.append(tile(x0 + i * step, 226, cw, cw, c, i in HI, 18, 6))
    p.append(t(W / 2, 298, '10 个字母，三个 r 一眼可见', 15, MUTED, anchor='middle'))
    p.append(t(M, 372, '它看见的', 16, MUTED))
    for tx, tw, lab in ((53, 126, 'str'), (185, 82, 'aw'), (273, 214, 'berry')):
        p.append(tile(tx, 390, tw, cw, lab, False, 20, 7))
    for sx in (181, 269):
        for (ya, yb) in ((216, 272), (378, 436)):        # 断开，避开中间那行说明文字
            p.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="1.6" '
                     'stroke-dasharray="4 4" opacity="0.7"/>' % (sx, ya, sx, yb, SEAM))
    p.append(t(W / 2, 462, '3 个块。r 全藏在块的内部', 15, MUTED, anchor='middle'))
    p += [t(M, 556, '它不是笨。', 26, INK, wt='700'),
          t(M, 600, '是它看到的东西', 26, INK, wt='700'),
          t(M, 644, '和你看到的不一样。', 26, SEAM, wt='700')]
    cards.append(card(3, p))

    # ---- 4 三种切法 ----
    p = [t(M, 150, '为什么切成这种碎片', 26, INK, wt='700')]
    rows = [(196, '✗ 按字母切', '序列长到吓人，单个字母不带意思', 'tokenization', None, False),
            (356, '✗ 按整词切', '词表爆炸，遇到生词直接失明', 'tokenization', '???', False),
            (516, '✓ 按碎片切', '词表可控，任何词都拼得出来', 'token', 'ization', True)]
    for (ry, name, why, a, b, win) in rows:
        p.append('<rect x="%d" y="%d" width="%d" height="128" rx="10" fill="%s" stroke="%s" stroke-width="1.6"/>'
                 % (M, ry, W - 2 * M, ACC_SOFT if win else SURFACE, SEAM if win else LINE))
        p.append(t(M + 20, ry + 34, name, 19, SEAM if win else INK, wt='700'))
        p.append(t(M + 20, ry + 60, why, 14, MUTED))
        if ry == 196:                                    # 逐字母：12 个小格
            for i, c in enumerate(a):
                p.append(tile(M + 20 + i * 34, ry + 76, 30, 34, c, False, 15, 5))
        elif b == '???':
            p.append(tile(M + 20, ry + 76, 220, 34, a, False, 16, 6))
            p.append(tile(M + 256, ry + 76, 80, 34, b, True, 16, 6))
        else:
            p.append(tile(M + 20, ry + 76, 150, 34, a, False, 16, 6))
            p.append(tile(M + 178, ry + 76, 180, 34, b, False, 16, 6))
            p.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="1.6" '
                     'stroke-dasharray="4 4"/>' % (M + 174, ry + 70, M + 174, ry + 116, SEAM))
    cards.append(card(4, p))

    # ---- 5 这些碎片叫 token ----
    p = [t(M, 178, '这些碎片有个名字', 26, INK, wt='700'),
         t(W / 2, 320, 'token', 76, SEAM, anchor='middle', fam=MONO, wt='600'),
         t(M, 420, '你听过的"上下文 100 万 token"', 19, INK),
         t(M, 456, '"API 按 token 计费"，说的就是它。', 19, INK),
         t(M, 536, '为什么按 token 计费而不是按字数？', 16, MUTED),
         t(M, 566, '因为 token 才是模型真正处理的单位。', 16, MUTED),
         t(M, 596, '同样意思的一句话，中文和英文切出来的', 16, MUTED),
         t(M, 626, '块数不一样，字数相同费用可能差不少。', 16, MUTED)]
    cards.append(card(5, p))

    # ---- 6 自己试一下 ----
    p = ['<rect x="%d" y="150" width="%d" height="330" rx="12" fill="%s" stroke="%s" '
         'stroke-width="2" stroke-dasharray="7 5"/>' % (M, W - 2 * M, SEAM_SOFT, SEAM),
         t(M + 24, 196, '自己试一下（30 秒）', 24, SEAM, wt='700'),
         t(M + 24, 236, '搜"tokenizer 在线"，把这些贴进去，', 16, INK),
         t(M + 24, 264, '看看各自被切成几块：', 16, INK)]
    for i, item in enumerate(('你的名字，中文和拼音各试一次', 'strawberry',
                              '一个长数字，比如 20260903', '一句你平时会问 AI 的话')):
        p.append(t(M + 30, 306 + i * 38, '·', 18, SEAM, wt='700'))
        p.append(t(M + 48, 306 + i * 38, item, 16, INK))
    p.append(t(M + 24, 460, '你会发现切法完全不像你的直觉。', 16, MUTED))
    p += [t(M, 556, '把"碎片"从一个说法，', 24, INK, wt='700'),
          t(M, 598, '变成你亲眼见过的东西。', 24, SEAM, wt='700')]
    cards.append(card(6, p))

    # ---- 7 预告 ----
    p = [t(M, 168, '但 token 还是文字。', 24, INK, wt='700'),
         t(M, 210, '而模型只会算数——它算不了 berry。', 18, MUTED),
         t(M, 286, '所以还要再走一步：', 18, INK),
         t(M, 328, '每个 token 换成一串数字。', 26, SEAM, wt='700')]
    for tx, tw, lab, hi in ((M, 120, 'berry', False), (M + 136, 96, '15717', False)):
        p.append(tile(tx, 360, tw, 46, lab, hi, 20, 8))
    p.append('<rect x="%d" y="360" width="180" height="46" rx="8" fill="%s" stroke="%s" stroke-width="1.6"/>'
             % (M + 248, ACC_SOFT, '#2563eb'))
    p.append(t(M + 338, 390, '0.21 −0.88 …', 15, '#2563eb', anchor='middle', fam=MONO, wt='600'))
    p += [t(M, 464, 'cat 和 kitten 拼写差很远，', 18, INK),
          t(M, 496, '换出来的数字却挨得很近。甚至能做加减法：', 18, INK),
          t(M, 560, '国王 − 男人 + 女人 ≈ 女王', 26, SEAM, wt='700'),
          '<line x1="%d" y1="596" x2="%d" y2="596" stroke="%s" stroke-width="2" stroke-dasharray="6 5"/>' % (M, W - M, SEAM),
          t(M, 630, '下一课讲这个 →', 20, SEAM, wt='700')]
    cards.append(card(7, p))


if LESSON == 2:
    # ---- 1 封面：把答案藏起来 ----
    p = [t(M, 268, '国王 − 男人', 44, INK, wt='700'),
         t(M, 326, '+ 女人', 44, INK, wt='700'),
         t(M, 404, '= ？', 62, SEAM, wt='700'),
         '<rect x="%d" y="470" width="300" height="44" rx="8" fill="%s" stroke="%s" stroke-width="1.6"/>' % (M, SEAM_SOFT, SEAM),
         t(M + 150, 500, '0.21  −0.88  0.34  …', 18, SEAM, anchor='middle', fam=MONO, wt='600'),
         t(M, 552, '每个词，都是一串数字', 16, MUTED)]
    cards.append(card(1, p))

    # ---- 2 答案 ----
    p = [t(W / 2, 210, '国王 − 男人 + 女人 =', 26, INK, anchor='middle'),
         t(W / 2, 340, '女王', 92, SEAM, anchor='middle', wt='700'),
         t(W / 2, 430, '不是文字游戏。', 20, INK, anchor='middle'),
         t(W / 2, 466, '也没有人把这条规则写进程序。', 20, INK, anchor='middle'),
         t(W / 2, 540, '是模型自己算出来的——', 17, MUTED, anchor='middle'),
         t(W / 2, 570, '真的在做加减法，加减的对象是"词"。', 17, MUTED, anchor='middle')]
    cards.append(card(2, p))

    # ---- 3 查表 ----
    p = [t(M, 150, '第一步：查一张表', 26, INK, wt='700'),
         t(M, 190, '模型内部有十几万行的一张表', 15, MUTED)]
    rows = [('0', '!', '0.03  −0.44  …', False), ('…', '…', '…', False),
            ('15717', 'berry', '0.21  −0.88  …', True), ('…', '…', '…', False)]
    for i, (rid, tok, num, hi) in enumerate(rows):
        y = 214 + i * 46
        p.append('<rect x="%d" y="%d" width="%d" height="40" rx="6" fill="%s" stroke="%s" stroke-width="%g"/>'
                 % (M, y, W - 2 * M, SEAM_SOFT if hi else '#ffffff', SEAM if hi else LINE, 1.5 if hi else 1))
        p.append(t(M + 14, y + 26, rid, 13, SEAM if hi else MUTED, fam=MONO, wt='600' if hi else '400'))
        p.append(t(M + 86, y + 26, tok, 15, SEAM if hi else INK, fam=MONO, wt='600' if hi else '400'))
        p.append(t(M + 190, y + 26, num, 14, SEAM if hi else MUTED, fam=MONO))
    p += [t(M, 448, '按行号取出那一行：4096 个数字。', 16, INK),
          t(M, 478, '这就是这个词的"坐标"。', 16, INK),
          t(M, 556, '这张表里的数字，', 24, INK, wt='700'),
          t(M, 598, '没有任何人写过。', 24, SEAM, wt='700')]
    cards.append(card(3, p))

    # ---- 4 表是学出来的 ----
    p = [t(M, 150, '那是谁填的？', 26, INK, wt='700'),
         '<rect x="%d" y="188" width="%d" height="96" rx="10" fill="%s" stroke="%s" stroke-width="1.5"/>' % (M, W - 2 * M, SURFACE, LINE),
         t(M + 20, 222, '刚造出来时', 15, MUTED),
         t(M + 20, 258, '全是随机数，一串乱码', 20, INK, wt='600'),
         t(W / 2, 316, '↓  看大量文本，反复猜下一个词  ↓', 15, SEAM, anchor='middle', wt='600'),
         '<rect x="%d" y="336" width="%d" height="96" rx="10" fill="%s" stroke="%s" stroke-width="1.6"/>' % (M, W - 2 * M, SEAM_SOFT, SEAM),
         t(M + 20, 370, '调了亿万次之后', 15, SEAM),
         t(M + 20, 406, '意思相近的词，数字也相近', 20, SEAM, wt='700'),
         t(M, 500, '没人告诉过它"猫和小猫是近义词"。', 16, INK),
         t(M, 532, '是它为了把下一个词猜得更准，', 16, INK),
         t(M, 564, '自己发现放近一点更划算。', 16, INK),
         t(M, 626, '这是副产品，不是设计出来的功能。', 15, MUTED)]
    cards.append(card(4, p))

    # ---- 5 意思变成距离 ----
    p = [t(M, 150, '于是"意思"变成了位置', 26, INK, wt='700'),
         '<rect x="%d" y="182" width="%d" height="300" rx="12" fill="#fcfcfd" stroke="%s" stroke-width="1.2"/>' % (M, W - 2 * M, LINE)]
    for (cx, cy, r, name, col, soft, pts) in (
            (170, 268, 74, '王室', '#2563eb', '#dbeafe', [(146, 240, '国王'), (196, 262, '女王'), (158, 306, '王子')]),
            (378, 396, 66, '动物', SEAM, SEAM_SOFT, [(352, 372, '猫'), (398, 392, '小猫'), (378, 440, '狗')])):
        p.append('<circle cx="%g" cy="%g" r="%g" fill="%s" stroke="%s" stroke-width="1.4" stroke-dasharray="5 4"/>'
                 % (cx, cy, r, soft, col))
        p.append(t(cx, cy - r - 10, name, 13, col, anchor='middle', wt='600'))
        for (x, y, lab) in pts:
            p.append('<circle cx="%g" cy="%g" r="4" fill="%s"/>' % (x, y, col))
            p.append(t(x + 9, y + 5, lab, 14, INK, wt='600'))
    p += [t(M + 12, 470, '图上只画了两维，真实是 4096 维', 13, MUTED),
          t(M, 540, 'cat 和 kitten 拼写差很远，', 17, INK),
          t(M, 572, '位置却很近——因为位置来自', 17, INK),
          t(M, 604, '它出现在什么语境里，不是怎么拼。', 17, SEAM, wt='600')]
    cards.append(card(5, p))

    # ---- 6 平行四边形 ----
    p = [t(M, 150, '所以词能做加减法', 26, INK, wt='700'),
         '<rect x="%d" y="184" width="%d" height="264" rx="12" fill="#fcfcfd" stroke="%s" stroke-width="1.2"/>' % (M, W - 2 * M, LINE),
         '<path d="M120 376 L196 260 L372 260 L296 376 Z" fill="%s" opacity="0.4"/>' % SURFACE]
    for (x1, y1, x2, y2) in ((120, 376, 196, 260), (296, 376, 372, 260)):
        p.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="2.4" marker-end="url(#a2)"/>'
                 % (x1, y1, x2, y2, SEAM))
    p.append('<defs><marker id="a2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
             'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="%s"/></marker></defs>' % SEAM)
    for (x, y, lab, below) in ((120, 376, '男人', True), (196, 260, '国王', False),
                               (296, 376, '女人', True), (372, 260, '女王', False)):
        p.append('<circle cx="%g" cy="%g" r="5" fill="%s"/>' % (x, y, MUTED))
        p.append(t(x, y + 26 if below else y - 14, lab, 16, INK, anchor='middle', wt='700'))
    p += [t(144, 330, '+ 王室', 13, SEAM, anchor='end', wt='600'),
          t(320, 330, '+ 王室', 13, SEAM, anchor='end', wt='600'),
          t(W / 2, 434, '两条箭头一样长、一样的方向', 14, MUTED, anchor='middle'),
          t(M, 510, '因为它们代表同一件事：', 17, INK),
          t(M, 552, '加上"王室身份"。', 24, SEAM, wt='700'),
          t(M, 620, '这条关系没有任何人写进去过。', 15, MUTED)]
    cards.append(card(6, p))

    # ---- 7 悬念 ----
    p = [t(M, 158, '但还有个问题', 26, INK, wt='700'),
         t(M, 206, 'the cat sat on the mat 里', 17, INK, fam=MONO),
         t(M, 240, '有两个 the。', 17, INK),
         t(M, 292, '它们查的是同一行，', 18, INK),
         t(M, 326, '拿到完全相同的数字。', 22, SEAM, wt='700'),
         '<rect x="%d" y="360" width="%d" height="88" rx="10" fill="%s" stroke="%s" stroke-width="1.5"/>' % (M, W - 2 * M, SURFACE, LINE),
         t(M + 18, 392, '位置丢了', 17, INK, wt='700'),
         t(M + 18, 424, '"狗咬人"和"人咬狗"用的字一样', 14, MUTED),
         '<rect x="%d" y="462" width="%d" height="88" rx="10" fill="%s" stroke="%s" stroke-width="1.5"/>' % (M, W - 2 * M, SURFACE, LINE),
         t(M + 18, 494, '语境丢了', 17, INK, wt='700'),
         t(M + 18, 526, '"河岸"和"银行"是同一个 bank', 14, MUTED),
         '<line x1="%d" y1="584" x2="%d" y2="584" stroke="%s" stroke-width="2" stroke-dasharray="6 5"/>' % (M, W - M, SEAM),
         t(M, 618, '下一课讲这个 →', 20, SEAM, wt='700')]
    cards.append(card(7, p))

os.makedirs('images', exist_ok=True)
for i, svg in enumerate(cards, 1):
    f = 'images/xhs%d_%02d.svg' % (LESSON, i)
    io.open(f, 'w', encoding='utf-8').write(svg)
    print('wrote', f)
