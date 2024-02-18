# TODO:
#   CHECK * Add Grouper option for collecting from an opening grouping symbol (i.e. '[') to its mating closing grouping symbol (i.e. ']')
#   CHECK * Create a new Perspective at the level of a "structure" where each entry will be one of: TAG_STATEMENT, TAG_BLOCK, TAG_MODULEDECLARATION
#       Start with "comments" Perspective and tag based on the limits of the structResults
#   * Add handling of:
#       * System calls/tasks
#       * attributes (* foo=bar *)

# Hierarchical Perspectives:
#   Level 0: comments, whitespace, strings, keywords, reserved chars, macros, generic
#   Level 1: statements, blockopen/blockclose, module instantiation headers, param lists, port lists,
#            module declaration headers, parammaps, portmaps, generate-for, generate-if
#   Level 2: statements, module declarations, module instantiations, always/initial blocks

from parser import Grouper, TagMap, StructParser
from constr import ConStr, Perspective, _tag, _subtag, MultiTag

__tags__ = (
    "TAG_GENERIC",
    "KEYWORD_MODULE",
    "KEYWORD_WIRE",
    "KEYWORD_REG",
    "KEYWORD_LOGIC",
    "KEYWORD_BEGIN",
    "KEYWORD_ALWAYS",
    "KEYWORD_INITIAL",
    "KEYWORD_IF",
    "KEYWORD_ELSE",
    "KEYWORD_INPUT",
    "KEYWORD_OUTPUT",
    "KEYWORD_INOUT",
    "KEYWORD_PARAMETER",
    "KEYWORD_LOCALPARAM",
    "KEYWORD_FOR",
    "KEYWORD_END",
    "KEYWORD_ASSIGN",
    "KEYWORD_ENDMODULE",
    "KEYWORD_POSEDGE",
    "KEYWORD_NEGEDGE",

    "RESERVED_EQUAL_DELAYED",
    "RESERVED_EQUAL",
    "RESERVED_PLUS",
    "RESERVED_MINUS",
    "RESERVED_MUL",
    "RESERVED_DIV",
    "RESERVED_PAREN_OPEN",
    "RESERVED_PAREN_CLOSE",
    "RESERVED_BRACE_OPEN",
    "RESERVED_BRACE_CLOSE",
    "RESERVED_BRACKET_OPEN",
    "RESERVED_BRACKET_CLOSE",
    "RESERVED_COMMA",
    "RESERVED_POUNDPAREN_OPEN",
    "RESERVED_ATPAREN_OPEN",
    "RESERVED_PARENSTAR_OPEN",
    "RESERVED_PARENSTAR_CLOSE",
    "RESERVED_SEMICOLON",
    "RESERVED_COLON",

    "MACRO_DEFINE",
    "MACRO_IFDEF",
    "MACRO_IFNDEF",
    "MACRO_ELSE",
    "MACRO_ENDIF",

    "TAG_KEYWORD",
    "TAG_COMMENT",
    "TAG_STRING",
    "TAG_RESERVED",
    "TAG_WHITESPACE",
    "TAG_MACRO",

    "TAG_STATEMENT",
    "TAG_BLOCK",
    "TAG_MODULEDECLARATION",
    "TAG_ATTRIBUTE",

    "TAG_ASSIGNS",
    "TAG_ASSIGN_SYNC",
    "TAG_WIREDECS",
    "TAG_REGDECS",
    "TAG_PARAMETERS",
    "TAG_LOCALPARAMS",
    "TAG_PORTS",
    "TAG_MODDEC",
    "TAG_INITIAL",
    "TAG_ALWAYS",
    "TAG_IF",
    "TAG_FOR",
)

__tag_offset = 0

for n in range(len(__tags__)):
    tag = __tags__[n]
    globals()[tag] = __tag_offset + n

def _tagstr(tag):
    if isinstance(tag, tuple) or isinstance(tag, list):
        tag, subtag = tag
        stag = "None" if tag is None else __tags__[tag-__tag_offset]
        ssubtag = "None" if subtag is None else __tags__[subtag-__tag_offset]
        return "({}, {})".format(stag, ssubtag)
    else:
        if tag is None:
            return "None"
        return __tags__[tag-__tag_offset]

import parser
parser._tagstr = _tagstr
import constr
constr._tagstr = _tagstr

