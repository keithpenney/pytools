#! python3

# A just-for-fun test of a generic parsing concept

# TODO:
#   * When walking a StructDef, return the object itself (not its first entry)

import re
from constr import ConStr, Perspective, _tag, _subtag, MultiTag

# ===================== Demo Keywords/Reserved/Tags ===================
TAG_GENERIC = 0
TAG_COMMENT = 1
TAG_STRING  = 2
TAG_KEYWORD = 3
TAG_RESERVED= 4
_colormap = {
    TAG_COMMENT: Perspective.COLOR_LIGHTCYAN_EX,
    TAG_STRING: Perspective.COLOR_RED,
    TAG_KEYWORD: Perspective.COLOR_GREEN,
    TAG_RESERVED: Perspective.COLOR_BLUE,
}
KEYWORD_AND = 4
KEYWORD_OR = 5
KEYWORD_NOT = 6
keywords = {
    KEYWORD_AND: "and",
    KEYWORD_OR: "or",
    KEYWORD_NOT: "not",
}
RESERVED_PLUS = 7
RESERVED_MINUS = 8
RESERVED_PAREN_OPEN = 9
RESERVED_PAREN_CLOSE = 10
RESERVED_MUL = 11
RESERVED_DIV = 12
reserved = {
    RESERVED_PLUS: ("+", "\+"),
    RESERVED_MINUS: ("-", "\-"),
    RESERVED_MUL: ("*", "\*"),
    RESERVED_DIV: ("/", "\/"),
    RESERVED_PAREN_OPEN: ("(", "\("),
    RESERVED_PAREN_CLOSE: (")", "\)"),
}
macros = {
}

_grouping_pairs = {
    '[': ']',
    '(': ')',
    '{': '}',
    '(*': '*)'
}
def get_closer_tag(tag):
    """Clobber me (for customization)"""
    ct = []
    closer = False
    for t in tag:
        _closerTag = _grouping_pairs.get(t, None)
        if _closerTag is not None:
            print(f"                                                             _closerTag = _{closerTag}")
            closer = True
            ct.append(_closerTag)
        else:
            ct.append(t)
    if closer:
        print(f"Returning closer {ct}")
        return MultiTag(ct)
    return None

#TODO
#   1. If a subtag is a list of ints, this should be able to match multiple tags.  How implement?
class StructDefEntry():
    """A single entry in a StructDef"""
    def __init__(self, tag, op, err):
        if not isinstance(tag, MultiTag) and not isinstance(tag, StructDef):
            tag = MultiTag(*tag)
        self.tag = tag
        self.op = op
        self.err = err

    def __eq__(self, other):
        return self.tag.__eq__(other)

    def __iter__(self):
        # We're an iterator now
        self._n = 0
        return self

    def __next__(self):
        if self._n < 3:
            item = (self.tag, self.op, self.err)[self._n]
            self._n += 1
            return item
        else:
            raise StopIteration

    def __str__(self):
        return f"StructDefEntry(tag={self.tag}, op={self.op}, err={self.err})"

    def __repr__(self):
        return self.__str__()


