from sys import argv
from pathlib import Path
from json import loads, dumps
from urllib.parse import urlparse, urlunparse



def sanitize_name(name: str) -> str:
    for c in ('\\', '/', '%2F', '%5C'):
        name = name.replace(c, '-')
    return name


def main() -> None:
    main_host = urlparse(argv[1]).netloc
    out_dir = Path(argv[2])

    challs_dir = out_dir / 'api' / 'v1' / 'challs'
    challs_file = challs_dir / 'index.json'
    challs_data = loads(challs_file.read_text())

    for item in challs_data['data']:
        item['id'] = sanitize_name(item['id'])
        for file in item['files']:
            u = urlparse(file['url'])
            file['url'] = u.path

    challs_file.write_text(dumps(challs_data))

    for d in challs_dir.iterdir():
        if not d.is_dir():
            continue

        replaced_name = sanitize_name(d.name)
        if d.name == replaced_name:
            continue

        dst = d.with_name(replaced_name)
        assert not dst.exists()
        d.rename(dst)


if __name__ == '__main__':
    main()
