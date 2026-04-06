"""
generate_blog.py
Minds Of Brands — AI Blog Generator
Uses Google Gemini API (FREE tier — no credit card needed)
Get your free key at: https://aistudio.google.com/apikey
"""

import os
import re
import json
import random
import requests
from datetime import datetime
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────

SITE_NAME      = "Minds Of Brands"
SITE_URL       = "https://mindsofbrands.com"
SITE_TAGLINE   = "Digital Marketing & Branding"
BLOG_DIR       = "blog"
BLOG_INDEX     = "blog/index.html"
SITEMAP_FILE   = "sitemap.xml"
TOPICS_FILE    = "topics.txt"

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

# ─── TOPIC SELECTION ──────────────────────────────────────────────────────────

DEFAULT_TOPICS = [
    "AI Tools for Startups",
    "Instagram Marketing Strategies",
    "Business Growth Strategies",
    "Digital Marketing Trends 2026",
    "Lead Generation Tips",
    "Email Marketing Best Practices",
    "SEO for Small Businesses",
    "Content Marketing Strategy",
    "Social Media ROI Measurement",
    "Personal Branding for Entrepreneurs",
    "WhatsApp Marketing for Businesses",
    "Google Ads vs Facebook Ads",
    "Video Marketing on a Budget",
    "CRM Tools for Growing Businesses",
    "Local SEO Strategies India",
]

def pick_topic():
    """Use manual input → topics.txt → default list (avoids repeats)."""
    manual = os.environ.get("MANUAL_TOPIC", "").strip()
    if manual:
        print(f"Using manually specified topic: {manual}")
        return manual

    # Load custom topics file if present
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE, "r") as f:
            topics = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        print(f"Loaded {len(topics)} topics from {TOPICS_FILE}")
    else:
        topics = DEFAULT_TOPICS

    # Avoid repeating topics that already have blog folders
    used_slugs = set()
    blog_path = Path(BLOG_DIR)
    if blog_path.exists():
        used_slugs = {p.name for p in blog_path.iterdir() if p.is_dir()}

    unused = [t for t in topics if slugify(t) not in used_slugs
              and not any(slugify(t) in s for s in used_slugs)]
    pool = unused if unused else topics
    chosen = random.choice(pool)
    print(f"Auto-selected topic: {chosen}")
    return chosen

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def slugify(text):
    """Convert topic to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text

def format_date(fmt="%B %d, %Y"):
    return datetime.now().strftime(fmt)

def iso_date():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00")

# ─── AI CONTENT GENERATION ────────────────────────────────────────────────────

def call_gemini(prompt, api_key):
    """Call Gemini 2.0 Flash (free tier) and return text."""
    url = f"{GEMINI_API_URL}?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 2048,
        }
    }
    resp = requests.post(url, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text}")
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()

def generate_blog_content(topic, api_key):
    """Generate full blog post content via Gemini."""
    prompt = f"""You are a professional digital marketing content writer for "{SITE_NAME}", 
a digital marketing agency based in India.

Write a detailed, SEO-optimized blog post about: "{topic}"

Requirements:
- Length: 700-900 words
- Tone: Professional but conversational, helpful
- Structure: Introduction, 3-4 main sections with H2 headings, Conclusion
- Include: Practical tips, real examples, actionable advice
- Target audience: Indian small business owners, entrepreneurs, startups
- SEO: Naturally use the main keyword "{topic}" 4-6 times