class StructDef():
    """A definition of a structure to match.
    To walk the StructDef, use the walk API:
        sd = StructDef(*args)
        sd.reset()
        while True:
            try:
                entry = sd.get()
            except StopIteration:
                break
            if matches(entry):
                sd.step()
            else:
                sd.step_out()
    """
    def __init__(self, sdelist):
        self._entries = []
        for item in sdelist:
            if not isinstance(item, StructDefEntry):
                item = StructDefEntry(*item)
            self._entries.append(item)
        self._len = len(self._entries)
        self.stack = [self]
        self._ix = 0

    def __str__(self):
        return f"StructDef({len(self._entries)})"

    def __len__(self):
        return self._entries.__len__()

    def __eq__(self, other):
        #print(f"__eq__: self._entries[{self._ix}] == {other}? : " + "{}".format(self._entries[self._ix].__eq__(other)))
        if self._ix < self._len:
            return self._entries[self._ix].__eq__(other)
        return False

    def __getitem__(self, n):
        item = self._entries.__getitem__(n)
        if isinstance(item, StructDef):
            return item.__getitem__(0)
        else:
            return item

    def copy(self):
        """Returns an independent copy of self."""
        return StructDef(self._entries)

    def reset(self):
        #print("    Stack reset")
        self.stack = [self]
        for item in self._entries:
            if hasattr(item, "tag") and hasattr(item.tag, "reset"):
                item.tag.reset()
        self._ix = 0

    def done(self):
        return self._ix == self._len

    def _inc(self):
        if self._ix < self._len:
            self._ix += 1
        return

    def get(self):
        """Returns an instance of either StructDefEntry or StructDef.
        Raises StopIteration when complete.
        Use reset() to begin a new walk."""
        if len(self.stack) == 0:
            raise StopIteration
        #if len(self.stack) > 1:
        #    print(f"    Stack depth: {len(self.stack)}")
        try:
            item = self.stack[-1]._get()
        except StopIteration:
            popped = self.stack.pop()
            #print(f"    Coming out of {popped}")
            if len(self.stack) > 0:
                self.stack[-1]._inc()
            return self.get()    # RECURSE
        return item

    def _get(self):
        if self._ix < self._len:
            return self._entries[self._ix]
        else:
            raise StopIteration

    def step_into(self):
        """Step into the current entry if it is a StructDef.  Behaves the same as step_out if
        this entry is a StructDefEntry."""
        item = self.get()
        if isinstance(item.tag, StructDef):
            #print(f"    Diving into {item.tag} (and resetting)")
            item.tag.reset()
            self.stack.append(item.tag)
            return True
        else:
            self.stack[-1]._inc()
        return False

    def step(self):
        if True:
            return self.step_into()
        self.stack[-1]._inc()
        return

    def step_out(self):
        """Step out of the current StructDef.
        Returns False if empty after step; else True."""
        if len(self.stack) > 1:
            self.stack.pop()
        if len(self.stack) > 0:
            self.stack[-1]._inc()
        return False

    def __iter__(self):
        # We're an iterator now
        self._n = 0
        return self

    def __next__(self):
        if self._ix < self._len:
            item = self._entries[self._n]
            self._n += 1
            return item
        else:
            raise StopIteration


