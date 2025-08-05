from tree_sitter import Node, QueryCursor

from patcher.types.ctx import Context


# `localStorage.getItem("token")` !== null => `true`
# `localStorage.getItem("token")` === null => `false`
# `localStorage.getItem("token")` != null => `true`
# `localStorage.getItem("token")` == null => `false`
def _apply_get_item_patch(ctx: Context, replacements: list[tuple[Node, bytes]]) -> None:
    captured = QueryCursor(
        ctx.language.query(r"""
        [
          (binary_expression
            left: (null)
            ["!=="
            "==="
            "=="
            "!="] @op
            right: (call_expression
              function: (member_expression
                object: (identifier) @obj
                property: (property_identifier) @method)
              arguments: (arguments (string) @key)))
          (binary_expression
            left: (call_expression
              function: (member_expression
                object: (identifier) @obj
                property: (property_identifier) @method)
              arguments: (arguments (string) @key))
            ["!=="
            "==="
            "=="
            "!="] @op
            right: (null))
        ] @to_replace
        (#eq? @obj "localStorage")
        (#eq? @method "getItem")
        (#eq? @key "\"token\"")
    """)
    ).captures(ctx.tree.root_node)
    for i, node in enumerate(captured['to_replace']):
        op: Node = captured['op'][i]
        evaluated_result = {
            b'==': b'false',
            b'===': b'false',
            b'!==': b'true',
            b'!=': b'true',
        }[ctx.source[op.start_byte : op.end_byte]]
        replacements.append((node, evaluated_result))


# !localStorage.token -> false
def _apply_unary_token_patch(ctx: Context, replacements: list[tuple[Node, bytes]]) -> None:
    captured = QueryCursor(
        ctx.language.query(r"""
        ((unary_expression
          operator: "!"
          argument: (member_expression
            object: (identifier) @obj
            property: (property_identifier) @prop)) @to_replace
        (#eq? @obj "localStorage")
        (#eq? @prop "token"))
    """)
    ).captures(ctx.tree.root_node)
    replacements.extend((node, b'false') for node in captured['to_replace'])


def pass_entry(ctx: Context) -> None:
    replacements = []
    _apply_get_item_patch(ctx, replacements)
    _apply_unary_token_patch(ctx, replacements)
    ctx.apply_replacements(replacements)
