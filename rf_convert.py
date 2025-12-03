# RF unit conversions

import si
import math

def _id(val, load_ohms=50):
    """Identity function"""
    return val

def vpp_to_dbm(vpp, load_ohms=50):
    return va_to_dbm(vpp/2, load_ohms=load_ohms)

def vpp_to_vrms(vpp, load_ohms=50):
    va = vpp_to_va(vpp)
    return va_to_vrms(va)

def vpp_to_w(vpp, load_ohms=50):
    vrms = vpp_to_vrms(vpp, load_ohms=load_ohms)
    return vrms_to_w(vrms, load_ohms=load_ohms)

def va_to_dbm(va, load_ohms=50):
    # vrms = Vamplitude/sqrt(2) = Vpp/(2*sqrt(2))
    vrms = va_to_vrms(va)
    return vrms_to_dbm(vrms, load_ohms=load_ohms)

def va_to_w(va, load_ohms=50):
    vrms = va_to_vrms(va)
    return vrms_to_w(vrms, load_ohms=load_ohms)

def w_to_vrms(w, load_ohms=50):
    return math.sqrt(w*load_ohms)

def w_to_va(w, load_ohms=50):
    vrms = w_to_vrms(w, load_ohms=load_ohms)
    return vrms_to_va(vrms)

def w_to_vpp(w, load_ohms=50):
    return 2*w_to_va(w, load_ohms=load_ohms)

def vrms_to_w(vrms, load_ohms=50):
    return (vrms**2) / load_ohms

def vrms_to_dbm(vrms, load_ohms=50):
    # W = Vrms**2/50 = ((Va/sqrt(2))**2)/50 = ((Va**2)/2)/50 = (((Vpp**2)/4)/2)/50
    w = (vrms**2) / load_ohms
    return w_to_dbm(w, load_ohms=load_ohms)

def vrms_to_va(vrms, load_ohms=50):
    return vrms*math.sqrt(2)

def vrms_to_vpp(vrms, load_ohms=50):
    return 2*vrms_to_va(vrms, load_ohms=load_ohms)

def w_to_dbm(w, load_ohms=50):
    return mw_to_dbm(1.0e3*w, load_ohms=load_ohms)

def mw_to_dbm(mw, load_ohms=50):
    dbm = 10*math.log10(mw)
    return dbm

def dbm_to_mw(dbm, load_ohms=50):
    mw = 10**(dbm/10)
    return mw

def dbm_to_w(dbm, load_ohms=50):
    return (1.0e-3) * dbm_to_mw(dbm, load_ohms=load_ohms)

def dbm_to_vrms(dbm, load_ohms=50):
    w = dbm_to_w(dbm, load_ohms=load_ohms)
    return math.sqrt(w*load_ohms)

def dbm_to_va(dbm, load_ohms=50):
    vrms = dbm_to_vrms(dbm, load_ohms=load_ohms)
    return vrms * math.sqrt(2)

def dbm_to_vpp(dbm, load_ohms=50):
    va = dbm_to_va(dbm, load_ohms=load_ohms)
    return 2*va

def va_to_vpp(va, load_ohms=50):
    return 2*va

def vpp_to_va(vpp, load_ohms=50):
    return vpp/2

def va_to_vrms(va, load_ohms=50):
    return va/math.sqrt(2)

_conversions = (
    (None  ,        "V",       "Vpp",      "Vrms",       "W",       "dBm"),
    ("V",           _id,   va_to_vpp,  va_to_vrms,   va_to_w,   va_to_dbm),
    ("Vpp",   vpp_to_va,         _id, vpp_to_vrms,  vpp_to_w,  vpp_to_dbm),
    ("Vrms", vrms_to_va, vrms_to_vpp,         _id, vrms_to_w, vrms_to_dbm),
    ("W",       w_to_va,    w_to_vpp,   w_to_vrms,       _id,    w_to_dbm),
    ("dBm",   dbm_to_va,  dbm_to_vpp, dbm_to_vrms,  dbm_to_w,         _id),
)

def handle_conversion(val, unit_from, unit_to, load_ohms=50):
    accepted_units = [x.lower() for x in _conversions[0][1:]]
    if unit_from.lower() not in accepted_units:
        print(f"Units {unit_from} not recognized")
        return None, None

    to_scale, unit_to_str = si.from_si_with_units(f"1 {unit_to}")
    if unit_to_str.lower() not in accepted_units:
        print(f"Units {unit_to} not recognized")
        return None, None

    index_from = accepted_units.index(unit_from.lower()) + 1
    index_to = accepted_units.index(unit_to_str.lower()) + 1
    #print(f"{index_from} -> {index_to}")
    converter = _conversions[index_from][index_to]
    #print(converter)
    newval = converter(val, load_ohms=load_ohms)
    return newval/to_scale, unit_to

if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser(description="Unit converter")
    _to_str = f"Units to conver to: " + " ".join(_conversions[0][1:])
    parser.add_argument("--to", default=None, help=_to_str)
    parser.add_argument("val", nargs="+", help="Value to convert (optionally with Si units)")
    args = parser.parse_args()

    inval = " ".join(args.val)
    val, units = si.from_si_with_units(inval)
    if units is None or units == "":
        units = "V"

    if args.to is None:
        print(f"{val:.3f} {units}")
    else:
        newval, newunits = handle_conversion(val, units, args.to)
        if newval is not None:
            print(f"{round(newval, 3):} {newunits}")
