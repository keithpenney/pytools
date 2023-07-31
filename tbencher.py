#! /usr/bin/python3

# Make a testbench from a single Verilog module

import instantiator

if __name__ == "__main__":
    import sys
    instantiator.doTestbench(sys.argv)
