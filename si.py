#! /usr/bin/python3

# Handy string handling using SI-prefixes

import re

_si = ((30, ("Q", "quetta")),
      (27, ("R", "ronna")),
      (24, ("Y", "yotta")),
      (21, ("Z", "zetta")),
      (18, ("E", "exa")),
      (15, ("P", "peta")),
      (12, ("T", "tera")),
      ( 9, ("G", "giga")),
      ( 6, ("M", "mega")),
      ( 3, ("k", "kilo")),
      ( 0, ("", "")),
      (-3, ("m", "milli")),
      (-6, ("u", "micro")),   # mu?
      (-9, ("n", "nano")),
     (-12, ("p", "pico")),
     (-15, ("f", "femto")),
     (-18, ("a", "atto")),
     (-21, ("z", "zepto")),
     (-24, ("y", "yocto")),
     (-27, ("r", "ronto")),
     (-30, ("q", "quecto")))

_sichars = "".join([x[1][0] for x in _si])
si_res = "^([\-0-9.]+)\s*([" + _sichars + "]?)"
si_res_percent = "^([\-0-9.]+)\s*([" + _sichars + "%]?)"

class SIFloat():
    def __init__(self, v):
        try:
            val = float(v)
        except ValueError:
            # This may raise an Exception, but that's intentional
            val = from_si(v)
        self.real = val.real
        self.conjugate = self.real

    def __repr__(self):
        return to_si(self.real)

    def __format__(self, fmt):
        if '.' in fmt:
            wstr, rhs = fmt.split('.', maxsplit=1)
            sigfigs = int(rhs.lower().strip('f'))
            sr = to_si(self.real, sigfigs=sigfigs)
        else:
            sr = to_si(self.real)
            wstr = fmt.lower().strip().strip('f')
        return ("{:" + wstr + "}").format(sr)

    def __str__(self):
        return self.__repr__()

    def __abs__(self):
        return SIFloat(abs(self.real))

    # TODO - These all ignore situation where other is complex
    def __add__(self, other):
        return SIFloat(self.real + other.real)

    def __sub__(self, other):
        return SIFloat(self.real - other.real)

    def __mul__(self, other):
        return SIFloat(self.real*other.real)

    def __div__(self, other):
        return SIFloat(self.real/other.real)

    def __truediv__(self, other):
        return self.__div__(other)

    def __ge__(self, other):
        return self.real >= other.real

    def __gt__(self, other):
        return self.real > other.real

    def __le__(self, other):
        return self.real <= other.real

    def __lt__(self, other):
        return self.real < other.real

    def __ne__(self, other):
        return self.real != other.real

    def __eq__(self, other):
        return self.real == other.real

    def __float__(self):
        """Returns float, not SIFloat"""
        return self.real.__float__()

    def __floor__(self):
        return SIFloat(self.real.__floor__())

    def __ceil__(self):
        return SIFloat(self.real.__ceil__())

    def as_integer_ratio(self):
        return self.real.as_integer_ratio()

    def hex(self):
        return self.real.hex()

    def is_integer(self):
        return self.real.is_integer()

    def fromhex(self, string):
        return SIFloat(self.real.fromhex(string))


class SIComplex():
    """WIP"""
    def __init__(self, v):
        try:
            val = complex(v)
        except ValueError:
            # This may raise an Exception, but that's intentional
            val = from_si(v)
        self.real = val.real
        self.imag = val.imag
        self.val = self.real + 1.0j*self.imag

    def __repr__(self):
        _rs = to_si(self.real)
        if self.imag != 0:
            _is = to_si(self.imag)
            if self.real == 0:
                if _is[0] == '-':
                    _is = "-j" + _is[1:]
                else:
                    _is = "j" + _is
            else:
                if _is[0] == '-':
                    _is = "- j" + _is
                else:
                    _is = "+ j" + _is
            return _rs + " " + _is
        return _rs

    def __str__(self):
        return self.__repr__()

    def __abs__(self, other):
        return SIComplex((self.real**2 + self.imag**2)**(1/2))

    def __add__(self, other):
        return SIComplex((self.real + other.real) + 1.0j*(self.imag + other.imag))

    def __sub__(self, other):
        return SIComplex((self.real - other.real) + 1.0j*(self.imag - other.imag))

    def __mul__(self, other):
        return SIComplex((self.real*other.real - self.imag*other.imag) \
                       + 1.0j*(self.real*other.imag + self.imag*other.real))

