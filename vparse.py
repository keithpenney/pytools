#! /usr/bin/python3

# Very much WIP
# Parse a single Verilog file with no preprocessing

# Parse file rules:
#   1. Macros are defined by line breaks!  Need to handle them in initial reading stage
#       1a. Preserve the line break on these lines only
#   2. Keep track of context with respect to multi-line comments
#   3. Remove comments and store along with line start, stop

# Need Stateful Parsing:
#   State by scope
#       STATE_TOP           // top-level
#       STATE_IN_BEGIN      // waiting for 'end' keyword; needs to be nestable
#       others??

import os
import re

def _int(x):
    try:
        return int(x)
    except ValueError:
        pass
    try:
        return int(x, 16)
    except ValueError:
        return None

class ModuleInstantiation():
    def __init__(self, modname, instname, parammap, portmap):
        self.modname = modname
        self.instname = instname
        self.paramMap = parammap
        self.portMap = portmap

    def __str__(self):
        ll = [
            "ModuleInstantiation():",
            "  instance {} of module {}".format(self.instname, self.modname),
        ]
        if len(self.paramMap) > 0:
            ll.append("  Param Map")
            for pname, pval in self.paramMap:
                ll.append("    .{}({})".format(pname, pval))
        if len(self.portMap) > 0:
            ll.append("  Port Map")
            for pname, pval in self.portMap:
                ll.append("    .{}({})".format(pname, pval))
        return "\n".join(ll)

    def getPortConnection(self, portName=None, index=None):
        if portName is not None:
            for name, val in self.portMap:
                if portName == name:
                    return val
        if index is not None and index < len(self.portMap):
            return self.portMap[index][1]
        return None

    def getParamValue(self, paramName=None, index=None):
        if paramName is not None:
            for name, val in self.paramMap:
                if paramName == name:
                    return val
        if index is not None and index < len(self.paramMap):
            return self.paramMap[index][1]
        return None

class _ModuleInstantiationHelper():
    def __init__(self, modname, instname, parammap, portmap):
        self.modname = modname.strip()
        self.instname = instname.strip()
        self._parammap = parammap.strip()
        self._portmap = portmap.strip()
        self.parse()

    def get(self):
        return ModuleInstantiation(self.modname, self.instname, self.paramMap, self.portMap)

    def parse(self):
        self.paramMap = self._parseParamMap(self._parammap)
        self.portMap = self._parsePortMap(self._portmap)
        return

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        ll = [
            "_ModuleInstantiationHelper():",
            "  instance {} of module {}".format(self.instname, self.modname),
        ]
        if len(self.paramMap) > 0:
            ll.append("  Param Map")
            for pname, pval in self.paramMap:
                ll.append("    .{}({})".format(pname, pval))
        if len(self.portMap) > 0:
            ll.append("  Port Map")
            for pname, pval in self.portMap:
                ll.append("    .{}({})".format(pname, pval))
        return "\n".join(ll)

    @classmethod
    def _parseParamMap(cls, line):
        return cls._parsePortMap(line)

    @classmethod
    def _parsePortMap(cls, line):
        _map = []
        # Remove outer parens
        line = line.strip()
        if len(line) == 0:
            return _map
        if (line[0] == '(') and (line[-1] == ')'):
            line = line[1:-1]
        pdecs = cls._splitByCommas(line)
        for pdec in pdecs:
            name, value = cls._parsePortDec(pdec)
            _map.append((name, value))
        return _map

    @staticmethod
    def _parsePortDec(line):
        # Handle two types:
        #   1. Positional
        #       foo
        #       bar[4:0]
        #       8'ha5
        #   2. Named
        #       .foo(foo)
        #       .foo(bar[4:0])
        #       .foo(8'ha5)
        line = line.strip()
        restr = "\.([^(]+)\((.+)\)"
        _match = re.match(restr, line)
        if _match:
            # Named type
            name, value = _match.groups()
        else:
            # Positional type
            name = ""
            value = line
        return (name, value)

    @staticmethod
    def _splitByCommas(line):
        return VParser._splitByCommas(line)

