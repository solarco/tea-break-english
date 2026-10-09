#!/usr/bin/env python3
"""Build index.html for the 茶水间英文新鲜事 transcript site.

Reads episodes.json + translations.json from this directory and writes
a self-contained index.html (list view + detail view, pagination).

episodes.json: list of episode records, each:
  { "date": "2026-10-10",
    "title": "茶水间英文 - 10月10日 | 话题1、话题2、话题3",
    "word_count": 750,
    "audio": "https://raw.githubusercontent.com/.../mp3/2026-10-10.mp3",
    "hook": "One punchy English line covering the 3 topics.",
    "summary": "中文一句话速览",
    "topics": [{"name": "话题一", "start": 2, "end": 10}, ...],
    "quickq": [28, 33],
    "vocab": [["word", "中文解释"], ...] }
  Turn indices are 0-based into the episode's turns; translations.json
  maps date -> [chinese per turn], aligned with turns in order.

translations.json: { "2026-10-10": ["中文1", "中文2", ...] }
The turns themselves live in ~/workspace/podcasts/<slug>/<slug>-script.txt
(labelled "Alex:" / "Jordan:" lines); this script re-parses them from the
"turns" field — see note below.

NOTE: episodes.json records also carry a "turns" list:
  "turns": [{"speaker": "Alex", "text": "..."}, ...]
The daily cron appends full records; this script never fetches the script file.
"""
import json
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PER_PAGE = 10
PODCAST_URL = "https://www.xiaoyuzhoufm.com/podcast/6abf5fc2e7bc828fc1f788e9"


def esc(s):
    return html.escape(s, quote=True)


def turns_html(turns, zhs, lo, hi):
    out = []
    for i in range(lo, hi + 1):
        t, z = turns[i], zhs[i]
        cls = "alex" if t["speaker"] == "Alex" else "jordan"
        out.append(
            f'<div class="turn {cls}"><span class="speaker">{t["speaker"]}</span>'
            f'<div class="lines"><p class="en">{esc(t["text"])}</p>'
            f'<p class="zh">{esc(z)}</p></div></div>'
        )
    return "".join(out)