Return ONLY a JSON object with these exact keys (no markdown, no code blocks):
{{
  "title": "Compelling SEO title (55-60 chars)",
  "meta_description": "Meta description 150-160 chars with keyword",
  "intro": "Opening paragraph (2-3 sentences, hook the reader)",
  "sections": [
    {{
      "heading": "Section heading",
      "content": "2-3 paragraphs of content for this section"
    }}
  ],
  "conclusion": "Closing paragraph with CTA to contact Minds Of Brands",
  "tags": ["tag1", "tag2", "tag3"]
}}"""

    print("Calling Gemini API...")
    raw = call_gemini(prompt, api_key)

    # Strip any accidental markdown code fences
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)

    try:
        data = json.loads(raw)
        print(f"Generated title: {data.get('title', topic)}")
        return data
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}\nRaw output:\n{raw[:500]}")
        # Fallback: return basic structure
        return {
            "title": f"Ultimate Guide to {topic}",
            "meta_description": f"Learn everything about {topic} with actionable strategies for business growth.",
            "intro": f"{topic} is transforming the way businesses grow online. In this guide, we explore the most effective strategies you can apply today.",
            "sections": [
                {"heading": f"Why {topic} Matters", "content": f"{topic} helps businesses attract the right audience, improve visibility, and increase conversions. Companies that invest in {topic} see measurable results within months."},
                {"heading": "Key Strategies to Get Started", "content": "Start by defining your target audience clearly. Use data-driven tools to track performance. Consistency is the single most important factor in long-term success."},
                {"heading": "Common Mistakes to Avoid", "content": "Many businesses jump in without a clear strategy. Avoid spreading yourself too thin across every platform. Focus on 2-3 channels where your audience actually spends time."},
            ],
            "conclusion": f"Ready to implement {topic} for your business? Minds Of Brands helps you create strategies that deliver real results. Contact us today.",
            "tags": [topic, "digital marketing", "business growth"]
        }

# ─── HTML GENERATION ──────────────────────────────────────────────────────────

def build_sections_html(sections):
    html = ""
    for sec in sections:
        heading = sec.get("heading", "")
        content = sec.get("content", "")
        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
        para_html = "\n      ".join(f"<p>{p}</p>" for p in paragraphs)
        html += f"""
    <h2>{heading}</h2>
      {para_html}"""
    return html

def build_post_html(topic, slug, content):
    title          = content.get("title", f"Ultimate Guide to {topic}")
    meta_desc      = content.get("meta_description", "")
    intro          = content.get("intro", "")
    sections_html  = build_sections_html(content.get("sections", []))
    conclusion     = content.get("conclusion", "")
    tags           = content.get("tags", [])
    date_display   = format_date()
    date_iso       = iso_date()
    tags_html      = " ".join(f'<span class="tag">{t}</span>' for t in tags)
    canonical_url  = f"{SITE_URL}/blog/{slug}/"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | {SITE_NAME}</title>
  <meta name="description" content="{meta_desc}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{canonical_url}">

  <!-- Open Graph -->
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="{SITE_NAME}">

  <!-- Schema.org -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "headline": "{title}",
    "description": "{meta_desc}",
    "url": "{canonical_url}",
    "datePublished": "{date_iso}",
    "dateModified": "{date_iso}",
    "author": {{"@type": "Organization", "name": "{SITE_NAME}"}},
    "publisher": {{"@type": "Organization", "name": "{SITE_NAME}", "url": "{SITE_URL}"}}
  }}
  </script>

  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', Arial, sans-serif;
      color: #222;
      background: #fff;
      line-height: 1.7;
    }}
    header {{
      background: #111;
      color: #fff;
      padding: 14px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    header a {{ color: #fff; text-decoration: none; font-size: 20px; font-weight: 700; letter-spacing: .5px; }}
    nav a {{ color: #ccc; text-decoration: none; font-size: 14px; margin-left: 20px; }}
    nav a:hover {{ color: #fff; }}
    .hero {{
      background: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 100%);
      color: #fff;
      padding: 60px 24px 50px;
      text-align: center;
    }}
    .hero h1 {{ font-size: clamp(24px, 4vw, 40px); font-weight: 700; max-width: 800px; margin: 0 auto 16px; line-height: 1.25; }}
    .hero .meta {{ font-size: 14px; color: #aaa; }}
    .container {{ max-width: 820px; margin: 0 auto; padding: 48px 24px 64px; }}
    .container h2 {{ font-size: 24px; font-weight: 700; margin: 36px 0 14px; color: #111; border-left: 4px solid #e63; padding-left: 14px; }}
    .container p {{ font-size: 16px; margin-bottom: 18px; color: #333; }}
    .tags {{ margin: 32px 0 0; }}
    .tag {{
      display: inline-block; background: #f0f0f0; color: #555;
      font-size: 12px; padding: 4px 10px; border-radius: 20px; margin: 4px 4px 0 0;
    }}
    .cta-box {{
      background: #f7f7f7; border-left: 4px solid #e63;
      padding: 24px 28px; margin: 40px 0; border-radius: 0 8px 8px 0;
    }}
    .cta-box p {{ margin-bottom: 12px; font-weight: 500; }}
    .cta-box a {{
      display: inline-block; background: #e63; color: #fff;
      padding: 10px 22px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: 600;
    }}
    .cta-box a:hover {{ background: #c52; }}
    .back-link {{ display: inline-block; margin-top: 32px; color: #e63; text-decoration: none; font-size: 14px; }}
    .back-link:hover {{ text-decoration: underline; }}
    footer {{
      background: #111; color: #888; text-align: center;
      padding: 20px; font-size: 13px;
    }}
    footer a {{ color: #aaa; text-decoration: none; margin: 0 10px; }}
    @media (max-width: 600px) {{
      header {{ flex-direction: column; gap: 10px; }}
      nav a {{ margin: 0 8px; }}
    }}
  </style>
</head>
<body>

<header>
  <a href="/">{SITE_NAME}</a>
  <nav>
    <a href="/">Home</a>
    <a href="/services/">Services</a>
    <a href="/blog/">Blogs</a>
    <a href="/contactus/">Contact</a>
  </nav>
</header>

<div class="hero">
  <h1>{title}</h1>
  <p class="meta">By {SITE_NAME} &nbsp;|&nbsp; {date_display}</p>
</div>

<div class="container">

  <p>{intro}</p>
  {sections_html}

  <h2>Conclusion</h2>
  <p>{conclusion}</p>

  <div class="cta-box">
    <p>Ready to grow your brand with expert digital marketing?</p>
    <a href="/contactus/">Talk to Minds Of Brands →</a>
  </div>

  <div class="tags">{tags_html}</div>

  <a class="back-link" href="/blog/">← Back to All Blogs</a>

</div>

<footer>
  <p>© 2026 {SITE_NAME}. All rights reserved.</p>
  <p style="margin-top:8px">
    <a href="/">Home</a>
    <a href="/services/">Services</a>
    <a href="/blog/">Blogs</a>
    <a href="/contactus/">Contact</a>
  </p>
</footer>

</body>
</html>
"""

