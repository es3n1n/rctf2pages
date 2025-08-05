from dataclasses import dataclass

from tree_sitter import Language, Node, Parser, Tree


@dataclass(frozen=True)
class NodeToReplace:
    start_byte: int
    end_byte: int
    start_point: int
    end_point: int


@dataclass
class Context:
    tree: Tree
    parser: Parser
    source: bytes

    @property
    def language(self) -> Language:
        return self.parser.language

    def apply_replacements(self, replacements: list[tuple[Node | NodeToReplace, bytes]]) -> None:
        print(f'+++++ applying {len(replacements)} replacements')
        replacements.sort(key=lambda x: x[0].start_byte, reverse=True)
        buf = bytearray(self.source)

        for node, repl in replacements:
            s, e = node.start_byte, node.end_byte
            sp, ep = node.start_point, node.end_point
            new_len = len(repl)
            buf[s:e] = repl

            self.tree.edit(
                start_byte=s,
                old_end_byte=e,
                new_end_byte=s + new_len,
                start_point=sp,
                old_end_point=ep,
                new_end_point=(sp[0], sp[1] + new_len),
            )

        self.source = bytes(buf)
        self.tree = self.parser.parse(self.source, self.tree)
