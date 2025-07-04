from sys import argv
from pathlib import Path
from json import loads, dumps
from urllib.parse import urlparse, urlunparse

main_host = urlparse(argv[1]).netloc
out_dir = Path(argv[2])

challs_file = out_dir / 'api' / 'v1' / 'challs' / 'index.json'
challs_data = loads(challs_file.read_text())

for item in challs_data['data']:
    for file in item['files']:
        u = urlparse(file['url'])
        file['url'] = u.path

challs_file.write_text(dumps(challs_data))
