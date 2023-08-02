#! /usr/bin/python3

# Use yosys parsing to generate automatic instantiation for a verilog module

import os
import re
import subprocess
import json

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
            print(f"File {filename} not found")
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


    def strToDepth(self, depth=0):
        l = ["VParser({})".format(os.path.split(self._filename)[-1])]
        l.extend(self._strToDepth(self._dict, depth, indent=2))
        return '\n'.join(l)

    def __str__(self):
        if self._dict == None:
            return "BDParser(Uninitialized)"
        return self.strToDepth(3)

    def __repr__(self):
        return self.__str__()


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
        f"module name_tb;",
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
"           $display(\"No dumpfile name supplied; Wave data will not be saved.\");",
        "  end else begin",
        "    $dumpfile(dumpfile);",
"           $dumpvars;",
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

if __name__ == "__main__":
    import sys
    sys.exit(doInstantiate(sys.argv))
