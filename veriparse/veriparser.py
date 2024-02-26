# TODO:
#   CHECK * Add Grouper option for collecting from an opening grouping symbol (i.e. '[') to its mating closing grouping symbol (i.e. ']')
#   CHECK * Create a new Perspective at the level of a "structure" where each entry will be one of: TAG_STATEMENT, TAG_BLOCK, TAG_MODULEDECLARATION
#       Start with "comments" Perspective and tag based on the limits of the structResults
#   * Add handling of:
#       * System calls/tasks
#       * attributes (* foo=bar *)
#
# TODO - I need a fancier version of "complete" to match blocks starting with "begin" and ending with "end"

# Hierarchical Perspectives:
#   Level 0: comments, whitespace, strings, keywords, reserved chars, macros, generic
#   Level 1: statements, blockopen/blockclose, module instantiation headers, param lists, port lists,
#            module declaration headers, parammaps, portmaps, generate-for, generate-if
#   Level 2: statements, module declarations, module instantiations, always/initial blocks

from parser import Grouper, TagMap, StructParser, StructDef
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
    "RESERVED_PERIOD",
    "RESERVED_PAREN_OPEN",
    "RESERVED_PAREN_CLOSE",
    "RESERVED_BRACE_OPEN",
    "RESERVED_BRACE_CLOSE",
    "RESERVED_BRACKET_OPEN",
    "RESERVED_BRACKET_CLOSE",
    "RESERVED_COMMA",
    "RESERVED_POUND",
#    "RESERVED_POUNDPAREN_OPEN",
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
    "TAG_BLOCK_OPEN",
    "TAG_BLOCK",
    "TAG_MODULEDECLARATION",
    "TAG_ATTRIBUTE",
    "TAG_FIXED_DELAY",

    "TAG_ASSIGNS",
    "TAG_ASSIGN_SYNC",
    "TAG_WIREDECS",
    "TAG_REGDECS",
    "TAG_PARAMETERS",
    "TAG_LOCALPARAMS",
    "TAG_PORTMAP",
    "TAG_PORTS",
    "TAG_MODDEC",
    "TAG_MODINST",
#    "TAG_MODINST_OPEN",
    "TAG_SEQUENTIAL",
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
        if len(tag) == 2:
            tag, subtag = tag
            if tag is None:
                stag = "None"
            elif isinstance(tag, int):
                stag = __tags__[tag-__tag_offset]
            else:
                stag = str(tag)
            if subtag is None:
                ssubtag = "None"
            elif isinstance(subtag, int):
                ssubtag = __tags__[subtag-__tag_offset]
            else:
                ssubtag = str(subtag)
            return "({}, {})".format(stag, ssubtag)
        else:
            return "{}".format(tag)
    else:
        if tag is None:
            return "None"
        return __tags__[tag-__tag_offset]

import parser
parser._tagstr = _tagstr
import constr
constr._tagstr = _tagstr

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
    RESERVED_PERIOD: (".", "\."),
    RESERVED_PARENSTAR_OPEN: ("(*", "\(\*"),
    RESERVED_PARENSTAR_CLOSE: ("*)", "\*\)"),
    RESERVED_POUND: ("#", "#"),
#    RESERVED_POUNDPAREN_OPEN: ("#(", "#\("),
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


# TODO FIXME! The poundparen "complete" is not working because it expects "#(" to increase the group level and ")" to decrease it,
#               so it ignores "(" in the meantime
_grouping_pairs = {
    '[': ']',
    '(': ')',
    '#(': ')', # FIXME!
    '{': '}',
    '(*': '*)'
}

_keyword_grouping_pairs = {
    "begin" : "end",
}

