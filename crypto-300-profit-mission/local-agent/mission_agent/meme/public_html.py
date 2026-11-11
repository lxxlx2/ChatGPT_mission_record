"""One public HTTPS HTML read in a short-lived, credential-free worker.

No redirect, proxy, cookie, authentication, script execution or recursive crawl.
DNS is checked once and the checked IPv4 is pinned while TLS verifies the host.
"""
import base64
import http.client
import ipaddress
import json
from pathlib import Path
import re
import socket
import ssl
import subprocess
import sys
from urllib.parse import urlsplit,urlunsplit,unquote

MAX_HTML_BYTES=256*1024


def canonical_url(value):
    if not isinstance(value,str) or len(value)>2048 or any(ord(c)<33 or c=='\\' for c in value):raise ValueError('URL_NOT_ALLOWED')
    try:
        u=urlsplit(value);host=(u.hostname or '').lower().rstrip('.')
        host=host.encode('idna').decode('ascii')
        if u.scheme!='https' or u.username is not None or u.password is not None or u.port not in (None,443) or u.query:raise ValueError()
        if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?',host) or '.' not in host:raise ValueError()
        if any(host==suffix or host.endswith('.'+suffix) for suffix in ('localhost','local','internal','lan','home','onion','test','invalid','cn','xn--fiqs8s','xn--fiqz9s')):raise ValueError()
        try:ipaddress.ip_address(host)
        except ValueError:pass
        else:raise ValueError()
        path=u.path or '/'
        if len(path)>1024 or path.startswith('//') or any(ord(c)<32 or c=='\\' for c in unquote(path)):raise ValueError()
        return urlunsplit(('https',host,path,'',''))
    except (ValueError,UnicodeError):raise ValueError('URL_NOT_ALLOWED') from None


def public_address(value):
    try:ip=ipaddress.ip_address(value)
    except ValueError:return False
    return ip.is_global and not (ip.is_multicast or ip.is_reserved or ip.is_loopback or ip.is_link_local or ip.is_unspecified) and getattr(ip,'ipv4_mapped',None) is None


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self,host,ip,timeout=5):
        if not public_address(ip) or ipaddress.ip_address(ip).version!=4:raise ValueError('DNS_NOT_PUBLIC')
        super().__init__(host,443,timeout=timeout)
        self.pinned_ip=ip
    def connect(self):
        if self._tunnel_host or not self._context.check_hostname or self._context.verify_mode!=ssl.CERT_REQUIRED:raise ValueError('TLS_POLICY_INVALID')
        raw=socket.create_connection((self.pinned_ip,443),self.timeout)
        try:self.sock=self._context.wrap_socket(raw,server_hostname=self.host)
        except Exception:raw.close();raise


def fetch_public_html(url,*,resolver=socket.getaddrinfo,connection_factory=PinnedHTTPSConnection):
    try:url=canonical_url(url)
    except ValueError:return {'status':'UNAVAILABLE','reason':'URL_NOT_ALLOWED'}
    parsed=urlsplit(url);host=parsed.hostname
    try:
        records=resolver(host,443,type=socket.SOCK_STREAM)
        addresses={row[4][0] for row in records}
        if not addresses or len(addresses)>32 or not all(public_address(ip) for ip in addresses):return {'status':'UNAVAILABLE','reason':'DNS_NOT_PUBLIC'}
        ipv4=sorted(ip for ip in addresses if ipaddress.ip_address(ip).version==4)
        if not ipv4:return {'status':'UNAVAILABLE','reason':'PUBLIC_IPV4_UNAVAILABLE'}
    except (OSError,ValueError,TypeError,IndexError):return {'status':'UNAVAILABLE','reason':'DNS_UNAVAILABLE'}
    connection=None
    try:
        connection=connection_factory(host,ipv4[0],timeout=5)
        connection.request('GET',parsed.path or '/',headers={'Accept':'text/html, application/xhtml+xml','User-Agent':'mission-meme-research/4','Connection':'close'})
        response=connection.getresponse()
        if 300<=response.status<400:return {'status':'UNAVAILABLE','reason':'REDIRECT_NOT_FOLLOWED'}
        if response.status!=200:return {'status':'UNAVAILABLE','reason':'HTTP_'+str(response.status)}
        content_type=(response.getheader('Content-Type') or '').lower()
        if content_type.split(';')[0].strip() not in {'text/html','application/xhtml+xml'}:return {'status':'UNAVAILABLE','reason':'NOT_HTML'}
        encoding=(response.getheader('Content-Encoding') or 'identity').lower()
        if encoding!='identity':return {'status':'UNAVAILABLE','reason':'COMPRESSED_BODY_NOT_SUPPORTED'}
        raw=response.read(MAX_HTML_BYTES+1)
        if len(raw)>MAX_HTML_BYTES:return {'status':'UNAVAILABLE','reason':'RESPONSE_LIMIT'}
        return {'status':'OK','body_b64':base64.b64encode(raw).decode('ascii')}
    except (OSError,ValueError,http.client.HTTPException):return {'status':'UNAVAILABLE','reason':'SOURCE_UNAVAILABLE'}
    finally:
        if connection is not None:connection.close()


def read_public_html(url):
    try:url=canonical_url(url)
    except ValueError:return {'status':'UNAVAILABLE','reason':'URL_NOT_ALLOWED'}
    try:
        result=subprocess.run([sys.executable,'-I','-S',str(Path(__file__).resolve()),'--fetch',url],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=False,env={'LANG':'C'})
        if result.returncode!=0 or len(result.stdout)>2*MAX_HTML_BYTES:return {'status':'UNAVAILABLE','reason':'FETCH_WORKER_FAILED'}
        value=json.loads(result.stdout)
        if not isinstance(value,dict) or value.get('status') not in {'OK','UNAVAILABLE'}:raise ValueError()
        return value
    except subprocess.TimeoutExpired:return {'status':'UNAVAILABLE','reason':'FETCH_TIMEOUT'}
    except (OSError,ValueError,TypeError):return {'status':'UNAVAILABLE','reason':'FETCH_WORKER_FAILED'}


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--fetch':print(json.dumps(fetch_public_html(sys.argv[2])))
