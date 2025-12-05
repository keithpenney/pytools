#! Browse a (potentially very big) JSON file

import re
import json
import os

DEBUG_WALK = False

def strStruct(struct, depth=-1):
    sb = StructBrowser(struct)
    return sb.strToDepth(depth=depth, partSelect=None)


class StructBrowser():
    _class_string_ = "StructBrowser"
    def __init__(self, d):
        self._struct = d

    def _strToDepth(self, item, depth=0, indent=0):
        """RECURSIVE"""
        if depth == 0:
            return []
        l = []
        sindent = " "*indent
        if hasattr(item, "items"):
            _iter = item.items()
        else:
            _iter = enumerate(item)
        for key, val in _iter:
            if hasattr(val, 'keys'):
                l.append(f"{sindent}{key} : dict size {len(val)}")
                l.extend(self._strToDepth(val, depth-1, indent+2))
            elif hasattr(val, "__len__") and not hasattr(val, "lower"): # list
                l.append(f"{sindent}{key} : list size {len(val)}")
                l.extend(self._strToDepth(val, depth-1, indent+2))
            else:
                l.append(f"{sindent}{key} : {val}")
        return l

    def _get_class_string(self):
        return "StructBrowser()"

    def strToDepth(self, depth=0, partSelect=None):
        _d = self.selectPart(partSelect)
        l = [self._get_class_string()]
        l.extend(self._strToDepth(_d, depth, indent=2))
        return '\n'.join(l)

    def __str__(self):
        return self.strToDepth(1)

    def __repr__(self):
        return self.__str__()

    def selectPart(self, partSelect = None):
        _d = self._struct
        if partSelect is not None:
            parts = partSelect.split('.')
            for nselect in range(len(parts)):
                select = parts[nselect]
                matched = False
                if hasattr(_d, "items"):
                    # It's a dict
                    try:
                        _d = _d[select]
                        matched = True
                    except KeyError:
                        pass
                else:
                    # It's a list?
                    select = int(select)
                    try:
                        _d = _d[select]
                        matched = True
                    except IndexError:
                        pass
                if not matched:
                    raise Exception(f"Failed to match part-select at: {select}")
        return _d

    def search(self, target_key):
        """Search the dict structure for all keys that match 'target_key' and return as a nested dict."""
        hitlist = []
        def _do(trace, val):
            if len(trace) > 0:
                key = trace[-1]
                if hasattr(key, "lower"):
                    if re.search(target_key, key):
                        tstr = '.'.join([str(x) for x in trace[:-1]])
                        hitlist.append((tstr, key))
                if hasattr(val, "lower"):
                    if re.search(target_key, val):
                        tstr = '.'.join([str(x) for x in trace])
                        hitlist.append((tstr, val))
        self.walk(_do)
        return hitlist

    def walk(self, do = lambda trace, val : None, depth=-1):
        # I have to do this dumb thing where I actually
        # walk the generator and discard everything or
        # else the function exits early and doesn't walk?
        _iter = self._walk(self._struct, [], do, depth=depth)
        for x in _iter:
            pass
        return True

    def iter_walk(self, do = lambda trace, val : False, depth=-1):
        return self._walk(self._struct, [], do, depth=depth)

    @classmethod
    def _walk(cls, td, trace = [], do = lambda trace, val : False, depth=-1):
        """Depth-first recursive walk"""
        if depth == 0:
            return True
        rval = do(trace, td)
        if rval:
            yield td
        if hasattr(td, "items"):
            _iter = td.items()
        else:
            _iter = enumerate(td)
        for key, val in _iter:
            if DEBUG_WALK:
                if hasattr(val, "lower") or hasattr(val, "imag"):
                    vstr = str(val)
                else:
                    vstr = "[] or {}"
                print(f"{trace} {key} : {vstr}")
            trace.append(key)   # Add key
            if hasattr(val, 'items') or (hasattr(val, "__len__") and not hasattr(val, "lower")):
                yield from cls._walk(val, trace, do, depth=depth-1) # When this returns, we are done with this dict/list
            else:
                rval = do(trace, val)
                if rval:
                    yield val
            trace.pop() # So we can pop the key from the trace and continue the loop
        return True


class JSONBrowser(StructBrowser):
    def __init__(self, filename):
        self._filename = filename
        self.valid = self.load()

    def load(self):
        with open(self._filename, 'r') as fd:
            struct = json.load(fd)
        self._struct = struct
        return True

    def _get_class_string(self):
        return "JSONBrowser({})".format(os.path.split(self._filename)[-1])


def handleBrowse(args):
    filename = args.filename
    depth = int(args.depth)
    partSelect = args.select
    jb = JSONBrowser(filename)
    if not jb.valid:
        return False
    print(jb.strToDepth(depth, partSelect))
    return True


def handleSearch(args):
    filename = args.filename
    jb = JSONBrowser(filename)
    hitlist = jb.search(args.regex)
    for trace, val in hitlist:
        if hasattr(val, 'items'):
            vstr = f"dict len {len(val)}"
        elif (hasattr(val, "__len__") and not hasattr(val, "lower")):
            vstr = f"list len {len(val)}"
        else:
            vstr = str(val)
        print(f"{trace} : {vstr}")
    return


def doBrowse(argv):
    import argparse
    parser = argparse.ArgumentParser(description="Browse a JSON file interactively")
    parser.add_argument("filename", default=-1, help="The JSON file to parse.")
    parser.set_defaults(handler=lambda args: None)
    subparsers = parser.add_subparsers(help="Subcommands")
    sub_browse = subparsers.add_parser("browse", aliases=('b'))
    sub_browse.add_argument("depth", default=-1, help="The depth of a nested dict to show (-1 = All).", nargs='?')
    sub_browse.add_argument("-s", "--select", default=None, help="A hierarchical dereference to select and use as the top when printing.")
    sub_browse.set_defaults(handler=handleBrowse)
    sub_search = subparsers.add_parser("search", aliases=('s'))
    sub_search.add_argument("regex", help="Regex compared against everything hit during the walk")
    sub_search.set_defaults(handler=handleSearch)
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    import sys
    doBrowse(sys.argv)
