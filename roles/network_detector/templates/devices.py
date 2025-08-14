def set_interface(s, interfaces, iface):
    s.dev = iface
    if interfaces[iface].vlan.dev:
        s.raw_dev = interfaces[iface].vlan.dev
    s.ip = interfaces[iface].ip
    s.netmask = interfaces[iface].netmask
    if interfaces[iface].gateway:
        s.gateway = interfaces[iface].gateway
    return True

def set_primary_private_interface(interfaces, iface):
    if 'primary' in settings.params.network.devices.private:
        return False
    primary = settings.params.network.devices.private.primary
    return set_interface(primary, interfaces, iface)

def set_secondary_private_interface(interfaces, iface):
    if 'secondary' in settings.params.network.devices.private:
        return False
    secondary = settings.params.network.devices.private.secondary
    return set_interface(secondary, interfaces, iface)

def set_primary_public_interface(interfaces, iface):
    if 'primary' in settings.params.network.devices.public:
        return False
    primary = settings.params.network.devices.public.primary
    return set_interface(primary, interfaces, iface)

def set_private_devices(interfaces):
    private_interfaces = []
    for i in interfaces:
        if interfaces[i].private:
            private_interfaces.append(i)

    if forced_primary_private_interface != "" and forced_primary_private_interface in private_interfaces:
        if set_primary_private_interface(interfaces, forced_primary_private_interface):
            private_interfaces.remove(forced_primary_private_interface)

    if forced_secondary_private_interface != "" and forced_secondary_private_interface in private_interfaces:
        if set_secondary_private_interface(interfaces, forced_secondary_private_interface):
            private_interfaces.remove(forced_secondary_private_interface)

    # auto-detect ...
    # prefer interface with default route, if any
    for i in private_interfaces:
        if interfaces[i].default:
            if set_primary_private_interface(interfaces, i):
                private_interfaces.remove(i)
                break
    # otherwise, take the first one we find as primary
    if len(private_interfaces) > 0:
        if set_primary_private_interface(interfaces, private_interfaces[0]):
            private_interfaces.remove(private_interfaces[0])
    # if there's one left, let's consider it as secondary
    if len(private_interfaces) > 0:
        if set_secondary_private_interface(interfaces, private_interfaces[0]):
            private_interfaces.remove(private_interfaces[0])

def set_public_devices(interfaces):
    public_interfaces = []
    for i in interfaces:
        if not interfaces[i].private:
            public_interfaces.append(i)

    if forced_primary_public_interface != "" and forced_primary_public_interface in public_interfaces:
        if set_primary_public_interface(interfaces, forced_primary_public_interface):
            public_interfaces.remove(forced_primary_public_interface)
    elif forced_primary_public_interface != "" and len(public_interfaces) == 0:
        set_primary_public_interface(interfaces, forced_primary_public_interface)

    # auto-detect ...
    # prefer interface with default route, if any
    for i in public_interfaces:
        if interfaces[i].default:
            if set_primary_public_interface(interfaces, i):
                public_interfaces.remove(i)
                break
    # otherwise, take the first one we find as primary
    if len(public_interfaces) > 0:
        if set_primary_public_interface(interfaces, public_interfaces[0]):
            public_interfaces.remove(public_interfaces[0])

def finalize_devices():
    if not settings.params.network.devices.public:
        settings.params.network.devices.public.primary = settings.params.network.devices.private.primary

    settings.params.network.devices.public.primary.mode = "direct"
    aws = settings.params.aws
    if aws:
        if aws.network.ipv4.public != "" and aws.network.ipv4.private != aws.network.ipv4.public:
            # unique network interface, use global info for NAT
            settings.params.network.devices.public.primary.mode = "nat"