class VParser():
    # = Regexps =
    # Hit on any Verilog module declaration
    reVModDecl = "module\s+([A-Za-z_][A-Za-z_0-9]*)\s+([^;]+);$"
    # Hit on any port declaration
    reVPortDecl = "^(input|output|inout)(\s+wire|\s+reg)?\s*(\[[^\]]+\])?\s+([A-Za-z0-9_]+)\s*,?$"
    # Hit on any Verilog integer literal
    reVLitHit = "([^\[\]:,.\s+-]+)"
    # Hit on any decimal (baseless) integer literal
    reVLitDec = "([\d_]+)?"
    # Hit on a Verilog integer literal with explicit base
    reVLitBase = "(\d+)?\s*('[hHbBdD])\s*([0-9a-fA-F_]+)"
    # Hit on any pair of Verilog indices
    reVIndices = "^\[?\s*([^\[\]:]+)\s*([+\-]?)\s*:\s*([^\[\]:]+)\s*\]?$"
    # Hit on any single Verilog index
    reVIndex = "^\[?\s*([^\[\]:]+)\s*\]?$"
    # Hit on a pair of Verilog indices as explicit integer literals
    reVIndicesLit = "^\[?\s*"+reVLitHit+"\s*([+\-]?)\s*:\s*"+reVLitHit+"\s*\]?$"
    # Hit on a single Verilog index as explicit integer literal
    reVIndexLit = "^\[?\s*"+reVLitHit+"\s*\]?$"

    # Helper values
    LINETYPE_PARAM = 0
    LINETYPE_PORT  = 0
    LINETYPE_MACRO = 1

    LINETYPE_UNKNOWN                = 2
    LINETYPE_MODULE_DECLARATION     = 3
    LINETYPE_MODULE_INSTANTIATION   = 4
    LINETYPE_INITIAL_BEGIN_BLOCK    = 5
    LINETYPE_INITIAL_LINE           = 6
    LINETYPE_ALWAYS_BEGIN_BLOCK     = 7
    LINETYPE_ALWAYS_LINE            = 8
    LINETYPE_ASSIGN                 = 9
    LINETYPE_PARAMETER              = 10
    LINETYPE_LOCALPARAM             = 11
    LINETYPE_GENERATE               = 12
    LINETYPE_SYSCALL                = 13
    LINETYPE_REG                    = 14
    LINETYPE_WIRE                   = 15

    def __init__(self, filename = ""):
        self.filename = filename
        self.valid = False
        self.modname = ""
        self.ports = []
        self.params = []
        self._parsed = False
        self._parsedModDecl = False
        # A list to contain any modules instantiated within the parent module
        self.instantiated_modules = []
        self.readFile()

    def readFile(self):
        if not os.path.exists(self.filename):
            print(f"{self.filename} does not exist")
            return
        nline = 0
        multi = False # In multi-line comment
        comments = {}
        with open(self.filename, 'r') as fd:
            procLine = ""
            ncomment = 0
            line = True
            while line:
                line = fd.readline()
                nline += 1
                # =========== Remove End-of-Line Comments ============
                segs = self._splitEndComment(line)
                codeLine = segs[0]
                if len(segs) > 1:
                    eolcomment = segs[1]
                    comments[nline] = commentLine
                if True:
                    # NEW-style
                    # =========== Handle Multi-Line Comments ============
                    ncomment, codeLine, commentLine = self.commentLevel(codeLine, ncomment)
                    if len(commentLine) > 0:
                        comments[nline] = commentLine
                    if len(codeLine) == 0:
                        continue
                    procLine += codeLine
                    linetype, iscomplete = self.isComplete(procLine)
                    if iscomplete:
                        print(f"processing (linetype {linetype}): {procLine}")
                        self.process(procLine, linetype)
                        procLine = ""
                    else:
                        #print(f"Not processing: {procLine}")
                        pass
                else:
                    # OLD-style
                    if multi:
                        comment, line, ends = self.endsComment(line)
                        if len(comment) > 0:
                            comments[nline] = comment
                        if ends:
                            multi = False
                    else:
                        line, comment, multi = self.hasComment(line)
                        if len(comment) > 0:
                            comments[nline] = comment
                        procLine += line
                        linetype, iscomplete = self.isComplete(procLine)
                        if iscomplete:
                            #print(f"processing: {procLine}")
                            self.process(procLine, linetype)
                            procLine = ""
        self._parsed = True
        #print("COMMENTS")
        #for nline, comment in comments.items():
        #    print(f"[{nline}] : {comment}", end='')
        #printSummary()
        self.valid = True
        return

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

    def getPorts(self):
        """Return list of (linetype, name, dirstr, rangeStart, rangeEnd), one for
        each port in the parsed module. If linetype is 1 (self.LINETYPE_MACRO), the
        'name' is actually a string of an entire macro line ('dirstr', 'rangeStart'
        and 'rangeEnd' are all None in this case).  If linetype is 0 (self.LINETYPE_PORT),
        it is a normal port where 'rangeStart' and 'rangeEnd' can be None, indicating
        a single-bit signal."""
        return self.ports

    def getParams(self):
        """Return list of (linetype, name, rspec, val), one for each parameter in the
        parsed module. If linetype is 1 (self.LINETYPE_MACRO), the 'name' is actually a
        string of an entire macro line ('rspec', 'val' are both None in this case).
        If linetype is 0 (self.LINETYPE_PARAM), it is a normal parameter where 'rspec'
        can be None, indicating a parameter with no bit range specified."""
        return self.params

    def getModules(self):
        """Return a list of ModuleInstantiation objects representing all the modules
        instantiated within the parent."""
        return self.instantiated_modules

    def printSummary(self):
        print(f"MODULE {self.modname}")
        for param in self.params:
            linetype, name, rspec, val = param
            if linetype == self.LINETYPE_MACRO:
                print(f"  Macro: {name}")
            else:
                if len(rspec) > 0:
                    rspec += " "
                print(f"  parameter {rspec}{name} = {val}")
        for port in self.ports:
            linetype, name, dirstr, rangeStart, rangeEnd = port
            if linetype == self.LINETYPE_MACRO:
                print(f"  Macro: {name}")
            else:
                if rangeStart is not None and rangeEnd is not None:
                    rstr = f" [{rangeStart}:{rangeEnd}] "
                else:
                    rstr = " "
                print(f"  {dirstr}{rstr}{name}")
        print(f"Instantiated modules:")
        for module in self.getModules():
            print(module)
        return

    @classmethod
    def isComplete(cls, line):
        """Return True if line is ready for processing.  This is tricky because there are
        so many top-level cases to handle."""
        # TODO
        # To handle:
        #   Module declaration
        #       Ends in semicolon
        #   initial and always blocks
        #       If 'begin' keyword; use context count to find matching 'end' keyword
        #       Otherwise ends with semicolon
        #   assign
        #       Ends in semicolon
        #   parameter
        #       Ends in semicolon
        #   localparam
        #       Ends in semicolon
        #   module instantiation
        #       Ends in semicolon
        #   generate
        #       Ends in endgenerate
        #   macros
        #       Ends after one line
        linetype = cls.lineType(line)
        semicolon_enders = (
            cls.LINETYPE_MODULE_DECLARATION,
            cls.LINETYPE_ASSIGN,
            cls.LINETYPE_ALWAYS_LINE,
            cls.LINETYPE_INITIAL_LINE,
            cls.LINETYPE_PARAMETER,
            cls.LINETYPE_LOCALPARAM,
            cls.LINETYPE_REG,
            cls.LINETYPE_WIRE,
            cls.LINETYPE_UNKNOWN,   # Let's discard unknown lines at semicolons too
        )
        if linetype in semicolon_enders:
            if line.strip().endswith(';'):
                return linetype, True
        elif linetype in (cls.LINETYPE_ALWAYS_BEGIN_BLOCK, cls.LINETYPE_INITIAL_BEGIN_BLOCK):
            if line.strip().endswith("end"):
                return linetype, True
        elif linetype == cls.LINETYPE_GENERATE:
            if line.strip().endswith("endgenerate"):
                return linetype, True
        elif linetype == cls.LINETYPE_MACRO:
            # Macros end after one line
            return linetype, True
        return linetype, False

    @classmethod
    def lineType(cls, line):
        # To handle:
        #   Module declaration
        #       Ends in semicolon
        #   initial and always blocks
        #       If 'begin' keyword; use context count to find matching 'end' keyword
        #       Otherwise ends with semicolon
        #   assign
        #       Ends in semicolon
        #   parameter
        #       Ends in semicolon
        #   localparam
        #       Ends in semicolon
        #   module instantiation
        #       Ends in semicolon
        #   generate
        #       Ends in endgenerate
        #   macros
        #       Ends after one line
        #   syscalls:
        #       Ends in semicolon
        # === Handle keyword blocks first (they're easiest)
        ls = line.strip()
        if ls.startswith("module"):
            return cls.LINETYPE_MODULE_DECLARATION
        elif ls.startswith("initial"):
            lss = ls.split()
            if len(lss) > 1 and lss[1].strip() == "begin":
                return cls.LINETYPE_INITIAL_BEGIN_BLOCK
            else:
                return cls.LINETYPE_INITIAL_LINE
        elif ls.startswith("always"):
            return cls._getLineTypeAlways(ls)
        elif ls.startswith("assign"):
            return cls.LINETYPE_ASSIGN
        elif ls.startswith("parameter"):
            return cls.LINETYPE_PARAMETER
        elif ls.startswith("localparam"):
            return cls.LINETYPE_LOCALPARAM
        elif ls.startswith("generate"):
            return cls.LINETYPE_GENERATE
        elif ls.startswith("reg"):
            return cls.LINETYPE_REG
        elif ls.startswith("wire"):
            return cls.LINETYPE_WIRE
        elif ls.startswith("`"):
            return cls.LINETYPE_MACRO
        # Need additional checks to confirm module instantiation (LINETYPE_MODULE_INSTANTIATION)
        return cls.LINETYPE_UNKNOWN

    def _getLineTypeAlways(cls, line):
        """Get the LINETYPE of a string 'line' starting with keyword 'always'"""
        segs = cls._splitBySpace(line.strip())
        # Handle two types:
        #   always @(posedge clk) [begin]
        #   always #10 [begin]
        if len(segs) == 0 or segs[0].strip() != "always":
            return cls.LINETYPE_UNKNOWN
        if len(segs) > 1:
            if segs[1].strip() == "begin":
                return cls.LINETYPE_ALWAYS_BEGIN_BLOCK
        if len(segs) > 2:
            if segs[2].strip() == "begin":
                return cls.LINETYPE_ALWAYS_BEGIN_BLOCK
        return cls.LINETYPE_ALWAYS_LINE

    @classmethod
    def parseModuleInstantiation(cls, line):
        # Formats:
        #   1: modname instname (....);
        #   2: modname #(....) instname (....);
        mtype = 1
        if '#' in line:
            mtype = 2
            pix = line.index('#')
            if line[pix+1] != '(':
                # Don't tolerate whitespace between # and (
                # Syntax error or non-module-instantiation
                print("Don't tolerate whitespace between # and (")
                return None
            modname = line[:pix]
            paramdec, line = cls._popParens(line[pix+1:])
        if '(' not in line:
            # Syntax error or non-module-instantiation
            print(f"No open parens in line {line}")
            return None
        pix = line.index('(')
        modinst = line[:pix]
        if mtype == 1:
            paramdec = ""
            try:
                modname, instname = modinst.split()[0:2]
            except ValueError:
                # Syntax error or non-module-instantiation
                print(f"Can't split {modinst}")
                return None
        else:
            instname = modinst
        portmap, trail = cls._popParens(line[pix:])
        #print(f"Pop portmap from: {line[pix:]}\n  Yields: {portmap}      {trail}")
        if trail.strip() != ';':
            # Syntax error or non-module-instantiation
            print(f"No trailing semicolon in {trail}")
            return None
        return _ModuleInstantiationHelper(modname, instname, paramdec, portmap).get()

    @staticmethod
    def _popParens(line):
        """Split off the first chunk of line contained within parentheses:
        E.g. if line == "(foo(), bar(bop())) lorem ipsum", then
            returns ("(foo(), bar(bop()))", " lorem ipsum")
        """
        if not '(' in line:
            return ("", line)
        #pix = line.index('(')
        plevel = 0
        escaped = False
        instring = False
        foundParen = False
        n = 0
        for n in range(len(line)):
            c = line[n]
            if c == '"':
                if not escaped:
                    if instring:
                        instring = False
                    else:
                        instring = True
                escaped = False
            elif c == '\\':
                if not escaped:
                    escaped = True
                else:
                    escaped = False
            elif c == '(':
                if not instring and not escaped:
                    foundParen = True
                    plevel += 1
                escaped = False
            elif c == ')':
                if not instring and not escaped:
                    plevel -= 1
                escaped = False
            if foundParen and plevel == 0:
                break
        return (line[:n+1], line[n+1:])

    @staticmethod
    def _splitBySpace(line):
        """Split line by whitespace, respecting parentheses and quotes"""
        segments = cls._splitByCharacters(line, (' ', '\n', '\t'))
        _segments = []
        # Filter out any empty strings
        for segment in segments:
            if len(segment) > 0:
                _segments.append(segment)
        return _segments

    @classmethod
    def _splitByCommas(cls, line):
        """Split line by commas, respecting parentheses and quotes"""
        return cls._splitByCharacters(line, (',',))

    @staticmethod
    def _splitByCharacters(line, splitchars=(',',)):
        """Split line by any chars in 'splitchars', respecting parentheses and quotes"""
        # Handle explicit simple case first
        inline = False
        for char in splitchars:
            if char in line:
                inline = True
        if not inline:
            return [line]
        ixs = []
        plevel = 0
        escaped = False
        instring = False
        for n in range(len(line)):
            c = line[n]
            if c == '"':
                if not escaped:
                    if instring:
                        instring = False
                    else:
                        instring = True
                escaped = False
            elif c == '\\':
                if not escaped:
                    escaped = True
                else:
                    escaped = False
            elif c == '(':
                if not instring and not escaped:
                    plevel += 1
                escaped = False
            elif c == ')':
                if not instring and not escaped:
                    plevel -= 1
                escaped = False
            elif c in splitchars:
                if not instring and not escaped and plevel == 0:
                    ixs.append(n)
                escaped = False
        segments = []
        ixlast = 0
        for n in range(len(ixs)):
            segments.append(line[ixlast:ixs[n]])
            ixlast = ixs[n]+1
        segments.append(line[ixlast:])
        return segments

    @classmethod
    def _splitEndComment(cls, line):
        return cls._splitByString(line, splitstr="//", respect_quotes=True, respect_parens=False, allow_escape=False, max_splits=1)

    @staticmethod
    def _splitByString(line, splitstr="", respect_quotes=True, respect_parens=True, allow_escape=True, max_splits=0):
        """Split line by string 'splitstr', respecting parentheses and quotes"""
        # Handle explicit simple case first
        sl = len(splitstr)
        if (sl == 0) or (len(line) < sl):
            return [line]
        chars = [c for c in line[:len(splitstr)]]
        ixs = []
        plevel = 0
        escaped = False
        instring = False
        for n in range(len(splitstr)-1, len(line)):
            # Shift register
            c = line[n]
            chars = chars[1:] + [c]
            if c == '"':
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
            elif "".join(chars) == splitstr:
                if not instring and not escaped and plevel == 0:
                    ixs.append(n)
                    if len(ixs) == max_splits:
                        break
                escaped = False
        segments = []
        ixlast = 0
        for n in range(len(ixs)):
            segments.append(line[ixlast:ixs[n]-(sl-1)])
            ixlast = ixs[n]+1
        segments.append(line[ixlast:])
        return segments

    def process(self, line, linetype=LINETYPE_UNKNOWN):
        if not self._parsedModDecl:
            print("parseModDecl")
            rval = self.parseModDecl(line)
            if rval:
                self._parsedModDecl = True
                self.modname, self.params, self.ports = rval
            print(f"rval = {rval}")
        if linetype in (self.LINETYPE_UNKNOWN, self.LINETYPE_MODULE_INSTANTIATION):
            print("parseModuleInstantiation")
            rval = self.parseModuleInstantiation(line)
            if rval is not None:
                self.instantiated_modules.append(rval)
        else:
            print(f"Skipping linetype {linetype}")
        # Do other stuff like:
        #   Capture parameters
        return

    @staticmethod
    def hasComment(line):
        # TODO - Handle the case of // and /* within strings
        """Split off any end-of-line comments in string 'line'.
        returns (line, comment, multi) where 'comment' can be empty string and 'multi' tells
        whether the comment begins a multi-line comment"""
        try:
            ix = line.index('//')
            #print(f"Splitting: {line[:ix]}...{line[ix:]}")
            return (line[:ix], line[ix:], False)
        except ValueError:
            pass
        try:
            ix = line.index('/*')
            #print(f"Multi-Splitting: {line[:ix]}...{line[ix:]}")
            return (line[:ix], line[ix:], True)
        except ValueError:
            #print(f"Not splitting: {line}")
            return (line, "", False)

    @staticmethod
    def endsComment(line):
        """Should be used when parsing has already encountered an open multi-line comment
        Look for end of multi-line comment and split string.
        Returns (comment, code, ends) where 'code' is anything after the comment ends
        and 'ends' is a boolean indicating whether the comment ending sequence was found."""
        try:
            ix = line.index('*/')
            return (line[:ix+2], line[ix+2:], True)
        except ValueError:
            return (line, '', False)

    @classmethod
    def parseModDecl(cls, line):
        """Note: line should include all text from 'module' to ending semicolon"""
        _match = re.search(cls.reVModDecl, line)
        if _match:
            groups = _match.groups()
            modname = groups[0]
            #print(f"modname = {modname}")
            rval = cls.parseModParamsAndPorts(groups[1])
            if rval is None:
                return False
            paramdec, portdec = rval
            if len(paramdec) > 0:
                params = cls.parseModParams(paramdec)
            else:
                params = ()
            if len(portdec) > 0:
                ports = cls.parseModPorts(portdec)
            else:
                ports = ()
            #print(f"  params = {params}")
            #print(f"  ports = {ports}")
            return (modname, params, ports)
        return None

    @classmethod
    def parseModParamsAndPorts(cls, line):
        """Note: line should be all of the test after 'module modname' up to (not including) the
        final semicolon."""
        split_ix = 0
        params = ""
        if line.startswith('#'):
            pcnt = 0 # Parenthesis count
            # Separate params portion
            for n in range(len(line)):
                c = line[n]
                if c == ')':
                    pcnt -= 1
                if pcnt > 0:
                    params += c
                else:
                    # If we are back at pcnt = 0 and have contents in params, split to ports
                    if len(params) > 0:
                        split_ix = n
                        break
                if c == '(':
                    pcnt += 1
        try:
            # Look for next opening parenthesis
            open_ix = split_ix + line[split_ix:].index('(')
            # Look for last closing parenthesis
            close_ix = line.rindex(')')
        except ValueError:
            print("No match")
            return None
        ports = line[open_ix+1:close_ix]
        return (params, ports)

    @classmethod
    def parseModParams(cls, line):
        """Note: line should be all parameter declarations separated by commas."""
        instr = False
        bcnt = 0 # Brace count for concatenations
        phasename = True # Alternate 'name' and 'val' phase
        params = []
        # Tricky parsing because parameter values can be strings which could in theory
        # include the word 'parameter' and commas and equals signs, etc.
        # Also need to handle preprocessor macros!
        namestr = ""
        valstr = ""
        rangespec = ""
        phaserange = False
        n = 0
        while n < len(line):
            c = line[n]
            if instr:
                if c == '"':
                    instr = False
                else:
                    pstr += line[n]
            else:
                # Skip the keyword
                if line[n:].startswith('parameter'):
                    n += len('parameter') - 1
                else:
                    if phasename:
                        # TODO - This is a bit hackish and will be triggered on any backtick ` in the 'name' area
                        if c == '`': # Capture macro
                            macrostr = cls.captureLine(line[n:])
                            n += len(macrostr)
                            params.append((cls.LINETYPE_MACRO, macrostr.strip(), None, None))
                        elif c == '[':
                            phaserange = True
                            rangespec += c
                        elif c == ']':
                            phaserange = False
                            rangespec += c
                        elif c == '=':
                            phasename = False
                        else:
                            if phaserange:
                                rangespec += c
                            else:
                                namestr += c
                    else:
                        # Look for commas outside of braces
                        if bcnt == 0:
                            if c == ',':
                                params.append((cls.LINETYPE_PARAM, namestr.strip(), rangespec.strip(), valstr.strip()))
                                namestr = ""
                                valstr = ""
                                rangespec = ""
                                phasename = True
                            else:
                                valstr += c
                        if c == '"':
                            instr = True
                        elif c == '{':
                            bcnt += 1
                        elif c == '}':
                            bcnt -= 1
            n += 1
        return params

    @classmethod
    def parseModPorts(cls, line):
        """Note: line should contain all port declaration text from after the first opening parenthesis
        up until and not including the final closing parenthesis."""
        # TODO This will break if there's a macro defined with multiple parameters in the ports block
        # This also breaks for two macros in a row (no commas)
        lines = line.split(',')
        ports = []
        n = 0
        _line = lines[n]
        while n < len(lines) - 1:
            #for _line in lines:
            if _line.strip().startswith('`'): # Capture macro
                ix = _line.index('`')
                macrostr = cls.captureLine(_line[ix:])
                ports.append((cls.LINETYPE_MACRO, macrostr.strip(), None, None, None))
                msl = len(macrostr)
                #print(f"--------- macrostr = |{macrostr}|")
                if ix+msl < len(_line): # More line content to process!
                    _line = _line[ix+msl:]
                    #print(f"Continuing with {_line}")
                    continue
            else:
                rval = cls.parseModPort(_line.strip())
                if rval is not None:
                    name, dirstr, rangeStart, rangeEnd = rval
                    ports.append((cls.LINETYPE_PORT, name, dirstr, rangeStart, rangeEnd))
                else:
                    raise SyntaxError(f"Unknown line in port declaration: {_line}")
            n += 1
            _line = lines[n]
        return ports

    @classmethod
    def parseModPort(cls, line):
        """Note: line should be a single port declaration with no trailing comma"""
        _match = re.match(cls.reVPortDecl, line)
        if _match:
            groups = _match.groups()
            dirstr, typestr, rangestr, name = groups
            # Enforce reserved keyword syntax rules
            if name in ('reg', 'wire'):
                return None
            rangeStart, rangeEnd = cls.splitRange(rangestr)
            return (name.strip(), dirstr.strip(), rangeStart, rangeEnd)
        return None

    @classmethod
    def splitRange(cls, rstr):
        """Split range string [start:end] into (start, end) where 'start' and 'end' are both
        strings (not evaluated)."""
        if rstr is None:
            return (None, None)
        if ':' not in rstr:
            return (None, None)
        try:
            # Look for opening bracket
            open_ix = rstr.index('[')
            # Look for closing bracket
            close_ix = rstr.rindex(']')
            rstr = rstr[open_ix+1:close_ix]
        except ValueError:
            # Range string is not enclosed in brackets
            return (None, None)
        return [x.strip() for x in rstr.split(':')]

    @staticmethod
    def captureLine(line):
        """Very simply just capture and return the first line (up to line break) in string 'line'"""
        _match = re.search("\r\n|\n", line)
        if _match:
            ix = _match.end()
            return line[:ix]
        return line

    @classmethod
    def captureMacro(cls, line):
        """Capture a preprocessor macro line from the start of 'line' and return it."""
        if not line.startswith('`'):
            print("No start")
            return None
        _match = re.match("`(ifdef|ifndef|if|define|undef|else|elsif|endif)", line)
        end = 0
        nexpr = 0
        if _match:
            kw = _match.groups()[0]
            print(f"match: kw = {kw}")
            end = _match.end()
            if kw.strip() in ('if', 'ifdef', 'elsif', 'undef'):
                nexpr = 1
            elif kw.strip() in ('define',):
                nexpr = 2
        else:
            print("No match")
        exprs = []
        ix = end + 1
        for n in range(nexpr):
            expr = cls.captureExpression(line[ix:])
            ix += len(expr)
        if ix == len(line)-1:
            ix = len(line)
        #print(f"returning \"{line[:ix]}\"")
        return line[:ix]

    @staticmethod
    def captureExpression(line):
        """Capture a string representing a single boolean line and return it unaltered."""
        # Go char-by-char with lookahead to next non-white char
        # Need to use syntax to understand when an expression ends
        # If we see an operator, we need to know the next non-white char to check for proper usage
        chatter = False
        def p(*args, **kwargs):
            if chatter:
                print(*args, **kwargs)
        p(f"line = {line}")
        def isw(s):
            _match = re.match("\s", s)
            if _match:
                return True
            return False
        def w(s):
            _match = re.search("\s", s)
            if _match:
                return _match.start()
            return None
        def nw(s):
            _match = re.search("\S", s)
            if _match:
                return _match.start()
            return None
        def bop(s):
            """Test if s starts with a binary operator"""
            _match = re.match("^\(|==|!=|<=|>=|<<|>>|[^>]>|[^<]<|\+|-|\*|/", s)
            p(f"bop? {s[:2]}", end='')
            if _match:
                p(f" Yes, {s[:_match.end()]}")
                return _match.end()
            p(" No")
            return None
        cplt = True # Binary operator complete
        n = nw(line)
        nonwhite = True
        while n < len(line):
            c = line[n]
            if nonwhite and isw(c):
                p(f"Found white at {n}")
                nonwhite = False
                # Found whitespace. Need to look ahead to next nonwhite
                nn = nw(line[n:])
                if nn is not None:
                    n += nn
                    p(f"Next nonwhite at {n}")
                    nonwhite = True
                    # If cplt, look ahead for another binary operator
                    if cplt:
                        p(f"[{line[:n]}] Complete - looking ahead for a binary operator")
                        nn = bop(line[n:])
                        if nn is None:
                            p(f"Next nonwhite ({line[n]}) is not binary operator. We're done")
                            # We're done
                            break
                        else:
                            p(f"Another binary operator found: {line[n:n+nn+1]}")
                            # Another binary operator
                            cplt = False
                            n += nn
                    else:
                        p(f"[{line[:n]}] Incomplete. Looking for second arg of binary operator")
                        # Else, consume the next word
                        nn = w(line[n:])
                        if nn is not None:
                            p(f"Consuming {line[n:n+nn+1]}. Now complete.")
                            n += nn
                            cplt = True
                        else:
                            p("Cannot find anymore whitespace")
                            # I guess we consumed the whole thing
                            n = len(line)
                            break
                    n -= 1 # Decrement for loop increment
                else:
                    # No additional non-whitespace found
                    n = len(line)
                    break
            elif nw(c):
                nonwhite = True
            n += 1
        if n < len(line):
            p(f"Split: {line[:n]}...{line[n:]}")
        else:
            p("Consumed")
        return line[:n]

    @staticmethod
    def splitBoolean(line):
        """Split line into boolean (A, cmp, B) where 'cmp' is one of the binary boolean operators:
            ==, >, <, >=, <=, !=
        """
        # Be careful! A and B can include bitshifts << and >>
        # Guard against '<>' (whatever that might be)
        ix0 = -1
        ix1 = -1
        n = 0
        while n < len(line)-1:
            cx = line[n:n+2]
            if cx in ('==', '>=', '<=', '!='):
                ix0 = n-1
                ix1 = n+2
                break
            elif cx[0] in ('<', '>'):
                if cx[1] == cx[0]: # >> and <<
                    n += 1 # Skip the next char
                else:
                    ix0 = n
                    ix1 = n+1
                    break
            n += 1
        arg_cmp = ''
        arg_b = ''
        if ix0 == -1:
            arg_a = line
        else:
            arg_a = line[:ix0].strip()
            arg_cmp = line[ix0:ix1].strip()
            arg_b = line[ix1:].strip()
        return (arg_a, arg_cmp, arg_b)

    def parseLiteral(string):
        """Parse verilog integer literal (i.e. 1'b0, 8'hcc, 'd100, etc.) and return (size, base, value)"""
        restr = reVLitDec
        _match = re.match("^" + restr+ "$", string)
        if _match:
            val = _match.groups()[0]
            try:
                val = _int(val.replace('_',''))
            except ValueError:
                return None
            return (None, None, val)
        # Next try a Verilog-style literal with specified base
        _match = re.match("^" + reVLitBase + "$", string)
        if _match:
            groups = _match.groups()
            size, base, val = groups
            #print(f"size = {size}, base = {base}, val = {val}")
            if size not in (None, ""):
                size = _int(size)
                if size < 1: # Invalid size
                    return None
            else:
                size = None
            if base not in (None, ""):
                base = base.lower()
                if base[-1] == 'h':
                    nbase = 16
                elif base[-1] == 'b':
                    nbase = 2
                elif base[-1] == 'd':
                    nbase = 10
                try:
                    val = int(val, nbase)
                except ValueError:
                    return None
            else:
                base = None
                # The first digit of 
                val = int(size+val)
            return (size, base, val)
        return None

