import csv
import os
from datetime import datetime

import humanize
from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    data_dir = 'data'
    stories = {}
    files = {'top': 'Top', 'new': 'New', 'ask': 'Ask HN', 'show': 'Show HN'}

    for key, value in files.items():
        stories[value] = []
        file_path = os.path.join(data_dir, f'{key}.csv')
        if not os.path.isfile(file_path):
            continue

        with open(os.path.join(data_dir, f'{key}.csv')) as file:
            reader = csv.DictReader(file)
            for item in list(reader)[:30]:
                time = int(item.pop('time'))
                ago_time = humanize.naturaltime(datetime.utcnow() - datetime.utcfromtimestamp(time))
                item['time'] = ago_time
                item['hn_url'] = f'https://news.ycombinator.com/item?id={item["id"]}'
                item['user_url'] = f'https://news.ycombinator.com/user?id={item["by"]}'
                stories[value].append(item)

    return render_template('index.html', stories=stories)


if __name__ == '__main__':
<<<<<<< HEAD
    app.run(host='0.0.0.0', port=9443, ssl_context=("cert.pem", "key.pem"))
=======
    app.run(host='0.0.0.0', port=5000, debug=True)
>>>>>>> fd7038064d3a9d6c7618393bb1ce6894a0c45d97
