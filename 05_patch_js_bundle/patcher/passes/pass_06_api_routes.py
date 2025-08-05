from tree_sitter import Node, QueryCursor

from patcher.types.ctx import Context, NodeToReplace


def resolve_mapping(ctx: Context, node: Node) -> dict[str, str]:
    mapping = {}
    for item in ctx.source[node.start_byte : node.end_byte].decode().strip('{}').split(','):
        args = item.split(':')
        mapping[args[0]] = args[1]
    return mapping


# `/leaderboard/now`
def _apply_leaderboard_now_patch(ctx: Context, replacements: list[tuple[Node | NodeToReplace, bytes]]) -> None:
    captured = QueryCursor(
        ctx.language.query(r"""
        ((string) @str
        (#eq? @str "\"/leaderboard/now\""))
    """)
    ).captures(ctx.tree.root_node)

    assert len(captured['str']) == 1

    for string in captured['str']:
        get_params = string.next_sibling.next_sibling
        assert get_params.type == 'object'
        replacements.append((get_params, b'{}'))

        mapping = resolve_mapping(ctx, get_params)
        replacements.append(
            (
                string,
                f'`/leaderboard/now-${{{mapping["division"]}||"all"}}-${{{mapping["limit"]}}}-${{{mapping["offset"]}}}`'.encode(),
            )
        )


# `/leaderboard/graph`
def _apply_leaderboard_graph_patch(ctx: Context, replacements: list[tuple[Node | NodeToReplace, bytes]]) -> None:
    captured = QueryCursor(
        ctx.language.query(r"""
        ((string) @str
        (#eq? @str "\"/leaderboard/graph\""))
    """)
    ).captures(ctx.tree.root_node)

    assert len(captured['str']) == 1

    for string in captured['str']:
        get_params = string.next_sibling.next_sibling
        assert get_params.type == 'object'
        replacements.append((get_params, b'{}'))

        mapping = resolve_mapping(ctx, get_params)
        replacements.append(
            (string, f'`/leaderboard/graph-${{{mapping["division"]}||"all"}}-${{{mapping["limit"]}}}`'.encode())
        )


# `/challs/[id]/solves`
def _apply_challs_solves_patch(ctx: Context, replacements: list[tuple[Node | NodeToReplace, bytes]]) -> None:
    captured = QueryCursor(
        ctx.language.query(r"""
        ((template_string) @str
        (#match? @str "^`/challs/\\$\\{encodeURIComponent\\([^}]+\\)}/solves`$"))
    """)
    ).captures(ctx.tree.root_node)

    for string in captured['str']:
        get_params = string.next_sibling.next_sibling
        assert get_params.type == 'object'
        replacements.append((get_params, b'{}'))
        mapping = resolve_mapping(ctx, get_params)

        new_str = ctx.source[string.start_byte : string.end_byte].decode()
        new_str = new_str.replace('/solves', f'/solves-${{{mapping["limit"]}}}-${{{mapping["offset"]}}}')
        replacements.append((string, new_str.encode()))


def pass_entry(ctx: Context) -> None:
    replacements = []
    _apply_leaderboard_now_patch(ctx, replacements)
    _apply_leaderboard_graph_patch(ctx, replacements)
    _apply_challs_solves_patch(ctx, replacements)
    ctx.apply_replacements(replacements)
