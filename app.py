import csv
import os
import re
from datetime import datetime

import humanize
from flask import Flask, render_template

app = Flask(__name__)

PAGE_REFRESH_SECONDS = 10 * 60


def clean_rss_title(title):
    """Strip repost markers and leading @handle so cards show just the post text."""
    title = re.sub(r'^@[A-Za-z0-9_]+\s+reposted\s+', '', title or '').strip()
    return re.sub(r'^@[A-Za-z0-9_]+\s*:\s*', '', title).strip()


def load_csv_stories(data_dir, key, limit=30, is_rss=False):
    file_path = os.path.join(data_dir, f'{key}.csv')
    if not os.path.isfile(file_path):
        return []

    items = []
    with open(file_path) as file:
        reader = csv.DictReader(file)
        for item in list(reader)[:limit]:
            time = int(item.pop('time') or 0)
            if time:
                ago_time = humanize.naturaltime(datetime.utcnow() - datetime.utcfromtimestamp(time))
            else:
                ago_time = ''
            item['time'] = ago_time
            item['is_rss'] = is_rss
            if is_rss:
                link = item.get('url') or ''
                by = item.get('by') or ''
                item['title'] = clean_rss_title(item.get('title'))
                item['hn_url'] = link
                item['user_url'] = f'https://x.com/{by}' if by else link
                item['score'] = None
                item['descendants'] = None
            else:
                item['hn_url'] = f'https://news.ycombinator.com/item?id={item["id"]}'
                item['user_url'] = f'https://news.ycombinator.com/user?id={item["by"]}'
            items.append(item)
    return items


@app.route('/')
def index():
    data_dir = 'data'
    rss_title_path = os.path.join(data_dir, 'rss_title.txt')
    rss_title = 'MyTwitter'
    if os.path.isfile(rss_title_path):
        with open(rss_title_path) as file:
            rss_title = file.read().strip() or rss_title

    stories = {
        'Top': load_csv_stories(data_dir, 'top'),
        'New': load_csv_stories(data_dir, 'new'),
        rss_title: load_csv_stories(data_dir, 'rss', is_rss=True),
        'Show HN': load_csv_stories(data_dir, 'show'),
        'New Show HN': load_csv_stories(data_dir, 'shownew'),
    }

    return render_template(
        'index.html',
        stories=stories,
        refresh_seconds=PAGE_REFRESH_SECONDS,
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
