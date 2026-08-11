#!/usr/bin/env python3
"""html_to_text.py — 把 stdin 的 HTML 转成纯文本输出到 stdout。

用法:
  curl -s -m 40 -A "<UA>" -H "Accept-Language: zh-CN,zh;q=0.9" "https://目标站/..." | python html_to_text.py
  curl -s ... | python html_to_text.py | head -c 4000          # 只看开头
  curl -s ... | python html_to_text.py | python -c "import sys;t=sys.stdin.read();i=t.find('关键词');print(t[max(0,i-200):i+3000] if i>=0 else t[:3000])"   # 定位关键词段落

说明:
  - 去掉 <script>/<style> 块，避免 JS 噪声
  - 去标签、HTML unescape、压缩空白
  - 可选: 把脚本所在目录加入 PATH，或直接用绝对路径调用
"""
import sys
import re
import html as h

t = sys.stdin.read()
if not t.strip():
    print("")  # 空输入 = 被挡/域名失效，调用方应检查
    sys.exit(0)
t = re.sub(r"<script[^>]*>.*?</script>", "", t, flags=re.S)
t = re.sub(r"<style[^>]*>.*?</style>", "", t, flags=re.S)
t = re.sub(r"<[^>]+>", " ", t)
t = h.unescape(t)
t = re.sub(r"\s+", " ", t)
print(t.strip())
