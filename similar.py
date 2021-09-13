try:
    from requests import get
    from urllib.parse import urlparse
except ImportError as err:
    print(f"Failed to import required modules {err}")


def similarGet(website):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
               'Referer': 'https://collector-px53qntki3.perimeterx.net',
               "Connection": "keep-alive",
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
               'Accept-Language': 'en-US,en;q=0.5',
               'Accept-Encoding': 'gzip, deflate, br'}
    domain = '{uri.netloc}'.format(uri=urlparse(website))
    domain = domain.replace("www.", "")
    ENDPOINT = 'https://data.similarweb.com/api/v1/data?domain=' + domain
    resp = get(ENDPOINT, headers=headers)

    if resp.status_code == 200:
        return resp.json()
    else:
        print(resp.text)
        resp.raise_for_status()
        return False
