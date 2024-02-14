#! python3

# A just-for-fun test of a generic parsing concept

import re
from constr import ConStr, Perspective

# TODO:
#   CHECK * Add Grouper option for collecting from an opening grouping symbol (i.e. '[') to its mating closing grouping symbol (i.e. ']')
#   * Create a new Perspective at the level of a "structure" where each entry will be one of: TAG_STATEMENT, TAG_BLOCK, TAG_MODULEDECLARATION
#       Start with "comments" Perspective and tag based on the limits of the structResults

KEYWORD_MODULE = 0
KEYWORD_WIRE = 1
KEYWORD_REG = 2
KEYWORD_LOGIC = 3
KEYWORD_BEGIN = 4
KEYWORD_ALWAYS = 5
KEYWORD_INITIAL = 6
KEYWORD_IF = 7
KEYWORD_ELSE = 8
KEYWORD_INPUT = 9
KEYWORD_OUTPUT = 10
KEYWORD_INOUT = 11
KEYWORD_PARAMETER = 12
KEYWORD_LOCALPARAM = 13
KEYWORD_FOR = 14
KEYWORD_END = 15
KEYWORD_ASSIGN = 16
KEYWORD_ENDMODULE = 17

RESERVED_EQUAL_DELAYED = 1
RESERVED_EQUAL = 2
RESERVED_PLUS = 3
RESERVED_MINUS = 4
RESERVED_MUL = 5
RESERVED_DIV = 6
RESERVED_PAREN_OPEN = 7
RESERVED_PAREN_CLOSE = 8
RESERVED_BRACE_OPEN = 9
RESERVED_BRACE_CLOSE = 10
RESERVED_BRACKET_OPEN = 11
RESERVED_BRACKET_CLOSE = 12
RESERVED_COMMA = 13
RESERVED_POUNDPAREN_OPEN = 14
RESERVED_SEMICOLON = 15
RESERVED_COLON = 16

_grouping_pairs = {
    RESERVED_PAREN_OPEN: RESERVED_PAREN_CLOSE,
    RESERVED_BRACE_OPEN: RESERVED_BRACE_CLOSE,
    RESERVED_BRACKET_OPEN: RESERVED_BRACKET_CLOSE,
}

MACRO_DEFINE = 0
MACRO_IFDEF = 1
MACRO_ENDIF = 2

TAG_GENERIC = ConStr.TagGeneric
TAG_KEYWORD = 1
TAG_COMMENT = 2
TAG_STRING = 3
TAG_RESERVED = 4
TAG_WHITESPACE = 5
TAG_MACRO = 6

_colormap = {
    TAG_COMMENT: Perspective.COLOR_LIGHTCYAN_EX,
    TAG_STRING: Perspective.COLOR_RED,
    (TAG_MACRO, MACRO_DEFINE): Perspective.COLOR_MAGENTA,
    (TAG_MACRO, MACRO_IFDEF): Perspective.COLOR_MAGENTA,
    (TAG_MACRO, MACRO_ENDIF): Perspective.COLOR_MAGENTA,
    (TAG_KEYWORD, KEYWORD_MODULE): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_WIRE): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_REG): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_BEGIN): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_ALWAYS): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_INITIAL): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_IF): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_ELSE): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_INPUT): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_OUTPUT): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_INOUT): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_PARAMETER): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_LOCALPARAM): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_FOR): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_END): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_ASSIGN): Perspective.COLOR_YELLOW,
    (TAG_KEYWORD, KEYWORD_ENDMODULE): Perspective.COLOR_YELLOW,
    (TAG_RESERVED, RESERVED_EQUAL_DELAYED): Perspective.COLOR_GREEN,
    (TAG_RESERVED, RESERVED_EQUAL): Perspective.COLOR_GREEN,
    (TAG_RESERVED, RESERVED_PLUS): Perspective.COLOR_GREEN,
    (TAG_RESERVED, RESERVED_MINUS): Perspective.COLOR_GREEN,
    (TAG_RESERVED, RESERVED_MUL): Perspective.COLOR_GREEN,
    (TAG_RESERVED, RESERVED_DIV): Perspective.COLOR_GREEN,
    (TAG_RESERVED, RESERVED_POUNDPAREN_OPEN): Perspective.COLOR_GREEN,
    (TAG_RESERVED, RESERVED_PAREN_OPEN): Perspective.COLOR_GREEN,
    (TAG_RESERVED, RESERVED_PAREN_CLOSE): Perspective.COLOR_GREEN,
    (TAG_RESERVED, RESERVED_BRACE_OPEN): Perspective.COLOR_GREEN,
    (TAG_RESERVED, RESERVED_BRACE_CLOSE): Perspective.COLOR_GREEN,
    (TAG_RESERVED, RESERVED_BRACKET_OPEN): Perspective.COLOR_GREEN,
    (TAG_RESERVED, RESERVED_BRACKET_CLOSE): Perspective.COLOR_GREEN,
    (TAG_RESERVED, RESERVED_COMMA): Perspective.COLOR_GREEN,
    (TAG_RESERVED, RESERVED_SEMICOLON): Perspective.COLOR_GREEN,
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

