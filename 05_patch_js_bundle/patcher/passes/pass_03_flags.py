from tree_sitter import Node, QueryCursor

from patcher.types.ctx import Context, NodeToReplace
from patcher.utils.ast import advance_to_comma


# Submit flag form
def _apply_submit_flag_form_patch(ctx: Context, replacements: list[tuple[Node | NodeToReplace, bytes]]) -> None:
    captured = QueryCursor(
        ctx.language.query(r"""
        ((parenthesized_expression
          (ternary_expression
            condition: (identifier)
            consequence: (string) @s_true
            alternative: (string) @s_false)) @to_replace
        (#eq? @s_true "\" (solved)\"")
        (#eq? @s_false "\"\""))
    """)
    ).captures(ctx.tree.root_node)

    assert len(captured['to_replace']) == 1
    for node in captured['to_replace']:
        expr = node
        for _ in range(3):
            expr = expr.parent
            while expr.type != 'call_expression':
                expr = expr.parent

        replacements.append((advance_to_comma(expr), b''))


def pass_entry(ctx: Context) -> None:
    replacements = []
    _apply_submit_flag_form_patch(ctx, replacements)
    ctx.apply_replacements(replacements)