def testfunction(testDict, fn):
    failCount = 0
    num = 0
    for key, val in testDict.items():
        #print(f"Testing: {key}")
        result = fn(key)
        if result != val:
            failCount += 1
            print(f"FAILED on string ({num}): {key}")
            if True:
                print(f"    Target: {val}")
                print(f"    Result: {result}")
        num += 1
    return failCount

def test_VParser_parseModDecl():
    modGood1 = """module foo (input clk, output d, output [3:0] status);"""
    modGood2 = """module foo #(parameter CW = 6, parameter DW = 8) (input clk, output d, output [3:0] status);"""
    def parseModDecl(*args, **kwargs):
        if VParser.parseModDecl(*args, **kwargs):
            return True
        return False
    d = {
        modGood1 : True,
        modGood2 : True,
    }
    return testfunction(d, parseModDecl)

def test_VParser_parseModPort():
    d = {
        # Goodies
        "input clk": ('clk', 'input', None, None),
        "output d": ('d', 'output', None, None),
        "input clk,": ('clk', 'input', None, None), # Trailing commas ok
        "output data": ('data', 'output', None, None),
        "input wire clk": ('clk', 'input', None, None),
        "input reg clk": ('clk', 'input', None, None),
        "input [7:0] clk": ('clk', 'input', '7', '0'),
        "input wire [7:0] clk": ('clk', 'input', '7', '0'),
        "input [1<<CW:0] tdata": ('tdata', 'input', '1<<CW', '0'),
        "output [AW-1:0] taddr": ('taddr', 'output', 'AW-1', '0'),
        # Baddies
        "inputclk": None, # Missing whitespace
        "inputwire clk": None, # Missing whitespace
        "inputreg clk": None, # Missing whitespace
        "input wire": None, # Illegal syntax
        "input reg": None, # Illegal syntax
        "inpuf clk": None, # keyword typo on direction
        "input wirf clk": None, # keyword typo on optional type
    }
    return testfunction(d, VParser.parseModPort)