def _tag(t):
    if isinstance(t.tag, tuple) or isinstance(t.tag, list):
        return t.tag[0]
    else:
        return t.tag

def _subtag(t):
    if isinstance(t.tag, tuple) or isinstance(t.tag, list):
        return t.tag[1]
    else:
        return None

class StructureDefinition():
    _re_kw = "k\{(\w)+}"
    _re_tag = "t\{(\w)+}"
    _re_subtag = "s\{(\w)+}"
    def __init__(self, ss):
        pass

class StructParser():
    complete = 3
    collect = 2
    must = 1
    can = 0
    def __init__(self, name, structdef, tag=None):
        self.name = name
        self._structdef = structdef
        self.tag = tag
        self.reset()

    def reset(self):
        self.structs = []
        self.struct = []
        self.npart = 0
        self.retry = False
        self.groupLevel = 0

    def doParse(self, token, retrying, verbose=False):
        # 'retry' = True means try this same token again
        if retrying != self.retry:
            return False
        self.retry = False
        tag = _tag(token)
        subtag = _subtag(token)
        #print(f"token = {token}")
        tgt_tag, tgt_subtag, do, ef = self._structdef[self.npart]
        hit = tgt_tag == tag
        if do == self.complete:
            closing_subtag = _grouping_pairs.get(tgt_subtag)
            hit_close = (tgt_tag == tag) and (closing_subtag == subtag)
        else:
            hit_close = False
        if ef is not None:
            if (not hit) and (not hit_close) and ef(token):
                raise SyntaxError(f"Syntax error parsing token: {token}")
        if tgt_subtag is not None:
            hit = hit and (tgt_subtag == subtag)
        if (do == self.can):
            if not hit:
                # This token must match the next rule
                if verbose:
                    print(f"[{self.npart}] Pass on optional: {token}")
                self.retry = True
            else:
                if verbose:
                    print(f"[{self.npart}] Hit on token: {token}")
                self.struct.append(token)
            self.npart += 1
        elif ((do == self.must) and hit):
            if verbose:
                print(f"[{self.npart}] Hit on token: {token}")
            self.struct.append(token)
            self.npart += 1
        elif do == self.collect:
            if verbose:
                print(f"[{self.npart}] Collecting token: {token}")
            self.struct.append(token)
            if hit:
                self.npart += 1
        elif do == self.complete:
            if hit:
                if verbose:
                    print(f"Complete hit open on {token}")
                self.groupLevel += 1
            elif hit_close:
                if verbose:
                    print(f"Complete hit close on {token}")
                self.groupLevel -= 1
            self.struct.append(token)
            if self.groupLevel == 0:
                self.npart += 1
        else:
            if verbose:
                print(f"[{self.npart}] Reset; not the target structure")
            self.npart = 0
            self.struct = []
        if self.npart == len(self._structdef):
            if verbose:
                print(f"Assign completed")
            self.structs.append(self.struct)
            self.struct = []
            self.npart = 0
        return self.retry

    def get(self):
        self.structs.append(self.struct)
        return self.structs

class Grouper():
    def __init__(self, *args, **kwargs):
        self.structparsers = []
        self.tk = Tokenizer(*args, **kwargs)

    def tokenize(self, s):
        self.cs = self.tk.parse(s)
        return

    def parseStructure(self):
        # Assign is:
        self.cs.setActivePerspective("keywords")
        ics = iter(self.cs)
        getNewToken = True
        retry = False
        while True:
            if not retry:
                try:
                    token = next(ics)
                except StopIteration:
                    break
            retrying = retry
            retry = False
            for sp in self.structparsers:
                verbose = False
                err = None
                try:
                    if sp.doParse(token, retrying, verbose):
                        retry = True
                except SyntaxError as se:
                    err = str(se)
                if err is not None:
                    nline, nchar = self.cs.charToLineChar(token.start)
                    raise SyntaxError("[line {}: char {}] ".format(nline, nchar) + err)
        structResults = {}
        for sp in self.structparsers:
            structResults[sp.name] = sp.get()
        return structResults

    def printStructs(self, structs, label=""):
        print(f"=== {label} ===")
        for n in range(len(structs)):
            struct = structs[n]
            print("  ", end="")
            for token in struct:
                print(token.value, end="")
            print()


