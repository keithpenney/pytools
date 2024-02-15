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
from constr import ConStr, Perspective, _tag, _subtag

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
    "RESERVED_SEMICOLON",
    "RESERVED_COLON",

    "MACRO_DEFINE",
    "MACRO_IFDEF",
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

    "TAG_ASSIGNS",
    "TAG_WIREDECS",
    "TAG_REGDECS",
    "TAG_PARAMETERS",
    "TAG_LOCALPARAMS",
    "TAG_PORTS",
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

_grouping_pairs = {
    RESERVED_PAREN_OPEN: RESERVED_PAREN_CLOSE,
    RESERVED_BRACE_OPEN: RESERVED_BRACE_CLOSE,
    RESERVED_BRACKET_OPEN: RESERVED_BRACKET_CLOSE,
}

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
}

# Reserved characters always have syntactic meaning (unless in a string or comment)
reserved = {
    # (char pattern, escaped char pattern)
    RESERVED_EQUAL_DELAYED: ("<=", "\<\="),
    RESERVED_EQUAL: ("=", "\="),
    RESERVED_PLUS: ("+", "\+"),
    RESERVED_MINUS: ("-", "\-"),
    RESERVED_MUL: ("*", "\*"),
    RESERVED_DIV: ("/", "\/"),
    RESERVED_POUNDPAREN_OPEN: ("#(", "#\("),
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

macros = {
    MACRO_DEFINE: "`define",
    MACRO_IFDEF: "`ifdef",
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

    _port = [
        #   mandatory keyword input/output/inout
        (TAG_KEYWORD, (KEYWORD_INPUT, KEYWORD_OUTPUT, KEYWORD_INOUT), must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   mandatory signal name
        (TAG_GENERIC, None, must, None),
        #   collect until reserved ';',',',')'
        #       Error on any keywords
        (TAG_RESERVED, (RESERVED_SEMICOLON, RESERVED_COMMA, RESERVED_PAREN_CLOSE), collect_drop, lambda t: _tag(t) == TAG_KEYWORD),
    ]

    _port_with_range = [
        #   mandatory keyword input/output/inout
        (TAG_KEYWORD, (KEYWORD_INPUT, KEYWORD_OUTPUT, KEYWORD_INOUT), must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   complete open reserved '[' with its mating close reserved ']'
        (TAG_RESERVED, RESERVED_BRACKET_OPEN, complete, lambda t: _tag(t) != TAG_GENERIC),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   mandatory signal name
        (TAG_GENERIC, None, must, None),
        #   collect until reserved ';',',',')'
        #       Error on any keywords
        (TAG_RESERVED, (RESERVED_SEMICOLON, RESERVED_COMMA, RESERVED_PAREN_CLOSE), collect_drop, lambda t: _tag(t) == TAG_KEYWORD),
    ]

    _assign = [
        # Tag, subtag, must/can, error if true
        #   mandatory keyword assign
        (TAG_KEYWORD, KEYWORD_ASSIGN, must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   mandatory signal name
        (TAG_GENERIC, None, must, None),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   mandatory reserved '='
        (TAG_RESERVED, RESERVED_EQUAL, must, None),
        #   collect until reserved ';'
        #       Error on any keywords
        (TAG_RESERVED, RESERVED_SEMICOLON, collect, lambda t: _tag(t) == TAG_KEYWORD),
    ]

    _assign_with_range = [
        # Tag, subtag, must/can, error if true
        #   mandatory keyword assign
        (TAG_KEYWORD, KEYWORD_ASSIGN, must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   mandatory signal name
        (TAG_GENERIC, None, must, None),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   complete open reserved '[' with its mating close reserved ']'
        (TAG_RESERVED, RESERVED_BRACKET_OPEN, complete, lambda t: _tag(t) != TAG_GENERIC),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   mandatory reserved '='
        (TAG_RESERVED, RESERVED_EQUAL, must, None),
        #   collect until reserved ';'
        #       Error on any keywords
        (TAG_RESERVED, RESERVED_SEMICOLON, collect, lambda t: _tag(t) == TAG_KEYWORD),
    ]

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

    _paramdec_with_range = [
        # Tag, subtag, must/can, error if true
        #   mandatory keyword reg
        (TAG_KEYWORD, KEYWORD_PARAMETER, must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   complete open reserved '[' with its mating close reserved ']'
        (TAG_RESERVED, RESERVED_BRACKET_OPEN, complete, lambda t: _tag(t) != TAG_GENERIC),
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

    @classmethod
    def _dec(cls, keyword):
        _structdef = [
            # Tag, subtag, must/can, error if true
            #   mandatory keyword reg
            (TAG_KEYWORD, keyword, cls.must, None),
            #   mandatory whitespace
            (TAG_WHITESPACE, None, cls.must, None),
            #   mandatory signal name
            (TAG_GENERIC, None, cls.must, None),
            #   collect until reserved ';'
            #       Error on any keywords
            (TAG_RESERVED, RESERVED_SEMICOLON, cls.collect, lambda t: _tag(t) == TAG_KEYWORD),
        ]
        return _structdef

    @classmethod
    def _dec_with_range(cls, keyword):
        _structdef = [
            # Tag, subtag, must/can, error if true
            #   mandatory keyword
            (TAG_KEYWORD, keyword, cls.must, None),
            #   mandatory whitespace
            (TAG_WHITESPACE, None, cls.must, None),
            #   complete open reserved '[' with its mating close reserved ']'
            (TAG_RESERVED, RESERVED_BRACKET_OPEN, cls.complete, lambda t: _tag(t) != TAG_GENERIC),
            #   optional whitespace
            (TAG_WHITESPACE, None, cls.can, None),
            #   mandatory signal name
            (TAG_GENERIC, None, cls.must, None),
            #   collect until reserved ';'
            #       Error on any keywords
            (TAG_RESERVED, RESERVED_SEMICOLON, cls.collect, lambda t: _tag(t) == TAG_KEYWORD),
        ]
        return _structdef

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addParsers()

    def addParsers(self):
        tag = (TAG_STATEMENT, TAG_REGDECS)
        self._regdec = self._dec(KEYWORD_REG)
        self.structparsers.append(StructParser("regdecs", self._regdec, tag=tag))
        self._regdec_with_range = self._dec_with_range(KEYWORD_REG)
        self.structparsers.append(StructParser("regdecs_with_range", self._regdec_with_range, tag=tag))

        tag = (TAG_STATEMENT, TAG_WIREDECS)
        self._wiredec = self._dec(KEYWORD_WIRE)
        self.structparsers.append(StructParser("wiredecs", self._wiredec, tag=tag))
        self._wiredec_with_range = self._dec_with_range(KEYWORD_WIRE)
        self.structparsers.append(StructParser("wiredecs_with_range", self._wiredec_with_range, tag=tag))

        tag = (TAG_STATEMENT, TAG_ASSIGNS)
        self.structparsers.append(StructParser("assigns", self._assign, tag=tag))
        self.structparsers.append(StructParser("assigns_with_range", self._assign_with_range, tag=tag))

        tag = (TAG_STATEMENT, TAG_PARAMETERS)
        self.structparsers.append(StructParser("paramdec", self._paramdec, tag=tag))
        self.structparsers.append(StructParser("paramdec_with_range", self._paramdec_with_range, tag=tag))

        tag = (TAG_STATEMENT, TAG_LOCALPARAMS)
        self._localparamdec = self._dec(KEYWORD_LOCALPARAM)
        self.structparsers.append(StructParser("localparamdec", self._localparamdec, tag=tag))
        self._localparamdec_with_range = self._dec_with_range(KEYWORD_LOCALPARAM)
        self.structparsers.append(StructParser("localparamdec_with_range", self._localparamdec_with_range, tag=tag))

        tag = (TAG_STATEMENT, TAG_PORTS)
        self.structparsers.append(StructParser("port", self._port, tag=tag))
        self.structparsers.append(StructParser("port_with_range", self._port_with_range, tag=tag))
        #self._verboseParsers = ["paramdec"]

    def parseLayer1(self, verbose=False):
        structdict = self.parseStructure()
        self.cs.copyPerspective("comments", "layer1")
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
        self.cs.setActivePerspective("layer1")
        return

    def printLayer1(self):
        self.cs.setActivePerspective("layer1")
        _colormap = {
            TAG_COMMENT: Perspective.COLOR_LIGHTCYAN_EX,
            TAG_STATEMENT: Perspective.COLOR_RED,
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
    gp = VerilogGrouper(reserved=reserved, keywords=keywords, macros=macros, tagmap=tagmap)
    gp.tokenize(instr)
    structdict = gp.parseStructure()
    #gp.printStructDict(structdict)
    gp.parseLayer1(verbose=False)
    gp.printLayer1()
    return

if __name__ == "__main__":
    parseFile()
