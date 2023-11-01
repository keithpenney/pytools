#! /usr/bin/python3

# Common Built-In Self-Test functionality

# Usage Example:
#   # [example.py]
#
#   def foo(x, inc=1):
#       try:
#           return x+inc
#       except TypeError:
#           return None
#
#   if __name__ == "__main__":
#       # Only include tests if run as main
#       import bist
#       # Optionally change your chatter preferences
#       bist.elaborate = False
#       # Create a target (function to test)
#       target = bist.Target(foo)
#       # Add some test cases with target.add(desired_result, *args, **kwargs)
#       target.add(1, 0)                        # 0+1 = 1
#       target.add(10, 6, inc=4)                # 6+4 = 10
#       target.add(0, 6, inc=-6)                # 6-6 = 0
#       target.add("hello world", "hello", inc=" world") # Works on strings too!
#       # Catch bad usages too
#       target.add(None, "hello")               # "hello"+1 raises TypeError
#       # Register every target you want to run
#       bist.register(target)
#       # Run all tests
#       bist.run()

# If verbose == True, print function strings as they are called
verbose = True
# If elaborate == True, print desired & actual result for all failures
elaborate = True

# Private
_targets = []

def register(target):
    _targets.append(target)

def run(silent=False):
    failCount = 0
    testsRun = 0
    for target in _targets:
        failCount += target.run(silent=silent)
        testsRun += 1
    if failCount > 0:
        _pass = False
        res = "FAIL"
    else:
        _pass = True
        res = "PASS"
    if not silent:
        print(f"{res} : {testsRun} tests run")
    return _pass

class Target():
    """A collection of tests against function 'fn'"""
    PASS = 1
    FAIL = 0
    NOT_RUN = -1
    def __init__(self, fn):
        self._fn = fn
        self._maps = []
        self.failCount = 0

    def add(self, result, *args, **kwargs):
        """Add a test to the Target. and the desired result when called with 'args' and
        'kwargs'.  If the actual result != 'result', it's a FAIL, otherwise a PASS."""
        self._maps.append([args, kwargs, result, self.NOT_RUN])

    def run(self, silent = False):
        self.failCount = 0
        num = 0
        if verbose and not silent:
            print("Testing Function: {}".format(self._fn.__name__))
        for n in range(len(self._maps)):
            assoc = self._maps[n]
            args, kwargs, result = assoc[0:3]
            real_result = self._fn(*args, **kwargs)
            if real_result != result:
                self._maps[n][3] = self.FAIL
                self.failCount += 1
                argstring = ", ".join([str(arg) for arg in args])
                kwargstring = ", ".join(["{key}={val}" for key, val in kwargs.items()])
                funcargs = f"{self._fn.__name__}(" + ", ".join((argstring, kwargstring)) + ")"
                if not silent:
                    print(f"FAILED on association ({num}): {funcargs}")
                    if elaborate:
                        print(f"    Target: {result}")
                        print(f"    Result: {real_result}")
            else:
                self._maps[n][3] = self.PASS
            num += 1
        return self.failCount
