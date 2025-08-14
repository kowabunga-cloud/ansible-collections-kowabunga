import netifaces
import ipaddress
import subprocess

NIC_ETHERNET_PREFIX = [ "en", "eth", "vlan", "macvlan", "ipvlan", "ipvl", "bond", "br", "wan", "lan" ]
NIC_ETHERNET_PREFIX_BLACKLIST = [ "docker", "br-" ]

def InterfaceAddresses(iface, gateways):
    addr = netifaces.ifaddresses(iface)
    if not netifaces.AF_INET in addr:
        return

    s = settings.params.network.interfaces[iface]
    if netifaces.AF_LINK in addr:
        s.hw = addr[netifaces.AF_LINK][0]['addr']
    inet = addr[netifaces.AF_INET]
    s.ip = inet[0]['addr']
    s.netmask = inet[0]['netmask']
    s.private = ipaddress.ip_address(s.ip).is_private

    # is there an associated gateway ?
    s.default = False
    for gw in gateways[netifaces.AF_INET]:
        if gw[1] != iface:
            continue
        s.gateway = gw[0]
        s.default = gw[2]

    vlan_idx = iface.find('.')
    if vlan_idx != -1 or iface.startswith("vlan"):
        base_query = "sudo cat /proc/net/vlan/" + iface
        dev_query = base_query + " | grep Device | sed \'s/Device: //\'"
        id_query = base_query + " | head -1 | cut -d \':\' -f 2 | sed \'s% *\([0-9]*\).*%\\1%\'"
        s.vlan.dev = subprocess.Popen([dev_query], shell=True, stdout=subprocess.PIPE).communicate()[0].rstrip().decode("utf-8")
        s.vlan.id = subprocess.Popen([id_query], shell=True, stdout=subprocess.PIPE).communicate()[0].rstrip().decode("utf-8")

class ContinueLoop(Exception):
    pass
continue_loop = ContinueLoop()

def DetectNetworkInterfaces():
    interfaces = netifaces.interfaces()
    gws = netifaces.gateways()
    for i in sorted(interfaces):
        try:
            for b in NIC_ETHERNET_PREFIX_BLACKLIST:
                if i.startswith(b):
                    raise continue_loop
            for p in NIC_ETHERNET_PREFIX:
                if i.startswith(p):
                    InterfaceAddresses(i, gws)
                    continue
        except:
            continue
