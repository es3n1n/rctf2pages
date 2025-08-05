from tree_sitter import Node, QueryCursor

from patcher.types.ctx import Context, NodeToReplace
from patcher.utils.ast import advance_to_comma


# Show solved filter block
def _apply_show_solved_patch(ctx: Context, replacements: list[tuple[Node | NodeToReplace, bytes]]) -> None:
    captured = QueryCursor(
        ctx.language.query(r"""
        ((pair
          key: (property_identifier) @key
          value: (string) @str) @pair
        (#eq? @key "id")
        (#eq? @str "\"show-solved\""))
    """)
    ).captures(ctx.tree.root_node)

    assert len(captured['pair']) == 1
    for node in captured['pair']:
        expr = node
        for _ in range(5):
            expr = expr.parent
            while expr.type != 'call_expression':
                expr = expr.parent

        replacements.append((advance_to_comma(expr), b''))


def pass_entry(ctx: Context) -> None:
    replacements = []
    _apply_show_solved_patch(ctx, replacements)
    ctx.apply_replacements(replacements)
