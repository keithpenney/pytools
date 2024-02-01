# Decode an ethernet packet by bytes

MIN_PKT_SIZE = 60

# == Eth ==
OFFSET_DEST_MAC     = 0
OFFSET_SRC_MAC      = 6
OFFSET_ETHERTYPE    = 12

# == ARP ==
OFFSET_ARP_HTYPE    = 14
OFFSET_ARP_PTYPE    = 16
OFFSET_ARP_HLEN     = 18
OFFSET_ARP_PLEN     = 19
OFFSET_ARP_OPER     = 20
OFFSET_ARP_SHA      = 22
OFFSET_ARP_SPA      = 28
OFFSET_ARP_THA      = 32
OFFSET_ARP_TPA      = 38

# == IPv4 ==
OFFSET_IP_VERSION_IHL = 14
OFFSET_IP_DSCP_ECN  = 15
OFFSET_IP_TOTAL_LENGTH = 16
OFFSET_IP_ID        = 18
OFFSET_IP_FLAG_FRAG = 20
OFFSET_IP_TTL       = 22
OFFSET_IP_PROTOCOL  = 23
OFFSET_IP_CHECKSUM  = 24
OFFSET_IP_SRC_IP    = 26
OFFSET_IP_DEST_IP   = 30

# == IPv6 ==
OFFSET_IPV6_VERSION_TC_FLOWLABEL = 14
OFFSET_IPV6_PAYLOAD_LENGTH = 18
OFFSET_IPV6_NEXT_HEADER = 20
OFFSET_IPV6_HOP_LIMIT = 21
OFFSET_IPV6_SRC_IP    = 22
OFFSET_IPV6_DEST_IP   = 38
OFFSET_IPV6_PAYLOAD   = 54

# == ICMP ==
PAYLOAD_OFFSET_ICMP_TYPE = 0
PAYLOAD_OFFSET_ICMP_CODE = 1
PAYLOAD_OFFSET_ICMP_CHECKSUM = 2
PAYLOAD_OFFSET_ICMP_REST_OF_HEADER = 4

# == UDP ==
PAYLOAD_OFFSET_UDP_SRC_PORT = 14
PAYLOAD_OFFSET_UDP_DEST_PORT = 16
PAYLOAD_OFFSET_UDP_LENGTH   = 18
PAYLOAD_OFFSET_UDP_CHECKSUM = 20
PAYLOAD_OFFSET_UDP_DATA     = 22

# ===== Ethertypes =====
ETHERTYPE_IPV4      = 0x0800
ETHERTYPE_ARP       = 0x0806
ETHERTYPE_WOL       = 0x0842
ETHERTYPE_VLAN      = 0x8100
ETHERTYPE_IPV6      = 0x86DD
ETHERTYPE_STAG      = 0x88A8
ETHERTYPE_PTP       = 0x88F7

# ===== IPv4 Protocols =====
IP_PROTOCOL_IP    = 0
IP_PROTOCOL_ICMP  = 1
IP_PROTOCOL_IPENCAP = 4
IP_PROTOCOL_TCP   = 6
IP_PROTOCOL_EGP   = 8
IP_PROTOCOL_UDP   = 17
IP_PROTOCOL_HMP   = 20
IP_PROTOCOL_RDP   = 27
IP_PROTOCOL_DDP   = 37
IP_PROTOCOL_IPV6  = 41
IP_PROTOCOL_IPV6_ROUTE = 43
IP_PROTOCOL_IPV6_FRAG = 44
IP_PROTOCOL_IDRP  = 45
IP_PROTOCOL_IPV6_ICMP = 58
IP_PROTOCOL_IPV6_NONXT = 59
IP_PROTOCOL_IPV6_OPTS = 60
IP_PROTOCOL_PIM   = 103
IP_PROTOCOL_L2TP  = 115
IP_PROTOCOL_SCTP  = 132
IP_PROTOCOL_UDPLITE = 136

