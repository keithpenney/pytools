#! /usr/bin/python3

# Trace a signal through a yosys-parsed verilog file

if __name__ == "__main__":
    import sys
    import instantiator
    instantiator.doTrace(sys.argv)
