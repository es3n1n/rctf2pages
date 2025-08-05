from tree_sitter import Node, QueryCursor

from patcher.types.ctx import Context, NodeToReplace


RCTF_URL = 'https://rctf.redpwn.net/'
REPO_URL = 'https://github.com/es3n1n/rctf2pages'


# `Powered by rCTF` -> `Powered by ~~rCTF~~ rctf2pages`
def _apply_easter_egg_patch(ctx: Context, replacements: list[tuple[Node | NodeToReplace, bytes]]) -> None:
    captured = QueryCursor(
        ctx.language.query(r"""
        ((string) @str
        (#eq? @str "\"Powered by\""))
    """)
    ).captures(ctx.tree.root_node)

    if not captured.get('str'):
        return

    assert len(captured['str']) == 1
    for string in captured['str']:
        arr = string.parent
        func_call = string
        while func_call and func_call.type != 'call_expression':
            func_call = func_call.next_sibling

        if not func_call or not func_call.children:
            continue

        func_name_node = func_call.children[0]
        func_name = ctx.source[func_name_node.start_byte : func_name_node.end_byte].decode()

        new_array = '["Powered by"," "'
        new_array += (
            f',{func_name}("s",{{children:{func_name}("a",{{href:"'
            f'{RCTF_URL}",target:"_blank",rel:"noopener noreferrer",children:"rCTF"}})}})'
        )
        new_array += (
            f'," ",{func_name}("a",{{href:"{REPO_URL}",target:"_blank",'
            f'rel:"noopener noreferrer",children:"rctf2pages"}})'
        )
        new_array += ']'
        replacements.append((arr, new_array.encode()))


def pass_entry(ctx: Context) -> None:
    replacements = []
    _apply_easter_egg_patch(ctx, replacements)
    ctx.apply_replacements(replacements)