def build():
    episodes = json.load(open(os.path.join(HERE, "episodes.json"), encoding="utf-8"))
    zh_all = json.load(open(os.path.join(HERE, "translations.json"), encoding="utf-8"))
    episodes = sorted(episodes, key=lambda e: e["date"], reverse=True)

    data = []
    for ep in episodes:
        zhs = zh_all[ep["date"]]
        turns = ep["turns"]
        topics_html = ""
        for n, tp in enumerate(ep["topics"], 1):
            topics_html += (
                f'<div class="topic"><div class="topic-head">'
                f'<span class="topic-num">{n}</span>{esc(tp["name"])}</div>'
                f'{turns_html(turns, zhs, tp["start"], tp["end"])}</div>'
            )
        qlo, qhi = ep["quickq"]
        quickq_html = (
            f'<div class="quickq"><div class="quickq-title">🎲 今日快问</div>'
            f'{turns_html(turns, zhs, qlo, qhi)}</div>'
        )
        vocab_html = "".join(
            f'<li><b>{esc(w)}</b><span>{esc(c)}</span></li>' for w, c in ep["vocab"]
        )
        audio = (
            f'<audio controls preload="none" src="{ep["audio"]}"></audio>'
            if ep.get("audio")
            else f'<div class="no-audio">音频请在小宇宙 App 内收听 '
            f'<a href="{PODCAST_URL}" target="_blank">去小宇宙 &gt;</a></div>'
        )
        row = (
            f'<div class="ep-row" data-date="{ep["date"]}">'
            f'<div class="ep-row-title">{esc(ep["title"])}</div>'
            f'<div class="ep-row-hook">{esc(ep["hook"])}</div>'
            f'<div class="ep-row-meta">{ep["date"]} · 全文 {ep["word_count"]} 词</div></div>'
        )
        detail = f"""
    <button class="back" onclick="showList()">← 返回列表</button>
    <article class="ep">
      <h2>{esc(ep['title'])}</h2>
      <div class="meta">{ep['date']} · 全文 {ep['word_count']} 词</div>
      <div class="summary"><b>📌 一句话速览</b>　{esc(ep['summary'])}</div>
      {audio}
      <details open>
        <summary>📄 中英对照文字稿</summary>
        <div class="transcript">{topics_html}{quickq_html}</div>
      </details>
      <div class="vocab"><div class="vocab-title">📝 Words to steal 生词本</div><ul>{vocab_html}</ul></div>
    </article>"""
        data.append({"date": ep["date"], "row": row, "detail": detail})

    js_data = "const EPISODES = " + json.dumps(data, ensure_ascii=False) + ";"

    page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>茶水间英文新鲜事 · 中英对照文字稿</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
         background: #faf7f2; color: #2b2b2b; line-height: 1.7; padding: 0 0 60px; }
  body.hide-zh .zh { display: none; }
  header { background: linear-gradient(135deg, #ff9a3c, #ff6b6b); color: #fff;
           padding: 30px 20px 26px; text-align: center; }
  header h1 { font-size: 24px; margin-bottom: 6px; }
  header p { opacity: .92; font-size: 14px; }
  #zhToggle { position: fixed; top: 14px; right: 14px; z-index: 99;
              background: rgba(0,0,0,.55); color: #fff; border: none; border-radius: 20px;
              padding: 8px 16px; font-size: 13px; cursor: pointer; backdrop-filter: blur(4px); }
  .wrap { max-width: 720px; margin: 0 auto; padding: 20px 16px; }
  .ep-row { background: #fff; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,.05); cursor: pointer; }
  .ep-row:active { background: #fff8f0; }
  .ep-row-title { font-size: 15px; font-weight: 600; }
  .ep-row-hook { font-size: 13px; color: #777; margin-top: 3px; }
  .ep-row-meta { font-size: 12px; color: #999; margin-top: 4px; }
  .pager { display: flex; align-items: center; justify-content: center; gap: 16px;
           margin-top: 18px; font-size: 14px; color: #666; }
  .pager button { background: #fff; border: 1px solid #eee; border-radius: 20px;
                  padding: 6px 18px; font-size: 13px; cursor: pointer; color: #e8590c; }
  .pager button:disabled { color: #ccc; cursor: default; }
  .back { background: none; border: none; color: #e8590c; font-size: 14px; cursor: pointer;
          margin-bottom: 12px; padding: 4px 0; }
  .ep { background: #fff; border-radius: 14px; padding: 20px; margin-bottom: 18px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06); }
  .ep h2 { font-size: 17px; margin-bottom: 6px; }
  .meta { font-size: 12px; color: #999; margin-bottom: 12px; }
  .summary { background: #fff8ec; border-left: 4px solid #ff9a3c; border-radius: 0 10px 10px 0;
             padding: 10px 14px; font-size: 14px; margin-bottom: 12px; }
  .summary b { color: #e8590c; }
  audio { width: 100%; margin-bottom: 6px; }
  .no-audio { font-size: 13px; color: #888; background: #f6f3ee; border-radius: 8px;
              padding: 10px 12px; margin-bottom: 10px; }
  .no-audio a { color: #e8590c; }
  .vocab { background: #fffdf5; border: 1px dashed #f0c987; border-radius: 10px;
           padding: 12px 14px; margin-top: 12px; }
  .vocab-title { font-size: 14px; font-weight: 700; margin-bottom: 8px; }
  .vocab ul { list-style: none; }
  .vocab li { font-size: 13px; margin-bottom: 6px; }
  .vocab li b { color: #e8590c; margin-right: 8px; }
  .vocab li span { color: #666; }
  details summary { cursor: pointer; font-size: 14px; color: #e8590c; font-weight: 600;
                    padding: 6px 0; }
  .transcript { margin-top: 4px; border-top: 1px dashed #eee; padding-top: 6px; }
  .topic { margin: 14px 0 4px; }
  .topic-head { display: flex; align-items: center; gap: 8px; font-size: 15px;
                font-weight: 700; margin-bottom: 10px; }
  .topic-num { background: linear-gradient(135deg, #ff9a3c, #ff6b6b); color: #fff;
               width: 24px; height: 24px; border-radius: 50%; font-size: 13px;
               display: flex; align-items: center; justify-content: center; flex: 0 0 auto; }
  .quickq { background: #f3f0ff; border-radius: 10px; padding: 12px 14px; margin: 14px 0 4px; }
  .quickq-title { font-size: 14px; font-weight: 700; margin-bottom: 8px; }
  .turn { display: flex; gap: 10px; margin-bottom: 14px; }
  .turn:last-child { margin-bottom: 4px; }
  .speaker { flex: 0 0 auto; font-size: 12px; font-weight: 700; border-radius: 20px;
             padding: 2px 10px; height: fit-content; margin-top: 2px; }
  .alex .speaker { background: #fff3e0; color: #e8590c; }
  .jordan .speaker { background: #e3f2fd; color: #1971c2; }
  .lines { flex: 1; }
  .en { font-size: 14px; }
  .zh { font-size: 13px; color: #8a8a8a; margin-top: 2px; }
  footer { text-align: center; font-size: 12px; color: #aaa; margin-top: 30px; }
  footer a { color: #e8590c; }
</style>
</head>
<body>
<button id="zhToggle" style="display:none">隐藏译文</button>
<header>
  <h1>☕ 茶水间英文新鲜事</h1>
  <p>每天 5 分钟，英语聊新鲜事 · 中英对照文字稿</p>
</header>
<div class="wrap">
  <div id="listView"></div>
  <div id="detailView" style="display:none"></div>
  <footer>
    由 AI 全自动生成 · <a href="__PODCAST_URL__" target="_blank">在小宇宙收听</a>
  </footer>
</div>
<script>
__JS_DATA__
const PER_PAGE = 10;
let curPage = 1;
const listView = document.getElementById('listView');
const detailView = document.getElementById('detailView');
const zhToggle = document.getElementById('zhToggle');

function showList(page) {
  if (page) curPage = page;
  detailView.style.display = 'none';
  listView.style.display = '';
  zhToggle.style.display = 'none';
  const total = Math.ceil(EPISODES.length / PER_PAGE);
  curPage = Math.min(Math.max(curPage, 1), total);
  const items = EPISODES.slice((curPage - 1) * PER_PAGE, curPage * PER_PAGE);
  let html = items.map(e => e.row).join('');
  if (total > 1) {
    html += '<div class="pager">'
      + '<button ' + (curPage <= 1 ? 'disabled' : '') + ' onclick="showList(' + (curPage - 1) + ')">← 上一页</button>'
      + '<span>第 ' + curPage + ' / ' + total + ' 页</span>'
      + '<button ' + (curPage >= total ? 'disabled' : '') + ' onclick="showList(' + (curPage + 1) + ')">下一页 →</button>'
      + '</div>';
  }
  listView.innerHTML = html;
  listView.querySelectorAll('.ep-row').forEach(r =>
    r.addEventListener('click', () => showDetail(r.dataset.date)));
  window.scrollTo(0, 0);
}

function showDetail(date) {
  const ep = EPISODES.find(e => e.date === date);
  if (!ep) return;
  listView.style.display = 'none';
  detailView.style.display = '';
  detailView.innerHTML = ep.detail;
  zhToggle.style.display = '';
  window.scrollTo(0, 0);
}

zhToggle.addEventListener('click', () => {
  const hidden = document.body.classList.toggle('hide-zh');
  zhToggle.textContent = hidden ? '显示译文' : '隐藏译文';
});

showList(1);
</script>
</body>
</html>"""

    page = page.replace("__PODCAST_URL__", PODCAST_URL).replace("__JS_DATA__", js_data)
    out = os.path.join(HERE, "index.html")
    open(out, "w", encoding="utf-8").write(page)
    print(f"wrote {out}, {len(page)//1024} KB, {len(episodes)} episodes")


if __name__ == "__main__":
    build()