def test_VParser_captureExpression():
    d = {
        # Goodies
        "foo": "foo",
        "foo<<1": "foo<<1",
        "foo<2 ": "foo<2 ",
        "foo<2 hello": "foo<2 ",
        "foo==2 hello": "foo==2 ",
        "foo==bar hello": "foo==bar ",
        "test>>4==1'b0 hello": "test>>4==1'b0 ",
        "test >> 4 == 1'b0 hello": "test >> 4 == 1'b0 ",
    }
    return testfunction(d, VParser.captureExpression)

def test_VParser_captureMacro():
    d = {
        # Goodies
        "`if foo" : "`if foo",
        "`if foo input data" : "`if foo ",
        "`if foo==1 input data" : "`if foo==1 ",
        "`if foo == 1 input data" : "`if foo == 1 ",
        "`if foo >> 2 == 4'h0 input data" : "`if foo >> 2 == 4'h0 ",
        "`if (foo * 6) >> 2 == 4'h0 input data" : "`if (foo * 6) >> 2 == 4'h0 ",
        "`ifdef SIMULATE output SCL_o" : "`ifdef SIMULATE ",
        "`elsif foo == 1 input data" : "`elsif foo == 1 ",
        "`define bar(x) x + 1 input data" : "`define bar(x) x + 1 ",
        "`define SIMULATE output data" : "`define SIMULATE ",
        "`endif" : "`endif",
        "`endif input data" : "`endif ",
    }
    return testfunction(d, VParser.captureMacro)

