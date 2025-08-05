from tree_sitter import Node, QueryCursor

from patcher.types.ctx import Context, NodeToReplace
from patcher.utils.ast import advance_to_comma


# Profile button
def _apply_profile_button_patch(ctx: Context, replacements: list[tuple[Node | NodeToReplace, bytes]]) -> None:
    captured = QueryCursor(
        ctx.language.query(r"""
        ((pair
          key: (property_identifier) @key
          value: (call_expression
            function: (identifier)
              arguments: (arguments
                (identifier)
                (object)
                (string) @str))) @pair
        (#eq? @key "element")
        (#eq? @str "\"profile-private\""))
    """)
    ).captures(ctx.tree.root_node)

    assert len(captured['pair']) == 1
    replacements.extend((advance_to_comma(pair_node.parent), b'') for pair_node in captured['pair'])


# Logout button
def _apply_logout_button_patch(ctx: Context, replacements: list[tuple[Node | NodeToReplace, bytes]]) -> None:
    captured = QueryCursor(
        ctx.language.query(r"""
        ((object
          (pair
            key: (property_identifier) @href_key
            value: (string) @href_val)
          (pair
            key: (property_identifier) @click_key
            value: (identifier) @handler)
          (pair
            key: (property_identifier) @children_key
            value: (string) @children_val)) @obj
        (#eq? @href_key "href")
        (#eq? @href_val "\"#\"")
        (#eq? @click_key "onClick")
        (#eq? @children_key "children")
        (#eq? @children_val "\"Logout\""))
    """)
    ).captures(ctx.tree.root_node)

    assert len(captured['obj']) == 1
    for obj in captured['obj']:
        parent = obj
        while parent.type != 'array':
            parent = parent.parent
        replacements.append((parent, b'[]'))


def pass_entry(ctx: Context) -> None:
    replacements = []
    _apply_profile_button_patch(ctx, replacements)
    _apply_logout_button_patch(ctx, replacements)
    ctx.apply_replacements(replacements)