class StructParser():
    can = 0             # Optional
    must = 1            # Mandatory
    collect = 2         # Collect until match, including the match
    collect_drop = 3    # Collect until match, dropping the match
    complete = 4        # Get opening grouper, collect until matching closing grouper

    def __init__(self, name, structdef, tag=None, verbose=False):
        self.name = name
        self.structdef = StructDef(structdef)
        self.tag = tag
        self.reset()
        self.verbose = verbose

    def reset(self):
        self.new()
        self.structs = []
        self.retry = False
        self.groupLevel = 0
        self.inmatch = False

    def done(self):
        return self.structdef.done()

    def new(self):
        self.struct = []
        self.structdef.reset()
        return

    def getNextEntry(self, autoreset=False):
        entry = self.structdef.get()
        return (entry.tag, entry.op, entry.err)

    def step(self):
        return self.structdef.step()

    def step_out(self):
        return self.structdef.step_out()

    def step_into(self):
        return self.structdef.step_into()

    def _subParse(self, token, verbose=False):
        """Return True to continue subparsing"""
        if not verbose:
            verbose = self.verbose
        # If we hit at this level, try again one level down (return True)
        if hit:
            if self.step_into():
                return True
        # If there are no levels down, return False
        return False

    def doParse(self, token, verbose=False):
        """Do one round of parsing.
        Unused return value
        """
        if not verbose:
            verbose = self.verbose
        def consume(x):
            self.struct.append(x)
        retry = False
        tag = token.tag
        tgt_tag, do, ef = self.getNextEntry(autoreset=False)
        hit = tgt_tag == tag
        if do == self.complete:
            try:
                closing_tag = get_closer_tag(tgt_tag)
            except AttributeError:
                print(f"#{self.name}: Why am I looking for a closer on tgt_tag {tgt_tag}? {self.structdef[len(self.struct)]}")
            hit_close = (closing_tag == tag)
            #print(f"closing_tag = {closing_tag} == {tag} ? {closing_tag == tag}")
        else:
            hit_close = False
        if verbose:
            #print(f"{_tagstr(tgt_tag)}, {_tagstr(tgt_subtag)}, {_tagstr(closing_subtag)}, {_tagstr(tag)}, {_tagstr(subtag)}")
            #print(f"token = {token}")
            pass
        if ef is not None:
            if (not hit) and (not hit_close) and ef(token):
                raise SyntaxError(f"({self.name}) Syntax error parsing token: {token}")
        if (do == self.can):
            if not hit:
                if verbose:
                    print(f"#{self.name}: [{len(self.struct)}] Pass on optional: {token}")
                if not self.done():
                    # This token must match the next rule
                    retry = True
                if self.step_out():
                    retry = True
            else:
                if verbose:
                    print(f"#{self.name}: [{len(self.struct)}] Hit on optional: {token}")
                if self.step():
                    retry = True
                else:
                    consume(token)
        elif ((do == self.must) and hit):
            if verbose:
                print(f"#{self.name}: [{len(self.struct)}] Hit on mandatory: {token}")
            if self.step():
                retry = True
            else:
                consume(token)
        elif do == self.collect:
            if verbose:
                print(f"#{self.name}: [{len(self.struct)}] Collecting: {token}")
            consume(token)
            if hit:
                self.step()
        elif do == self.collect_drop:
            if hit:
                if verbose:
                    print(f"#{self.name}: [{len(self.struct)}] Dropping hit: {token}")
                self.step()
            else:
                if verbose:
                    print(f"#{self.name}: [{len(self.struct)}] Collecting: {token}")
                consume(token)
        elif do == self.complete:
            #if verbose:
            #    print(f"closing_tag = {closing_tag}")
            if not self.inmatch:
                if hit:
                    #print("COMPLETE HIT!")
                    self.inmatch = True
                else:
                    #print(f"COMPLETE MISS! {tgt_tag} != {tag}")
                    pass
            if self.inmatch:
                if hit:
                    if verbose:
                        print(f"#{self.name}: [{len(self.struct)}] Complete hit open on {token}")
                    self.groupLevel += 1
                elif hit_close:
                    if verbose:
                        print(f"#{self.name}: [{len(self.struct)}] Complete hit close on {token}")
                    self.groupLevel -= 1
                else:
                    if verbose:
                        print(f"#{self.name}: [{len(self.struct)}] Complete collecting {token}")
                consume(token)
                if self.groupLevel == 0:
                    if verbose:
                        print(f"#{self.name}: Stepping out of complete")
                    self.inmatch = False
                    if self.step():
                        retry = True
            else:
                if (len(self.struct) > 0) and verbose:
                    print(f"#{self.name}: Terminating early on {token}")
                self.new()
        else:
            if verbose:
                if len(self.struct) > 0:
                    print(f"#{self.name}: [{len(self.struct)}] Reset on {token}; not the target structure")
            self.new()
        if self.done():
            self.structs.append(self.struct)
            if verbose:
                print(f"#{self.name}: " + "Parse {} completed: ".format(len(self.structs)), end="")
                for token in self.struct:
                    print(token.value, end="")
                print()
            self.new()
        if retry:
            if verbose:
                print(f"#{self.name}: R E T R Y")
            self.doParse(token, verbose=verbose)
        return

    def get(self):
        """Get the results of parsing."""
        if len(self.struct) > 0:
            self.structs.append(self.struct)
        return self.structs

