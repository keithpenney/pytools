#! /usr/bin/python3

# Use yosys parsing to generate automatic instantiation for a verilog module

import os
import re
import subprocess
import json
import vparse
from collections import OrderedDict

# ======== Clock matching regexp ==========
# Match any port that ends in 'clk' (case insensitive)
reClk = "[Cc][Ll][Kk]$"

class VParser():
    def __init__(self, filename):
        self._filename = filename
        self.valid = self.parse()

    def parse(self):
        self._dict = None
        if not os.path.exists(self._filename):
            print(f"File {self._filename} not found")
            return False
        ycmd = f'yosys -q -p "read_verilog {self._filename}" -p write_json'
        try:
            jsfile = subprocess.check_output(ycmd, shell=True).decode('latin-1')
        except subprocess.CalledProcessError as e:
            print(e)
            return False
        self._dict = json.loads(jsfile)
        return True

    def getDict(self):
        return self._dict

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

    def strToDepth(self, depth=0, partSelect = None):
        _d = self.selectPart(partSelect)
        l = ["VParser({})".format(os.path.split(self._filename)[-1])]
        l.extend(self._strToDepth(_d, depth, indent=2))
        return '\n'.join(l)

    def __str__(self):
        if self._dict == None:
            return "BDParser(Uninitialized)"
        return self.strToDepth(3)

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

    def getTrace(self, partselect):
        sigdict = self.selectPart(partselect)
        selftrace = [s.strip() for s in partselect.split('.')]
        # The resulting dict needs to have a 'bits' key
        bits = sigdict.get('bits', None)
        if bits is None:
            print(f"Partselect {partselect} does not refer to a valid net dict (key of 'netnames' dict)")
            return None
        bitlist = []
        for net in bits:
            bitlist.append([net, []])
        # Now walk the whole top-level dict and look connected nets by index
        def _do(trace, val):
            if trace == selftrace:
                return # Don't count yourself
            if hasattr(val, 'get'):
                valbits = val.get('bits', None)
                if valbits is not None:
                    # FIXME
                    # trstr = '.'.join(trace)
                    # print(f"{trstr} : {valbits}")
                    for net, hitlist in bitlist:
                        if not isinstance(net, int):
                            # Skip special nets '0' and '1'
                            continue
                        if net in valbits:
                            valbitIndex = valbits.index(net)
                            trstr = '.'.join(trace)
                            if len(valbits) > 1:
                                trstr += f'[{valbitIndex}]'
                            hitlist.append(trstr)
        self.walk(_do)
        # print the bit dict
        for n in range(len(bitlist)):
            net, hitlist = bitlist[n]
            if not isinstance(net, int):
                print(f"{n} : 1'b{net}")
            else:
                print(f"{n} : {hitlist}")
        return

    def search(self, target_key):
        """Search the dict structure for all keys that match 'target_key' and return as a nested dict."""
        hitlist = []
        def _do(trace, val):
            if trace[-1] == target_key:
                tstr = '.'.join(trace)
                hitlist.append((tstr, val))
        self.walk(_do)
        print(f"hitlist = {hitlist}")
        return

    def walk(self, do = lambda trace, val : None):
        return self._walk(self._dict, [], do)

    @classmethod
    def _walk(cls, td, trace = [], do = lambda trace, val : None):
        """RECURSIVE"""
        if not hasattr(td, 'items'):
            return False
        for key, val in td.items():
            trace.append(key)   # Add key
            do(trace, val)
            if hasattr(val, 'items'):
                cls._walk(val, trace, do)   # When this returns, we are done with this dict
            trace.pop() # So we can pop the key from the trace and continue the loop
        return True

def _decomma(s):
    """Remove the comma from the end of a port instantiation string."""
    if ',' in s:
        b, e, = s.split(',')
        return b+e
    else:
        return s


def makeTemplate(filename):
    vp = VParser(filename)
    if not vp.valid:
        return False
    #print(vp.strToDepth(3))
    d = vp.getDict()
    mod = d.get("modules", None)
    if mod is None:
        print("// no modules")
        return
    # Get first (should be only) module
    name,mdict = [x for x in mod.items()][0]
    ports = mdict.get('ports', None)
    # find clkname
    clkname = 'clk'
    for portname,vdict in ports.items():
        pdir = vdict.get('direction')
        pbits = vdict.get('bits')
        pw = len(pbits)
        if pdir == 'input' and pw == 1:
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
            print(makeWires(ports, skip=[clkname]))
            print(makeInstantiator(name, ports))
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


def makeWires(ports, params=None, skip=[]):
    # TODO - Get/handle parameters
    l = []
    for portname,vdict in ports.items():
        if portname in skip:
            continue
        pdir = vdict.get('direction')
        pbits = vdict.get('bits')
        if pdir == 'input':
            ptype = 'reg'
        else:
            ptype = 'wire'
        pw = len(pbits)
        if pw > 1:
            sel = f" [{pw-1}:0]"
        else:
            sel = ''
        l.append(f'{ptype}{sel} {portname};')
    return '\n'.join(l)

def makeInstantiator(name, ports, params=None):
    # TODO - Get/handle parameters
    l = [f'{name} {name}_i (\n']
    for portname,vdict in ports.items():
        portdir = vdict.get('direction', 'unknown')
        pbits = vdict.get('bits', [0])
        pw = len(pbits)
        if pw > 1:
            portwidth = f" [{pw-1}:0]"
        else:
            portwidth = ""
        l.append('  .{0}({0}), // {1}{2}\n'.format(portname, portdir, portwidth))
    # Hack. Remove the comma from the last entry
    l[-1] = _decomma(l[-1])
    l.append(');')
    return ''.join(l)

def instantiate(filename):
    vp = VParser(filename)
    if not vp.valid:
        return False
    #print(vp.strToDepth(3))
    d = vp.getDict()
    mod = d.get("modules", None)
    if mod is not None:
        # Get first (should be only) module
        name,mdict = [x for x in mod.items()][0]
        ports = mdict.get('ports', None)
        if ports is not None:
            print(makeWires(ports))
            print(makeInstantiator(name, ports))
    return True

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

def doBrowse(argv):
    USAGE = f"python3 {argv[0]} filename.v [DEPTH] [PART_SELECT]"
    if len(argv) > 1:
        filename = argv[1]
    else:
        print(USAGE)
        return False
    depth = 4
    partSelect = None
    for arg in argv[2:]:
        try:
            arg = int(arg)
            depth = arg
        except:
            partSelect = arg
    vp = VParser(filename)
    if not vp.valid:
        return False
    print(vp.strToDepth(depth, partSelect))
    return True

def doTrace(argv):
    USAGE = f"python3 {argv[0]} filename.v part_select"
    if len(argv) < 3:
        print(USAGE)
        return False
    filename = argv[1]
    partselect = argv[2]
    vp = VParser(filename)
    #vp.search(partselect)
    sigtrace = vp.getTrace(partselect)

if __name__ == "__main__":
    import sys
    sys.exit(doInstantiate(sys.argv))
