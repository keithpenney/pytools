#! python3

# ContextualString

# New paradigm
#   A single ContextualString can have multiple "Perspectives"
#   Each Perspective is a list of tags that apply over non-overlapping, contiguous regions
#   A Perspective's tag map should span the whole string (default map is a "generic" tag that spans the entire length)
#   A Perspective can contain as many types of tags as needed
#   And finally, let's see if we can enforce this rule:
#     Each tag can only exist in one Perspective (i.e. 1-to-1 mapping of perspective and tag type)

import colorama

# TODO:
#   I'm currently dynamically building the tagDict when needed.  If it turns out to be a critical resource, we can
#   instead maintain the tagDict as an object attribute and update in the Perspective.tag() method, but that's non-trivial.
class Perspective():
    TagGeneric = 0
    COLOR_DEFAULT=0
    COLOR_RED=1
    COLOR_BLACK=2
    COLOR_BLUE=3
    COLOR_CYAN=4
    COLOR_GREEN=5
    COLOR_WHITE=6
    COLOR_YELLOW=7
    COLOR_MAGENTA=8
    COLOR_LIGHTBLACK_EX=9
    COLOR_LIGHTBLUE_EX=10
    COLOR_LIGHTCYAN_EX=11
    COLOR_LIGHTGREEN_EX=12
    COLOR_LIGHTMAGENTA_EX=13
    COLOR_LIGHTRED_EX=14
    COLOR_LIGHTWHITE_EX=15
    COLOR_LIGHTYELLOW_EX=16
    _colorama_map = {
        COLOR_DEFAULT:"WHITE",
        COLOR_RED:"RED",
        COLOR_BLACK:"BLACK",
        COLOR_BLUE:"BLUE",
        COLOR_CYAN:"CYAN",
        COLOR_GREEN:"GREEN",
        COLOR_WHITE:"WHITE",
        COLOR_YELLOW:"YELLOW",
        COLOR_MAGENTA:"MAGENTA",
        COLOR_LIGHTBLACK_EX:"LIGHTBLACK_EX",
        COLOR_LIGHTBLUE_EX:"LIGHTBLUE_EX",
        COLOR_LIGHTCYAN_EX:"LIGHTCYAN_EX",
        COLOR_LIGHTGREEN_EX:"LIGHTGREEN_EX",
        COLOR_LIGHTMAGENTA_EX:"LIGHTMAGENTA_EX",
        COLOR_LIGHTRED_EX:"LIGHTRED_EX",
        COLOR_LIGHTWHITE_EX:"LIGHTWHITE_EX",
        COLOR_LIGHTYELLOW_EX:"LIGHTYELLOW_EX",
    }

    @classmethod
    def printColor(cls, ss, color=COLOR_DEFAULT, end="\n"):
        ccolor = getattr(colorama.Fore, cls._colorama_map.get(color))
        print(ccolor + ss + colorama.Style.RESET_ALL, end=end)
        return

    def __init__(self, stop, start=0, tagmap=[]):
        self.stop = stop
        self.start = start
        #self._tagDict = {self.TagGeneric : [(start, stop)]}
        self._map = [(start, stop, self.TagGeneric)]
        self._colorMap = {}
        self.applyTags(tagmap)

    def __str__(self):
        return str(self._map)

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return self._map.__len__()

    def setColorMap(self, colormap):
        for tag, color in colormap.items():
            if color <= self.COLOR_LIGHTYELLOW_EX:
                self._colorMap[tag] = color
            else:
                self._colorMap[tag] = self.COLOR_DEFAULT
        return

    def getColorMap(self):
        return self._colorMap

    def _mkTagDict(self):
        td = {}
        for start, stop, label in self._map:
            ranges = td.get(label, None)
            if ranges is not None:
                ranges.append((start, stop))
                td[label] = ranges
            else:
                td[label] = [(start, stop)]
        return td

    def printTags(self):
        td = self._mkTagDict()
        for tag, ranges in td.items():
            print("{}: {}".format(tag, ranges))

    def applyTags(self, tagmap):
        for start, stop, label in tagmap:
            self.tag(start, stop, label)

    def isComplete(self):
        # Check start boundary
        if self._map[0][0] != self.start:
            return False
        # Check stop boundary
        if self._map[-1][1] != self.stop:
            return False
        # Ensure contiguous tags
        for n in range(0, len(self._map)-1):
            start, stop, label = self._map[n]
            _start, _stop, _label = self._map[n+1]
            if _start != stop:
                return False
        return True

    def tag(self, start, stop, label, verbose=False):
        if (start > self.stop) or (stop > self.stop):
            raise Exception("Cannot add tag ({}, {}) outside the Perspective region ({}, {})".format(
                start, stop, self.start, self.stop))
        n = 0
        if verbose:
            print(f"Tagging: ({start}, {stop}, {label})")
        while n < len(self._map):
            _start, _stop, _label = self._map[n]
            if start >= _stop:
                # First, find the section where this applies
                n += 1
                continue
            if verbose:
                print(f"  Considering [{n}]: {self._map[n]}")
            deleted = False
            if start >= _start:
                # It starts here
                if verbose:
                    print(f"    Starts here ({start} >= {_start})")
                before = (_start, start, _label)
                # We'll need to replace this section, so remove it
                if before[1]-before[0] > 0:
                    if not deleted:
                        self._map[n] = before
                        deleted = True
                    else:
                        self._map.insert(n, before)
                    n += 1
                this = (start, stop, label)
                if this[1]-this[0] > 0:
                    if not deleted:
                        self._map[n] = this
                        deleted = True
                    else:
                        self._map.insert(n, this)
                    n += 1
            elif stop > _stop:
                # It clobbers this
                if verbose:
                    print(f"    Clobbers this {self._map[n]}: ({stop} > {_stop})")
                if not deleted:
                    del self._map[n]
                    deleted = True
            if stop <= _stop:
                # It ends here
                if verbose:
                    print(f"    Ends here ({stop} <= {_stop})")
                after = (stop, _stop, _label)
                if not deleted:
                    del self._map[n]
                    deleted = True
                if after[1]-after[0] > 0:
                    self._map.insert(n, after)
                    n += 1
                break
        return

    def getTagAtIndex(self, index):
        for tags in self._map:
            _start, _stop, _label = tags
            if (index >= _start) and (index < _stop):
                return _label
        return None

    def getTags(self):
        td = self._mkTagDict()
        return [x for x in td.keys()]

    def copy(self):
        psp = Perspective(self.stop, self.start)
        psp._map = self._map.copy()
        return psp

