#! python3

# A just-for-fun test of a generic parsing concept

from constr import ConStr

"""
reserved = {
    KEYWORD_MODULE: "module",
    KEYWORD_WIRE: "wire",
    KEYWORD_REG: "reg",
    KEYWORD_LOGIC: "logic",
    KEYWORD_BEGIN: "begin",
    KEYWORD_ALWAYS: "always",
    KEYWORD_INITIAL: "initial",
    KEYWORD_IF: "if",
    KEYWORD_ELSE: "else",
    RESERVED_EQUAL_DELAYED: "<=",
    RESERVED_EQUAL: "=",
    RESERVED_PLUS: "+",
    RESERVED_MINUS: "-",
    RESERVED_MUL: "*",
    RESERVED_DIV: "/",
    RESERVED_PAREN_OPEN: "(",
    RESERVED_PAREN_CLOSE: ")",
    RESERVED_BRACE_OPEN: "{",
    RESERVED_BRACE_CLOSE: "}",
    RESERVED_BRACKET_OPEN: "[",
    RESERVED_BRACKET_CLOSE: "]",
    RESERVED_COMMA: ",",
}

STRING_QUOTE = '"'
COMMENT_SINGLE_LINE = "//"
COMMENT_MULTI_LINE_OPEN = "/*"
COMMENT_MULTI_LINE_CLOSE = "*/"

whitespace = {
    WHITESPACE_SPACE: " ",
    WHITESPACE_TAB: "\t",
    WHITESPACE_NEWLINE: "\n",
}
"""

TAG_KEYWORD = 1

class Parser():
    def __init__(self, quote = '"', comment_single = "//", comment_multi = ("/*", "*/"), reserved = {}, whitespace = {}):
        self._quote = quote
        self._comment_single = comment_single
        self._comment_multi = comment_multi
        self._reserved = reserved
        self._whitespace = whitespace

    def parse(self, string):
        cs = ConStr(string)
        cs.addPerspective("comments")
        self.tagComment(cs)
        #self.tagWhitespace(cs)
        return cs

    def tagComment(self, cs):
        """Split line by string 'splitstr', respecting parentheses and quotes"""
        cs.setActivePerspective("comments")
        instr, outstr = self._comment_multi
        inranges = self._rangesByString(str(cs), instr=instr, outstr=outstr, respect_quotes=True, respect_parens=False,
                                        allow_escape=True, max_splits=0, start_in=False)
        for start, stop in inranges:
            sl = slice(start, stop)
            cs.tag(sl, TAG_KEYWORD)
        return len(inranges)

    def tagWhitespace(self, cs):
        pass

    @staticmethod
    def _rangesByString(line, instr="", outstr="", respect_quotes=True, respect_parens=True,
                        allow_escape=True, max_splits=0, start_in=False):
        """Split line by string 'splitstr', respecting parentheses and quotes"""
        line = str(line)
        # Handle explicit simple case first
        il = len(instr)
        ol = len(outstr)
        minlen = min(il, ol)
        if (il == 0) or (ol == 0) or (len(line) < minlen):
            return []
        chars = [c for c in line[:minlen]]
        ixs = []
        plevel = 0
        escaped = False
        instring = False
        isin = start_in
        if isin:
            inpoint = 0
        else:
            inpoint = None
        inranges = []
        for n in range(minlen-1, len(line)):
            # Shift register
            c = line[n]
            chars = chars[1:] + [c]
            if c == '"':
                if respect_quotes:
                    if not escaped:
                        if instring:
                            instring = False
                        else:
                            instring = True
                escaped = False
            elif c == '\\':
                if allow_escape:
                    if not escaped:
                        escaped = True
                    else:
                        escaped = False
            elif c == '(':
                if respect_parens:
                    if not instring and not escaped:
                        plevel += 1
                    escaped = False
            elif c == ')':
                if respect_parens:
                    if not instring and not escaped:
                        plevel -= 1
                    escaped = False
            elif isin:
                if "".join(chars[-ol:]) == outstr:
                    print("outstr matched at {}: {}".format(n, "".join(chars)))
                    if not instring and not escaped and plevel == 0:
                        inranges.append((inpoint, n + (ol-1)))
                        inpoint = None
                        isin = False
                        if len(inranges) == max_splits:
                            break
                escaped = False
            else:
                if "".join(chars[-il:]) == instr:
                    print("instr matched at {}: {}".format(n, "".join(chars)))
                    if not instring and not escaped and plevel == 0:
                        inpoint = n - il
                        isin = True
                escaped = False
        if inpoint is not None:
            inranges.append((inpoint, len(line)))
        return inranges

    @staticmethod
    def commentLevel(line, ncomment=0):
        """
        Returns (ncomment, codestring, commentstring)
        'ncomment':
            +1: the line enters a multi-line comment.
            -1: the line exits a multi-line comment.
             0: the line both exits and enters a multi-line comment.
             0: the line neither enters nor exits a multi-line comment.
        'codestring' is any portion of the line that is not within a comment (could be empty)
        'commentstring' is any portion of the line that is within a comment (could be empty)
        """
        ml_in = "/*"
        ml_out = "*/"
        out_lines = []
        in_lines = []
        if ncomment > 0:
            line_in = line
            line_out = ""
        else:
            line_in = ""
            line_out = line
        if (ml_in not in line_out) and (ml_out not in line_in):
            return (ncomment, line_out, line_in)
        while (ml_in in line_out) or (ml_out in line_in):
            # Handle entering comments
            if ml_in in line_out:
                line_out, line_in = line_out.split(ml_in, maxsplit=1)
                out_lines.append(line_out)
                line_out = ""
                ncomment += 1
            # Handle exiting comments
            if ml_out in line_in:
                line_in, line_out= line_in.split(ml_out, maxsplit=1)
                in_lines.append(line_in)
                line_in = ""
                ncomment -= 1
        out_lines.append(line_out)
        in_lines.append(line_in)
        return (ncomment, "".join(out_lines), "".join(in_lines))

def testParser(argv):
    if len(argv) < 2:
        print("Need a string")
        return
    parser = Parser()
    from colorama import Fore, Back, Style
    def printRed(s, end="\n"):
        print(Fore.RED + s + Style.RESET_ALL, end=end)
    # Print tokens as they come
    cs = parser.parse(argv[1])
    for token in cs:
        tag, value = token
        if tag == TAG_KEYWORD:
            printRed(value, end="")
        else:
            print(value, end="")
    print()
    return

if __name__ == "__main__":
    import sys
    testParser(sys.argv)
