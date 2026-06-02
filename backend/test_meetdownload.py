from app.crawler.dldownload import _safe_get
from bs4 import BeautifulSoup

print("=== Testing hdmovies4u homepage ===")
res = _safe_get('https://hdmovies4u.in')
if res:
    soup = BeautifulSoup(res.text, 'lxml')
    print('STATUS: OK')
    print('TITLE: ' + str(soup.title))
    print()
    print('=== All links on homepage ===')
    links = soup.find_all('a', href=True)
    for a in links[0:30]:
        print(a['href'])
else:
    print('FAILED to reach hdmovies4u.in')

print()
print("=== Testing robots.txt ===")
res2 = _safe_get('https://hdmovies4u.in/robots.txt')
if res2:
    print(res2.text[0:1000])
else:
    print('No robots.txt')

print()
print("=== Testing post sitemap ===")
res3 = _safe_get('https://hdmovies4u.in/post-sitemap.xml')
if res3:
    soup3 = BeautifulSoup(res3.text, 'xml')
    urls = soup3.find_all('loc')
    print(f'Found {len(urls)} URLs in post-sitemap.xml')
    for loc in urls[:10]:
        print(loc.text.strip())
else:
    print('Could not fetch post-sitemap.xml')