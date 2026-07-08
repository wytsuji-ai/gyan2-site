# -*- coding: utf-8 -*-
"""ギャン2ラボ 静的サイトビルダー。content/posts/*.md → docs/ にHTML生成。
実行: python build.py  (要: pip install markdown)"""
from pathlib import Path
import shutil, re, html
from datetime import datetime, timezone, timedelta
import markdown

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
POSTS = ROOT / "content" / "posts"
PAGES = ROOT / "content" / "pages"
SITE_URL = "https://gyan2.net"
SITE_NAME = "ギャン2ラボ"
SITE_DESC = "人間ひとり×AIひとつの二人組で「稼ぐ」を実験するラボ。Claude Codeに仕事を任せる30日チャレンジ実践記。"
JST = timezone(timedelta(hours=9))

BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")


def parse_post(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    meta = {}
    body = text
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2)
    html_body = markdown.markdown(body, extensions=["extra", "toc"])
    slug = path.stem
    return {
        "slug": slug,
        "title": meta.get("title", slug),
        "date": meta.get("date", ""),
        "day": meta.get("day", ""),
        "description": meta.get("description", ""),
        "body": html_body,
        "url": f"/posts/{slug}.html",
    }


def render(template: str, **kw) -> str:
    out = template
    for k, v in kw.items():
        out = out.replace("{{" + k + "}}", v)
    return out


def page(title, description, content, path_url):
    return render(
        BASE,
        title=html.escape(title),
        description=html.escape(description),
        content=content,
        canonical=SITE_URL + path_url,
        site_name=SITE_NAME,
        year=str(datetime.now(JST).year),
    )


def post_html(p):
    day_label = f'<span class="day-chip">Day {html.escape(p["day"])}</span>' if p["day"] else ""
    art = f"""
<article class="post">
  <header class="post-head">
    {day_label}
    <h1>{html.escape(p["title"])}</h1>
    <time datetime="{p["date"]}">{p["date"]}</time>
  </header>
  <div class="post-body">{p["body"]}</div>
  <footer class="post-foot"><a href="/">← ラボのトップへ</a></footer>
</article>"""
    return page(f'{p["title"]} | {SITE_NAME}', p["description"] or SITE_DESC, art, p["url"])


def page_html(p):
    art = f"""
<article class="post">
  <header class="post-head">
    <h1>{html.escape(p["title"])}</h1>
    <time datetime="{p["date"]}">{p["date"]}</time>
  </header>
  <div class="post-body">{p["body"]}</div>
  <footer class="post-foot"><a href="/">← ラボのトップへ</a></footer>
</article>"""
    return page(f'{p["title"]} | {SITE_NAME}', p["description"] or SITE_DESC, art, f"/{p['slug']}.html")


def index_html(posts):
    cards = "\n".join(
        f"""<li class="card">
  <a href="{p['url']}">
    {f'<span class="day-chip">Day {html.escape(p["day"])}</span>' if p['day'] else ''}
    <h2>{html.escape(p['title'])}</h2>
    <p>{html.escape(p['description'])}</p>
    <time datetime="{p['date']}">{p['date']}</time>
  </a>
</li>"""
        for p in posts
    )
    latest_day = max((int(p["day"]) for p in posts if p["day"].isdigit()), default=0)
    hero = f"""
<section class="hero">
  <p class="hero-eyebrow">人間ひとり × AIひとつ</p>
  <h1 class="hero-logo">ギャン2<span class="logo-lab">ラボ</span></h1>
  <div class="dialog" aria-label="人間とAIのやりとり">
    <p class="line human"><span class="who">人間</span>今日なにやる?</p>
    <p class="line ai"><span class="who">AI</span>収益化まで、あと {30 - latest_day} 日。次のタスクを出します。</p>
  </div>
  <p class="hero-desc">{SITE_DESC}<br>PCの作業はぜんぶAI(Claude Code)。人間は決めることと払うことだけ。<br>その過程を、盛らずに全部書きます。</p>
  <div class="progress" role="img" aria-label="30日チャレンジ {latest_day}日目">
    <div class="progress-bar" style="width:{int(latest_day / 30 * 100)}%"></div>
    <span class="progress-label">Day {latest_day} / 30</span>
  </div>
</section>
<section class="posts">
  <h2 class="sec-title">実践ログ</h2>
  <ul class="cards">{cards}</ul>
</section>"""
    return page(f"{SITE_NAME} — AIと二人組で稼ぐ30日チャレンジ", SITE_DESC, hero, "/")


def feeds(posts):
    items = "\n".join(
        f"""<item><title>{html.escape(p['title'])}</title><link>{SITE_URL}{p['url']}</link>
<guid>{SITE_URL}{p['url']}</guid><pubDate>{p['date']}</pubDate>
<description>{html.escape(p['description'])}</description></item>"""
        for p in posts
    )
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{SITE_NAME}</title><link>{SITE_URL}</link>
<description>{html.escape(SITE_DESC)}</description>{items}</channel></rss>"""
    urls = "\n".join(f"<url><loc>{SITE_URL}{p['url']}</loc></url>" for p in posts)
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>{SITE_URL}/</loc></url>{urls}</urlset>"""
    return rss, sitemap


def main():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    (DOCS / "posts").mkdir(parents=True)
    shutil.copytree(ROOT / "assets", DOCS / "assets")
    for f in (ROOT / "static").glob("*"):
        shutil.copy(f, DOCS / f.name)

    posts = sorted((parse_post(p) for p in POSTS.glob("*.md")), key=lambda p: p["date"], reverse=True)
    for p in posts:
        (DOCS / "posts" / f"{p['slug']}.html").write_text(post_html(p), encoding="utf-8")
    pages = [parse_post(p) for p in PAGES.glob("*.md")] if PAGES.exists() else []
    for p in pages:
        (DOCS / f"{p['slug']}.html").write_text(page_html(p), encoding="utf-8")
    (DOCS / "index.html").write_text(index_html(posts), encoding="utf-8")
    rss, sitemap = feeds(posts)
    (DOCS / "feed.xml").write_text(rss, encoding="utf-8")
    (DOCS / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print(f"OK: {len(posts)} posts -> {DOCS}")


if __name__ == "__main__":
    main()
