#! python3

# A just-for-fun test of a generic parsing concept

import re
from constr import ConStr, Perspective

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
    """TODO"""
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

    def doParse(self, token, retrying, grouping_pairs, verbose=False):
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
            closing_subtag = grouping_pairs.get(tgt_subtag)
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
        self._grouping_pairs = self.tk._grouping_pairs

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
                if sp.name == "regdecs_with_range":
                    verbose = False
                try:
                    if sp.doParse(token, retrying, self._grouping_pairs, verbose):
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

class TagMap():
    comments = None
    macros = None
    strings = None
    whitespace = None
    reserved = None
    keywords = None
    def __init__(self, **kwargs):
        for kw, val in kwargs.items():
            if hasattr(self, kw):
                setattr(self, kw, val)

class Tokenizer():
    def __init__(self, quote='"', comment_single="//", comment_multi=("/*", "*/"),
                 keywords={}, reserved={}, macros={}, tagmap=None):
        self._quote = quote
        self._comment_single = comment_single
        self._comment_multi = comment_multi
        self._keywords = keywords
        self._reserved = reserved
        self._macros = macros
        if tagmap is None:
            self._tagmap = TagMap()
        else:
            self._tagmap = tagmap
        self._mkGroupingPairs()

    def _mkGroupingPairs(self):
        # Look for '[]'
        groupers = (('[', ']'), ('(', ')'), ('{', '}'))
        self._grouping_pairs = {}
        for opener, closer in groupers:
            otag = None
            ctag = None
            for tag, chars in self._reserved.items():
                char, escapedchar = chars
                if char == opener:
                    otag = tag
                elif char == closer:
                    ctag = tag
            #otag = self._reserved.get(opener, None)
            #ctag = self._reserved.get(closer, None)
            if (otag is not None) and (ctag is not None):
                self._grouping_pairs[otag] = ctag
        return

    def parse(self, string):
        cs = ConStr(string)
        cs.addPerspective("top")
        tm = self._tagmap
        self.tagComments(cs, tm.comments)
        self.tagMacros(cs, tm.macros)
        self.tagStrings(cs, tm.strings)
        self.tagWhitespace(cs, tm.whitespace)
        self.tagReserved(cs, tm.reserved)
        self.tagKeywords(cs, tm.keywords)
        return cs

    def tagComments(self, cs, tag):
        # First single-line comments
        inranges = self._rangesByString(str(cs), instr=self._comment_single, outstr="\n", respect_quotes=True,
                                        respect_parens=False, allow_escape=True, max_splits=0, start_in=False, verbose=False)
        for start, stop in inranges:
            sl = slice(start, stop)
            cs.tag(sl, tag)

        # Then multi-line comments
        cs.copyPerspective("top", "comments1")
        instr, outstr = self._comment_multi
        for token in iter(cs):
            _tag = token.tag
            if _tag == cs.TagGeneric:
                inranges = self._rangesByString(str(cs), instr=instr, outstr=outstr, respect_quotes=True,
                                                respect_parens=False, allow_escape=True, max_splits=0, start_in=False,
                                                verbose=False)
                for start, stop in inranges:
                    sl = slice(start, stop)
                    cs.tag(sl, tag)
        return len(inranges)

    def tagMacros(self, cs, tag):
        cs.copyPerspective("comments1", "macros")
        for token in iter(cs):
            _tag = token.tag
            if _tag == cs.TagGeneric:
                for _mTag, macro in self._macros.items():
                    #print(f"Looking for {macro}")
                    inranges = self._rangesByString(str(cs), instr=macro, outstr="\n", respect_quotes=True,
                                                    respect_parens=False, allow_escape=True, max_splits=0, start_in=False,
                                                    verbose=False)
                    for start, stop in inranges:
                        sl = slice(start, stop)
                        cs.tag(sl, (tag, _mTag))
        return

    def tagStrings(self, cs, tag):
        cs.copyPerspective("macros", "strings")
        inranges = self._rangesByString(str(cs), instr=self._quote, outstr=self._quote, respect_quotes=False,
                                        respect_parens=False, allow_escape=True, max_splits=0, start_in=False)
        for start, stop in inranges:
            sl = slice(start, stop)
            cs.tag(sl, tag)
        return len(inranges)

    def tagWhitespace(self, cs, tag):
        cs.copyPerspective("strings", "whitespace")
        for token in iter(cs):
            _tag = token.tag
            #print(f"parsing {value}")
            if _tag == cs.TagGeneric:
                for _kwTag, keyword in self._reserved.items():
                    self._tagWhitespace(cs, token, tag)
        cs.setActiveGetPerspective("whitespace")
        return

    def tagReserved(self, cs, tag):
        cs.copyPerspective("whitespace", "reserved")
        token = None
        ics = iter(cs)
        while True:
            try:
                token = next(ics)
            except StopIteration:
                break
            _tag = token.tag
            #print(f"parsing {value}")
            if _tag == cs.TagGeneric:
                for _kwTag, reserved in self._reserved.items():
                    char, escapedchar = reserved
                    self._tagMatches(cs, token, escapedchar, (tag, _kwTag))
        cs.setActiveGetPerspective("reserved")
        return

    def tagKeywords(self, cs, tag):
        cs.copyPerspective("reserved", "keywords")
        token = None
        ics = iter(cs)
        while True:
            try:
                token = next(ics)
            except StopIteration:
                break
            _tag = token.tag
            #print(f"parsing {value}")
            if _tag == cs.TagGeneric:
                for _kwTag, keyword in self._keywords.items():
                    self._tagMatchesAtBoundaries(cs, token, keyword, (tag, _kwTag))
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
