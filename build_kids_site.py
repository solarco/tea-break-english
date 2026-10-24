#!/usr/bin/env python3
"""Build kids.html for the 小小英文新鲜事 transcript site.

Reads kids_episodes.json + kids_translations.json from this directory and writes
a self-contained kids.html (list view + detail view).

kids_episodes.json: list of episode records, each:
  { "date": "2026-10-10",
    "title": "小小英文新鲜事 - 1010 | 话题1、话题2、话题3",
    "word_count": 422,
    "audio": "https://raw.githubusercontent.com/.../mp3/2026-10-10.mp3",
    "stories": ["火星日出", "194岁乌龟", "深海新物种"],
    "word_of_day": ["species", "物种"],
    "ending_game": "中文一句话",
    "turns": [{"speaker": "Mia", "text": "..."}, ...] }
kids_translations.json: { "2026-10-10": ["中文1", "中文2", ...] }
"""
import json
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PODCAST_URL = "https://www.xiaoyuzhoufm.com/podcast/6ac96b8ee7bc828fc15f5898"
ADULT_URL = "https://solarco.github.io/tea-break-english/"


def esc(s):
    return html.escape(s, quote=True)


def turns_html(turns, zhs):
    out = []
    for t, z in zip(turns, zhs):
        cls = "mia" if t["speaker"] == "Mia" else "lina"
        out.append(
            f'<div class="turn {cls}"><span class="speaker">{t["speaker"]}</span>'
            f'<div class="lines"><p class="en">{esc(t["text"])}</p>'
            f'<p class="zh">{esc(z)}</p></div></div>'
        )
    return "".join(out)