# ===== IPv6 Extension Header Types =====
EXTENSION_HEADER_HOP_BY_HOP_OPTIONS = 0
EXTENSION_HEADER_ROUTING            = 43
EXTENSION_HEADER_FRAGMENT           = 44
EXTENSION_HEADER_ESP                = 50
EXTENSION_HEADER_AUTHENTICATION     = 51
EXTENSION_HEADER_DESTINATION_OPTIONS= 60
EXTENSION_HEADER_MOBILITY           = 135
EXTENSION_HEADER_HOST_ID_PROTOCOL   = 139
EXTENSION_HEADER_SHIM6_PROTOCOL     = 140
EXTENSION_HEADER_RESERVED0          = 253
EXTENSION_HEADER_RESERVED1          = 254
EXTENSION_HEADER_NOTHING            = 59

def print_mac(pkt, offset):
    print(':'.join(["{:x}".format(x) for x in pkt[offset:offset+6]]))
    return

def print_ip(pkt, offset):
    print('.'.join([str(x) for x in pkt[offset:offset+4]]))
    return

def ethertype(pkt, offset):
    ethtype = (pkt[offset] << 8) + pkt[offset+1]
    types = {
        ETHERTYPE_IPV4: "IPv4",
        ETHERTYPE_ARP: "ARP",
        ETHERTYPE_WOL: "Wake-on-LAN",
        ETHERTYPE_VLAN: "VLAN-tagged frame (IEEE 802.1Q)",
        ETHERTYPE_IPV6: "IPv6",
        ETHERTYPE_STAG: "Service VLAN tag identifier (S-Tag) on Q-in-Q Tunnel",
        ETHERTYPE_PTP: "Precision Time Protocol (PTP) over IEEE 802.3 Ethernet",
    }
    return (ethtype, types.get(ethtype, "Unknown 0x{:x}".format(ethtype)))

def _ipv4_protocol(pkt, offset):
    protocol = pkt[offset]
    protos = {
        IP_PROTOCOL_IP: "IP  # internet protocol, pseudo protocol number",
        IP_PROTOCOL_ICMP: "ICMP  # internet control message protocol",
        IP_PROTOCOL_IPENCAP: "IP-ENCAP # IP encapsulated in IP (officially ``IP'')",
        IP_PROTOCOL_TCP: "TCP  # transmission control protocol",
        IP_PROTOCOL_EGP: "EGP  # exterior gateway protocol",
        IP_PROTOCOL_UDP: "UDP  # user datagram protocol",
        IP_PROTOCOL_HMP: "HMP  # host monitoring protocol",
        IP_PROTOCOL_RDP: "RDP  # \"reliable datagram\" protocol",
        IP_PROTOCOL_DDP: "DDP  # Datagram Delivery Protocol",
        IP_PROTOCOL_IPV6: "IPv6  # Internet Protocol, version 6",
        IP_PROTOCOL_IPV6_ROUTE: "IPv6-Route # Routing Header for IPv6",
        IP_PROTOCOL_IPV6_FRAG: "IPv6-Frag # Fragment Header for IPv6",
        IP_PROTOCOL_IDRP: "IDRP  # Inter-Domain Routing Protocol",
        IP_PROTOCOL_IPV6_ICMP: "IPv6-ICMP # ICMP for IPv6",
        IP_PROTOCOL_IPV6_NONXT: "IPv6-NoNxt # No Next Header for IPv6",
        IP_PROTOCOL_IPV6_OPTS: "IPv6-Opts # Destination Options for IPv6",
        IP_PROTOCOL_PIM : "PIM  # Protocol Independent Multicast",
        IP_PROTOCOL_L2TP: "L2TP  # Layer Two Tunneling Protocol [RFC2661]",
        IP_PROTOCOL_SCTP: "SCTP  # Stream Control Transmission Protocol",
        IP_PROTOCOL_UDPLITE: "UDPLite  # UDP-Lite [RFC3828]",
    }
    return (protocol, protos.get(protocol, "Unknown 0x{:x}".format(protocol)))

