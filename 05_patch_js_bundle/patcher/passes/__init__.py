from collections.abc import Callable
from importlib import import_module
from pathlib import Path

from tree_sitter import Tree


pass_callbacks: list[tuple[str, Callable[[Tree], None]]] = []


def import_passes() -> int:
    for py in Path(__file__).parent.glob('*.py'):
        if py.name == '__init__.py':
            continue

        m = import_module(f'patcher.passes.{py.stem}')
        pass_func = m.pass_entry
        if not pass_func:
            continue

        pass_callbacks.append((py.stem, pass_func))

    return len(pass_callbacks)