def build():
    episodes = json.load(open(os.path.join(HERE, "kids_episodes.json"), encoding="utf-8"))
    zh_all = json.load(open(os.path.join(HERE, "kids_translations.json"), encoding="utf-8"))
    episodes = sorted(episodes, key=lambda e: e["date"], reverse=True)

    data = []
    for ep in episodes:
        zhs = zh_all[ep["date"]]
        turns = ep["turns"]
        assert len(turns) == len(zhs), f"{ep['date']}: {len(turns)} vs {len(zhs)}"
        stories_html = "".join(f"<li>{esc(s)}</li>" for s in ep["stories"])
        w_en, w_zh = ep["word_of_day"]
        vocab_html = ""
        if ep.get("vocab"):
            items = "".join(
                f'<div class="vocab-item"><div class="vocab-word">{esc(v["en"])}'
                f'<span>（{esc(v["zh"])}）</span></div>'
                f'<div class="vocab-def">{esc(v["def"])}</div>'
                f'<div class="vocab-ex">例：{esc(v["ex_en"])}（{esc(v["ex_zh"])}）</div></div>'
                for v in ep["vocab"]
            )
            vocab_html = (
                f'<div class="vocab"><div class="vocab-title">📝 生词本</div>'
                f'{items}</div>'
            )
        audio = (
            f'<audio controls preload="none" src="{ep["audio"]}"></audio>'
            if ep.get("audio")
            else f'<div class="no-audio">音频请在小宇宙 App 内收听 '
            f'<a href="{PODCAST_URL}" target="_blank">去小宇宙 &gt;</a></div>'
        )
        photos_html = ""
        if ep.get("photos"):
            items = "".join(
                f'<figure class="photo"><img src="{esc(p["url"])}" alt="{esc(p["story"])}" loading="lazy">'
                f'<figcaption>📷 {esc(p["story"])}<span class="photo-credit">{esc(p["credit"])}</span></figcaption></figure>'
                for p in ep["photos"]
            )
            photos_html = f'<div class="photos"><div class="photos-title">📸 本期真实照片</div>{items}</div>'
        row = (
            f'<div class="ep-row" data-date="{ep["date"]}">'
            f'<div class="ep-row-title">{esc(ep["title"])}</div>'
            f'<div class="ep-row-meta">{ep["date"]} · {ep["word_count"]} 词 · '
            f'Word of the day: {esc(w_en)}</div></div>'
        )
        detail = f"""
    <button class="back" onclick="showList()">← 返回列表</button>
    <article class="ep">
      <h2>🦁 {esc(ep['title'])}</h2>
      <div class="meta">{ep['date']} · 全文 {ep['word_count']} 词</div>
      <div class="stories"><b>📖 今天的三个新鲜事</b><ul>{stories_html}</ul></div>
      {photos_html}
      {audio}
      <div class="wordcard"><div class="wordcard-title">📖 Word of the day</div>
        <div class="wordcard-word">{esc(w_en)}<span>（{esc(w_zh)}）</span></div></div>
      <div class="game"><div class="game-title">🎮 结尾小游戏</div>
        <p>{esc(ep['ending_game'])}</p></div>
      <details open>
        <summary>📄 中英对照文字稿（跟读用）</summary>
        <div class="transcript">{turns_html(turns, zhs)}</div>
      </details>
      {vocab_html}
    </article>"""
        data.append({"date": ep["date"], "row": row, "detail": detail})

    js_data = "const EPISODES = " + json.dumps(data, ensure_ascii=False) + ";"

    page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>小小英文新鲜事 · 中英对照文字稿</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
         background: #fff9f0; color: #2b2b2b; line-height: 1.7; padding: 0 0 60px; }
  body.hide-zh .zh { display: none; }
  header { background: linear-gradient(135deg, #ffd43b, #ff9a3c); color: #5c3d00;
           padding: 32px 20px 26px; text-align: center; }
  header h1 { font-size: 26px; margin-bottom: 6px; }
  header p { opacity: .85; font-size: 14px; }
  header nav { margin-top: 10px; font-size: 13px; }
  header nav a { color: #5c3d00; opacity: .8; margin: 0 8px; }
  #zhToggle { position: fixed; top: 14px; right: 14px; z-index: 99;
              background: rgba(0,0,0,.55); color: #fff; border: none; border-radius: 20px;
              padding: 8px 16px; font-size: 13px; cursor: pointer; }
  .wrap { max-width: 720px; margin: 0 auto; padding: 20px 16px; }
  .ep-row { background: #fff; border-radius: 16px; padding: 14px 16px; margin-bottom: 10px;
            box-shadow: 0 2px 8px rgba(255,154,60,.12); cursor: pointer;
            border: 2px solid transparent; }
  .ep-row:active { border-color: #ffd43b; }
  .ep-row-title { font-size: 15px; font-weight: 600; }
  .ep-row-meta { font-size: 12px; color: #999; margin-top: 4px; }
  .back { background: none; border: none; color: #e8590c; font-size: 14px; cursor: pointer;
          margin-bottom: 12px; padding: 4px 0; }
  .ep { background: #fff; border-radius: 18px; padding: 20px; margin-bottom: 18px;
        box-shadow: 0 2px 10px rgba(255,154,60,.12); }
  .ep h2 { font-size: 17px; margin-bottom: 6px; }
  .meta { font-size: 12px; color: #999; margin-bottom: 12px; }
  .stories { background: #fff8ec; border-radius: 12px; padding: 10px 14px;
             font-size: 14px; margin-bottom: 12px; }
  .stories b { color: #e8590c; }
  .stories ul { margin: 6px 0 0 18px; }
  .photos { margin-bottom: 12px; }
  .photos-title { font-size: 14px; font-weight: 700; color: #e8590c; margin-bottom: 8px; }
  .photo { margin-bottom: 14px; }
  .photo img { width: 100%; max-width: 600px; border-radius: 14px; display: block; }
  .photo figcaption { font-size: 13px; color: #666; margin-top: 4px; }
  .photo-credit { display: block; font-size: 11px; color: #aaa; }
  audio { width: 100%; margin-bottom: 6px; }
  .no-audio { font-size: 13px; color: #888; background: #f6f3ee; border-radius: 8px;
              padding: 10px 12px; margin-bottom: 10px; }
  .no-audio a { color: #e8590c; }
  .wordcard { background: linear-gradient(135deg, #fff3bf, #ffe8cc); border-radius: 14px;
              padding: 14px 16px; margin: 12px 0; text-align: center; }
  .wordcard-title { font-size: 13px; font-weight: 700; color: #975a00; margin-bottom: 4px; }
  .wordcard-word { font-size: 26px; font-weight: 800; color: #e8590c; }
  .wordcard-word span { font-size: 15px; font-weight: 400; color: #975a00; margin-left: 8px; }
  .game { background: #f3f0ff; border-radius: 14px; padding: 12px 16px; margin: 12px 0; }
  .game-title { font-size: 14px; font-weight: 700; margin-bottom: 4px; }
  .game p { font-size: 14px; }
  .vocab { background: #e7f5ff; border-radius: 14px; padding: 12px 16px; margin: 12px 0; }
  .vocab-title { font-size: 14px; font-weight: 700; margin-bottom: 8px; color: #1864ab; }
  .vocab-item { margin-bottom: 10px; }
  .vocab-item:last-child { margin-bottom: 0; }
  .vocab-word { font-size: 17px; font-weight: 800; color: #1971c2; }
  .vocab-word span { font-size: 13px; font-weight: 400; color: #495057; margin-left: 6px; }
  .vocab-def { font-size: 13px; color: #495057; }
  .vocab-ex { font-size: 13px; color: #2b8a3e; }
  details summary { cursor: pointer; font-size: 14px; color: #e8590c; font-weight: 600;
                    padding: 6px 0; }
  .transcript { margin-top: 4px; border-top: 2px dashed #ffe8cc; padding-top: 6px; }
  .turn { display: flex; gap: 10px; margin-bottom: 14px; }
  .turn:last-child { margin-bottom: 4px; }
  .speaker { flex: 0 0 auto; font-size: 12px; font-weight: 700; border-radius: 20px;
             padding: 2px 10px; height: fit-content; margin-top: 2px; }
  .mia .speaker { background: #ffe8cc; color: #d9480f; }
  .lina .speaker { background: #d0ebff; color: #1971c2; }
  .lines { flex: 1; }
  .en { font-size: 15px; }
  .zh { font-size: 13px; color: #8a8a8a; margin-top: 2px; }
  footer { text-align: center; font-size: 12px; color: #aaa; margin-top: 30px; }
  footer a { color: #e8590c; margin: 0 8px; }
</style>
</head>
<body>
<button id="zhToggle" style="display:none">隐藏译文</button>
<header>
  <h1>🦁 小小英文新鲜事</h1>
  <p>每期 3 分钟，轻松英文看世界 · 中英对照文字稿</p>
  <nav><a href="__ADULT_URL__">☕ 茶水间英文新鲜事</a> · <a href="__PODCAST_URL__" target="_blank">去小宇宙收听</a></nav>
</header>
<div class="wrap">
  <div id="listView"></div>
  <div id="detailView" style="display:none"></div>
  <footer>
    <a href="__ADULT_URL__">☕ 茶水间英文新鲜事</a>
    <a href="__PODCAST_URL__" target="_blank">在小宇宙收听</a>
  </footer>
</div>
<script>
__JS_DATA__
const listView = document.getElementById('listView');
const detailView = document.getElementById('detailView');
const zhToggle = document.getElementById('zhToggle');
function showList() {
  detailView.style.display = 'none';
  listView.style.display = 'block';
  zhToggle.style.display = 'none';
  listView.innerHTML = EPISODES.map(e => e.row).join('');
  listView.querySelectorAll('.ep-row').forEach(r => {
    r.onclick = () => showDetail(r.dataset.date);
  });
  window.scrollTo(0, 0);
}
function showDetail(date) {
  const ep = EPISODES.find(e => e.date === date);
  if (!ep) return;
  listView.style.display = 'none';
  detailView.style.display = 'block';
  zhToggle.style.display = 'block';
  detailView.innerHTML = ep.detail;
  window.scrollTo(0, 0);
}
zhToggle.onclick = () => {
  document.body.classList.toggle('hide-zh');
  zhToggle.textContent = document.body.classList.contains('hide-zh') ? '显示译文' : '隐藏译文';
};
showList();
</script>
</body>
</html>"""
    page = (page.replace("__PODCAST_URL__", PODCAST_URL)
                .replace("__ADULT_URL__", ADULT_URL)
                .replace("__JS_DATA__", js_data))
    out = os.path.join(HERE, "kids.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote {out} ({len(episodes)} episodes)")


if __name__ == "__main__":
    build()