def _ipv4_decoder(pkt):
    version = pkt[OFFSET_IP_VERSION_IHL] >> 4
    if version != 4:
        print("=== ERROR: IPv4 Version is {}. Should be 4".format(version))
    ihl = pkt[OFFSET_IP_VERSION_IHL] & 0xf
    _len = 4*ihl
    if (ihl < 5) or (ihl > 15):
        print("=== ERROR: Invalid IPv4 header length. IHL = {} (len = {})".format(ihl, _len))
        ihl = None # Suppress further parsing
    total_len = (pkt[OFFSET_IP_TOTAL_LENGTH] << 8) + pkt[OFFSET_IP_TOTAL_LENGTH+1]
    print("TOTAL_LEN: {}".format(total_len))
    ttl = pkt[OFFSET_IP_TTL]
    print("TTL: {}".format(ttl))
    protocol, _protostr = _ipv4_protocol(pkt, OFFSET_IP_PROTOCOL)
    print("PROTOCOL: {}".format(_protostr))
    checksum = (pkt[OFFSET_IP_CHECKSUM] << 8) + pkt[OFFSET_IP_CHECKSUM+1]
    print("CHECKSUM: 0x{:04x}".format(checksum))
    print("SOURCE_IP: ", end="")
    print_ip(pkt, OFFSET_IP_SRC_IP)
    print("DEST_IP: ", end="")
    print_ip(pkt, OFFSET_IP_DEST_IP)
    if len(pkt) >= 14+total_len:
        payload = pkt[14+(4*ihl):14+total_len]
    else:
        payload = pkt[14+(4*ihl):]
    if ihl is not None:
        if (protocol == IP_PROTOCOL_ICMP):
            _ipv4_icmp_decoder(payload)
        elif (protocol == IP_PROTOCOL_UDP):
            _ipv4_udp_decoder(payload)
        else:
            print("No decoder for {}".format(_protostr))
    if (len(pkt) > 14+total_len):
        crc32 = "0x" + ''.join(["{:02x}".format(x) for x in pkt[14+total_len:]])
        print("CRC32: {}".format(crc32))
    else:
        print("CRC32: (truncated)")
    return

def _ipv4_icmp_decoder(payload):
    _type = payload[PAYLOAD_OFFSET_ICMP_TYPE]
    _code = payload[PAYLOAD_OFFSET_ICMP_CODE]
    if (_type == 8) and (_code == 0):
        print("TYPE/CODE: ICMP Request")
    elif (_type == 0) and (_code == 0):
        print("TYPE/CODE: ICMP Reply")
    else:
        print("TYPE/CODE: Unknown ({}/{})".format(_type, _code))
    checksum = (payload[PAYLOAD_OFFSET_ICMP_CHECKSUM] << 8) + payload[PAYLOAD_OFFSET_ICMP_CHECKSUM+1]
    print("ICMP_CHECKSUM: 0x{:04x}".format(checksum))
    roh = payload[PAYLOAD_OFFSET_ICMP_REST_OF_HEADER:]
    print("REST_OF_HEADER: {}".format([hex(x) for x in roh]))
    return

def _ipv4_udp_decoder(payload):
    src_port = (payload[PAYLOAD_OFFSET_UDP_SRC_PORT] << 8) + payload[PAYLOAD_OFFSET_UDP_SRC_PORT +1]
    print("SRC_PORT: {}".format(src_port))
    dest_port = (payload[PAYLOAD_OFFSET_UDP_DEST_PORT] << 8) + payload[PAYLOAD_OFFSET_UDP_DEST_PORT +1]
    print("DEST_PORT: {}".format(dest_port))
    length = (payload[PAYLOAD_OFFSET_UDP_LENGTH] << 8) + payload[PAYLOAD_OFFSET_UDP_LENGTH +1]
    print("UDP_LENGTH: {}".format(length))
    checksum = (payload[PAYLOAD_OFFSET_UDP_CHECKSUM] << 8) + payload[PAYLOAD_OFFSET_UDP_CHECKSUM +1]
    print("UDP_CHECKSUM: 0x{:04x}".format(checksum))
    data = payload[PAYLOAD_OFFSET_UDP_DATA:]
    print("UDP_DATA: {}".format([hex(x) for x in data]))
    return

