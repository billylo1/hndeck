import csv
import os
import re
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from xml.etree import ElementTree

import requests

RSS_FEED_URL = (
    'https://mytwitter-feed.web.app/feed.xml'
    '?token=PxfOyFq_Gb4FnU3jeOFylpf2wPIwboZ4'
)


def scrape_item(story):
    try:
        item_url = f'https://hacker-news.firebaseio.com/v0/item/{story}.json?print=pretty'
        item_response = requests.get(item_url, timeout=180)
        item = item_response.json()
    except:
        return

    if not item:
        return
    item.pop('kids', None)
    fields = list(item.keys())
    if 'url' not in fields:
        fields.append('url')
        item['url'] = ''
    if 'text' not in fields:
        fields.append('text')
        item['text'] = ''

    fields.append('domain')
    item['domain'] = ''
    if item['url']:
        parsed_uri = urlparse(item['url'])
        domain = parsed_uri.netloc
        if domain.count('.') > 1:
            if domain.startswith(sub_domains):
                domain = domain.split('.', 1)[1]
        item['domain'] = domain
    return item


def scrape_rss(limit=30):
    try:
        response = requests.get(RSS_FEED_URL, timeout=30)
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
    except Exception as exc:
        print(f'RSS fetch failed: {exc}')
        return 'MyTwitter', []

    channel = root.find('channel')
    column_title = (channel.findtext('title') if channel is not None else None) or 'MyTwitter'
    items = []

    for entry in root.findall('.//item')[:limit]:
        title = (entry.findtext('title') or '').strip()
        link = (entry.findtext('link') or '').strip()
        guid = (entry.findtext('guid') or link).strip()
        pub_date = (entry.findtext('pubDate') or '').strip()

        unix_time = 0
        if pub_date:
            try:
                published = parsedate_to_datetime(pub_date)
                unix_time = int(published.timestamp())
            except (TypeError, ValueError, IndexError, OverflowError):
                unix_time = 0

        by = ''
        match = re.match(r'@([A-Za-z0-9_]+)', title)
        if match:
            by = match.group(1)

        # Drop "@user reposted " so the title is just the original post text.
        title = re.sub(r'^@[A-Za-z0-9_]+\s+reposted\s+', '', title).strip()

        domain = urlparse(link).netloc if link else ''
        item = {
            'by': by,
            'id': guid,
            'time': unix_time,
            'title': title,
            'url': link,
            'domain': domain,
        }
        print(item)
        items.append(item)

    return column_title, items


if __name__ == '__main__':
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)

    urls = {
        'top': 'https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty',
        'new': 'https://hacker-news.firebaseio.com/v0/newstories.json?print=pretty',
        'show': 'https://hacker-news.firebaseio.com/v0/showstories.json?print=pretty',
    }

    sub_domains = ('www.', 'mail.', 'blog.', 'ns.', 'smtp.', 'webmail.', 'docs.', 'jobs.', 'cs.', 'apply.', 'boards.')

    for key, value in urls.items():
        print(f'Scraping {key}')

        try:
            response = requests.get(value, timeout=180)
            stories = response.json()
        except:
            continue

        items = []
        for story in stories[:30]:
            item = scrape_item(story)
            if item:
                print(item)
                items.append(item)

        if not items:
            continue

        with open(os.path.join(data_dir, f'{key}.csv'), 'w') as file:
            writer = csv.DictWriter(file, fieldnames=items[0].keys())
            writer.writeheader()
            writer.writerows(items)

    # Special handling for "New Show HN" - filter newest stories for "Show HN:" titles
    print('Scraping shownew')
    try:
        response = requests.get('https://hacker-news.firebaseio.com/v0/newstories.json?print=pretty', timeout=180)
        new_stories = response.json()
    except:
        new_stories = []

    items = []
    for story_id in new_stories:
        item = scrape_item(story_id)
        if item and item.get('title', '').startswith('Show HN:'):
            print(item)
            items.append(item)
            if len(items) >= 30:
                break

    if items:
        with open(os.path.join(data_dir, 'shownew.csv'), 'w') as file:
            writer = csv.DictWriter(file, fieldnames=items[0].keys())
            writer.writeheader()
            writer.writerows(items)

    print('Scraping rss')
    rss_title, rss_items = scrape_rss()
    if rss_items:
        with open(os.path.join(data_dir, 'rss.csv'), 'w') as file:
            writer = csv.DictWriter(file, fieldnames=rss_items[0].keys())
            writer.writeheader()
            writer.writerows(rss_items)
        with open(os.path.join(data_dir, 'rss_title.txt'), 'w') as file:
            file.write(rss_title)