class Grouper():
    can = StructParser.can
    must = StructParser.must
    collect = StructParser.collect
    collect_drop = StructParser.collect_drop
    complete = StructParser.complete

    def __init__(self, *args, **kwargs):
        self.structparsers = []
        self.tk = Tokenizer(*args, **kwargs)
        self._grouping_pairs = self.tk._grouping_pairs
        self._verboseParsers = []

    def tokenize(self, s):
        self.cs = self.tk.parse(s)
        return

    def parseStructure(self, skipTags=None):
        #import time
        #print("parseStructure")
        #__start = time.process_time()
        ics = iter(self.cs)
        while True:
            try:
                token = next(ics)
            except StopIteration:
                break
            if skipTags is not None:
                doSkip = False
                for tag in skipTags:
                    if token.tag == tag:
                        doSkip = True
                        break
                if doSkip:
                    continue
            for sp in self.structparsers:
                verbose = False
                err = None
                if sp.name in self._verboseParsers:
                    verbose = True
                try:
                    sp.doParse(token, verbose)
                except SyntaxError as se:
                    err = str(se)
                if err is not None:
                    nline, nchar = self.cs.charToLineChar(token.start)
                    raise SyntaxError("[line {}: char {}] ".format(nline, nchar) + err)
        structResults = {}
        for sp in self.structparsers:
            structResults[sp.name] = (sp.tag, sp.get())
        #__end = time.process_time()
        #print(f"DURATION: {__end-__start} seconds")
        return structResults

    @staticmethod
    def printStructs(self, structs, label=""):
        print(f"=== {label} ===")
        for n in range(len(structs)):
            struct = structs[n]
            print("  ", end="")
            for token in struct:
                print(token.value, end="")
            print()

    @staticmethod
    def printStructDict(structDict):
        for name, (tag, structs) in structdict.items():
            print(f"name = {name}, tag = {tag}")
            for struct in structs:
                print("  ", end="")
                for token in struct:
                    print(token.value, end="")
                print()
        return


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

    def __str__(self):
        ss = [
            "TagMap(",
            f"  comments = {self.comments}",
            f"  macros = {self.macros}",
            f"  strings = {self.strings}",
            f"  whitespace = {self.whitespace}",
            f"  reserved = {self.reserved}",
            f"  keywords = {self.keywords}",
            ")",
        ]
        return "\n".join(ss)

    def __repr__(self):
        return self.__str__()

class Tokenizer():
    def __init__(self, quote='"', comment_single="//", comment_multi=("/*", "*/"),
                 keywords={}, reserved={}, macros={}, tagmap=None, group_pairs=[]):
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
        self._mkGroupingPairs(group_pairs)

    def _mkGroupingPairs(self, pairs=None):
        # Look for '[]'
        if pairs is not None:
            groupers = pairs
        else:
            groupers = (('[', ']'), ('(', ')'), ('{', '}'))
        self._grouping_pairs = {}
        for opener, closer in groupers:
            otag = None
            ctag = None
            # Support both dicts and sorted lists
            if hasattr(self._reserved, 'items'):
                _iter = self._reserved.items()
            else:
                _iter = self._reserved
            for tag, chars in _iter:
                char, escapedchar = chars
                if char == opener:
                    otag = tag
                elif char == closer:
                    ctag = tag
            if (otag is not None) and (ctag is not None):
                self._grouping_pairs[otag] = ctag
        return

    def parse(self, string):
        cs = ConStr(string)
        cs.addPerspective("top")
        tm = self._tagmap
        #print(f"tagmap = {tm}")
        self.tagComments(cs, tm.comments)
        self.tagMacros(cs, tm.macros)
        self.tagStrings(cs, tm.strings)
        self.tagWhitespace(cs, tm.whitespace)
        self.tagReserved(cs, tm.reserved)
        self.tagKeywords(cs, tm.keywords)
        cs.setActivePerspective("keywords")
        return cs

    def tagComments(self, cs, tag):
        # First single-line comments
        inranges = self._rangesByString(str(cs), instr=self._comment_single, outstr="\n", respect_quotes=True,
                                        respect_parens=False, allow_escape=True, max_splits=0, start_in=False, verbose=False)
        for start, stop in inranges:
            sl = slice(start, stop)
            cs.tag(sl, tag)

        # Then multi-line comments
        cs.copyPerspective("top", "comments")
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
        cs.copyPerspective("comments", "macros")
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
        for token in iter(cs):
            _tag = token.tag
            if _tag == cs.TagGeneric:
                inranges = self._rangesByString(token.value, instr=self._quote, outstr=self._quote, respect_quotes=False,
                                                respect_parens=False, allow_escape=True, max_splits=0, start_in=False, verbose=False)
                for start, stop in inranges:
                    sl = slice(token.start+start, token.start+stop)
                    cs.tag(sl, tag)
        return len(inranges)

    def tagWhitespace(self, cs, tag):
        cs.copyPerspective("strings", "whitespace")
        for token in iter(cs):
            _tag = token.tag
            #print(f"parsing {value}")
            if _tag == cs.TagGeneric:
                # Support both dicts and ordered lists
                if hasattr(self._reserved, 'items'):
                    _iter = self._reserved.items()
                else:
                    _iter = self._reserved
                for _kwTag, keyword in _iter:
                    self._tagWhitespace(cs, token, tag)
        cs.setActiveGetPerspective("whitespace")
        return

    def tagReserved(self, cs, tag):
        cs.copyPerspective("whitespace", "reserved")
        # Need to 'get' from reserved as well to ensure each reserved char only gets tagged once
        # I.e. the tags for '(' and '*' don't come around and clobber "(*"
        cs.setActivePerspective("reserved")
        token = None
        # Support both dicts and sorted lists
        if hasattr(self._reserved, 'items'):
            _iter = self._reserved.items()
        else:
            _iter = self._reserved
        for _kwTag, reserved in _iter:
            char, escapedchar = reserved
            for token in iter(cs):
                _tag = token.tag
                if _tag == cs.TagGeneric:
                    self._tagMatches(cs, token, escapedchar, MultiTag(tag, _kwTag))
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
        #if tag == (TAG_RESERVED, RESERVED_PARENSTAR_OPEN):
        #    print(f"######## _iter = {_iter}, restr = {restr}")
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
                        print("outstr matched at {}: outstr = {}; chars[-{}:] = {}".format(
                            n, outstr, ol, chars[-ol:]))
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
                        print("instr matched at {}: outstr = {}; chars[-{}:] = {}".format(
                            n, instr, il, chars[-il:]))
                    if not instring and not escaped and plevel == 0:
                        inpoint = n - il + 1
                        isin = True
                escaped = False
        if inpoint is not None:
            inranges.append((inpoint, len(line)))
        return inranges

