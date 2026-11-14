"""Audit-only pytest guard; no outbound connections or production service commands."""
import ipaddress
import socket
import subprocess
import pytest

@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_popen = subprocess.Popen
    def check(address):
        if isinstance(address, tuple):
            try: allowed = ipaddress.ip_address(address[0]).is_loopback
            except ValueError: allowed = address[0] == 'localhost'
            if not allowed: raise AssertionError('AUDIT_EXTERNAL_NETWORK_FORBIDDEN')
    def connect(sock, address):
        check(address)
        return original_connect(sock, address)
    def connect_ex(sock, address):
        check(address)
        return original_connect_ex(sock, address)
    def popen(args, *a, **kw):
        command = args if isinstance(args, str) else ' '.join(map(str, args))
        if any(word in command for word in ('launchctl', '/usr/bin/osascript', 'terminal-notifier')):
            raise AssertionError('AUDIT_PRODUCTION_COMMAND_FORBIDDEN')
        if isinstance(args, (list, tuple)) and args and str(args[0]).endswith('git') and any(x in args for x in ('fetch', 'push', 'pull')):
            raise AssertionError('AUDIT_GIT_REMOTE_MUTATION_FORBIDDEN')
        return original_popen(args, *a, **kw)
    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    subprocess.Popen = popen
