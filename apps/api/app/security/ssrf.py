import ipaddress
import socket

_BLOCKED_HOSTS = frozenset({
    "169.254.169.254",  
    "metadata.google.internal",
    "metadata.google.com",
    "100.100.100.200", 
})

_BLOCKED_CIDR = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
]

def is_private_ip(ip_str: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return any(addr in net for net in _BLOCKED_CIDR)

def check_ssrf(url: str) -> str | None:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return "No hostname in URL"

    if hostname in _BLOCKED_HOSTS:
        return f"Blocked host: {hostname} (cloud metadata endpoint)"

    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        literal = None
        
    if literal is not None:
        if is_private_ip(hostname):
            return f"URL resolves to private IP: {hostname}"
        return None

    try:
        resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for _, _, _, _, sockaddr in resolved:
            ip = sockaddr[0]
            if is_private_ip(ip):
                return f"URL resolves to private IP: {ip}"
    except socket.gaierror:
        pass

    return None
