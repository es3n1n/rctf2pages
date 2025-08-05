from pathlib import Path
from sys import argv
from sys import exit as sys_exit
from typing import TYPE_CHECKING

from tree_sitter_language_pack import get_parser

from .passes import import_passes, pass_callbacks
from .types.ctx import Context


if TYPE_CHECKING:
    from tree_sitter import Tree


def get_bundle_path(out_dir: Path) -> Path:
    bundle_path = out_dir / 'assets'
    assert bundle_path.exists()

    js_files = list(bundle_path.glob('*.js'))
    assert len(js_files) == 1

    return js_files[0]


def main() -> int:
    out_dir = Path(argv[1])
    bundle_path = get_bundle_path(out_dir)

    parser = get_parser('javascript')
    source = bundle_path.read_bytes()
    tree: Tree = parser.parse(source)
    ctx = Context(tree=tree, parser=parser, source=source)

    print(f'+++ imported {import_passes()} passes')
    for name, callback in pass_callbacks:
        print(f'++++ running {name}')
        callback(ctx)

    print('+++ writing back')
    bundle_path.write_bytes(ctx.source)
    return 0


if __name__ == '__main__':
    sys_exit(main())
