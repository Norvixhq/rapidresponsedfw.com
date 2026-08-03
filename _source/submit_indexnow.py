#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Submit every URL in sitemap.xml to IndexNow.

IndexNow notifies Bing, Yandex, Seznam and Naver that pages have changed.
Google does NOT currently use IndexNow, so this does nothing for Google —
Search Console and the sitemap remain the route there.

Run from the _source directory after publishing changes:

    python3 submit_indexnow.py            # submit everything in the sitemap
    python3 submit_indexnow.py --dry-run  # show what would be sent
    python3 submit_indexnow.py /contact/ /services/mold-remediation/

Requires no packages — standard library only.
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error

HOST = "rapidresponsedfw.com"
KEY = "acf7ea79795d468590f3c43c38ca45d7"
KEY_LOCATION = "https://%s/%s.txt" % (HOST, KEY)
ENDPOINT = "https://api.indexnow.org/IndexNow"
SITE = "https://" + HOST

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITEMAP = os.path.join(ROOT, "sitemap.xml")

STATUS = {
    200: "OK — URLs accepted.",
    202: "Accepted — URLs received, key validation pending.",
    400: "Bad request — malformed JSON.",
    403: "Forbidden — key file not found at keyLocation, or key mismatch. "
         "Check https://%s/%s.txt loads and contains only the key." % (HOST, KEY),
    422: "Unprocessable — a URL does not belong to this host, or the key is malformed.",
    429: "Too many requests — wait before resubmitting.",
}


def urls_from_sitemap():
    if not os.path.exists(SITEMAP):
        sys.exit("sitemap.xml not found at %s — run page_misc.py first." % SITEMAP)
    with open(SITEMAP, encoding="utf-8") as fh:
        return re.findall(r"<loc>(.*?)</loc>", fh.read())


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry = "--dry-run" in sys.argv

    if args:
        urls = [a if a.startswith("http") else SITE + a for a in args]
    else:
        urls = urls_from_sitemap()

    bad = [u for u in urls if not u.startswith(SITE)]
    if bad:
        sys.exit("These URLs are not on %s and would be rejected:\n  %s"
                 % (HOST, "\n  ".join(bad)))

    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }

    print("host        : %s" % HOST)
    print("keyLocation : %s" % KEY_LOCATION)
    print("urls        : %d" % len(urls))
    for u in urls[:5]:
        print("              %s" % u)
    if len(urls) > 5:
        print("              ... and %d more" % (len(urls) - 5))

    if dry:
        print("\n--dry-run: nothing sent.")
        return

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=body, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            code = resp.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:
        sys.exit("\nRequest failed: %s" % e)

    print("\nHTTP %s — %s" % (code, STATUS.get(code, "Unexpected response.")))
    if code in (200, 202):
        print("Verify receipt in Bing Webmaster Tools > IndexNow.")


if __name__ == "__main__":
    main()