def _arp_decoder(pkt):
    # HTYPE (ethernet = 0x0001)
    htype = (pkt[OFFSET_ARP_HTYPE] << 8) + pkt[OFFSET_ARP_HTYPE + 1]
    if htype == 0x0001:
        print("HTYPE: Ethernet")
    else:
        print("HTYPE: Unknown 0x{:x}".format(htype))
    # PTYPE (protocol type)
    ptype = (pkt[OFFSET_ARP_PTYPE] << 8) + pkt[OFFSET_ARP_PTYPE + 1]
    if ptype == 0x0800:
        print("PTYPE: IPv4")
    else:
        print("PTYPE: Unknown 0x{:x}".format(ptype))
    # Hardware address length
    hlen = pkt[OFFSET_ARP_HLEN]
    if hlen != 6:
        print("=== ERROR: HLEN is {}. Should be 6".format(hlen))
    # IP address length
    plen = pkt[OFFSET_ARP_PLEN]
    if plen != 4:
        print("=== ERROR: PLEN is {}. Should be 4".format(plen))
    # Operation
    oper = (pkt[OFFSET_ARP_OPER] << 8) + pkt[OFFSET_ARP_OPER + 1]
    if oper == 1:
        print("OPER: request")
    elif oper == 2:
        print("OPER: reply")
    else:
        print("=== ERROR: Unknown OPER 0x{:x}".format(OPER))
    # SHA/SPA
    print("SHA: ", end="")
    print_mac(pkt, OFFSET_ARP_SHA)
    print("SPA: ", end="")
    print_ip(pkt, OFFSET_ARP_SPA)
    # THA/TPA
    print("THA: ", end="")
    print_mac(pkt, OFFSET_ARP_THA)
    print("TPA: ", end="")
    print_ip(pkt, OFFSET_ARP_TPA)
    return

def get_pkt_docoder(ethtype):
    if ethtype == ETHERTYPE_IPV4:
        return _ipv4_decoder
    elif ethtype == ETHERTYPE_ARP:
        return _arp_decoder
    elif ethtype == ETHERTYPE_WOL:
        print("TODO: WOL decoder")
    elif ethtype == ETHERTYPE_IPV6:
        return _ipv6_decoder
    else:
        print("I'm not writing a decoder for this")
    return None

def _ipv6_next_header(pkt, offset):
    next_header = pkt[offset]
    next_headers = {
        EXTENSION_HEADER_HOP_BY_HOP_OPTIONS: "Hop-by-Hop Options",
        EXTENSION_HEADER_ROUTING: "Routing",
        EXTENSION_HEADER_FRAGMENT: "Fragment",
        EXTENSION_HEADER_ESP: "Encapsulating Security Payload",
        EXTENSION_HEADER_AUTHENTICATION: "Authentication Header",
        EXTENSION_HEADER_DESTINATION_OPTIONS: "Destination Options",
        EXTENSION_HEADER_MOBILITY: "Mobility",
        EXTENSION_HEADER_HOST_ID_PROTOCOL: "Host Identity Protocol",
        EXTENSION_HEADER_SHIM6_PROTOCOL: "Shim6 Protocol",
        EXTENSION_HEADER_RESERVED0: "Reserved for future use: {}".format(EXTENSION_HEADER_RESERVED0),
        EXTENSION_HEADER_RESERVED1: "Reserved for future use: {}".format(EXTENSION_HEADER_RESERVED1),
        EXTENSION_HEADER_NOTHING: "{}: Ignore anything following this header.".format(EXTENSION_HEADER_NOTHING),
    }
    nhstr = next_headers.get(next_header, None)
    if nhstr is None:
        protocol, protostr = _ipv4_protocol(pkt, offset)
        return (False, protocol, protostr)
    return (True, next_header, "IPv6 Ext: " + nhstr)

def _ipv6_ip(pkt, offset):
    l = []
    for n in range(8):
        # Group as 16-bit hex numbers
        _b = (pkt[offset+(2*n)] << 8) + pkt[offset+(2*n + 1)]
        if _b == 0:
            # IPv6 address notation allows zeros to be skipped
            l.append("")
        else:
            l.append("{:04x}".format(_b))
    return ":".join(l)

