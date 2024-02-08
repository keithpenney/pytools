#! Extract GMII signals from a VCD file and parse the resulting packet

import os
import vcdextract as vcde
import eth_pkt as ethp

def resample(data, dt, start=1):
    rsd = [data[start]]
    t0, d0 = data[start]
    n = start + 1
    while n < len(data):
        t, d = data[n]
        t0 += dt
        if t0 >= t:
            d0 = d
            n += 1
        rsd.append((t0, d0))
    return rsd

# resample by 10ns
test_data = [
    (   0, 1),
    ( 100, 0),
    ( 110, 1),
    ( 120, 0),
    ( 160, 1),
    ( 280, 0),
    ( 300, 1)
]

test_rsd = [
    (   0, 1), (10, 1), (20, 1), (30, 1), (40, 1), (50, 1), (60, 1), (70, 1), (80, 1), (90, 1),
    ( 100, 0),
    ( 110, 1),
    ( 120, 0), (130, 0), (140, 0), (150, 0),
    ( 160, 1), (170, 1), (180, 1), (190, 1), (200, 1), (210, 1), (220, 1), (230, 1), (240, 1), (250, 1), (260, 1), (270, 1),
    ( 280, 0), (290, 0),
    ( 300, 1),
]

def testResample():
    rsd = resample(test_data, 10, start=0)
    #rsd_check = [x[1] for x in test_rsd]
    rsd_check = test_rsd
    if (rsd == rsd_check):
        print("PASS")
    else:
        print("rsd = (len {}) \n{}".format(len(rsd), rsd))
        print("\nrsd_check = (len {})\n{}".format(len(rsd_check), rsd_check))
    return

def main():
    import argparse
    parser = vcde.ArgumentParser(description="Extract GMII traces from a VCD file and parse the packets.")
    args = parser.parse_args()
    pkt_ratio = int(args.packet_ratio)
    fname, fext = os.path.splitext(args.filename)
    if fext == ".pickle":
        sig_data = vcde.unPickle(args.filename, signals=args.sig_names)
    else:
        sig_data = vcde.extract(args.filename, signals=args.sig_names)
    if pkt_ratio > 0:
        for _id, sl in sig_data.items():
            pkts = sl.splitPackets(pkt_ratio, start=1)
            print("{} split into {} packets.".format(sl.name, len(pkts)))
            #for n in range(1):
            #n = 2
            #if True:
            for n in range(len(pkts)):
                pkt = pkts[n]
                pkt_span = pkt[-1][0] - pkt[0][0]
                print("================ Packet {} spans {} ns (starting at {} ns) ================".format(n, pkt_span, pkt[0][0]))
                # TODO - Why do I need a factor of 2 here?
                rsd = vcde.resample(pkt, 2*sl.tclk, start=0)
                #print("len(rsd) = {}, pkt_span/(2*tclk) = {}".format(len(rsd), pkt_span/(2*sl.tclk)))
                #print([hex(x) for x in rsd])
                ethp.decode(rsd)

if __name__ == "__main__":
    main()
    #testResample()