def test_VParser_splitBoolean():
    d = {
        # Goodies
        "foo": ("foo", "", ""),
        "foo > bar": ("foo", ">", "bar"),
        "foo < bar": ("foo", "<", "bar"),
        "foo == bar": ("foo", "==", "bar"),
        "foo >= bar": ("foo", ">=", "bar"),
        "foo <= bar": ("foo", "<=", "bar"),
        "foo != bar": ("foo", "!=", "bar"),
        "foo<<4": ("foo<<4", "", ""),
        "foo<<CW": ("foo<<CW", "", ""),
        "foo << CW": ("foo << CW", "", ""),
        "foo >> x": ("foo >> x", "", ""),
        "(1 + 2) << 8": ("(1 + 2) << 8", "", ""),
        "foo << CW < 256": ("foo << CW", "<", "256"),
        "foo >> x != 0": ("foo >> x", "!=", "0"),
        # Baddies
        "": ('', '', ''),
    }
    return testfunction(d, VParser.splitBoolean)

def test_VParser_hasComment():
    # Returns (line, comment, multi)
    d = {
        "hello": ("hello", "", False),
        "hello world": ("hello world", "", False),
        "hello // world": ("hello ", "// world", False),
        "hello /* world": ("hello ", "/* world", True),
    }
    return testfunction(d, VParser.hasComment)

