from tree_sitter import Node

from patcher.types.ctx import NodeToReplace


def advance_to_comma(node: Node) -> NodeToReplace:
    start_byte = node.start_byte
    start_point = node.start_point

    end_byte = node.end_byte
    end_point = node.end_point

    next_sibling = node.next_sibling
    if next_sibling and next_sibling.type == ',':
        end_byte = next_sibling.end_byte
        end_point = next_sibling.end_point

    return NodeToReplace(start_byte=start_byte, end_byte=end_byte, start_point=start_point, end_point=end_point)
