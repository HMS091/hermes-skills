#!/usr/bin/env python3
"""批量补全占位图标：按 id 拼 URL 下载、严格校验、原地覆盖占位文件。

用法（先不加 --write 跑一遍看命中率）：
  python3 backfill_asset_icons.py --root /data/archive/pairs --root /data/archive/no-blurb \
      --url 'https://example.com/coins/{id}.svg' --spot-suffix _spot \
      --report /data/archive/fill_result.json --write

约定：
- --root 下每个子目录是一个标的，含一个 *.PLACEHOLDER.svg 和 meta.json（meta 里 coin 字段是标的 id，
  可能带 ':' 前缀如 xyz:AVGO，也可能带 '/' 表示现货对）。
- 现货对（id 含 '/'）先试 '<BASE><spot-suffix>' 再试 '<BASE>'；其它直接试原 id。
- 校验三件套：content-type 含 'svg' + 正文以 <svg 开头 + >150B；失败一律不动占位文件。
- 成功后真字节覆盖同名占位文件（文件名不变），meta 写 hasLogo/logoFile/logoSource/logoBytes。
"""
import argparse, glob, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/124.0 Safari/537.36',
      'Accept': 'image/svg+xml,image/*,*/*'}
MIN_BYTES = 150


def collect(roots, pattern='*.PLACEHOLDER.svg'):
    todo = []
    for root in roots:
        for ph in glob.glob(os.path.join(root, '*', pattern)):
            d = os.path.dirname(ph)
            mp = os.path.join(d, 'meta.json')
            meta = json.load(open(mp)) if os.path.exists(mp) else {}
            coin = meta.get('coin') or os.path.basename(d).replace('_', '/')
            todo.append({'dir': d, 'stem': os.path.basename(d), 'coin': coin,
                         'meta_path': mp, 'ph': ph, 'meta': meta})
    return todo


def coin_ids(coin, spot_suffix):
    if '/' in coin:
        base = coin.split('/')[0]
        return [base + spot_suffix, base] if spot_suffix else [base]
    return [coin]


def get(url):
    last = 'no-attempt'
    for attempt in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=18) as r:
                ct = (r.headers.get('content-type') or '').lower()
                body = r.read()
            if 'svg' not in ct:
                return None, 'bad-ct:%s(%dB)' % (ct or 'none', len(body))
            if body.lstrip()[:4] != b'<svg':
                return None, 'not-svg(%dB)' % len(body)
            if len(body) <= MIN_BYTES:
                return None, 'too-small(%dB)' % len(body)
            return body, 'ok'
        except Exception as e:                       # 超时/连接重置是常态，重试一次
            last = 'err:%s' % str(e)[:80]
            time.sleep(1.0 + attempt * 1.5)
    return None, last


def work(rec, url_tpl, spot_suffix):
    note = 'no-candidate'
    for cid in coin_ids(rec['coin'], spot_suffix):
        body, note = get(url_tpl.format(id=cid))
        if body:
            return rec, cid, body, note
    return rec, None, None, note


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', action='append', required=True)
    ap.add_argument('--url', required=True, help='含 {id} 的模板；分隔符(:/@)不要编码')
    ap.add_argument('--pattern', default='*.PLACEHOLDER.svg')
    ap.add_argument('--spot-suffix', default='_spot')
    ap.add_argument('--report', default=None)
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args()

    todo = collect(a.root, a.pattern)
    print('placeholders:', len(todo), flush=True)
    hits, misses, done = [], [], 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for rec, cid, body, note in ex.map(
                lambda r: work(r, a.url, a.spot_suffix), todo):
            done += 1
            if body and a.write:
                open(rec['ph'], 'wb').write(body)
                m = rec['meta']
                m.update({'hasLogo': True, 'logoFile': os.path.basename(rec['ph']),
                          'logoSource': cid, 'logoBytes': len(body)})
                if rec['meta_path']:
                    json.dump(m, open(rec['meta_path'], 'w'), indent=1, ensure_ascii=False)
            if body:
                hits.append({'coin': rec['coin'], 'id': cid, 'bytes': len(body),
                             'file': rec['ph']})
                print('FIX  %-16s <- %-18s %8dB [%d/%d]' % (rec['coin'], cid, len(body), done, len(todo)), flush=True)
            else:
                misses.append({'coin': rec['coin'], 'reason': note, 'file': rec['ph']})
                print('MISS %-16s %s [%d/%d]' % (rec['coin'], note, done, len(todo)), flush=True)

    print('\nfixed %d / %d, failed %d%s' % (len(hits), len(todo), len(misses),
                                            '' if a.write else ' (dry-run, nothing written)'))
    if a.report:
        json.dump({'total': len(todo), 'fixed': hits, 'failed': misses},
                  open(a.report, 'w'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
