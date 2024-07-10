#! /usr/bin/python3

# Use yosys parsing to generate automatic instantiation for a verilog module

import os
import re
from yoparse import VParser

# ==== Old format. TODO: make this parameterized
if False:
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
        "reg [TOW-1:0] r_timeout=0;",
        f"always @(posedge {clkname}) begin",
        "  if (r_timeout > 0) r_timeout <= r_timeout - 1;",
        "end",
        "wire to = ~(|r_timeout);",
        ""
    )
# ======== Clock matching regexp ==========
# Match any port that ends in 'clk' (case insensitive)
reClk = "[Cc][Ll][Kk]$"

def _decomma(s):
    """Remove the comma from the end of a port instantiation string."""
    if ',' in s:
        b, e, = s.split(',')
        return b+e
    else:
        return s

def makeTemplate(filelist, top=None):
    vp = VParser(filelist, top=top)
    if not vp.valid:
        return False
    name = vp.modname
    ports = vp.getPorts(parsed=False)
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
        f"localparam {clkname.upper()}_HALFPERIOD = 5;",
        f"localparam TICK = 2*{clkname.upper()}_HALFPERIOD;",
        f"reg {clkname}=1'b0;",
        f"always #{clkname.upper()}_HALFPERIOD {clkname} <= ~{clkname};",
        "",
        # Dumpfile
        "// VCD dump file for gtkwave",
        "initial begin",
        "  if ($test$plusargs(\"vcd\")) begin",
        f"    $dumpfile(\"{name}.vcd\");",
        "    $dumpvars();",
        "  end",
        "end",
        "",
        # Timeout
        ""
        "localparam TOW = 12;",
        "localparam TOSET = {TOW{1'b1}};",
        "reg [TOW-1:0] r_timeout=0;",
        f"always @(posedge {clkname}) begin",
        "  if (r_timeout > 0) r_timeout <= r_timeout - 1;",
        "end",
        "wire to = ~(|r_timeout);",
        f"`define wait_timeout(sig) r_timeout = TOSET; #TICK wait ((to) || sig)",
        "",
    )
    for s in sl:
        print(s)
    if len(params) > 0:
        print(makeParams(params))
        print()
    if ports is not None:
        print(makeWires(ports, skip=[clkname]))
        print(makeInstantiator(name, ports, params=params))
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

def makeParams(paramdict):
    l = []
    for pname, pval in paramdict.items():
        l.append(f"localparam {pname} = {pval};")
    return '\n'.join(l)

def makeWires(ports, skip=[]):
    l = []
    #for portname,vdict in ports.items():
    for port in ports:
        linetype, portname, pdir, rangeStart, rangeEnd = port
        init = ''
        if portname in skip:
            continue
        if pdir == 'input':
            ptype = 'reg'
        else:
            ptype = 'wire'
        if rangeStart is not None and rangeEnd is not None:
            sel = f" [{rangeStart}:{rangeEnd}]"
            if ptype == 'reg':
                init = "=0"
        else:
            sel = ''
            if ptype == 'reg':
                init = "=1'b0"
        l.append(f'{ptype}{sel} {portname}{init};')
    return '\n'.join(l)

def makeInstantiator(name, ports, params={}):
    if params is not None and len(params) > 0:
        p = ["#("]
        for pname, pvalue in params.items():
            #linetype, pname, rspec, val = param
            linetype = VParser.LINETYPE_PARAM
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


def instantiate(filelist, top=None):
    vp = VParser(filelist, top=top)
    if not vp.valid:
        return False
    #print(vp.strToDepth(3))
    d = vp.getDict()
    name = vp.modname
    ports = vp.getPorts(parsed=False)
    params = vp.getParams()
    if ports is not None:
        print(makeParams(params))
        print(makeWires(ports))
        print(makeInstantiator(name, ports, params=params))
    return True

def doTestbench(argv):
    import argparse
    parser = argparse.ArgumentParser("Browse a JSON AST from a verilog codebase")
    parser.add_argument("-t", "--top", default=None, help="Explicitly specify top module for hierarchy.")
    parser.add_argument("files", default=[], action="append", nargs="+", help="Source files.")
    args = parser.parse_args()
    makeTemplate(args.files[0], top=args.top)
    return

def doInstantiate(argv):
    import argparse
    parser = argparse.ArgumentParser("Browse a JSON AST from a verilog codebase")
    parser.add_argument("-t", "--top", default=None, help="Explicitly specify top module for hierarchy.")
    parser.add_argument("files", default=[], action="append", nargs="+", help="Source files.")
    args = parser.parse_args()
    if instantiate(args.files[0], top=args.top):
        return 0
    else:
        return 1

def doBrowse(argv):
    import argparse
    parser = argparse.ArgumentParser("Browse a JSON AST from a verilog codebase")
    parser.add_argument("-d", "--depth", default=4, help="Depth to browse from the partselect.")
    parser.add_argument("-s", "--select", default=None, help="Partselect string.")
    parser.add_argument("-t", "--top", default=None, help="Explicitly specify top module for hierarchy.")
    parser.add_argument("files", default=None, action="append", nargs="+", help="Source files.")
    args = parser.parse_args()
    vp = VParser(args.files[0], top=args.top)
    if not vp.valid:
        return False
    print(vp.strToDepth(int(args.depth), args.select))
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
