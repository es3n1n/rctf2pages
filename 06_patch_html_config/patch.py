import re, json, html
from pathlib import Path
from sys import argv


HTML_RE = re.compile(
    r'<meta\s+name=["\']rctf-config["\']\s+content=["\']([\s\S]*?)["\']\s*/?>',
    re.I | re.DOTALL,
)
ACTION_BUTTON_RE = re.compile(
    r'<action-button\b[^>]*(?:\/>|>[\s\S]*?<\/action-button\s*>)',
    re.I | re.DOTALL,
)


def main() -> None:
    out_dir = Path(argv[1])

    for p in out_dir.rglob('*.html'):
        print(f'+++ {p.name}')
        text = p.read_text()
        m = HTML_RE.search(text)
        if not m:
            msg = 'No rctf-config?'
            raise ValueError(msg)

        cfg = json.loads(html.unescape(m.group(1)))
        cfg['homeContent'] = ACTION_BUTTON_RE.sub('', cfg['homeContent'])

        new_value = html.escape(
            json.dumps(cfg, separators=(',', ':')),
            quote=True,
        )

        def repl(match: re.Match) -> str:
            return match.group(0).replace(match.group(1), new_value)

        new_text = HTML_RE.sub(repl, text, count=1)
        p.write_text(new_text)


if __name__ == '__main__':
    main()
