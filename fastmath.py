#!usr/bin/python3

# Generate an expression for multiplying or dividing by a constant using only
# addition and bit-shift operations.  For floats, we first find the nearest
# integer ratio via a Stern-Brocot tree walk.
# Configurable overhead bits for division allow for trading register depth
# for accuracy
#
# This seems like a good place to make a note about running statistics
#   Running Average:
#     On each acquisition:
#       nsamples++
#       avg = avg*nsamples/(nsamples+1) + sample/(nsamples+1)       # Unlikely to overflow. Uses 2 dividers.
#           = (nsamples*avg + sample)/(nsamples+1)                  # More likely to overflow. Uses 1 divider.
#
#   In many cases it would be computationally favorable to simply accumulate
#   samples in a buffer that is MAX_SAMPLES*SAMPLE_MAX in size and let the
#   host calculate sum/nsamples whenever the average is needed.

# TODO:
#   How do I properly limit the number of bits available?  Specifically, the
#   Stern-Brocot walk doesn't have an upper limit to integers.

import argparse
import math
import re

def _int(x):
    try:
        return int(x)
    except ValueError:
        pass
    try:
        return int(x, 16)
    except ValueError:
        return None

def _sfloat(f, precision=4):
    fmt = "{:."+str(precision)+"f}"
    s = fmt.format(f)
    # Trim any trailing zeros
    s = s.rstrip('0')
    # If f is integer, we'll end up with an awkward decimal point on the right side
    s = s.rstrip('.')
    return s

def floatToRatio(f, nIters = 32):
    """Implements the Stern-Brocot tree walk copied from Larry Doolittle's 'stern.c'
    Returns (numerator, denominator) whose ratio is a close (or exact) approximation
    to float 'f'."""
    left  = [0, 1]  # numerator, denominator
    right = [1, 0]
    new = [0, 0]
    f = abs(f)
    minErr = 1.0
    best = [1, 1]
    for n in range(nIters):
        new[0] = left[0] + right[0]
        new[1] = left[1] + right[1]
        v = new[0]/new[1]
        err = abs((f-v)/f)
        if f > v:
            #print("target > {:.03f} = {} / {}, err = {:.05f} %".format(v, new[0], new[1], err))
            left[0] = new[0]
            left[1] = new[1]
        else:
            #print("target <= {:.03f} = {} / {}, err = {:.05f} %".format(v, new[0], new[1], err))
            right[0] = new[0]
            right[1] = new[1]
        if err < minErr:
            minErr = err
            best = [new[0], new[1]]
        if err == 0:
            break
    return best

def mulInt(sarg, target, oBits):
    target = int(target)
    return _mulDivExpr(sarg, target, 1, target, oBits)

def divInt(sarg, target, oBits):
    target = int(target)
    return _mulDivExpr(sarg, 1, target, 1/target, oBits)

def mulFloat(sarg, target, oBits):
    num, den = floatToRatio(target)
    return _mulDivExpr(sarg, num, den, target, oBits)

def divFloat(sarg, target, oBits):
    # Just multiply by the inverse
    return mulFloat(sarg, 1/target, oBits)

def _mulDivExpr(sarg, num, den, target, oBits):
    err = None
    bestpwr = 0
    # Scale to make the denominator a power of 2 while keeping
    # the numerator an integer. Find the closest approximating
    # ratio
    if den > 1:
        for alpha in range(oBits):
            A = (2**alpha)/den
            beta = int(num*A) # int((x(*2**alpha)/den))
            thistgt = beta/(2**alpha)
            thiserr = abs(1 - thistgt/target)
            #print(f"{beta}//2**{alpha} = {thistgt}")
            if err is None:
                #print(f"{alpha}: err None -> {thiserr}")
                err = thiserr
                bestpwr = alpha
            elif thiserr < err:
                #print(f"{alpha}: err {err} -> {thiserr}")
                err = thiserr
                bestpwr = alpha
        num = int(num*(2**bestpwr)/den)
        # Now multiply by new numerator
        den = 2**bestpwr
    nbits = _getNBits(num)
    expr = _mkExpr(sarg, num, bestpwr, nbits)
    err = 100*_floatError(target, num, den)
    return (expr, err, num, den)

def _mkExpr(sarg, num, rshift, nbits):
    expr = []
    for n in range(nbits):
        if num & (1 << n):
            if n == 0:
                expr.append(f"{sarg}")
            else:
                expr.append(f"({sarg} << {n})")
    expr = " + ".join(expr)
    if rshift > 0:
        return f"({expr}) >> {rshift}"
    else:
        return f"{expr}"

def _getNBits(n):
    """Return the number of bits required to store integer 'n'"""
    return int(math.ceil(math.log2(n + 1)))

def _floatError(operand, m, d):
    return 1-((m/d)/operand)

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
            opint = False
            operand = float(operand)
        else:
            opint = True
            operand = _int(operand)
    else:
        print(f"Invalid argument: {argstr}")
        return False
    op = operation.strip().lower()
    if op in ('*', 'x'):
        multNdiv = True
    elif op in ('/', '//'):
        multNdiv = False
        if operand == 0:
            print("Stop trying to divide by zero!")
            return False
    if args.overhead_bits is None:
        obits = math.ceil(math.log2(operand)+1)
    else:
        obits = int(args.overhead_bits)
    if multNdiv:
        if opint:
            expr, err, num, den = mulInt(sarg, operand, 0) # oBits ignored for integer multiplication
            print(f"{sarg}*{operand} is:")
            print(expr)
        else:
            expr, err, num, den = mulFloat(sarg, operand, obits)
            print(f"{sarg}*{operand} is approximately {sarg}*{num}/{den} = {sarg}*{_sfloat(num/den, 5)} ({_sfloat(err, 5)}% error):")
            print(expr)
    else: # Division
        if opint:
            expr, err, num, den = divInt(sarg, operand, obits)
        else:
            expr, err, num, den = divFloat(sarg, operand, obits)
        print(f"{sarg}/{operand} is approximately {sarg}*{num}/{den} = {sarg}/{_sfloat(den/num, 5)} ({_sfloat(err, 5)}% error):")
        print(expr)
    return True

if __name__ == "__main__":
    import sys
    printExpr(sys.argv)
