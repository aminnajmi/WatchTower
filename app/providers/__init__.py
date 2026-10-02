from .ubuntu import UbuntuProvider
from .almalinux import AlmaLinuxProvider
from .fedora import FedoraProvider
from .rockylinux import RockyLinuxProvider
from .debian import DebianProvider
from .archlinux import ArchLinuxProvider
from .centos import CentOSProvider

PROVIDERS = {
    "ubuntu": UbuntuProvider(),
    "almalinux": AlmaLinuxProvider(),
    "fedora": FedoraProvider(),
    "rockylinux": RockyLinuxProvider(),
    "debian": DebianProvider(),
    "archlinux": ArchLinuxProvider(),
    "centos": CentOSProvider(),
}