def test_VParser_endsComment():
    # Returns (comment, code, ends)
    d = {
        "foo": ("foo", "", False),
        "foo */": ("foo */", "", True),
        "foo */ hello": ("foo */", " hello", True),
    }
    return testfunction(d, VParser.endsComment)

def test_VParser_captureLine():
    d = {
        "foo" : "foo",
        "foo\n" : "foo\n",
        "foo\nbar" : "foo\n",
        "foo\nbar\nbaz" : "foo\n",
        "foo\r\nbop" : "foo\r\n",
    }
    return testfunction(d, VParser.captureLine)

def test_VParser_popParens():
    d = {
        "foo" : ("", "foo"),
        "foo (bar)" : ("foo (bar)", ""),
        "(foo) bar" : ("(foo)", " bar"),
        "(foo(), bar(bop())) baz" : ("(foo(), bar(bop()))", " baz"),
        "(foo(), bar(bop())) baz (fwip)" : ("(foo(), bar(bop()))", " baz (fwip)"),
        "\"(foo)\"(bop) bar" : ("\"(foo)\"(bop)", " bar"),
    }
    return testfunction(d, VParser._popParens)

def test_VParser_splitByCommas():
    d = {
        "foo" : ["foo"],
        "foo, bar" : ["foo", " bar"],
        "foo, bar,  baz" : ["foo", " bar", "  baz"],
        "foo(,), bar,  baz" : ["foo(,)", " bar", "  baz"],
        "foo\",\", bar,  baz" : ["foo\",\"", " bar", "  baz"],
    }
    return testfunction(d, VParser._splitByCommas)

def test__ModuleInstantiationHelper_parseParamMap():
    d = {
        "(foo)" : [("", "foo")],
        "(foo, bar)" : [("", "foo"), ("", "bar")],
        "(foo, bar, 1'b0)" : [("", "foo"), ("", "bar"), ("", "1'b0")],
        "(\"true\", 100)" : [("", "\"true\""), ("", "100")],
        "(.FOO(foo), .BAR(bar))" : [("FOO", "foo"), ("BAR", "bar")],
        "(.FOO(\"true\"), .BAR(100))" : [("FOO", "\"true\""), ("BAR", "100")],
    }
    return testfunction(d, _ModuleInstantiationHelper._parseParamMap)

def test__ModuleInstantiationHelper_parsePortMap():
    d = {
        "(foo)" : [("", "foo")],
        "(foo, bar)" : [("", "foo"), ("", "bar")],
        "(foo, bar, 1'b0)" : [("", "foo"), ("", "bar"), ("", "1'b0")],
        "(.FOO(foo), .BAR(bar))" : [("FOO", "foo"), ("BAR", "bar")],
        "(.foo(baz[4:0]), .bar(100))" : [("foo", "baz[4:0]"), ("bar", "100")],
    }
    return testfunction(d, _ModuleInstantiationHelper._parsePortMap)

def test_VParser_parseModuleInstantiation():
    ss = [
        "foo #(.bar(1'b0), .baz(\"true\")) foo_i (.clk(testclk), .din(data[3:0]));",
        "ls_mod #(\n  .bar(1'b0),\n  .baz(\"true\")\n) ls_mod_i (\n  .clk(testclk),\n  .din(data[3:0])\n);",
        "larf_module_fancy lmf_i (\n  .clk(clk),\n  .addr(lb_addr),\n  .dout(lmf_dout)\n);",
        "boof boof_i (\n  clk,\n  lb_addr,\n  lmf_dout\n);",
    ]
    for _s in ss:
        vmod = VParser.parseModuleInstantiation(_s)
        print(vmod)
    return

# TODO needs update
def test_getSize():
    d = {
        "wire [3:0] selections;" : 4,
        "wire selections;" : 1,
        "wire [31:0] selections;" : 32,
        "wire [31:0] selections" : None,
        "reg [31:0] selections;" : None,
        "wire [31:0] foo;" : None,
        "assign selections[16] = foo[0];" : None,
    }
    return testfunction(d, getSize)

# TODO needs update
def test_splitIndices():
    d = {
        "0"   : (0, 0),
        "7"   : (7, 7),
        "[7]" : (7, 7),
        "1:2" : (1, 2),
        "2:1" : (1, 2),
        "[2:1]" : (1, 2),
        "[ 2 : 1 ]" : (1, 2),
        "[0:0]" : (0, 0),
        "0:0" : (0, 0),
        "4+:8" : (4, 11),
        "15-:8" : (8, 15),
        "15:x" : (None, None),
        "15 8" : (None, None),
        "7:-0" : (None, None),
        "7:+0" : (None, None),
    }
    return testfunction(d, splitIndices)

