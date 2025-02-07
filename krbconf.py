from argparse import ArgumentParser, Namespace
import argparse
import base64
import hashlib
import itertools
import os
import shlex
import sys
from typing import NoReturn

from impacket.krb5.ccache import CCache

KRBCONF_PREFIX = '/tmp/krbconf-'


class CustomParser(ArgumentParser):
    def print_help(self, file=None) -> None:
        print(self.format_help(), file=sys.stderr)

    def error(self, message: str) -> NoReturn:
        print(message, file=sys.stderr)
        sys.exit(1)


def main() -> None:
    entrypoint = CustomParser()
    parsers = entrypoint.add_subparsers(dest='command', required=True)

    parser = parsers.add_parser('import')
    parser.add_argument('-K', '--kdc', default='', metavar='HOSTNAME|FQDN')
    parser.add_argument('input', nargs='?', default='', metavar='-|base64:KIRBIBLOB|KIRBIFILE')
    parser.add_argument('output', nargs='?', default='', metavar='CCACHEFILE')

    parser = parsers.add_parser('export')
    parser.add_argument('input', nargs='?', default='', metavar='CCACHEFILE')

    parser = parsers.add_parser('set')
    parser.add_argument('-K', '--kdc', default='', metavar='HOSTNAME|FQDN')
    parser.add_argument('input', nargs=1, default='', metavar='CCACHEFILE')

    parser = parsers.add_parser('unset')

    parser = parsers.add_parser('whoami')
    parser.add_argument('input', nargs='?', default='', metavar='CCACHEFILE')

    parser = parsers.add_parser('exec')
    parser.add_argument('-K', '--kdc', default='', metavar='HOSTNAME|FQDN')
    parser.add_argument('input', nargs=1, default='', metavar='CCACHEFILE')
    parser.add_argument('cmdline', nargs=argparse.REMAINDER, metavar='COMMAND...')

    opts = entrypoint.parse_args()

    try:
        globals()[f'ccache_{opts.command}'](opts)
    except Exception as e:
        print(f'{e.__class__.__name__}: {e}', file=sys.stderr)
        exit(1)


def ccache_import(opts: Namespace) -> None:
    if not opts.input or opts.input == '-':
        ccache = CCache()
        ccache.fromKRBCRED(base64.b64decode(sys.stdin.buffer.read()))
    elif opts.input.startswith('base64:'):
        ccache = CCache()
        ccache.fromKRBCRED(base64.b64decode(opts.input.removeprefix('base64:')))
    elif opts.input.endswith('.kirbi'):
        ccache = CCache.loadKirbiFile(opts.input)
    else:
        raise ValueError('invalid input')
    if not ccache:
        raise ValueError('invalid kirbi ticket')

    domain, user, host = _extract_user_info(ccache)

    if opts.output:
        filename = opts.output
    else:
        filename = f'{user}.ccache'
        if os.path.exists(filename):
            newhash = hashlib.md5(ccache.getData()).hexdigest()
            with open(filename, 'rb') as file:
                oldhash = hashlib.md5(file.read()).hexdigest()
            if newhash != oldhash:
                for i in itertools.count():
                    filename = f'{user}{i}.ccache'
                    if not os.path.exists(filename):
                        break

    ccache.saveFile(filename)
    confpath = write_krbconf(domain, opts.kdc)
    print(_generate_exports(filename, domain, user, host, opts.kdc, confpath))


def ccache_export(opts: Namespace) -> None:
    ccache = CCache.loadFile(opts.input or os.environ['KRB5CCNAME'])
    if not ccache:
        raise ValueError('invalid ccache ticket')
    print(f'echo {base64.b64encode(ccache.toKRBCRED()).decode()}')


def ccache_set(opts: Namespace) -> None:
    ccache = CCache.loadFile(opts.input[0])
    if not ccache:
        raise ValueError('invalid ccache ticket')
    domain, user, host = _extract_user_info(ccache)
    confpath = write_krbconf(domain, opts.kdc)
    print(_generate_exports(opts.input[0], domain, user, host, opts.kdc, confpath))


