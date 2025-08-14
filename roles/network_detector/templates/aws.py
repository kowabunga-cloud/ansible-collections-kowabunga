import json
import requests

AWS_METADATA_URL = "http://169.254.169.254/latest"

class Ec2Metadata(object):
    def __init__(self):
        self.session = requests.Session()
        self.base_url = AWS_METADATA_URL
        self.dynamic_url = self.base_url + "/dynamic"
        self.meta_url = self.base_url + "/meta-data"

    def verify(self):
        try:
            self.session.get(self.base_url, timeout=0.1)
            return True
        except:
            return False

    def get(self, url, dynamic=False):
        uri = (self.dynamic_url if dynamic else self.meta_url) + url
        resp = self.session.get(uri, timeout=1.0)
        if resp.status_code != 200:
            return None
        return resp

    def text(self, url, dynamic=False):
        res = self.get(url, dynamic)
        return res.text if res else ""

    def json(self, url, dynamic=False):
        res = self.get(url, dynamic)
        return res.json() if res else {}

def DetectAwsSettings():
    meta = Ec2Metadata()
    if not meta.verify():
        return

    aws = settings.params.aws
    aws.az = meta.text("/placement/availability-zone")
    identity = meta.json("/instance-identity/document", True)
    aws.region = identity.get("region")
    aws.instance_id = meta.text("/instance-id")
    aws.instance_type = meta.text("/instance-type")

    aws.network.ipv4.private = meta.text("/local-ipv4")
    aws.network.ipv4.public = meta.text("/public-ipv4")

    macs_text = meta.text("/network/interfaces/macs")
    macs = [line.rstrip("/") for line in macs_text.splitlines()]
    if len(macs) > 0:
        mac = macs[0]
        net_url = f'/network/interfaces/macs/{mac}'
        aws.network.hostname.private = meta.text(net_url + "/local-hostname")
        aws.network.hostname.public = meta.text(net_url + "/public-hostname")
    for m in macs:
        n = aws.network.nics[m]
        net_url = f'/network/interfaces/macs/{m}'
        n.id = meta.text(net_url + "/interface-id")
        n.subnet.id = meta.text(net_url + "/subnet-id")
        n.subnet.ipv4 = meta.text(net_url + "/subnet-ipv4-cidr-block")
        n.vpc.id = meta.text(net_url + "/vpc-id")
        n.vpc.ipv4 = meta.text(net_url + "/vpc-ipv4-cidr-block")
        n.security_groups = meta.text(net_url + "/security-groups").splitlines()
        n.hostname.private = meta.text(net_url + "/local-hostname")
        n.hostname.public = meta.text(net_url + "/public-hostname")
        n.ipv4.private = meta.text(net_url + "/local-ipv4s").splitlines()
        n.ipv4.public = meta.text(net_url + "/pulibc-ipv4s").splitlines()