def _get_exp(s):
    """Get the exponent value associated with supposed SI prefix 's'."""
    for pwr, pfx in _si:
        if s in pfx:
            return pwr
    return None


def to_si(n, sigfigs=4, long=False, space=False):
    """Use SI prefixes to represent 'n' up to sigfigs significant figures."""
    import math
    try:
        n = float(n)
    except ValueError:
        return None
    if n == 0:
        return "0"
    sign = ""
    if n < 0:
        n = abs(n)
        sign = "-"
    npwr = math.log10(n)
    # x^N = y*10^N = z
    # log(x^N) = log(y*10^N) = log(y) + log(10^N) = log(y) + N = log(z)
    fmt = "{:." + str(int(sigfigs)) + "}"
    idx = 0
    sp = ""
    if long:
        idx = 1
    if space:
        sp = " "
    for pwr, pfx in _si:
        if npwr >= pwr:
            mant = 10**(npwr-pwr)
            s = sign + fmt.format(mant) + sp + pfx[idx]
            break
    return s


def from_si(s):
    return from_si_with_units(s)[0]


def from_si_with_units(s):
    """Interpret the number represented in string 's' using SI-prefixes"""
    try:
        n = float(s)
        return n, ""
    except ValueError:
        pass
    _match = re.match(si_res, s.strip())
    if _match:
        num, pfx = _match.groups()
        remainder = s[_match.span()[1]:]
        exp = _get_exp(pfx)
        if exp is None:
            return None
        return float(num)*(10**exp), remainder
    return None, None


def from_si_scale(s, scale=1):
    """Interpret the number represented in string 's' using SI-prefixes
    or optional percent of 'scale' with percentage '%' sign."""
    _match = re.match(si_res_percent, s.strip())
    if _match:
        num, pfx = _match.groups()
        if pfx == "%":
            return float(num)*scale/100
        exp = _get_exp(pfx)
        if exp is None:
            return None
        return float(num)*(10**exp)
    return None


def testSIFloat():
    import math
    x = SIFloat("299.8m")
    y = SIFloat("3.14159265u")
    print(f"{y:.05f}")
    print(f"{y:10f}")
    print(f"{y:>10}")
    print(f"{y:>20.8f}")
    print(f"{x} + {y} = {x + y}")
    print(f"{x} - {y} = {x - y}")
    print(f"{x} * {y} = {x * y}")
    print(f"{x} / {y} = {x / y}")
    print(f"{x} == {y} = {x == y}")
    print(f"{x} != {y} = {x != y}")
    print(f"{x} >= {y} = {x >= y}")
    print(f"{x} <= {y} = {x <= y}")
    print(f"{x} < {y} = {x < y}")
    print(f"{x} > {y} = {x > y}")
    print(f"abs({x}) = {abs(x)}")
    print(f"floor({x}) = {math.floor(x)}")
    print(f"ceil({x}) = {math.ceil(x)}")
    return

def self_test():
    import bist
    def test_to_si():
        target = bist.Target(to_si)
        # Goodies
        target.add("1.0", 1)
        target.add("1.0k", 1000)
        target.add("-1.0m", -0.001)
        target.add("9.9P", 9.9e15)
        target.add("9.9 P", 9.9e15, space=True)
        target.add("9.9 peta", 9.9e15, long=True, space=True)
        target.add("0", 0)
        target.add("0", 0.0)
        # Baddies
        target.add(None, "hello")
        bist.register(target)
    def test_from_si():
        target = bist.Target(from_si)
        # Goodies
        target.add(1.0, "1.0")
        target.add(1000, "1.0k")
        target.add(1000, "1.0 k")
        target.add(1000, "1.0 kilo")
        target.add(-9.9e-6, "-9.9u")
        target.add(0, "0")
        target.add(0, "0.0k") # weirdo
        # Baddies
        target.add(None, "hello")
        bist.register(target)
    test_to_si()
    test_from_si()
    bist.run()

def preprocess(line):
    """Replace any strings matching the SI-prefix literal pattern with a class instantiation."""
    # TODO
    # 1. Break up string by quote chars
    # 2. If not inside quotes AND preceding char is not [A-Za-z_] and following char is not [A-Za-z_]
    # 3. Replace matching_string with SIFloat("matching_string")
    res = "\W+" + si_res + "\W+"
    return line

def sishell():
    import repl
    intro = "SI Shell: Standard Python REPL which uses SI-prefixes for numeric literals"
    print(intro)
    repl.preprocess = preprocess
    repl.repl()

if __name__ == "__main__":
    sishell()