def _get_closer_tag(tag, keyword=False):
    """Clobber me (for customization)"""
    if keyword:
        grouper = _keyword_grouping_pairs
        dct = keywords
    else:
        grouper = _grouping_pairs
        dct = reserved
    ct = []
    closer = False
    for t in tag:
        rg = dct.get(t)
        if rg is not None:
            if keyword:
                char = rg
            else:
                char, enc = rg
            _closerChar = grouper.get(char, None)
            _closerTag = None
            for _t, _chars in dct.items():
                if keyword:
                    _char = _chars
                else:
                    _char = _chars[0]
                if _closerChar == _char:
                    _closerTag = _t
                    break
            if _closerTag is not None:
                closer = True
                ct.append(_closerTag)
            else:
                ct.append(t)
        else:
            ct.append(t)
    if closer:
        return MultiTag(*ct)
    return None

def get_closer_tag(tag):
    rval = _get_closer_tag(tag, keyword=False)
    if rval is not None:
        return rval
    return _get_closer_tag(tag, keyword=True)

# TODO FIXME HACK ALERT. There has got to be a better way to associate opener/closer tags
parser.get_closer_tag = get_closer_tag

class VerilogGrouper(Grouper):
    can = StructParser.can
    can_drop = StructParser.can_drop
    must = StructParser.must
    must_drop = StructParser.must_drop
    collect = StructParser.collect
    collect_drop = StructParser.collect_drop
    complete = StructParser.complete

    _range = StructDef((
        #   complete open reserved '[' with its mating close reserved ']'
        ((TAG_RESERVED, RESERVED_BRACKET_OPEN), complete, None),
    ))

    _param_block = StructDef((
        #   mandatory reserved '#'
        ((TAG_RESERVED, RESERVED_POUND), must, None),
        #   complete open reserved '(' with its mating close reserved ')'
        ((TAG_RESERVED, RESERVED_PAREN_OPEN), complete, None),
    ))

    _attribute = (
        #   collect from (* to *)
        ((TAG_RESERVED, RESERVED_PARENSTAR_OPEN), complete, None),
    )

    _port = (
        #   mandatory keyword input/output/inout
        ((TAG_KEYWORD, (KEYWORD_INPUT, KEYWORD_OUTPUT, KEYWORD_INOUT)), must, None),
        #   optional range
        (_range.copy(), can, None),
        #   mandatory signal name
        ((TAG_GENERIC, None), must, None),
        #   collect until reserved ';',',',')'
        #       Error on any keywords
        ((TAG_RESERVED, (RESERVED_SEMICOLON, RESERVED_COMMA, RESERVED_PAREN_CLOSE)), collect_drop, lambda t: _tag(t) == TAG_KEYWORD),
    )

    _assign = (
        # Tag, subtag, must/can, error if true
        #   mandatory keyword assign
        ((TAG_KEYWORD, KEYWORD_ASSIGN), must, None),
        #   mandatory signal name
        ((TAG_GENERIC, None), must, None),
        #   optional range
        (_range.copy(), can, None),
        #   mandatory reserved '='
        ((TAG_RESERVED, RESERVED_EQUAL), must, None),
        #   collect until reserved ';'
        #       Error on any keywords
        ((TAG_RESERVED, RESERVED_SEMICOLON), collect, lambda t: _tag(t) == TAG_KEYWORD),
    )

    _paramdec = (
        # Tag, subtag, must/can, error if true
        #   mandatory keyword reg
        ((TAG_KEYWORD, KEYWORD_PARAMETER), must, None),
        #   optional range
        (_range.copy(), can, None),
        #   mandatory signal name
        ((TAG_GENERIC, None), must, None),
        #   collect until reserved ';',',',')'
        #       Error on any keywords
        ((TAG_RESERVED, (RESERVED_SEMICOLON, RESERVED_COMMA, RESERVED_PAREN_CLOSE)), collect_drop, lambda t: _tag(t) == TAG_KEYWORD),
        #   optional semicolon
        ((TAG_RESERVED, RESERVED_SEMICOLON), can, None),
    )

    _moddec_open = (
        #   mandatory keyword module
        ((TAG_KEYWORD, KEYWORD_MODULE), must, None),
        #   mandatory module name
        ((TAG_GENERIC, None), must, None),
    )

    _initial_open = (
        #   mandatory keyword initial
        ((TAG_KEYWORD, KEYWORD_INITIAL), must, None),
        #   optional keyword begin
        ((TAG_KEYWORD, KEYWORD_BEGIN), can_drop, None),
    )

    # always @(posedge clk) begin
    _always_at_open = (
        #   mandatory keyword always
        ((TAG_KEYWORD, KEYWORD_ALWAYS), must, None),
        #   mandatory reserved '@('
        ((TAG_RESERVED, RESERVED_ATPAREN_OPEN), must, None),
        #   mandatory keyword always
        ((TAG_KEYWORD, (KEYWORD_POSEDGE, KEYWORD_NEGEDGE)), must, None),
        #   mandatory clk name
        ((TAG_GENERIC, None), must, None),
        #   mandatory reserved ')'
        ((TAG_RESERVED, RESERVED_PAREN_CLOSE), must, None),
        #   optional keyword begin
        ((TAG_KEYWORD, KEYWORD_BEGIN), can_drop, None),
    )

    _delay_value = (
        #   mandatory reserved '#'
        ((TAG_RESERVED, RESERVED_POUND), must, None),
        #   mandatory delay value
        ((TAG_GENERIC, None), must, None),
    )

    _if_open = (
        #   mandatory keyword if
        ((TAG_KEYWORD, KEYWORD_IF), must, None),
        #   complete from ( to )
        ((TAG_RESERVED, RESERVED_PAREN_OPEN), complete, None),
        #   optional keyword begin
        ((TAG_KEYWORD, KEYWORD_BEGIN), can_drop, None),
    )

    _for_open = (
        #   mandatory keyword if
        ((TAG_KEYWORD, KEYWORD_FOR), must, None),
        #   complete from ( to )
        ((TAG_RESERVED, RESERVED_PAREN_OPEN), complete, None),
        #   optional keyword begin
        ((TAG_KEYWORD, KEYWORD_BEGIN), can_drop, None),
    )

    _portmap = (
        #   mandatory reserved '.'
        ((TAG_RESERVED, RESERVED_PERIOD), must, None),
        #   mandatory port name
        ((TAG_GENERIC, None), must, None),
        #   complete from ( to )
        ((TAG_RESERVED, RESERVED_PAREN_OPEN), complete, None),
        #   mandatory reserved ',' or ')' but drop it
        ((TAG_RESERVED, (RESERVED_COMMA, RESERVED_PAREN_CLOSE)), must_drop, None),
    )

    # ============= LAYER 1 ===================

    _always_delay_open = (
        #   mandatory keyword always
        ((TAG_KEYWORD, KEYWORD_ALWAYS), must, None),
        #   optional delay value
        ((TAG_FIXED_DELAY, None), must, None),
        #   optional keyword begin
        ((TAG_KEYWORD, KEYWORD_BEGIN), can_drop, None),
    )

    _always_open = (
        #   mandatory keyword always
        ((TAG_KEYWORD, KEYWORD_ALWAYS), must, None),
        #   mandatory keyword begin
        ((TAG_KEYWORD, KEYWORD_BEGIN), must_drop, None),
    )

    _sync_assign = (
        #   mandatory signal value
        ((TAG_GENERIC, None), must, None),
        #   optional range
        (_range.copy(), can, None),
        #   mandatory reserved '=' or '<='
        ((TAG_RESERVED, (RESERVED_EQUAL, RESERVED_EQUAL_DELAYED)), must, None),
        #   collect until reserved ';'
        ((TAG_RESERVED, RESERVED_SEMICOLON), collect, None),
    )

    # This doesn't help
    #_modinst_open = (
    #    #   mandatory module name
    #    ((TAG_GENERIC, None), must, None),
    #    #   mandatory reserved '(' or '#(' but drop it
    #    ((TAG_RESERVED, (RESERVED_PAREN_OPEN, RESERVED_POUND)), must_drop, None),
    #)

    # ============= LAYER 2 ===================
    # TODO - I need a "repeat" function
    _modinst = (
        #   mandatory module instantiation opening line
        #((TAG_BLOCK, TAG_MODINST_OPEN), must, None),
        #   mandatory module name
        ((TAG_GENERIC, None), must, None),
        #   optional parameter block
        (_param_block.copy(), can, None),
        #((TAG_RESERVED, RESERVED_POUNDPAREN_OPEN), complete, None),
        #   mandatory instance name
        #((TAG_BLOCK, TAG_MODINST_OPEN), must, None),
        ((TAG_GENERIC, None), must, None),
        #   complete open reserved '(' with its mating close reserved ')'
        ((TAG_RESERVED, RESERVED_PAREN_OPEN), complete, None),
    )

    _top_block = (
        #   mandatory block opening of any kind
        ((TAG_BLOCK_OPEN, None), must, None),
        #   complete from "begin" to matching "end"
        ((TAG_KEYWORD, KEYWORD_BEGIN), complete, None),
    )

    @classmethod
    def _dec(cls, keyword):
        _structdef = [
            # Tag, subtag, must/can, error if true
            #   mandatory keyword reg
            ((TAG_KEYWORD, keyword), cls.must, None),
            #   optional range
            (cls._range.copy(), cls.can, None),
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
        def add(s, struct, verbose=False, tag=tag):
            self.structparsers.append(StructParser(s, struct, tag=tag, verbose=verbose))

        self._regdec = self._dec(KEYWORD_REG)
        self._wiredec = self._dec(KEYWORD_WIRE)
        self._localparamdec = self._dec(KEYWORD_LOCALPARAM)
        add("regdec",           self._regdec,           tag=(TAG_STATEMENT, TAG_REGDECS))
        add("wiredec",          self._wiredec,          tag=(TAG_STATEMENT, TAG_WIREDECS))
        add("attribute",        self._attribute,        tag=(TAG_ATTRIBUTE, None))
        add("delay_value",      self._delay_value,      tag=(TAG_FIXED_DELAY, None))
        add("assign",           self._assign,           tag=(TAG_STATEMENT, TAG_ASSIGNS), verbose=False)
        add("port",             self._port,             tag=(TAG_STATEMENT, TAG_PORTS), verbose=False)
        add("paramdec",         self._paramdec,         tag=(TAG_STATEMENT, TAG_PARAMETERS))
        add("localparamdec",    self._localparamdec,    tag=(TAG_STATEMENT, TAG_LOCALPARAMS), verbose=False)
        add("initial_open",     self._initial_open,     tag=(TAG_BLOCK_OPEN, TAG_INITIAL))
        add("always_at_open",   self._always_at_open,   tag=(TAG_BLOCK_OPEN, TAG_ALWAYS))
        add("if_open",          self._if_open,          tag=(TAG_BLOCK_OPEN, TAG_IF))
        add("for_open",         self._for_open,         tag=(TAG_BLOCK_OPEN, TAG_FOR))
        add("portmap",          self._portmap,          tag=(TAG_STATEMENT, TAG_PORTMAP))
        #add("moddec_open",      self._moddec_open,      tag=(TAG_BLOCK, TAG_MODDEC))

        #self._verboseParsers = ["assign", "port"]
        return

    def setParsersLayer1Pass1(self):
        self.structparsers = []
        def add(s, struct, verbose=False, tag=tag):
            self.structparsers.append(StructParser(s, struct, tag=tag, verbose=verbose))

        add("sync_assign", self._sync_assign, tag=(TAG_STATEMENT, TAG_ASSIGN_SYNC), verbose=False)
        add("always_delay_open",self._always_delay_open,tag=(TAG_BLOCK_OPEN, TAG_ALWAYS))
        add("always_open",self._always_open,tag=(TAG_BLOCK_OPEN, TAG_ALWAYS))
        #add("modinst_open", self._modinst_open, tag=(TAG_BLOCK, TAG_MODINST_OPEN), verbose=True)

        #self._verboseParsers = []
        return

    def parseLayer1(self, verbose=False):
        sd = self.parseLayer1Pass(0, verbose=verbose)
        sd.update(self.parseLayer1Pass(1, verbose=verbose))
        self.structLayer1 = sd
        return

    def parseLayer1Pass(self, npass=0, verbose=False):
        skipTags = (
            MultiTag(TAG_COMMENT),
            MultiTag(TAG_WHITESPACE),
        )
        if npass == 0:
            self.cs.copyPerspective("keywords", "layer1")
            self.cs.setActivePerspective("keywords")
            self.setParsersLayer1Pass0()
        elif npass == 1:
            self.cs.setActivePerspective("layer1")
            self.setParsersLayer1Pass1()
        structdict = self.parseStructure(skipTags=skipTags)
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
        return structdict

    def parseLayer2(self, verbose=False):
        self.structparsers = []
        tag=None
        def add(s, struct, verbose=False, tag=tag):
            self.structparsers.append(StructParser(s, struct, tag=tag, verbose=verbose))

        add("modinst", self._modinst, tag=(TAG_BLOCK, TAG_MODINST), verbose=False)
        add("top_block", self._top_block, tag=(TAG_BLOCK, TAG_SEQUENTIAL), verbose=True)

        skipTags = (
            MultiTag(TAG_COMMENT),
            MultiTag(TAG_WHITESPACE),
        )
        self.cs.copyPerspective("layer1", "layer2")
        structdict = self.parseStructure(skipTags=skipTags)
        self.cs.setActivePerspective("layer2")
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
        self.structLayer2 = structdict
        return

    def printLayer2(self):
        self.cs.setActivePerspective("layer2")
        _colormap = {
            MultiTag(TAG_COMMENT): Perspective.COLOR_LIGHTCYAN_EX,
            MultiTag(TAG_BLOCK, TAG_MODINST): Perspective.COLOR_RED,
            MultiTag(TAG_BLOCK, TAG_SEQUENTIAL): Perspective.COLOR_GREEN,
            MultiTag(TAG_MACRO): Perspective.COLOR_YELLOW,
            MultiTag(TAG_RESERVED): Perspective.COLOR_BLUE,
        }
        self.cs.setColorMap(_colormap)
        self.cs.printColor()
        return

    def printLayer1(self):
        self.cs.setActivePerspective("layer1")
        _colormap = {
            MultiTag(TAG_COMMENT): Perspective.COLOR_LIGHTCYAN_EX,
            MultiTag(TAG_FIXED_DELAY): Perspective.COLOR_YELLOW,
            MultiTag(TAG_STATEMENT): Perspective.COLOR_RED,
            MultiTag(TAG_ATTRIBUTE): Perspective.COLOR_GREEN,
            MultiTag(TAG_BLOCK_OPEN): Perspective.COLOR_MAGENTA,
            MultiTag(TAG_MACRO): Perspective.COLOR_YELLOW,
            MultiTag(TAG_KEYWORD): Perspective.COLOR_LIGHTGREEN_EX,
            MultiTag(TAG_STRING): Perspective.COLOR_BLUE,
            MultiTag(TAG_RESERVED): Perspective.COLOR_LIGHTMAGENTA_EX,
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

    def parse(self, vstr):
        self.tokenize(vstr)
        # This is helpful to clobber
        constr.charToLineChar = self.cs.charToLineChar
        #self.printStructDict(structdict)
        self.parseLayer1(verbose=False)
        self.parseLayer2(verbose=False)
        #self.printLayer0()
        #self.printLayer1()
        #self.printLayer2()
        return

def test_MultiTag():
    mt_keyword_reg = MultiTag(TAG_KEYWORD, keyword)
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
    gp = VerilogGrouper(reserved=_reserved_sorted, keywords=keywords, macros=macros, tagmap=tagmap)
    gp.parse(instr)
    print("\n==================== LAYER 0 =====================")
    gp.printLayer0()
    print("\n==================== LAYER 1 =====================")
    gp.printLayer1()
    print("\n==================== LAYER 2 =====================")
    gp.printLayer2()
    return

if __name__ == "__main__":
    parseFile()
