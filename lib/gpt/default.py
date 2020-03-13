#
# GPT
#
# Authors: Christoph Lehner 2020
#
import sys, gpt

def get(tag,default):
    if tag in sys.argv:
        i = sys.argv.index(tag)
        if i+1 < len(sys.argv):
            return sys.argv[i+1]
    return default

def get_float(tag, default = float("nan")):
    res=get(tag,None)
    if not res is None:
        return float(res)
    return default

def get_int(tag, default):
    res=get(tag,None)
    if not res is None:
        return int(res)
    return default

def get_ivec(tag, default):
    res=get(tag,None)
    if not res is None:
        return [ int(x) for x in res.split(".") ]
    return default

grid = get_ivec("--grid",[4,4,4,4])
precision = { "single" : gpt.single, "double" : gpt.double }[get("--precision","double")]
verbose = get("--verbose","").split(",")

if "--help" in sys.argv:
    print("--------------------------------------------------------------------------------")
    print(" GPT Help")
    print("--------------------------------------------------------------------------------")
    print("")
    print(" --grid X.Y.Z.T")
    print("")
    print("   sets the default grid for gpt")
    print("")
    print(" --precision single/double")
    print("")
    print("   sets the default precision for gpt")
    print("")
    print(" --verbose opt1,opt2,...")
    print("")
    print("   sets verbosity options.  candidates: eval,io")
    print("--------------------------------------------------------------------------------")