def _ipv6_ext_header_decoder(pkt, offset, header_type):
    if header_type == EXTENSION_HEADER_FRAGMENT:
        ext_length = 8
    else:
        ext_length = pkt[offset+1]
    is_ext, next_header, nhstr = _ipv6_next_header(pkt, offset)
    print("NEXT_HEADER: {}".format(nhstr))
    if is_ext:
        return _ipv6_ext_header_decoder(pkt, offset + ext_length, next_header)
    else:
        payload = pkt[offset+ext_length:]
        if (next_header == IP_PROTOCOL_ICMP):
            _ipv4_icmp_decoder(payload)
        elif (next_header == IP_PROTOCOL_UDP):
            _ipv4_udp_decoder(payload)
        if (next_header == IP_PROTOCOL_IPV6_ICMP):
            _ipv6_icmp_decoder(payload)
        else:
            print("No decoder for {}".format(nhstr))
    return

def _ipv6_icmp_decoder(payload):
    print("TODO IPv6_ICMP decoder")
    return

def _ipv6_decoder(pkt):
    version = pkt[OFFSET_IPV6_VERSION_TC_FLOWLABEL] >> 4
    if version != 6:
        print("=== ERROR: IPv6 Version is {}. Should be 6".format(version))
    payload_len = (pkt[OFFSET_IPV6_PAYLOAD_LENGTH] << 8) + pkt[OFFSET_IPV6_PAYLOAD_LENGTH+1]
    print("PAYLOAD_LENGTH: {}".format(payload_len))
    is_ext, next_header, nhstr = _ipv6_next_header(pkt, OFFSET_IPV6_NEXT_HEADER)
    print("NEXT_HEADER: {}".format(nhstr))
    print("HOP_LIMIT: {}".format(pkt[OFFSET_IPV6_HOP_LIMIT]))
    ipv6_src_ip = _ipv6_ip(pkt, OFFSET_IPV6_SRC_IP)
    print("SOURCE_IP: {}".format(ipv6_src_ip))
    ipv6_dest_ip = _ipv6_ip(pkt, OFFSET_IPV6_DEST_IP   )
    print("DEST_IP: {}".format(ipv6_dest_ip))
    if is_ext:
        return _ipv6_ext_header_decoder(pkt, OFFSET_IPV6_PAYLOAD, next_header)
    else:
        payload = pkt[OFFSET_IPV6_PAYLOAD:]
        if (next_header == IP_PROTOCOL_ICMP):
            _ipv4_icmp_decoder(payload)
        elif (next_header == IP_PROTOCOL_UDP):
            _ipv4_udp_decoder(payload)
        if (next_header == IP_PROTOCOL_IPV6_ICMP):
            _ipv6_icmp_decoder(payload)
        else:
            print("No decoder for {}".format(nhstr))
    return

def findStart(pkt):
    """Allow for packets with preamble and start sequence by first
    finding the beginning of packet data and returning that index."""
    preamble_detected = False
    # Just look at the first 8 bytes
    for n in range(8):
        _b = pkt[n]
        if preamble_detected:
            if _b not in (0x55, 0xaa, 0xd5, 0xab):
                # Give up and return the start
                break
            else:
                if _b in (0xd5, 0xab):
                    return n+1
        else:
            if _b in (0x55, 0xaa):
                preamble_detected = True
    return 0

def decode(pkt):
    start = findStart(pkt)
    # Discard the preamble & SOF
    pkt = pkt[start:]
    _len = len(pkt)
    if _len < MIN_PKT_SIZE:
        print("Pkt too small ({} < {})".format(len(pkt), MIN_PKT_SIZE))
    print("DEST_MAC: ", end="")
    print_mac(pkt, OFFSET_DEST_MAC)
    print("SRC_MAC: ", end="")
    print_mac(pkt, OFFSET_SRC_MAC)
    _ethtype, _etstr = ethertype(pkt, OFFSET_ETHERTYPE)
    print("ETHERTYPE: {}".format(_etstr))
    _decoder = get_pkt_docoder(_ethtype)
    if _decoder is not None:
        _decoder(pkt)
    return

def doPktDecode(argv):
    pktHex = argv[1:]
    lhex = []
    for arg in argv[1:]:
        lhex.extend(arg.split())
    pkt = [int(x, 16) for x in lhex]
    decode(pkt)

if __name__ == "__main__":
    import sys
    doPktDecode(sys.argv)