def test_Perspective_tag():
    # Preloaded tag map
    tagmap = [(50, 55, 123), (95, 100, 123)]
    pp = Perspective(100, tagmap=tagmap)
    print(pp)
    print(f"len(pp) = {len(pp)}. pp.isComplete() ? {pp.isComplete()}")
    pp.printTags()
    print("\nNow adding")
    pp.tag(0, 2, 500)
    pp.tag(2, 4, 501)
    pp.tag(4, 16, 502)
    # Leave a gap from 16-20
    pp.tag(20, 30, 500)
    pp.tag(30, 40, 504)
    pp.tag(50, 60, 501)
    print(pp)
    print(f"len(pp) = {len(pp)}. pp.isComplete() ? {pp.isComplete()}")
    pp.printTags()
    print("\nNow clobbering")
    pp.tag(10, 50, 600, verbose=True)
    print(pp)
    print(f"len(pp) = {len(pp)}. pp.isComplete() ? {pp.isComplete()}")
    pp.printTags()
    print("\nNow clobbering completely")
    pp.tag(0, 100, 700, verbose=True)
    print(pp)
    print(f"len(pp) = {len(pp)}. pp.isComplete() ? {pp.isComplete()}")
    return

class ContextualString():
    TagGeneric = Perspective.TagGeneric
    def __init__(self, s = ""):
        # Each entry of 'tags' is (start, stop, taglist)
        self._value = s
        _defaultPerspective = Perspective(len(self._value))
        self.perspectives = {
            "default": _defaultPerspective
        }
        self._activeGetPerspective = _defaultPerspective
        self._activeSetPerspective = _defaultPerspective

    def addPerspective(self, label):
        self.perspectives[label] = Perspective(len(self._value))
        self._activeGetPerspective = self.perspectives[label]
        self._activeSetPerspective = self.perspectives[label]
        return

    def copyPerspective(self, labelFrom, labelTo):
        psp = self.perspectives[labelFrom]
        self.perspectives[labelTo] = psp.copy()
        self._activeGetPerspective = psp
        self._activeSetPerspective = self.perspectives[labelTo]
        return

    def getPerspectives(self):
        return [x for x in self.perspectives.keys()]

    def setColorMap(self, colormap={}, perspective=None):
        if perspective is None:
            self._activeGetPerspective.setColorMap(colormap)
        else:
            psp = self.perspectives[perspective]
            psp.setColorMap(colormap)
        return

    def printColor(self):
        colorMap = self._activeGetPerspective.getColorMap()
        for token in self:
            tag = token.tag
            value = token.value
            color = colorMap.get(tag, None)
            if (color is None) or (color == self._activeGetPerspective.COLOR_DEFAULT):
                print(value, end="")
            else:
                self._activeGetPerspective.printColor(value, color, end="")
        print()
        return

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self._value

    def __add__(self, other):
        return ContextualString(self._value + other._value)

    def __getitem__(self, index):
        return self._value[index]

    def __sizeof__(self):
        return len(self._value)

    def join(self, lst):
        result = ContextualString()
        for n in range(len(lst)):
            ll = lst[n]
            result += ll
            if n < len(lst) - 1:
                result += self
        return result

    def tagToken(self, nToken, index, tag):
        """'index' can be int or slice()"""
        _map = self._activeSetPerspective._map
        if nToken >= len(_map):
            raise Exception("Token number {} out of range: [0,{}]".format(nToken, len(_map)-1))
        _start, _stop, _label = _map[nToken]
        if hasattr(index, "start"):
            start = index.start
            stop = index.stop
        else:
            start = index
            stop = index
        # index into token's range
        start += _start
        stop += _start
        sl = slice(start, stop)
        return self.tag(sl, tag)

    def tag(self, index, tag):
        """'index' can be int or slice()"""
        if hasattr(index, "start"):
            start = index.start
            stop = index.stop
        else:
            start = index
            stop = index
        self._activeSetPerspective.tag(start, stop, tag)
        return

    def setActivePerspective(self, label):
        psp = self.perspectives.get(label, None)
        if psp is not None:
            self._activeSetPerspective = psp
            self._activeGetPerspective = psp
        else:
            raise Exception(f"Invalid perspective label: {label}")
        return

    def setActiveSetPerspective(self, label):
        psp = self.perspectives.get(label, None)
        if psp is not None:
            self._activeSetPerspective = psp
        else:
            raise Exception(f"Invalid perspective label: {label}")
        return

    def setActiveGetPerspective(self, label):
        psp = self.perspectives.get(label, None)
        if psp is not None:
            self._activeGetPerspective = psp
        else:
            raise Exception(f"Invalid perspective label: {label}")
        return

    def __iter__(self):
        # We're an iterator now
        self._ntoken = 0
        return self

    def __next__(self):
        _map = self._activeGetPerspective._map
        if self._ntoken < len(_map):
            start, stop, label = _map[self._ntoken]
            self._ntoken += 1
            return StringToken(self._value[start:stop], label, start, stop)
        else:
            raise StopIteration