_grouping_pairs = (
    ('[', ']'), ('(', ')'), ('{', '}'), ('(*', '*)')
)

_colormap = {
    TAG_COMMENT: Perspective.COLOR_LIGHTCYAN_EX,
    TAG_STRING: Perspective.COLOR_RED,
    TAG_MACRO: Perspective.COLOR_MAGENTA,
    TAG_KEYWORD: Perspective.COLOR_YELLOW,
    TAG_RESERVED: Perspective.COLOR_GREEN,
}
# Keywords are only reserved when the adjacent characters are not [a-zA-Z0-9_]
keywords = {
    KEYWORD_MODULE: "module",
    KEYWORD_WIRE: "wire",
    KEYWORD_REG: "reg",
    KEYWORD_LOGIC: "logic",
    KEYWORD_BEGIN: "begin",
    KEYWORD_ALWAYS: "always",
    KEYWORD_INITIAL: "initial",
    KEYWORD_IF: "if",
    KEYWORD_ELSE: "else",
    KEYWORD_INPUT: "input",
    KEYWORD_OUTPUT: "output",
    KEYWORD_INOUT: "inout",
    KEYWORD_PARAMETER: "parameter",
    KEYWORD_LOCALPARAM: "localparam",
    KEYWORD_FOR: "for",
    KEYWORD_END: "end",
    KEYWORD_ASSIGN: "assign",
    KEYWORD_ENDMODULE: "endmodule",
    KEYWORD_POSEDGE: "posedge",
    KEYWORD_NEGEDGE: "negedge",
}

# TODO - Order these by length (num chars) before parsing
# Reserved characters always have syntactic meaning (unless in a string or comment)
reserved = {
    # (char pattern, escaped char pattern)
    RESERVED_EQUAL_DELAYED: ("<=", "\<\="),
    RESERVED_EQUAL: ("=", "\="),
    RESERVED_PLUS: ("+", "\+"),
    RESERVED_MINUS: ("-", "\-"),
    RESERVED_MUL: ("*", "\*"),
    RESERVED_DIV: ("/", "\/"),
    RESERVED_PARENSTAR_OPEN: ("(*", "\(\*"),
    RESERVED_PARENSTAR_CLOSE: ("*)", "\*\)"),
    RESERVED_POUNDPAREN_OPEN: ("#(", "#\("),
    RESERVED_ATPAREN_OPEN: ("@(", "@\("),
    RESERVED_PAREN_OPEN: ("(", "\("),
    RESERVED_PAREN_CLOSE: (")", "\)"),
    RESERVED_BRACE_OPEN: ("{", "\{"),
    RESERVED_BRACE_CLOSE: ("}", "\}"),
    RESERVED_BRACKET_OPEN: ("[", "\["),
    RESERVED_BRACKET_CLOSE: ("]", "\]"),
    RESERVED_COMMA: (",", "\,"),
    RESERVED_SEMICOLON: (";", ";"),
    RESERVED_COLON: (":", "\:"),
}

_reserved_sorted = [(key, val) for key, val in reserved.items()]
_reserved_sorted.sort(key=lambda x: len(x[1][0]))
_reserved_sorted.reverse()

macros = {
    MACRO_DEFINE: "`define",
    MACRO_IFDEF: "`ifdef",
    MACRO_IFNDEF: "`ifndef",
    MACRO_ELSE: "`else",
    MACRO_ENDIF: "`endif",
}

STRING_QUOTE = '"'
COMMENT_SINGLE_LINE = "//"
COMMENT_MULTI_LINE_OPEN = "/*"
COMMENT_MULTI_LINE_CLOSE = "*/"


