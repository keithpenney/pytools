#! Browse a (potentially very big) JSON file

import json
import os

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


def doBrowse(argv):
    import argparse
    parser = argparse.ArgumentParser(description="Browse a JSON file interactively")
    parser.add_argument('filename', default=-1, help="The JSON file to parse.")
    parser.add_argument('depth', default=-1, help="The depth of a nested dict to show (-1 = All).", nargs='?')
    parser.add_argument('-s', '--select', default=None, help="A hierarchical dereference to select and use as the top when printing.")
    args = parser.parse_args()
    filename = args.filename
    depth = int(args.depth)
    partSelect = args.select
    jp = JSONBrowser(filename)
    if not jp.valid:
        return False
    print(jp.strToDepth(depth, partSelect))
    return True


if __name__ == "__main__":
    import sys
    doBrowse(sys.argv)
