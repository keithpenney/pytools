#! /usr/bin/python3

# Let's get a regex going to match against verilog module instantations
# Ultimately I'll turn this into a vim one-liner

import re

# Dang... nevermind.  Syntax has nested parentheses.  Not sure how to handle that.
# Giving up for now.
reMod = "^(\w+)\s+(#?\([^\)]*\))?\s+(\w+)\s+(\([^\)]*\))?;?"

goods = (
    "foo #() foo_i ();",
    "foo #(.p0(1)) foo_i (.i(i), .o(o));",
)

bads = (
    "foo <= baz;",
)


def isMatch(s):
    m = re.match(reMod, s)
    if m:
        print(f"groups: {m.groups()}")
        return True
    return False


def testRegex(argv):
    failures = 0
    for s in goods:
        if not isMatch(s):
            print(f"Failed to match: {s}")
            failures += 1
    for s in bads:
        if isMatch(s):
            print(f"Matched incorrectly: {s}")
            failures += 1
    if failures == 0:
        print("PASS!")
    else:
        print(f"FAIL: {failures}")
    return


if __name__ == "__main__":
    import sys
    testRegex(sys.argv)
