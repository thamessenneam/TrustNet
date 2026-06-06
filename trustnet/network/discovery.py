"""mDNS peer discovery — auto-finds TrustNet nodes on the local network."""

import socket
import threading
import time
from trustnet.network import DEFAULT_PORT, SERVICE_TYPE

_zeroconf = None
_browser  = None
_info     = None
_lock     = threading.Lock()

_on_found_cb   = None
_on_removed_cb = None


def _local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def start(node_id: str, port: int = DEFAULT_PORT,
          on_found=None, on_removed=None) -> bool:
    """Register this node and browse for peers. Returns True on success."""
    global _zeroconf, _browser, _info, _on_found_cb, _on_removed_cb
    try:
        from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser

        _on_found_cb   = on_found
        _on_removed_cb = on_removed

        local_ip = _local_ip()
        service_name = f"TrustNet-{node_id[:12]}.{SERVICE_TYPE}"

        _info = ServiceInfo(
            SERVICE_TYPE,
            service_name,
            addresses=[socket.inet_aton(local_ip)],
            port=port,
            properties={
                b"node_id": node_id.encode(),
                b"version": b"1.0.0",
            },
        )

        _zeroconf = Zeroconf()
        _zeroconf.register_service(_info)

        class _Listener:
            def add_service(self, zc, stype, name):
                info = zc.get_service_info(stype, name)
                if info and _on_found_cb:
                    for addr in info.parsed_scoped_addresses():
                        if addr != local_ip:
                            props = {
                                k.decode(): v.decode() if isinstance(v, bytes) else v
                                for k, v in (info.properties or {}).items()
                            }
                            _on_found_cb(addr, info.port, props.get("node_id", ""))
                            break

            def remove_service(self, zc, stype, name):
                if _on_removed_cb:
                    try:
                        info = zc.get_service_info(stype, name)
                        if info:
                            for addr in info.parsed_scoped_addresses():
                                _on_removed_cb(addr, info.port)
                                break
                    except Exception:
                        pass

            def update_service(self, zc, stype, name):
                pass

        _browser = ServiceBrowser(_zeroconf, SERVICE_TYPE, _Listener())
        return True
    except Exception as e:
        return False


def stop() -> None:
    global _zeroconf, _browser, _info
    try:
        if _zeroconf and _info:
            _zeroconf.unregister_service(_info)
            _zeroconf.close()
    except Exception:
        pass
    _zeroconf = _browser = _info = None
