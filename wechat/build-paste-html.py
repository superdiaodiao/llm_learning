#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 wechat/*.md 转成可直接粘进公众号编辑器的行内样式 HTML。

公众号编辑器会剥掉 <style> 标签和 class 选择器，只保留元素上的行内 style，
所以这里把所有样式都写进 style 属性。生成的页面用浏览器打开，点"复制正文"，
再到编辑器里 Ctrl/Cmd+V 即可。

    python3 wechat/build-paste-html.py wechat/01a-why-it-cant-count-r.md
"""
import html
import os
import re
import sys

# 公众号正文的实际渲染环境：浅色背景、系统字体、无法加载自定义字体。
S = {
    'p':      'margin:0 0 20px;font-size:16px;line-height:1.9;color:#3f3f46;',
    'h2':     'margin:36px 0 16px;padding-left:11px;border-left:4px solid #be123c;'
              'font-size:19px;font-weight:700;line-height:1.5;color:#1b1f27;',
    'strong': 'font-weight:700;color:#1b1f27;',
    'code':   'font-family:Menlo,Consolas,monospace;font-size:14px;color:#be123c;'
              'background:#f6f7f9;padding:1px 5px;border-radius:3px;',
    'ul':     'margin:0 0 14px;padding-left:22px;',
    'li':     'margin:0 0 8px;font-size:15px;line-height:1.85;color:#3f3f46;',
    'box':    'margin:28px 0;padding:20px 20px 6px;background:#fff5f7;'
              'border:1px dashed #be123c;border-radius:8px;',
    'boxh':   'margin:0 0 12px;font-size:16px;font-weight:700;color:#be123c;',
    'ph':     'margin:24px 0;padding:26px 16px;background:#f6f7f9;'
              'border:1px dashed #b6bcc6;border-radius:8px;text-align:center;'
              'font-size:14px;color:#6a7280;line-height:1.7;',
    'kick':   'margin:32px 0 0;padding-top:20px;border-top:1px dashed #be123c;'
              'font-size:16px;font-weight:700;color:#be123c;',
    'tail':   'margin:40px 0 0;padding:18px 20px 4px;background:#f6f7f9;'
              'border-radius:8px;',
    'tailh':  'margin:0 0 10px;font-size:14px;font-weight:700;color:#6a7280;',
    'tailp':  'margin:0 0 14px;font-size:14px;line-height:1.85;color:#6a7280;',
}

# 这些小标题整段套高亮框（读者被要求动手的地方）
BOXED = ('自己试一下',)

# 这些整段走页脚样式，和正文视觉分开
TAIL = ('关于这个系列',)


def inline(t):
    """行内标记：**粗体**、`代码`。先转义，避免正文里的尖括号被当标签。"""
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', lambda m: '<strong style="%s">%s</strong>' % (S['strong'], m.group(1)), t)
    t = re.sub(r'`(.+?)`', lambda m: '<code style="%s">%s</code>' % (S['code'], m.group(1)), t)
    return t


def convert(md):
    lines = md.split('\n')
    title, out = '', []
    i, n = 0, len(lines)
    box_open = in_tail = False

    def close_box():
        nonlocal box_open, in_tail
        if box_open:
            out.append('</section>')
            box_open = in_tail = False

    while i < n:
        ln = lines[i].rstrip()

        if not ln:
            i += 1
            continue

        if ln.startswith('# '):                      # 标题单独交给公众号标题栏
            title = ln[2:].strip()
            i += 1
            continue

        if ln.startswith('> '):                      # 仓库自用的说明块，不进正文
            i += 1
            continue

        if ln.startswith('## '):
            close_box()
            head = ln[3:].strip()
            if head.startswith(BOXED):
                out.append('<section style="%s">' % S['box'])
                out.append('<p style="%s">%s</p>' % (S['boxh'], inline(head)))
                box_open = True
            elif head.startswith(TAIL):
                out.append('<section style="%s">' % S['tail'])
                out.append('<p style="%s">%s</p>' % (S['tailh'], inline(head)))
                box_open = in_tail = True
            else:
                out.append('<h2 style="%s">%s</h2>' % (S['h2'], inline(head)))
            i += 1
            continue

        m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', ln)
        if m:                                        # 图片必须在编辑器里另行上传
            out.append('<section style="%s">在这里插入图片<br><b>%s</b><br>%s</section>'
                       % (S['ph'], html.escape(os.path.basename(m.group(2))), html.escape(m.group(1))))
            i += 1
            continue

        if ln.startswith('- '):
            items = []
            while i < n and lines[i].rstrip().startswith('- '):
                items.append('<li style="%s">%s</li>' % (S['li'], inline(lines[i].rstrip()[2:])))
                i += 1
            out.append('<ul style="%s">%s</ul>' % (S['ul'], ''.join(items)))
            continue

        # 普通段落；末段"下一篇讲这个。"当收尾
        style = S['tailp'] if in_tail else S['p']
        if ln.startswith('下一篇') and not in_tail:
            style = S['kick']
        out.append('<p style="%s">%s</p>' % (style, inline(ln)))
        i += 1

    close_box()
    return title, '\n'.join(out)


PAGE = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s · 粘贴到公众号</title></head>
<body style="margin:0;background:#eef0f4;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;">
<div style="max-width:720px;margin:0 auto;padding:24px 16px 60px;">

  <div style="background:#fff;border:1px solid #d6d9e0;border-radius:10px;padding:20px 22px;margin-bottom:20px;">
    <div style="font-size:12px;letter-spacing:.1em;color:#8a9099;margin-bottom:12px;">粘贴到公众号编辑器</div>
    <div style="font-size:14px;line-height:1.9;color:#3f3f46;">
      <b>1.</b> 标题栏填：<span id="t" style="background:#f6f7f9;padding:2px 7px;border-radius:4px;">%(title)s</span>
      <button onclick="cp(document.getElementById('t'))" style="margin-left:6px;font-size:12px;padding:3px 9px;cursor:pointer;border:1px solid #b6bcc6;background:#fff;border-radius:5px;">复制标题</button><br>
      <b>2.</b> 点下面的按钮复制正文，到编辑器里 Ctrl/Cmd+V<br>
      <b>3.</b> 正文里三个虚线框是图片位，删掉框、用编辑器的"图片"按钮上传对应 PNG<br>
      <b>4.</b> 微信会重写图片地址，所以图必须在编辑器里传，不能靠外链
    </div>
    <button onclick="cp(document.getElementById('a'))" style="margin-top:16px;font-size:14px;font-weight:600;padding:9px 18px;cursor:pointer;border:0;background:#be123c;color:#fff;border-radius:6px;">复制正文</button>
    <span id="ok" style="margin-left:10px;font-size:13px;color:#15803d;"></span>
  </div>

  <div style="background:#fff;border:1px solid #d6d9e0;border-radius:10px;padding:28px 26px;">
    <div id="a">
%(body)s
    </div>
  </div>
</div>
<script>
function cp(el){
  var r=document.createRange(); r.selectNodeContents(el);
  var s=getSelection(); s.removeAllRanges(); s.addRange(r);
  var ok=false; try{ ok=document.execCommand('copy'); }catch(e){}
  s.removeAllRanges();
  var n=document.getElementById('ok');
  n.textContent = ok ? '已复制，去编辑器粘贴' : '复制失败，请手动选中';
  setTimeout(function(){ n.textContent=''; }, 4000);
}
</script>
</body></html>
'''

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'wechat/01a-why-it-cant-count-r.md'
    with open(src, encoding='utf-8') as f:
        title, body = convert(f.read())
    dst = os.path.splitext(src)[0] + '.paste.html'
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(PAGE % {'title': html.escape(title), 'body': body})
    print('%s\n  -> %s\n  标题：%s' % (src, dst, title))