def ccache_unset(_) -> None:
    confpath = os.environ.get('KRB5_CONFIG')
    if confpath and confpath.startswith(KRBCONF_PREFIX):
        os.unlink(confpath)
    print('unset KRB5CCNAME KRB5_CONFIG KRB5CCNAME_DOMAIN KRB5CCNAME_USER KRB5CCNAME_KDC KRB5CCNAME_HOST')


def ccache_whoami(opts: Namespace) -> None:
    ccache = CCache.loadFile(opts.input or os.environ['KRB5CCNAME'])
    if not ccache:
        raise ValueError('invalid ccache ticket')
    domain, user, host = _extract_user_info(ccache)
    info = f'{domain}/{user}@{host}' if host else f'{domain}/{user}'
    print(f'echo {shlex.quote(info)}')


def ccache_exec(opts: Namespace) -> None:
    filename = opts.input[0] or os.environ['KRB5CCNAME']
    ccache = CCache.loadFile(filename)
    if not ccache:
        raise ValueError('invalid ccache ticket')
    domain, user, host = _extract_user_info(ccache)
    cmdline = ' '.join(shlex.quote(item) for item in opts.cmdline) if opts.cmdline else os.environ.get('SHELL', '/bin/sh')
    confpath = write_krbconf(domain, opts.kdc)
    print(_generate_variables(filename, domain, user, host, opts.kdc, confpath) + ' ' + cmdline)


def _extract_user_info(ccache: CCache) -> tuple[str, str, str]:
    credential = ccache.credentials[0]
    user = credential['client'].toPrincipal()
    assert len(user.components) == 1
    server = credential['server'].toPrincipal()
    assert len(server.components) == 2
    domain = user.realm.lower()
    username = user.components[0].lower()
    service = server.components[0].lower()
    hostname = '' if service == 'krbtgt' else server.components[1].lower()
    return domain, username, hostname


def _generate_exports(path: str, domain: str, user: str, host: str, kdc: str|None, krbconf: str|None) -> str:
    return f'export {_generate_variables(path, domain, user, host, kdc, krbconf)}'


def _generate_variables(path: str, domain: str, user: str, host: str, kdc: str|None, krbconf: str|None) -> str:
    return f'KRB5CCNAME={shlex.quote(os.path.realpath(path))} KRB5_CONFIG={shlex.quote(krbconf) if krbconf else ''} KRB5CCNAME_DOMAIN={shlex.quote(domain)} KRB5CCNAME_USER={shlex.quote(user)} KRB5CCNAME_KDC={shlex.quote(kdc) if kdc else ''} KRB5CCNAME_HOST={shlex.quote(host)}'


def write_krbconf(domain: str, kdc: str) -> str:
    pid = os.environ.get('SHELL_PID', '0')
    path = f'{KRBCONF_PREFIX}{pid}.conf'
    with open(path, 'w') as file:
        file.write(_generate_krbconf(domain, kdc))
    return path


def _generate_krbconf(domain: str, kdc: str) -> str:
    if '.' not in kdc:
        kdc = f'{kdc}.{domain}'
    return '\n'.join([
        r'[libdefaults]',
        r'  dns_lookup_kdc = false',
        r'  dns_lookup_realm = false',
        f'  default_realm = {domain.upper()}',
        r'',
        r'[realms]',
        f'  {domain.upper()} = ' + '{',
        f'    kdc = {kdc.lower()}',
        f'    admin_server = {kdc.lower()}',
        f'    default_domain = {domain.lower()}',
        r'  }',
        r'',
        r'[domain_realm]',
        f'  .{domain.lower()} = {domain.upper()}',
        f'  {domain.lower()} = {domain.upper()}',
    ])


if __name__ == '__main__':
    main()
