import os

SYSTEMD_DETECT_VIRT = "systemd-detect-virt"
SUPPORTED_VIRT_ENGINES = ["qemu", "kvm", "vmware", "xen", "microsoft", "lxc"]

def DetectVirtualization():
    settings.params.general.type = 'physical'
    settings.params.general.virtualization = 'none'
    virt = os.popen(SYSTEMD_DETECT_VIRT).read()
    for engine in SUPPORTED_VIRT_ENGINES:
        if virt.startswith(engine):
            settings.params.general.type = 'virtual'
            settings.params.general.virtualization = engine
            break
