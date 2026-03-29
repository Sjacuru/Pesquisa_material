import httpx
from bs4 import BeautifulSoup

q = "9786557423902"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
r = httpx.get("https://www.amazon.com.br/s", params={"k": q, "language": "pt_BR"}, headers=headers, timeout=25.0, follow_redirects=True)
print('final_url=', r.url)
print('status=', r.status_code, 'bytes=', len(r.text or ''))
soup = BeautifulSoup(r.text, "html.parser")
cards = soup.select('[data-component-type="s-search-result"]')
print('cards=', len(cards))

dp_links = soup.select('a[href*="/dp/"]')
print('dp_links=', len(dp_links))
seen = set()
count = 0
for a in dp_links:
    href = a.get('href') or ''
    if not href or href in seen:
        continue
    seen.add(href)
    text = a.get_text(' ', strip=True)
    parent = a
    price = ''
    for _ in range(5):
        parent = parent.parent
        if not parent:
            break
        pe = parent.select_one('.a-price .a-offscreen')
        if pe:
            price = pe.get_text(strip=True)
            break
    print('-', href[:110], '| text=', text[:70], '| price=', price)
    count += 1
    if count >= 15:
        break

print('has_no_results=', bool(soup.select_one('.s-no-results-section')))
