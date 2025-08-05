from tree_sitter import Node, QueryCursor

from patcher.types.ctx import Context, NodeToReplace


# `The CTF is over.` -> `The CTF is archived.`
def _apply_ctf_is_archived_patch(ctx: Context, replacements: list[tuple[Node | NodeToReplace, bytes]]) -> None:
    captured = QueryCursor(
        ctx.language.query(r"""
        ((string) @str
        (#eq? @str "\"The CTF is over.\""))
    """)
    ).captures(ctx.tree.root_node)
    replacements.extend((string, b'"The CTF is archived."') for string in captured['str'])


def pass_entry(ctx: Context) -> None:
    replacements = []
    _apply_ctf_is_archived_patch(ctx, replacements)
    ctx.apply_replacements(replacements)
