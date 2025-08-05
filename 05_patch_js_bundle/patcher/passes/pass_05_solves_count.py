from tree_sitter import Node, QueryCursor

from patcher.types.ctx import Context, NodeToReplace


# Show solved filter block
def _apply_solves_count_patch(ctx: Context, replacements: list[tuple[Node | NodeToReplace, bytes]]) -> None:
    captured = QueryCursor(
        ctx.language.query(r"""
        ((array
          "["
          (identifier)
          ","
          (string) @s1
          ","
          (identifier)
          ","
          (string) @s2
          ","
          (identifier)
          ","
          (string) @s3
          "]") @arr
        (#eq? @s1 "\" (\"")
        (#eq? @s2 "\"/\"")
        (#eq? @s3 "\" solved)\""))
    """)
    ).captures(ctx.tree.root_node)

    assert len(captured['arr']) == 1
    for node in captured['arr']:
        child = node.children[1]
        assert child.type == 'identifier'
        child_text = ctx.source[child.start_byte : child.end_byte].decode()
        replacements.append((node, f'[{child_text}]'.encode()))


def pass_entry(ctx: Context) -> None:
    replacements = []
    _apply_solves_count_patch(ctx, replacements)
    ctx.apply_replacements(replacements)