# Alias
class ConStr(ContextualString):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class StringToken():
    def __init__(self, value, tag, start, stop):
        self.value = value
        self.tag = tag
        self.start = start
        self.stop = stop

    def __str__(self):
        return f"Token([{self.start}, {self.stop}], tag = {self.tag}, value = {self.value})"

    def __repr__(self):
        return self.__str__()

def testConStr():
    sa = ConStr("String A")
    sb = ConStr("Item B")
    print(f"sa = {sa}")
    print(f"sb = {sb}")
    print(f"sa + sb = {sa + sb}")
    print(f"ConStr('.').join([sa, sb]) = {ConStr('.').join([sa, sb])}")
    print(f"sa[2] = {sa[2]}")
    print(f"sa[2:5] = {sa[2:5]}")
    return

def testCurses():
    print("Testing curses")
    import curses
    from curses import wrapper
    def foo(stdscr):
        #curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
        print("Curses?  What's up?")
        stdscr.addstr("Hello curses", curses.color_pair(1))
        stdscr.refresh()
        return
    wrapper(foo)
    return

def testColorama():
    from colorama import Fore, Back, Style
    def printRed(s, end="\n"):
        print(Fore.RED + "colorama" + Style.RESET_ALL, end=end)
    print("Hello ", end="")
    printRed("colorama", end="")
    print(". But does it work?")
    return

def testHighlighter(argv):
    if len(argv) < 2:
        print("Need a string")
        return
    keyword = "help"
    ss = argv[1]
    cs = ConStr(ss)
    cs.addPerspective("keywords")
    index = 0
    search = 0
    TAG_KEYWORD = 1
    while keyword in ss[search:]:
        index = ss.index(keyword, search)
        sl = slice(index, index+len(keyword))
        cs.tag(sl, TAG_KEYWORD)
        search = index + len(keyword)
    from colorama import Fore, Back, Style
    def printRed(s, end="\n"):
        print(Fore.RED + s + Style.RESET_ALL, end=end)
    # Print tokens as they come
    for token in cs:
        tag = token.tag
        value = token.value
        if tag == TAG_KEYWORD:
            printRed(value, end="")
        else:
            print(value, end="")
    print()
    return

if __name__ == "__main__":
    import sys
    #testConStr()
    #test_Perspective_tag()
    #testCurses()
    #testColorama()
    testHighlighter(sys.argv)
