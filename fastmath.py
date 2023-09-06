#!usr/bin/python3

# Generate an expression for multiplying or dividing by a constant integer
# using only addition and bit-shift operations.
# Configurable overhead bits for division allow for trading register depth
# for accuracy

import argparse
import math
import re

# TODO
#   To support floats, need to find the closest integral ratio representing the number
#   I.e. convert a rational number to a ratio

def _int(x):
    try:
        return int(x)
    except ValueError:
        pass
    try:
        return int(x, 16)
    except ValueError:
        return None

def divExpr(sarg, d, oBits):
    """Return the logical expression for dividing by divisor 'd' (integer)
    using 'oBits' (integer) overhead bits."""
    # Detect powers of two
    if (math.log2(d) % 1) == 0:
        # d is power of two
        return "{} >> {}".format(sarg, int(math.log2(d)))
    n = round((1 << oBits)/d)
    me = mulExpr(sarg, n)
    return "({}) >> {}".format(me, oBits)

def mulExpr(sarg, d):
    """Return a string containing the logical expression of multiplying
    string 'sarg' by an integer 'd' using only addition and bit-shift
    operations."""
    d = int(d)
    nbits = _getNBits(d)
    l = []
    for n in range(nbits):
        if d & (1 << n):
            if n == 0:
                l.append(sarg)
            else:
                l.append("({} << {})".format(sarg, n))
    return " + ".join(l)

def _getNBits(n):
    """Return the number of bits required to store integer 'n'"""
    return int(math.ceil(math.log2(n + 1)))

def _getError(d, oBits):
    """Return the error associated with dividing by integer 'd' using 'oBits'
    overhead bits."""
    d = int(d)
    oBits = int(oBits)
    n = round((1 << oBits)/d)
    nexact = (1 << oBits)/d
    return 1 - (n/nexact)

def printExpr(argv):
    USAGE = "python3 {} (*/)operand".format(argv[0])
    parser = argparse.ArgumentParser(description="Convert static multiplication and division to addition and bitshift", epilog = USAGE)
    parser.add_argument('-s', '--string_arg', default='x', help="Variable name for printing")
    parser.add_argument('-b', '--overhead_bits', default=None, help="Overhead bits for additional precision in division (default = clog2(operand))")
    parser.add_argument('args', default=None, help='Operation and multiplicand or divisor (i.e. *15 or /3.14159)', nargs='+')
    args = parser.parse_args()
    argstr = ''.join(args.args)
    _match = re.match("(\w+)?(\*|/)([0-9a-fA-Fx.]+)", argstr)
    if _match:
        sarg, operation, operand = _match.groups()
        if sarg is None or len(sarg) == 0:
            sarg ='x'
        if '.' in operand:
            operand = float(operand)
            twostage = True
            print("Floats not yet supported. Aborting")
            return False
        else:
            twostage = False
            operand = _int(operand)
    else:
        print("Invalid argument: {argstr}")
        return False
    op = operation.strip().lower()
    if op in ('*', 'x'):
        multNdiv = True
    elif op in ('/', '//'):
        multNdiv = False
    if args.overhead_bits is None:
        nbits = math.ceil(math.log2(operand)+1)
    else:
        nbits = int(args.overhead_bits)
    if multNdiv:
        expr = mulExpr(sarg, operand)
        print("{}*{} is {}".format(sarg, operand, expr))
    else:
        expr = divExpr(sarg, operand, nbits)
        err = 100*_getError(operand, nbits)
        print("{}/{} is approximately ({:.2f}% error):".format(sarg, operand, err))
        print(expr)
    return True

if __name__ == "__main__":
    import sys
    printExpr(sys.argv)