class VerilogGrouper(Grouper):
    can = StructParser.can
    must = StructParser.must
    collect = StructParser.collect
    collect_drop = StructParser.collect_drop
    complete = StructParser.complete

    _attribute = [
        #   collect from (* to *)
        ((TAG_RESERVED, RESERVED_PARENSTAR_OPEN), complete, None),
    ]

    _port = [
        #   mandatory keyword input/output/inout
        ((TAG_KEYWORD, (KEYWORD_INPUT, KEYWORD_OUTPUT, KEYWORD_INOUT)), must, None),
        #   mandatory whitespace
        ((TAG_WHITESPACE, None), must, None),
        #   mandatory signal name
        ((TAG_GENERIC, None), must, None),
        #   collect until reserved ';',',',')'
        #       Error on any keywords
        ((TAG_RESERVED, (RESERVED_SEMICOLON, RESERVED_COMMA, RESERVED_PAREN_CLOSE)), collect_drop, lambda t: _tag(t) == TAG_KEYWORD),
    ]

    _port_with_range = [
        #   mandatory keyword input/output/inout
        ((TAG_KEYWORD, (KEYWORD_INPUT, KEYWORD_OUTPUT, KEYWORD_INOUT)), must, None),
        #   mandatory whitespace
        ((TAG_WHITESPACE, None), must, None),
        #   complete open reserved '[' with its mating close reserved ']'
        ((TAG_RESERVED, RESERVED_BRACKET_OPEN), complete, lambda t: _tag(t) != TAG_GENERIC),
        #   optional whitespace
        ((TAG_WHITESPACE, None), can, None),
        #   mandatory signal name
        ((TAG_GENERIC, None), must, None),
        #   collect until reserved ';',',',')'
        #       Error on any keywords
        ((TAG_RESERVED, (RESERVED_SEMICOLON, RESERVED_COMMA, RESERVED_PAREN_CLOSE)), collect_drop, lambda t: _tag(t) == TAG_KEYWORD),
    ]

    _assign = [
        # Tag, subtag, must/can, error if true
        #   mandatory keyword assign
        ((TAG_KEYWORD, KEYWORD_ASSIGN), must, None),
        #   mandatory whitespace
        ((TAG_WHITESPACE, None), must, None),
        #   mandatory signal name
        ((TAG_GENERIC, None), must, None),
        #   optional whitespace
        ((TAG_WHITESPACE, None), can, None),
        #   mandatory reserved '='
        ((TAG_RESERVED, RESERVED_EQUAL), must, None),
        #   collect until reserved ';'
        #       Error on any keywords
        ((TAG_RESERVED, RESERVED_SEMICOLON), collect, lambda t: _tag(t) == TAG_KEYWORD),
    ]

    _assign_with_range = [
        # Tag, subtag, must/can, error if true
        #   mandatory keyword assign
        ((TAG_KEYWORD, KEYWORD_ASSIGN), must, None),
        #   mandatory whitespace
        ((TAG_WHITESPACE, None), must, None),
        #   mandatory signal name
        ((TAG_GENERIC, None), must, None),
        #   optional whitespace
        ((TAG_WHITESPACE, None), can, None),
        #   complete open reserved '[' with its mating close reserved ']'
        ((TAG_RESERVED, RESERVED_BRACKET_OPEN), complete, lambda t: _tag(t) != TAG_GENERIC),
        #   optional whitespace
        ((TAG_WHITESPACE, None), can, None),
        #   mandatory reserved '='
        ((TAG_RESERVED, RESERVED_EQUAL), must, None),
        #   collect until reserved ';'
        #       Error on any keywords
        ((TAG_RESERVED, RESERVED_SEMICOLON), collect, lambda t: _tag(t) == TAG_KEYWORD),
    ]

    # FIXME
    _paramdec = [
        # Tag, subtag, must/can, error if true
        #   mandatory keyword reg
        (TAG_KEYWORD, KEYWORD_PARAMETER, must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   mandatory signal name
        (TAG_GENERIC, None, must, None),
        #   collect until reserved ';',',',')'
        #       Error on any keywords
        (TAG_RESERVED, (RESERVED_SEMICOLON, RESERVED_COMMA, RESERVED_PAREN_CLOSE), collect_drop, lambda t: _tag(t) == TAG_KEYWORD),
        #   optional semicolon
        (TAG_RESERVED, RESERVED_SEMICOLON, can, None),
    ]

    # FIXME
    _paramdec_with_range = [
        # Tag, subtag, must/can, error if true
        #   mandatory keyword reg
        (TAG_KEYWORD, KEYWORD_PARAMETER, must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   complete open reserved '[' with its mating close reserved ']'
        (TAG_RESERVED, RESERVED_BRACKET_OPEN, complete, None),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   mandatory signal name
        (TAG_GENERIC, None, must, None),
        #   collect until reserved ';', ',', or ')'
        #       Error on any keywords
        (TAG_RESERVED, (RESERVED_SEMICOLON, RESERVED_COMMA, RESERVED_PAREN_CLOSE), collect_drop, lambda t: _tag(t) == TAG_KEYWORD),
        #   optional semicolon
        (TAG_RESERVED, RESERVED_SEMICOLON, can, None),
    ]

    # FIXME
    _moddec_open = [
        #   mandatory keyword module
        (TAG_KEYWORD, KEYWORD_MODULE, must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   mandatory module name
        (TAG_GENERIC, None, must, None),
    ]

    # FIXME
    _initial_open = [
        #   mandatory keyword initial
        (TAG_KEYWORD, KEYWORD_INITIAL, must, None),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   optional keyword begin
        (TAG_KEYWORD, KEYWORD_BEGIN, can, None),
    ]

    # FIXME
    # always @(posedge clk) begin
    _always_at_open = [
        #   mandatory keyword always
        (TAG_KEYWORD, KEYWORD_ALWAYS, must, None),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   mandatory reserved '@('
        (TAG_RESERVED, RESERVED_ATPAREN_OPEN, must, None),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   mandatory keyword always
        (TAG_KEYWORD, (KEYWORD_POSEDGE, KEYWORD_NEGEDGE), must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   mandatory clk name
        (TAG_GENERIC, None, must, None),
        #   mandatory reserved ')'
        (TAG_RESERVED, RESERVED_PAREN_CLOSE, must, None),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   optional keyword begin
        (TAG_KEYWORD, KEYWORD_BEGIN, can, None),
    ]

    # FIXME
    _always_delay_open = [
        #   mandatory keyword always
        (TAG_KEYWORD, KEYWORD_ALWAYS, must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   optional delay value
        (TAG_GENERIC, None, can, None),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   mandatory keyword begin
        (TAG_KEYWORD, KEYWORD_BEGIN, must, None),
    ]

    # FIXME
    _if_open = [
        #   mandatory keyword if
        (TAG_KEYWORD, KEYWORD_IF, must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   complete from ( to )
        (TAG_RESERVED, RESERVED_PAREN_OPEN, complete, None),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   optional keyword begin
        (TAG_KEYWORD, KEYWORD_BEGIN, can, None),
    ]

    # FIXME
    _for_open = [
        #   mandatory keyword if
        (TAG_KEYWORD, KEYWORD_FOR, must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   complete from ( to )
        (TAG_RESERVED, RESERVED_PAREN_OPEN, complete, None),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   optional keyword begin
        (TAG_KEYWORD, KEYWORD_BEGIN, can, None),
    ]

    # FIXME
    _sync_assign = [
        #   mandatory signal value
        (TAG_GENERIC, None, must, None),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   mandatory reserved '=' or '<='
        (TAG_RESERVED, (RESERVED_EQUAL, RESERVED_EQUAL_DELAYED), must, None),
        #   collect until reserved ';'
        (TAG_RESERVED, RESERVED_SEMICOLON, collect, None),
    ]

    # FIXME
    _sync_assign_with_range = [
        #   mandatory signal value
        (TAG_GENERIC, None, must, None),
        #   complete from [ to ]
        (TAG_RESERVED, RESERVED_BRACKET_OPEN, complete, None),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   mandatory reserved '=' or '<='
        (TAG_RESERVED, (RESERVED_EQUAL, RESERVED_EQUAL_DELAYED), must, None),
        #   collect until reserved ';'
        (TAG_RESERVED, RESERVED_SEMICOLON, collect, None),
    ]

    @classmethod
    def _dec(cls, keyword):
        _structdef = [
            # Tag, subtag, must/can, error if true
            #   mandatory keyword reg
            ((TAG_KEYWORD, keyword), cls.must, None),
            #   mandatory whitespace
            ((TAG_WHITESPACE, None), cls.must, None),
            #   mandatory signal name
            ((TAG_GENERIC, None), cls.must, None),
            #   collect until reserved ';'
            #       Error on any keywords
            ((TAG_RESERVED, RESERVED_SEMICOLON), cls.collect, lambda t: _tag(t) == TAG_KEYWORD),
        ]
        return _structdef

    @classmethod
    def _dec_with_range(cls, keyword):
        _structdef = [
            # Tag, subtag, must/can, error if true
            #   mandatory keyword
            ((TAG_KEYWORD, keyword), cls.must, None),
            #   mandatory whitespace
            ((TAG_WHITESPACE, None), cls.must, None),
            #   complete open reserved '[' with its mating close reserved ']'
            ((TAG_RESERVED, RESERVED_BRACKET_OPEN), cls.complete, lambda t: _tag(t) != TAG_GENERIC),
            #   optional whitespace
            ((TAG_WHITESPACE, None), cls.can, None),
            #   mandatory signal name
            ((TAG_GENERIC, None), cls.must, None),
            #   collect until reserved ';'
            #       Error on any keywords
            ((TAG_RESERVED, RESERVED_SEMICOLON), cls.collect, lambda t: _tag(t) == TAG_KEYWORD),
        ]
        return _structdef

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setParsersLayer1Pass0(self):
        self.structparsers = []

        tag = (TAG_STATEMENT, TAG_REGDECS)
        self._regdec = self._dec(KEYWORD_REG)
        self.structparsers.append(StructParser("regdec", self._regdec, tag=tag))
        self._regdec_with_range = self._dec_with_range(KEYWORD_REG)
        self.structparsers.append(StructParser("regdec_with_range", self._regdec_with_range, tag=tag))

        tag = (TAG_STATEMENT, TAG_WIREDECS)
        self._wiredec = self._dec(KEYWORD_WIRE)
        self.structparsers.append(StructParser("wiredec", self._wiredec, tag=tag))
        self._wiredec_with_range = self._dec_with_range(KEYWORD_WIRE)
        self.structparsers.append(StructParser("wiredec_with_range", self._wiredec_with_range, tag=tag))

        tag = (TAG_STATEMENT, TAG_ASSIGNS)
        self.structparsers.append(StructParser("assigns", self._assign, tag=tag))
        self.structparsers.append(StructParser("assigns_with_range", self._assign_with_range, tag=tag))

        tag = (TAG_ATTRIBUTE, None)
        self.structparsers.append(StructParser("attribute", self._attribute, tag=tag, verbose=False))

        tag = (TAG_STATEMENT, TAG_PORTS)
        self.structparsers.append(StructParser("port", self._port, tag=tag))
        self.structparsers.append(StructParser("port_with_range", self._port_with_range, tag=tag))

        # FIXME
        return

        tag = (TAG_STATEMENT, TAG_PARAMETERS)
        self.structparsers.append(StructParser("paramdec", self._paramdec, tag=tag))
        self.structparsers.append(StructParser("paramdec_with_range", self._paramdec_with_range, tag=tag, verbose=True))

        tag = (TAG_STATEMENT, TAG_LOCALPARAMS)
        self._localparamdec = self._dec(KEYWORD_LOCALPARAM)
        self.structparsers.append(StructParser("localparamdec", self._localparamdec, tag=tag))
        self._localparamdec_with_range = self._dec_with_range(KEYWORD_LOCALPARAM)
        self.structparsers.append(StructParser("localparamdec_with_range", self._localparamdec_with_range, tag=tag))

        tag = (TAG_BLOCK, TAG_MODDEC)
        self.structparsers.append(StructParser("moddec_open", self._moddec_open, tag=tag, verbose=False))

        tag = (TAG_BLOCK, TAG_INITIAL)
        self.structparsers.append(StructParser("initial_open", self._initial_open, tag=tag, verbose=False))

        tag = (TAG_BLOCK, TAG_ALWAYS)
        self.structparsers.append(StructParser("always_at_open", self._always_at_open, tag=tag, verbose=False))
        self.structparsers.append(StructParser("always_delay_open", self._always_delay_open, tag=tag, verbose=False))

        tag = (TAG_BLOCK, TAG_IF)
        self.structparsers.append(StructParser("if_open", self._if_open, tag=tag, verbose=False))

        tag = (TAG_BLOCK, TAG_FOR)
        self.structparsers.append(StructParser("for_open", self._for_open, tag=tag, verbose=False))

        #self._verboseParsers = ["attribute"]

    def setParsersLayer1Pass1(self):
        self.structparsers = []
        # FIXME
        return

        tag = (TAG_STATEMENT, TAG_ASSIGN_SYNC)
        self.structparsers.append(StructParser("sync_assign", self._sync_assign, tag=tag, verbose=False))
        self.structparsers.append(StructParser("sync_assign_with_range", self._sync_assign_with_range, tag=tag, verbose=False))

    def parseLayer1(self, verbose=False):
        self.parseLayer1Pass(0, verbose=verbose)
        self.parseLayer1Pass(1, verbose=verbose)

    def parseLayer1Pass(self, npass=0, verbose=False):
        if npass == 0:
            self.cs.copyPerspective("keywords", "layer1")
            self.cs.setActivePerspective("keywords")
            self.setParsersLayer1Pass0()
        elif npass == 1:
            self.cs.setActivePerspective("layer1")
            self.setParsersLayer1Pass1()
        structdict = self.parseStructure()
        self.cs.setActivePerspective("layer1")
        for name, (tag, structs) in structdict.items():
            if verbose and (len(structs) == 0):
                print(f"{name} yielded no structs")
            for struct in structs:
                if len(struct) == 0:
                    continue
                #for token in struct:
                #    print(token.value, end="")
                #print()
                start = struct[0].start
                stop = struct[-1].stop
                if verbose:
                    sline, schar = self.cs.charToLineChar(start)
                    pline, pchar = self.cs.charToLineChar(stop)
                    print(f"Tagging line {sline}[{schar}] to line {pline}[{pchar}] with {_tagstr(tag)}")
                self.cs.tag(slice(start, stop), tag)
        return

    def printLayer1(self):
        self.cs.setActivePerspective("layer1")
        _colormap = {
            MultiTag(TAG_COMMENT): Perspective.COLOR_LIGHTCYAN_EX,
            MultiTag(TAG_STATEMENT): Perspective.COLOR_LIGHTCYAN_EX,
            MultiTag(TAG_ATTRIBUTE): Perspective.COLOR_GREEN,
            MultiTag(TAG_BLOCK): Perspective.COLOR_MAGENTA,
            MultiTag(TAG_MACRO): Perspective.COLOR_YELLOW,
            MultiTag(TAG_KEYWORD): Perspective.COLOR_LIGHTGREEN_EX,
            MultiTag(TAG_STRING): Perspective.COLOR_RED,
            MultiTag(TAG_RESERVED): Perspective.COLOR_BLUE,
        }
        self.cs.setColorMap(_colormap)
        self.cs.printColor()
        return

    def printLayer0(self):
        self.cs.setActivePerspective("keywords")
        _colormap = {
            MultiTag(TAG_COMMENT): Perspective.COLOR_LIGHTCYAN_EX,
            MultiTag(TAG_STRING): Perspective.COLOR_RED,
            MultiTag(TAG_MACRO): Perspective.COLOR_YELLOW,
            MultiTag(TAG_KEYWORD): Perspective.COLOR_GREEN,
            MultiTag(TAG_RESERVED): Perspective.COLOR_BLUE,
        }
        self.cs.setColorMap(_colormap)
        self.cs.printColor()
        return

def test_GrouperParseAssign():
    goods = [
        "assign foo=bar;",
        "assign foo = bar;",
        "assign foo[3:0] = bar[7:4];",
        "assign my_signal= {4{1'b0},baz};",
    ]
    gp = VerilogGrouper(reserved=reserved, keywords=keywords, macros=macros)
    for s in goods:
        print("PARSING: {}".format(s))
        gp.tokenize(s)
        assigns = gp.parseAssigns()
        if len(assigns) > 0:
            gp.printStructs(assigns, "Assigns")
        else:
            assigns = gp.parseAssignsWithRange()
            gp.printStructs(assigns, "Assigns")
    return

def parseFile():
    import argparse
    parser = argparse.ArgumentParser(description="Hand-rolled Verilog parser")
    parser.set_defaults(handler=lambda args: parser.print_help())
    parser.add_argument('filename', default=None, help="The Verilog file to parse.")
    args = parser.parse_args()
    instr = None
    with open(args.filename, 'r') as fd:
        instr = fd.read()
    if instr is None:
        print("Failed to parse {}".format(args.filename))
        return
    tagmap = TagMap(
        comments=TAG_COMMENT,
        macros=TAG_MACRO,
        strings=TAG_STRING,
        whitespace=TAG_WHITESPACE,
        reserved=TAG_RESERVED,
        keywords=TAG_KEYWORD
    )
    gp = VerilogGrouper(reserved=_reserved_sorted, keywords=keywords, macros=macros,
                        tagmap=tagmap, group_pairs=_grouping_pairs)
    gp.tokenize(instr)
    #gp.printStructDict(structdict)
    gp.parseLayer1(verbose=False)
    #gp.printLayer0()
    gp.printLayer1()
    return

if __name__ == "__main__":
    parseFile()
