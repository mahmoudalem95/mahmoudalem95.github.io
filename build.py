#!/usr/bin/env python3
"""Builds the root site (mahmoudalem95.github.io) as exact copies of the MAHALCO home pages.

    python3 build.py /path/to/mahalco-checkout

Pages copied (source in the mahalco repo -> path here):
    index.html      -> index.html      (Hebrew home)
    ar/index.html   -> ar/index.html   (Arabic home)
    apis-he.html    -> apis-he.html    (forwards to the Hebrew home, as on the site)
    apis-ar.html    -> apis-ar.html    (forwards to the Arabic home, as on the site)

Each copy gets <base href=".../mahalco/<dir>/"> so every style, script, image and tool link
keeps loading from the real site. Links between the copied pages stay on the root address.
Missing paths fall back to the same path under /mahalco/ (404.html).
Do not edit the copies by hand: edit the mahalco repo; the GitHub Action rebuilds these.
"""
import os
import posixpath
import re
import sys

SITE = "https://mahmoudalem95.github.io/mahalco/"
PAGES = {"index.html": "index.html", "ar/index.html": "ar/index.html",
         "apis-he.html": "apis-he.html", "apis-ar.html": "apis-ar.html"}
# where links to the copied pages should point on the root address
LOCAL = {"index.html": "/", "": "/", "apis-he.html": "/",
         "ar/index.html": "/ar/", "ar/": "/ar/", "ar": "/ar/", "apis-ar.html": "/ar/"}

HASH_FIX = ("<script>/* root copy: in-page #links stay on this page despite <base> */"
            "document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href^=\"#\"]');"
            "if(!a)return;var h=a.getAttribute('href');if(h.length<2)return;e.preventDefault();"
            "if(location.hash!==h)history.pushState(null,'',location.pathname+location.search+h);"
            "var t=document.getElementById(decodeURIComponent(h.slice(1)));if(t)t.scrollIntoView();"
            "window.dispatchEvent(new HashChangeEvent('hashchange'));},true);</script>")

ATTR = re.compile(r'(\s(?:href|data-en)=")([^"]*)(")')
SKIP = re.compile(r'^(?:[a-z][a-z0-9+.-]*:|//|/|#|\{)', re.I)


def localize(src_path: str, html: str) -> str:
    d = posixpath.dirname(src_path)
    base = SITE + (d + "/" if d else "")

    def fix(m):
        url = m.group(2)
        if SKIP.match(url) or not url:
            return m.group(0)
        path, tail = re.match(r'([^?#]*)(.*)', url).groups()
        target = posixpath.normpath(posixpath.join(d, path)) if path else src_path
        if target == ".":
            target = ""
        if path.endswith("/") and target:
            target += "/"
        if m.group(1).strip().startswith("data-en"):          # read with location.href, not <base>
            return m.group(1) + SITE + target + tail + m.group(3)
        if target in LOCAL:
            return m.group(1) + LOCAL[target] + tail + m.group(3)
        return m.group(0)                                     # resolved by <base>

    html = ATTR.sub(fix, html)
    # JS redirects in the forwarding pages
    for t, loc in (("index.html", "/"), ("ar/index.html", "/ar/")):
        html = html.replace('location.replace("%s"' % t, 'location.replace("%s"' % loc)
        html = html.replace('url=%s"' % t, 'url=%s"' % loc)
    head = re.search(r'<head[^>]*>', html, re.I)
    if not head:
        raise SystemExit("no <head> in " + src_path)
    at = head.end()
    cs = re.search(r'<meta\s+charset=[^>]*>', html[at:at + 2000], re.I)   # keep charset first
    if cs:
        at += cs.end()
    inject = '\n<base href="%s">\n%s' % (base, HASH_FIX)
    return html[:at] + inject + html[at:]


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    src_root = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    for src, dst in PAGES.items():
        with open(os.path.join(src_root, src), encoding="utf-8") as f:
            out = localize(src, f.read())
        p = os.path.join(here, dst)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(out)
        print("built", dst)


if __name__ == "__main__":
    main()
