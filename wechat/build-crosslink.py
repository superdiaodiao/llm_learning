#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成新闻文末"接一课"的可粘贴块（行内样式）。

    python3 wechat/build-crosslink.py 7      # 主线第 7 课
    python3 wechat/build-crosslink.py h1     # 实操第 1 篇
    python3 wechat/build-crosslink.py 7 "它为什么会先夸你一句？"   # 自定义引子
    python3 wechat/build-crosslink.py 8 "引子" "就在今天推送的第 3 条" math   # 第 3 个参数替换"→ 合集"那段（同一次推送时用），第 4 个参数是输出文件后缀

粘贴后，选中课程标题那行，用编辑器"插入链接 → 公众号文章"链到对应文章。
"""
import html
import sys

MAIN = {
    1: ('它为什么连这个都数不清？', '它能写代码，却数不清三个 r'),
    2: ('它是怎么"懂"一个词的？', '国王 − 男人 + 女人 = ？'),
    3: ('它是怎么分清谁跟谁的？', '人咬狗和狗咬人，AI 怎么分得清'),
    4: ('它为什么会编？', 'AI 为什么每次回答都不一样'),
    5: ('它为什么记不住前面？', '发给 AI 的长文档，它为什么总忘了前面'),
    6: ('这些能力是从哪来的？', '没人教它，AI 是怎么学会说话的'),
    7: ('它为什么会先夸你一句？', 'AI 怎么从只会接话，变成会聊天'),
    8: ('它"想一会儿"是在想什么？', 'AI 的深度思考，是怎么练出来的'),
}
HANDS = {
    1: ('想让它听懂，该怎么说？', '跟 AI 说话，为什么不能像跟人说话'),
}

BOX = ('margin:32px 0 0;padding:16px 18px;background:#f6f7f9;border-left:4px solid %s;'
       'border-radius:0 8px 8px 0;')
LEAD = 'margin:0 0 6px;font-size:15px;font-weight:700;color:#1b1f27;line-height:1.7;'
LINE = 'margin:0;font-size:14px;color:#3f3f46;line-height:1.8;'
LINK = 'color:%s;font-weight:600;'
TAG = 'color:#6a7280;'

if __name__ == '__main__':
    key = sys.argv[1]
    hands = key.startswith('h')
    n = int(key[1:] if hands else key)
    lead, title = (HANDS if hands else MAIN)[n]
    if len(sys.argv) > 2:
        lead = sys.argv[2]
    tail = ('　→ ' + sys.argv[3]) if len(sys.argv) > 3 else None
    suffix = ('-' + sys.argv[4]) if len(sys.argv) > 4 else ''
    accent = '#2563eb' if hands else '#be123c'
    where = ('实操第 %d 篇' % n) if hands else ('第 %d 课' % n)
    series = '动手用大模型' if hands else '从零看懂大模型'
    block = ('<section style="%s">'
             '<p style="%s">%s</p>'
             '<p style="%s">%s讲过：<span style="%s">%s</span>'
             '<span style="%s">%s</span></p>'
             '</section>' % (BOX % accent, LEAD, html.escape(lead), LINE, where,
                             LINK % accent, html.escape(title), TAG,
                             html.escape(tail) if tail else '　→ 合集「%s」' % series))
    page = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>接一课 · %s</title></head>'
            '<body style="margin:0;background:#eef0f4;font-family:-apple-system,BlinkMacSystemFont,\'PingFang SC\','
            '\'Microsoft YaHei\',sans-serif;"><div style="max-width:720px;margin:0 auto;padding:24px 16px;">'
            '<div style="background:#fff;border:1px solid #d6d9e0;border-radius:10px;padding:20px 22px;margin-bottom:16px;'
            'font-size:14px;line-height:1.9;color:#3f3f46;">粘到新闻正文最后、页脚之前。粘完选中课程标题那行，'
            '用编辑器「插入链接 → 公众号文章」链到对应文章。'
            '<br><button onclick="cp()" style="margin-top:12px;font-size:14px;font-weight:600;padding:8px 16px;'
            'cursor:pointer;border:0;background:%s;color:#fff;border-radius:6px;">复制</button>'
            '<span id="ok" style="margin-left:10px;font-size:13px;color:#15803d;"></span></div>'
            '<div style="background:#fff;border:1px solid #d6d9e0;border-radius:10px;padding:20px 22px;"><div id="a">%s</div></div>'
            '</div><script>function cp(){var r=document.createRange();r.selectNodeContents(document.getElementById("a"));'
            'var s=window.getSelection();s.removeAllRanges();s.addRange(r);document.execCommand("copy");s.removeAllRanges();'
            'document.getElementById("ok").textContent="已复制";}</script></body></html>' % (where, accent, block))
    dst = 'wechat/crosslink-%s%s.html' % (key, suffix)
    open(dst, 'w', encoding='utf-8').write(page)
    print(dst)
    print('  %s\n  %s讲过：%s %s' % (lead, where, title, tail or '→ 合集「%s」' % series))