class VerilogGrouper(Grouper):
    TAG_STATEMENT = 1
    TAG_BLOCK = 2
    TAG_MODULEDECLARATION = 3

    TAG_ASSIGNS = 1
    TAG_WIREDECS = 2
    TAG_REGDECS = 3

    complete = 3
    collect = 2
    must = 1
    can = 0
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

    _wiredec = [
        # Tag, subtag, must/can, error if true
        #   mandatory keyword wire
        (TAG_KEYWORD, KEYWORD_WIRE, must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   mandatory signal name
        (TAG_GENERIC, None, must, None),
        #   collect until reserved ';'
        #       Error on any keywords
        (TAG_RESERVED, RESERVED_SEMICOLON, collect, lambda t: _tag(t) == TAG_KEYWORD),
    ]

    _wiredec_with_range = [
        # Tag, subtag, must/can, error if true
        #   mandatory keyword wire
        (TAG_KEYWORD, KEYWORD_WIRE, must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   complete open reserved '[' with its mating close reserved ']'
        (TAG_RESERVED, RESERVED_BRACKET_OPEN, complete, lambda t: _tag(t) != TAG_GENERIC),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   mandatory signal name
        (TAG_GENERIC, None, must, None),
        #   collect until reserved ';'
        #       Error on any keywords
        (TAG_RESERVED, RESERVED_SEMICOLON, collect, lambda t: _tag(t) == TAG_KEYWORD),
    ]

    _regdec = [
        # Tag, subtag, must/can, error if true
        #   mandatory keyword reg
        (TAG_KEYWORD, KEYWORD_REG, must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   mandatory signal name
        (TAG_GENERIC, None, must, None),
        #   collect until reserved ';'
        #       Error on any keywords
        (TAG_RESERVED, RESERVED_SEMICOLON, collect, lambda t: _tag(t) == TAG_KEYWORD),
    ]

    _regdec_with_range = [
        # Tag, subtag, must/can, error if true
        #   mandatory keyword reg
        (TAG_KEYWORD, KEYWORD_REG, must, None),
        #   mandatory whitespace
        (TAG_WHITESPACE, None, must, None),
        #   complete open reserved '[' with its mating close reserved ']'
        (TAG_RESERVED, RESERVED_BRACKET_OPEN, complete, lambda t: _tag(t) != TAG_GENERIC),
        #   optional whitespace
        (TAG_WHITESPACE, None, can, None),
        #   mandatory signal name
        (TAG_GENERIC, None, must, None),
        #   collect until reserved ';'
        #       Error on any keywords
        (TAG_RESERVED, RESERVED_SEMICOLON, collect, lambda t: _tag(t) == TAG_KEYWORD),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addParsers()

    def addParsers(self):
        tag = (self.TAG_STATEMENT, self.TAG_REGDECS)
        self.structparsers.append(StructParser("regdecs", self._regdec, tag=tag))

        tag = (self.TAG_STATEMENT, self.TAG_REGDECS)
        self.structparsers.append(StructParser("regdecs_with_range", self._regdec_with_range, tag=tag))

        tag = (self.TAG_STATEMENT, self.TAG_WIREDECS)
        self.structparsers.append(StructParser("wiredecs", self._wiredec, tag=tag))

        tag = (self.TAG_STATEMENT, self.TAG_WIREDECS)
        self.structparsers.append(StructParser("wiredecs_with_range", self._wiredec_with_range, tag=tag))

        tag = (self.TAG_STATEMENT, self.TAG_ASSIGNS)
        self.structparsers.append(StructParser("assigns", self._assign, tag=tag))

        tag = (self.TAG_STATEMENT, self.TAG_ASSIGNS)
        self.structparsers.append(StructParser("assigns_with_range", self._assign_with_range, tag=tag))


class Tokenizer():
    def __init__(self, quote='"', comment_single="//", comment_multi=("/*", "*/"),
                 keywords={}, reserved={}, macros={}):
        self._quote = quote
        self._comment_single = comment_single
        self._comment_multi = comment_multi
        self._keywords = keywords
        self._reserved = reserved
        self._macros = macros

    def parse(self, string):
        cs = ConStr(string)
        cs.addPerspective("top")
        self.tagComments(cs)
        self.tagMacros(cs)
        self.tagStrings(cs)
        self.tagWhitespace(cs)
        self.tagReserved(cs)
        self.tagKeywords(cs)
        return cs

    def tagComments(self, cs):
        # First single-line comments
        inranges = self._rangesByString(str(cs), instr=self._comment_single, outstr="\n", respect_quotes=True,
                                        respect_parens=False, allow_escape=True, max_splits=0, start_in=False, verbose=False)
        for start, stop in inranges:
            sl = slice(start, stop)
            cs.tag(sl, TAG_COMMENT)

        # Then multi-line comments
        cs.copyPerspective("top", "comments1")
        instr, outstr = self._comment_multi
        for token in iter(cs):
            tag = token.tag
            if tag == cs.TagGeneric:
                inranges = self._rangesByString(str(cs), instr=instr, outstr=outstr, respect_quotes=True,
                                                respect_parens=False, allow_escape=True, max_splits=0, start_in=False,
                                                verbose=False)
                for start, stop in inranges:
                    sl = slice(start, stop)
                    cs.tag(sl, TAG_COMMENT)
        return len(inranges)

    def tagMacros(self, cs):
        cs.copyPerspective("comments1", "macros")
        for token in iter(cs):
            tag = token.tag
            if tag == cs.TagGeneric:
                for _mTag, macro in self._macros.items():
                    #print(f"Looking for {macro}")
                    inranges = self._rangesByString(str(cs), instr=macro, outstr="\n", respect_quotes=True,
                                                    respect_parens=False, allow_escape=True, max_splits=0, start_in=False,
                                                    verbose=False)
                    for start, stop in inranges:
                        sl = slice(start, stop)
                        cs.tag(sl, (TAG_MACRO, _mTag))
        return

    def tagStrings(self, cs):
        cs.copyPerspective("macros", "strings")
        inranges = self._rangesByString(str(cs), instr=self._quote, outstr=self._quote, respect_quotes=False,
                                        respect_parens=False, allow_escape=True, max_splits=0, start_in=False)
        for start, stop in inranges:
            sl = slice(start, stop)
            cs.tag(sl, TAG_STRING)
        return len(inranges)

    def tagWhitespace(self, cs):
        cs.copyPerspective("strings", "whitespace")
        for token in iter(cs):
            tag = token.tag
            #print(f"parsing {value}")
            if tag == cs.TagGeneric:
                for _kwTag, keyword in self._reserved.items():
                    self._tagWhitespace(cs, token, TAG_WHITESPACE)
        cs.setActiveGetPerspective("whitespace")
        return

    def tagReserved(self, cs):
        cs.copyPerspective("whitespace", "reserved")
        token = None
        ics = iter(cs)
        while True:
            try:
                token = next(ics)
            except StopIteration:
                break
            tag = token.tag
            #print(f"parsing {value}")
            if tag == cs.TagGeneric:
                for _kwTag, reserved in self._reserved.items():
                    char, escapedchar = reserved
                    self._tagMatches(cs, token, escapedchar, (TAG_RESERVED, _kwTag))
        cs.setActiveGetPerspective("reserved")
        return

    def tagKeywords(self, cs):
        cs.copyPerspective("reserved", "keywords")
        token = None
        ics = iter(cs)
        while True:
            try:
                token = next(ics)
            except StopIteration:
                break
            tag = token.tag
            #print(f"parsing {value}")
            if tag == cs.TagGeneric:
                for _kwTag, keyword in self._keywords.items():
                    self._tagMatchesAtBoundaries(cs, token, keyword, (TAG_KEYWORD, _kwTag))
        cs.setActiveGetPerspective("keywords")
        return

    def _tagMatchesAtBoundaries(self, cs, token, keyword, tag):
        restr = r"\b" + keyword + r"\b"
        offset = token.start
        _iter = re.finditer(restr, token.value)
        for _match in _iter:
            #print(f"matched with {keyword}")
            start, stop = _match.span()
            sl = slice(offset+start, offset+stop)
            cs.tag(sl, tag)
        return

    def _tagMatches(self, cs, token, keyword, tag):
        restr = keyword
        offset = token.start
        _iter = re.finditer(restr, token.value)
        for _match in _iter:
            #print(f"matched with {keyword}")
            start, stop = _match.span()
            sl = slice(offset+start, offset+stop)
            cs.tag(sl, tag)
        return

    def _tagWhitespace(self, cs, token, tag):
        restr = "\s+"
        offset = token.start
        _iter = re.finditer(restr, token.value)
        for _match in _iter:
            #print(f"matched with {keyword}")
            start, stop = _match.span()
            sl = slice(offset+start, offset+stop)
            cs.tag(sl, tag)
        return

    @staticmethod
    def _rangesByString(line, instr="", outstr="", respect_quotes=True, respect_parens=True,
                        allow_escape=True, max_splits=0, start_in=False, verbose=False):
        """Split line by string 'splitstr', respecting parentheses and quotes"""
        line = str(line)
        # Handle explicit simple case first
        il = len(instr)
        ol = len(outstr)
        maxlen = max(il, ol)
        if (il == 0) or (ol == 0) or (len(line) < maxlen):
            return []
        if maxlen > 1:
            chars = [None] + [c for c in line[:maxlen-1]]
        else:
            chars = []
        plevel = 0
        escaped = False
        instring = False
        isin = start_in
        if isin:
            inpoint = 0
        else:
            inpoint = None
        inranges = []
        for n in range(maxlen-1, len(line)):
            # Shift register
            c = line[n]
            chars = chars[1:] + [c]
            if respect_quotes and (c == '"'):
                if not escaped:
                    if instring:
                        instring = False
                    else:
                        instring = True
                escaped = False
            elif allow_escape and (c == '\\'):
                if not escaped:
                    escaped = True
                else:
                    escaped = False
            elif respect_parens and (c == '('):
                if not instring and not escaped:
                    plevel += 1
                escaped = False
            elif respect_parens and (c == ')'):
                if not instring and not escaped:
                    plevel -= 1
                escaped = False
            elif isin:
                if "".join(chars[-ol:]) == outstr:
                    if verbose:
                        print("outstr matched at {}".format(n))
                    if not instring and not escaped and plevel == 0:
                        inranges.append((inpoint, n + 1))
                        inpoint = None
                        isin = False
                        if len(inranges) == max_splits:
                            break
                escaped = False
            else:
                if "".join(chars[-il:]) == instr:
                    if verbose:
                        print("instr matched at {}".format(n))
                    if not instring and not escaped and plevel == 0:
                        inpoint = n - il + 1
                        isin = True
                escaped = False
        if inpoint is not None:
            inranges.append((inpoint, len(line)))
        return inranges

def testTokenizer(argv):
    if len(argv) < 2:
        print("Need a string")
        return
    tkzr = Tokenizer(reserved=reserved, keywords=keywords, macros=macros)
    from colorama import Fore, Back, Style
    def printRed(s, end="\n"):
        print(Fore.RED + s + Style.RESET_ALL, end=end)
    # Print tokens as they come
    cs = tkzr.parse(argv[1])
    cs.setActivePerspective("keywords")
    cs.setColorMap(_colormap)
    cs.printColor()
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
    gp = VerilogGrouper(reserved=reserved, keywords=keywords, macros=macros)
    gp.tokenize(instr)
    structdict = gp.parseStructure()
    for name, structs in structdict.items():
        gp.printStructs(structs, name)
    return

def tokenizeFile():
    import argparse
    parser = argparse.ArgumentParser(description="Hand-rolled Verilog parser")
    parser.set_defaults(handler=lambda args: parser.print_help())
    parser.add_argument('filename', default=None, help="The Verilog file to parse.")
    args = parser.parse_args()
    #return args.handler(args)
    instr = None
    with open(args.filename, 'r') as fd:
        instr = fd.read()
    if instr is None:
        print("Failed to parse {}".format(args.filename))
        return
    tkzr = Tokenizer(reserved=reserved, keywords=keywords, macros=macros)
    cs = tkzr.parse(instr)
    cs.setActivePerspective("keywords")
    cs.setColorMap(_colormap)
    cs.printColor()
    return

if __name__ == "__main__":
    import sys
    #testTokenizer(sys.argv)
    #tokenizeFile()
    #test_GrouperParseAssign()
    parseFile()