# TODO needs update
def test_parseLiteral():
    d = {
        "0" : (None, None, 0),
        "1" : (None, None, 1),
        "'hff" : (None, "'h", 0xff),
        "1'b0" : (1, "'b", 0),
        "1'B1" : (1, "'b", 1),
        "4'hf" : (4,"'h", 0xf),
        "16 'H 1F" : (16,"'h", 0x1f),
        "10 'd100" : (10,"'d", 100),
        "10' d100" : None,
        "4'df" : None,
        "1'b2" : None,
        "0'b0" : None,
    }
    return testfunction(d, parseLiteral)

# TODO needs update
def test_getSignalRange():
    d = {
        "foo" : ("foo", None, None),
        "foo[0:0]" : ("foo", 0, 0),
        "foo[7:0]" : ("foo", 0, 7),
        "bar[7:0]" : ("bar", 0, 7),
        "bar[7-:8]" : ("bar", 0, 7),
        "bar[15-:8]" : ("bar", 8, 15),
        "bar[10+:4]" : ("bar", 10, 13),
        "bar [7:0]" : None,
        "1'b0" : None,
    }
    return testfunction(d, getSignalRange)

# TODO needs update
def test_getAssign():
    d = {
        # (signal, solo, vIndexLo, vIndexHi, sIndexLo, sIndexHi)
        "assign selections[0] = 1'b0;" : ("0", True, 0, 0, None, None),
        "assign selections[0] = 1'b1;" : ("1", True, 0, 0, None, None),
        "assign selections[16] = foo[0];" : ("foo", False, 16, 16, 0, 0),
        "assign selections[0]=foo;" : ("foo", True, 0, 0, None, None),
        "assign selections[0] = foo" : None,
        "assign selections[0] = foo[];" : None,
        "assign selections[11:10] = foo[1:0];" : ("foo", False, 10, 11, 0, 1),
        "assign selections[16:19] = eth_rxd[0:3];" : ("eth_rxd", False, 16, 19, 0, 3),
        "assign selections[16:19] = eth_rxd;" : ("eth_rxd", True, 16, 19, None, None),
        # Note that this function does not check for mismatched lengths
        "assign selections[10] = bar[7:0];" : ("bar", False, 10, 10, 0, 7),
        "assign selections[10:] = bar[7:0];" : None,
        "assign _selections[10] = bar;" : None,
        "assign selections = bar;" : None, # Maybe someday support this
    }
    return testfunction(d, lambda x: getAssign(x, vector="selections"))

# TODO needs update
def test_parseAssignment():
    global parseDict
    parseDict = {
        0  : "foo",
        1  : "bar",
        2  : "0",
        3  : "1",
        4  : "baz[0]",
        5  : "baz[1]",
        6  : "baz[2]",
        7  : "baz[3]",
        8  : "baz[4]",
        9  : "baz[5]",
        10 : "baz[6]",
        11 : "baz[7]",
        12 : "baz[8]",
        13 : "baz[9]",
        14 : "baz[10]",
        15 : "baz[11]",
    }
    d = {
        # ==== Goodies ====
        # Type 0: Single channel index = single signal index
        "0=4" : [(0, 4)],
        # Type 1: Single index = wire signal
        "0=foo" : [(0, 0)],
        # Type 1: Single index = wire signal with whitespace
        " 8 = bar " : [(8, 1)],
        # Type 2: Single index = an element of an array
        "1=baz[3]" : [(1, 7)],
        # Type 3: Range channel indices = same signal index
        "10:8=0xf" : [(8, 0xf), (9, 0xf), (10, 0xf)],
        # Type 4: Range indicies = same signal
        "[0:1]=foo" : [(0, 0), (1, 0)],
        # Type 4: Range indicies (no brackets) = same signal
        "0:1=foo" : [(0, 0), (1, 0)],
        # Type 4: Range indicies (no brackets) = same signal with whitespace
        " 0:1 = bar" : [(0, 1), (1, 1)],
        # Type 5: Range indicies = same element of an array
        "[0:1]=baz[3]" : [(0, 7), (1, 7)],
        # Type 6: Range indices = range of an array
        "[0:1]=baz[2:3]" : [(0, 6), (1, 7)],
        # Type 6: Range idicies (no brackets) = range of an array
        "0:1=baz[2:3]" : [(0, 6), (1, 7)],
        # Type 6: Range indices (hex) = range of an array (hex)
        "[0xa:0x9]=baz[0xb:0xa]" : [(0x9, 14), (0xa, 15)],
        # Type 7: Range channel indices = static bit map
        "9:6=4'ha" : [(6, 2), (7, 3), (8, 2), (9, 3)],
        # Type 7: Range channel indices = static bit map
        "9:6='ha" : [(6, 2), (7, 3), (8, 2), (9, 3)],
        # ==== Baddies ====
        # No '=' or RHS
        "0" : None,
        # No '=' or LHS
        "foo" : None,
        # Using '-' instead of '='
        "0-foo" : None,
        # Unknown character
        "0=-foo" : None,
        # Unknown character
        "0=+foo" : None,
        # Unknown character
        "9+=foo" : None,
        # Unknown character
        "4=foo$" : None,
        # Unknown character
        "3=#foo" : None,
        # Attempting to index RHS without brackets
        "1=foo2:3" : None,
    }
    return testfunction(d, parseAssignment)

# TODO needs update
def doTests():
    todo = (
        # Name,             fn,                         do
        ("parseModDecl",    test_VParser_parseModDecl,  0),
        ("parseModPort",    test_VParser_parseModPort,  0),
        ("captureExpression", test_VParser_captureExpression,0),
        ("captureMacro",    test_VParser_captureMacro,  0),
        ("splitBoolean",    test_VParser_splitBoolean,  0),
        ("hasComment",      test_VParser_hasComment,    0),
        ("endsComment",     test_VParser_endsComment,   0),
        ("captureLine",     test_VParser_captureLine,   0),
        ("_popParens",      test_VParser_popParens,     0),
        ("_splitByCommas",  test_VParser_splitByCommas, 0),
        ("_parseParamMap",  test__ModuleInstantiationHelper_parseParamMap, 0),
        ("_parsePortMap",   test__ModuleInstantiationHelper_parsePortMap, 0),
        ("getSize",         test_getSize,               0),
        ("parseLiteral",    test_parseLiteral,          0),
        ("getAssign",       test_getAssign,             0),
        ("splitIndices",    test_splitIndices,          0),
        ("getSignalRange",  test_getSignalRange,        0),
        ("parseAssignment", test_parseAssignment,       0),
    )
    failcnt = 0
    testsRun = 0
    for name, fn, do in todo:
        if do:
            print(f":::: {name:^20s} ::::")
            cnt = fn()
            if cnt > 0:
                print(f"{name} failed {cnt} times")
            failcnt += cnt
            testsRun += 1
    if testsRun == len(todo):
        summary = "All tests run"
    else:
        summary = "{}/{} tests run".format(testsRun, len(todo))
    if failcnt > 0:
        print(f"FAIL : {summary}")
    else:
        print(f"PASS : {summary}")
    return