# ─── BLOG INDEX REGENERATOR ───────────────────────────────────────────────────

def regenerate_blog_index():
    """Scan all blog folders and rebuild blog/index.html."""
    blog_path = Path(BLOG_DIR)
    posts = []

    for folder in sorted(blog_path.iterdir(), reverse=True):
        post_file = folder / "index.html"
        if not folder.is_dir() or not post_file.exists():
            continue

        # Read title + description from the post file
        html = post_file.read_text(encoding="utf-8")

        title_match = re.search(r'<title>(.*?)\s*\|', html)
        desc_match  = re.search(r'<meta name="description" content="(.*?)"', html)
        date_match  = re.search(r'<p class="meta">.*?(\w+ \d+, \d{4})', html)

        title = title_match.group(1).strip() if title_match else folder.name.replace("-", " ").title()
        desc  = desc_match.group(1).strip()  if desc_match  else "Read this post on our blog."
        date  = date_match.group(1).strip()  if date_match  else ""

        posts.append({"slug": folder.name, "title": title, "desc": desc, "date": date})

    cards_html = ""
    for p in posts:
        cards_html += f"""
    <div class="post-card">
      <h2><a href="/blog/{p['slug']}/">{p['title']}</a></h2>
      {"<p class='post-date'>" + p['date'] + "</p>" if p['date'] else ""}
      <p>{p['desc']}</p>
      <a href="/blog/{p['slug']}/" class="read-more">Read More →</a>
    </div>"""

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blog | {SITE_NAME}</title>
  <meta name="description" content="Digital marketing insights, SEO tips, and branding strategies from {SITE_NAME}.">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #fff; color: #222; }}
    header {{
      background: #111; color: #fff; padding: 14px 24px;
      display: flex; align-items: center; justify-content: space-between;
    }}
    header a {{ color: #fff; text-decoration: none; font-size: 20px; font-weight: 700; }}
    nav a {{ color: #ccc; text-decoration: none; font-size: 14px; margin-left: 20px; }}
    nav a:hover {{ color: #fff; }}
    .hero {{ background: #111; color: #fff; padding: 50px 24px; text-align: center; }}
    .hero h1 {{ font-size: 36px; font-weight: 700; }}
    .hero p {{ color: #aaa; margin-top: 10px; }}
    .container {{ max-width: 900px; margin: 0 auto; padding: 48px 24px; }}
    .post-card {{
      border: 1px solid #eee; border-radius: 10px;
      padding: 24px 28px; margin-bottom: 24px;
      transition: box-shadow .2s;
    }}
    .post-card:hover {{ box-shadow: 0 4px 20px rgba(0,0,0,.08); }}
    .post-card h2 {{ font-size: 20px; margin-bottom: 8px; }}
    .post-card h2 a {{ color: #111; text-decoration: none; }}
    .post-card h2 a:hover {{ color: #e63; }}
    .post-date {{ font-size: 13px; color: #999; margin-bottom: 8px; }}
    .post-card p {{ font-size: 15px; color: #555; line-height: 1.6; margin-bottom: 14px; }}
    .read-more {{ color: #e63; text-decoration: none; font-size: 14px; font-weight: 600; }}
    .read-more:hover {{ text-decoration: underline; }}
    footer {{
      background: #111; color: #888; text-align: center;
      padding: 20px; font-size: 13px; margin-top: 40px;
    }}
    footer a {{ color: #aaa; text-decoration: none; margin: 0 10px; }}
  </style>
</head>
<body>
<header>
  <a href="/">{SITE_NAME}</a>
  <nav>
    <a href="/">Home</a><a href="/services/">Services</a>
    <a href="/blog/">Blogs</a><a href="/contactus/">Contact</a>
  </nav>
</header>
<div class="hero">
  <h1>Our Blogs</h1>
  <p>Digital marketing insights to grow your business</p>
</div>
<div class="container">
  {cards_html if cards_html else "<p>No blog posts yet. Check back soon!</p>"}
</div>
<footer>
  <p>© 2026 {SITE_NAME}. All rights reserved.</p>
  <p style="margin-top:8px">
    <a href="/">Home</a><a href="/services/">Services</a>
    <a href="/blog/">Blogs</a><a href="/contactus/">Contact</a>
  </p>
</footer>
</body>
</html>"""

    Path(BLOG_INDEX).write_text(index_html, encoding="utf-8")
    print(f"Blog index regenerated with {len(posts)} posts.")

# ─── SITEMAP GENERATOR ────────────────────────────────────────────────────────

def regenerate_sitemap():
    """Auto-rebuild sitemap.xml from all blog folders."""
    blog_path = Path(BLOG_DIR)
    urls = [
        f"  <url><loc>{SITE_URL}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>",
        f"  <url><loc>{SITE_URL}/blog/</loc><changefreq>daily</changefreq><priority>0.9</priority></url>",
        f"  <url><loc>{SITE_URL}/services/</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>",
        f"  <url><loc>{SITE_URL}/about/</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>",
        f"  <url><loc>{SITE_URL}/contactus/</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>",
    ]
    if blog_path.exists():
        for folder in sorted(blog_path.iterdir()):
            if folder.is_dir() and (folder / "index.html").exists():
                urls.append(
                    f"  <url><loc>{SITE_URL}/blog/{folder.name}/</loc>"
                    f"<changefreq>monthly</changefreq><priority>0.7</priority></url>"
                )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>"
    )
    Path(SITEMAP_FILE).write_text(sitemap, encoding="utf-8")
    print(f"Sitemap updated with {len(urls)} URLs.")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY secret is not set!\n"
            "Go to: GitHub repo → Settings → Secrets → Actions → New secret\n"
            "Name: GEMINI_API_KEY\n"
            "Get free key: https://aistudio.google.com/apikey"
        )

    # 1. Pick topic
    topic = pick_topic()

    # 2. Generate content via Gemini
    content = generate_blog_content(topic, api_key)

    # 3. Build slug and folder
    slug = slugify(content.get("title", topic))
    folder = Path(BLOG_DIR) / slug
    folder.mkdir(parents=True, exist_ok=True)

    # 4. Write post HTML
    post_html = build_post_html(topic, slug, content)
    post_file = folder / "index.html"
    post_file.write_text(post_html, encoding="utf-8")
    print(f"Created: {post_file}")

    # 5. Rebuild blog index
    regenerate_blog_index()

    # 6. Rebuild sitemap
    regenerate_sitemap()

    print("Done! Blog post published successfully.")

if __name__ == "__main__":
    main()