def test_StructDef_walk():
    # (0, 1, 2, (3, 4, (5, 6, 7, 8)), 9)
    sd0 = StructDef((((5,),0,0), ((6,),0,0), ((7,),0,0), ((8,),0,0)))
    sd1 = StructDef((((3,),0,0), ((4,),0,0), (sd0,0,0)))
    sd2 = StructDef((((0,),0,0), ((1,),0,0), ((2,),0,0), (sd1,0,0), ((9,),0,0)))
    sd2.reset()
    print("Stepping all: Should be (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)")
    while True:
        try:
            item = sd2.get()
        except StopIteration:
            break
        if isinstance(item, StructDef):
            continue
        print(f"  {item}")
        sd2.step()

    print("\nStepping out: should be (0, 1, 2, 3, 9)")
    sd2.reset()
    while True:
        try:
            item = sd2.get()
        except StopIteration:
            print("Break")
            break
        if isinstance(item, StructDef):
            continue
        print(f"  {item}")
        if item in (5, 3):
            print("    step_out")
            sd2.step_out()
        else:
            sd2.step()
    return


tagmap = TagMap(
    comments=TAG_COMMENT,
    macros=None,
    strings=TAG_STRING,
    whitespace=None,
    reserved=TAG_RESERVED,
    keywords=TAG_KEYWORD,
)

def testTokenizer(argv):
    if len(argv) < 2:
        print("Need a string")
        return
    tkzr = Tokenizer(reserved=reserved, keywords=keywords, macros=macros, tagmap=tagmap)
    # Print tokens as they come
    cs = tkzr.parse(argv[1])
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
    tkzr = Tokenizer(reserved=reserved, keywords=keywords, macros=macros, tagmap=tagmap)
    cs = tkzr.parse(instr)
    cs.setColorMap(_colormap)
    cs.printColor()
    return

if __name__ == "__main__":
    import sys
    #testTokenizer(sys.argv)
    #tokenizeFile()
    test_StructDef_walk()