def test_VParser_splitEndComment():
    lines = [
        "hello there // this is a comment",
        "I don't have a comment",
        "// I'm entirely a comment!",
        "This string \"this one here // has a comment\" has a comment // but you should ignore it!",
    ]
    for line in lines:
        segs = VParser._splitEndComment(line)
        print(f"line")
        for seg in segs:
            print(f"  {seg}")

def doVParserReadFile(argv):
    USAGE = f"python3 {argv[0]} filename"
    if len(argv) < 2:
        print(USAGE)
        return False
    filename = argv[1]
    vp = VParser(filename)
    vp.readFile()
    return True

def _decomma(s):
    """Remove the comma from the end of a port instantiation string."""
    if ',' in s:
        b, e, = s.split(',')
        return b+e
    else:
        return s

def makeWires(ports, params=[], skip=[]):
    l = []
    if params is None:
        params = []
    for param in params:
        linetype, name, rspec, val = param
        if linetype == VParser.LINETYPE_MACRO:
            #print(f"  Macro: {name}")
            l.append(f"{name}")
        else:
            #print(f"  parameter {name} = {val}")
            l.append(f"localparam {name} = {val};")
    #for portname,vdict in ports.items():
    for port in ports:
        linetype, portname, pdir, rangeStart, rangeEnd = port
        if portname in skip:
            continue
        if pdir == 'input':
            ptype = 'reg'
        else:
            ptype = 'wire'
        if rangeStart is not None and rangeEnd is not None:
            sel = f" [{rangeStart}:{rangeEnd}]"
        else:
            sel = ''
        l.append(f'{ptype}{sel} {portname};')
    return '\n'.join(l)

def makeInstantiator(name, ports, params=[]):
    if params is not None and len(params) > 0:
        p = ["#("]
        for param in params:
            linetype, pname, rspec, val = param
            if linetype == VParser.LINETYPE_MACRO:
                #print(f"  Macro: {name}")
                p.append(f"{pname}")
            else:
                #print(f"  parameter {name} = {val}")
                p.append(f"  .{pname}({pname}),")
        # Hack. Remove the comma from the last entry
        p[-1] = _decomma(p[-1])
        p.append(")")
        pstr = " " + '\n'.join(p) + " "
    else:
        pstr = " "
    l = [f'{name}{pstr}{name}_i (\n']
    #for portname,vdict in ports.items():
    for port in ports:
        linetype, pname, pdir, rangeStart, rangeEnd = port
        if linetype == VParser.LINETYPE_MACRO:
            l.append('{}\n'.format(pname))
        else:
            if rangeStart is not None and rangeEnd is not None:
                pw = f" [{rangeStart}:{rangeEnd}]"
            else:
                pw = ''
            l.append('  .{0}({0}), // {1}{2}\n'.format(pname, pdir, pw))
    # Hack. Remove the comma from the last entry
    l[-1] = _decomma(l[-1])
    l.append(');')
    return ''.join(l)

def instantiate(filename):
    vp = VParser(filename)
    if not vp.valid:
        return False
    #print(vp.strToDepth(3))
    if vp._parsedModDecl:
        print(makeWires(vp.getPorts(), vp.getParams()))
        print(makeInstantiator(vp.modname, vp.getPorts(), vp.getParams()))
    return True

def makeTemplate(filename):
    vp = VParser(filename)
    if not vp.valid:
        return False
    name = vp.modname
    ports = vp.getPorts()
    params = vp.getParams()
    # find clkname
    clkname = 'clk'
    #for portname,vdict in ports.items():
    for port in ports:
        linetype, portname, pdir, rangeStart, rangeEnd = port
        if rangeStart is None or rangeEnd is None:
            # pw = 1
            if pdir == 'input':
                if re.match(reClk, 'clk'):
                    clkname = portname
                    break
    sl = (
        "`timescale 1ns/1ns",
        "",
        f"module {name}_tb;",
        "",
        # Clock
        f"reg {clkname}=1'b0;",
        f"always #5 {clkname} <= ~{clkname};",
        "",
        # Dumpfile
        "// VCD dump file for gtkwave",
        "reg [32*8-1:0] dumpfile; // 32-chars max",
        "initial begin",
        "  if (! $value$plusargs(\"df=%s\", dumpfile)) begin",
        "    $display(\"No dumpfile name supplied; Wave data will not be saved.\");",
        "  end else begin",
        "    $dumpfile(dumpfile);",
        "    $dumpvars;",
        "  end",
        "end",
        "",
        # Timeout
        ""
        "localparam TOW = 12;",
        "localparam TOSET = {TOW{1'b1}};",
        "reg [TOW-1:0] timeout=0;",
        f"always @(posedge {clkname}) begin",
        "  if (timeout > 0) timeout <= timeout - 1;",
        "end",
        "wire to = ~(|timeout);",
        ""
    )
    for s in sl:
        print(s)
    if ports is not None:
            print(makeWires(ports, params, skip=[clkname]))
            print(makeInstantiator(name, ports, params))
    sl = (
        "",
        "// =========== Stimulus =============",
        "initial begin",
        "  $display(\"Done\");",
        "  $finish(0);",
        "end",
        "",
        "endmodule"
    )
    for s in sl:
        print(s)
    return

def doTestbench(argv):
    USAGE = "python3 {} filename.v".format(argv[0])
    if len(argv) < 2:
        print(USAGE)
        return 1
    filename = argv[1]
    makeTemplate(filename)
    return

def doInstantiate(argv):
    USAGE = "python3 {} filename.v".format(argv[0])
    if len(argv) < 2:
        print(USAGE)
        return 1
    filename = argv[1]
    if instantiate(filename):
        return 0
    else:
        return 1

def doSubModules(args):
    vp = VParser(args.filename)
    mods = vp.getModules()
    print("{} modules instantiated".format(len(mods)))
    print(f"args.modname = {args.modname}")
    if args.modname in ("list", "*"):
        for mod in mods:
            print(f"mod = {mod}")
    else:
        for mod in mods:
            if fnmatch.fnmatch(args.modname, mod.modname):
                print(mod)
    return True

def doParse():
    import argparse
    parser = argparse.ArgumentParser(description="Hand-rolled Verilog parser")
    parser.set_defaults(handler=lambda args: parser.print_help())
    parser.add_argument('filename', default=None, help="The Verilog file to parse.")
    subparsers = parser.add_subparsers(help="Subcommands")
    # ==== modules ====
    parserModules = subparsers.add_parser("modules", help="Parse and query modules.")
    parserModules.add_argument('modname', default=None, help="The name of the module you're interested in.")
    parserModules.set_defaults(handler=doSubModules)
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    import sys
    #doTests()
    #doVParserReadFile(sys.argv)
    #sys.exit(doInstantiate(sys.argv))
    #test_VParser_parseModuleInstantiation()
    doParse()
    #test_VParser_splitEndComment()
