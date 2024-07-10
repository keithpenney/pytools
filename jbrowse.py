#! Browse a (potentially very big) JSON file

import json
import os

def strDict(_dict, depth=-1):
    def _strToDepth(_dict, depth=0, indent=0):
        """RECURSIVE"""
        if depth == 0:
            return []
        l = []
        sindent = " "*indent
        for key, val in _dict.items():
            if hasattr(val, 'keys'):
                l.append(f"{sindent}{key} : dict size {len(val)}")
                l.extend(_strToDepth(val, depth-1, indent+2))
            else:
                l.append(f"{sindent}{key} : {val}")
        return l
    l = []
    l.extend(_strToDepth(_dict, depth, indent=2))
    return '\n'.join(l)


class DictBrowser():
    def __init__(self, d):
        self._dict = d
        self._dicts = [d]

    def _strToDepth(self, _dict, depth=0, indent=0):
        """RECURSIVE"""
        if depth == 0:
            return []
        l = []
        sindent = " "*indent
        for key, val in _dict.items():
            if hasattr(val, 'keys'):
                l.append(f"{sindent}{key} : dict size {len(val)}")
                l.extend(self._strToDepth(val, depth-1, indent+2))
            else:
                l.append(f"{sindent}{key} : {val}")
        return l

    def strToDepth(self, depth=0, partSelect=None):
        _d = self.selectPart(partSelect)
        l = ["DictBrowser()"]
        l.extend(self._strToDepth(_d, depth, indent=2))
        return '\n'.join(l)

    def __str__(self):
        if self._dicts[0] == None:
            return "DictBrowser(Uninitialized)"
        return self.strToDepth(1)

    def __repr__(self):
        return self.__str__()

    def selectPart(self, partSelect = None):
        _d = self._dict
        if partSelect is not None:
            parts = partSelect.split('.')
            for nselect in range(len(parts)):
                select = parts[nselect]
                for key, val in _d.items():
                    if key == select:
                        _d = val
        if not isinstance(_d, dict):
            _d = self._dict
        return _d


class JSONParser():
    # Helper values
    LINETYPE_PARAM = 0
    LINETYPE_PORT  = 0
    LINETYPE_MACRO = 1

    def __init__(self, filename):
        self._filename = filename
        self.valid = self.load()

    def load(self):
        with open(self._filename, 'r') as fd:
            self.struct = json.load(fd)
        if hasattr(self.struct, 'items'):
            self._dicts = [self.struct]
        elif hasattr(self.struct, '__getitem__'):
            self._dicts = self.struct
        self._dict = self._dicts[0]
        return True

    def getDict(self, index=0):
        return self._dicts[index]

    def _strToDepth(self, _dict, depth=0, indent=0):
        """RECURSIVE"""
        if depth == 0:
            return []
        l = []
        sindent = " "*indent
        for key, val in _dict.items():
            if hasattr(val, 'keys'):
                l.append(f"{sindent}{key} : dict size {len(val)}")
                l.extend(self._strToDepth(val, depth-1, indent+2))
            else:
                l.append(f"{sindent}{key} : {val}")
        return l

    def strToDepth(self, depth=0, partSelect = None, index=0):
        _d = self.selectPart(partSelect, index=index)
        l = ["JSONParser({})".format(os.path.split(self._filename)[-1])]
        l.extend(self._strToDepth(_d, depth, indent=2))
        return '\n'.join(l)

    def __str__(self):
        if self._dicts[0] == None:
            return "JSONParser(Uninitialized)"
        return self.strToDepth(3)

    def __repr__(self):
        return self.__str__()

    def selectPart(self, partSelect = None, index=0):
        _d = self._dicts[index]
        if partSelect is not None:
            parts = partSelect.split('.')
            for nselect in range(len(parts)):
                select = parts[nselect]
                for key, val in _d.items():
                    if key == select:
                        _d = val
        if not isinstance(_d, dict):
            _d = self._dicts[index]
        return _d

def doBrowse(argv):
    import argparse
    parser = argparse.ArgumentParser(description="Browse a JSON file interactively")
    parser.add_argument('filename', default=-1, help="The JSON file to parse.")
    parser.add_argument('depth', default=-1, help="The depth of a nested dict to show (-1 = All).", nargs='?')
    parser.add_argument('-i', '--index', default=0, help="Index of top dict in case of list of dicts")
    parser.add_argument('-s', '--select', default=None, help="A hierarchical dereference to select and use as the top when printing.")
    args = parser.parse_args()
    filename = args.filename
    index = int(args.index)
    depth = int(args.depth)
    partSelect = args.select
    jp = JSONParser(filename)
    if not jp.valid:
        return False
    print(jp.strToDepth(depth, partSelect, index=index))
    return True

if __name__ == "__main__":
    import sys
    doBrowse(sys.argv)
