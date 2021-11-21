from __future__ import annotations

import argparse
import os.path
import subprocess
import tempfile
from typing import NamedTuple

from packaging.version import Version
from packaging.markers import Marker
from packaging.specifiers import Specifier


class PyBI(NamedTuple):
    impl: str
    version: Version
    platform: str

    @classmethod
    def parse(cls, s: str) -> PyBI:
        base, _ = os.path.splitext(os.path.basename(s))
        impl, version_s, platform = base.split('-', 2)
        version = Version(version_s)

        return cls(impl, version, platform)


class Module(NamedTuple):
    mod: str
    specifier: Specifier | None = None
    marker: Marker | None = None

    def is_satisfied(self, info: PyBI) -> bool:
        satisfied = True

        if self.specifier is not None:
            satisfied &= self.specifier.contains(info.version)

        if self.marker is not None:
            sys_platform = PLATFORM_TAG_TO_SYS_PLATFORM[info.platform]
            satisfied &= self.marker.evaluate({"sys_platform": sys_platform})

        return satisfied


PLATFORM_TAG_TO_SYS_PLATFORM = {
    'macosx_10_6_intel': 'darwin',
    'macosx_10_9_x86_64': 'darwin',
    'macosx_11_0_universal2': 'darwin',
    'manylinux_2_17_x86_64': 'linux',
    'win32': 'win32',
    'win_amd64': 'win32',
}

MODULES: tuple[Module, ...] = (
    Module('ctypes'),
    Module('hashlib'),
    Module('lzma'),
    Module('sqlite3'),
    Module('ssl'),
    Module('tkinter'),
    Module('uuid'),  # TODO: run a test on the particular function
    Module('venv'),  # TODO: make sure we can create a venv
    Module('zlib'),
    # not on windows
    Module('curses', marker=Marker('sys_platform!="win32"')),
    Module('readline', marker=Marker('sys_platform!="win32"')),
    Module('dbm.gnu', marker=Marker('sys_platform!="win32"')),
    Module('dbm.ndbm', marker=Marker('sys_platform!="win32"')),
    # version specific

    # uuid is available on non-windows platform or on windows starting in 3.9
    Module('_uuid', marker=Marker('sys_platform!="win32"')),
    Module(
        '_uuid',
        # TODO: which alpha version?
        specifier=Specifier('>=3.9'),
        marker=Marker('sys_platform=="win32"'),
    ),
)


def _get_modules_for_info(info: PyBI) -> list[Module]:
    return [module for module in MODULES if module.is_satisfied(info)]


def test_imports(exe: str, info: PyBI) -> None:
    imports = ', '.join(module.mod for module in _get_modules_for_info(info))
    print(f'importing: {imports}')
    import_str = f'import {imports}'
    subprocess.check_call((exe, '-c', import_str))


def _header(s: str) -> None:
    print(f' {s} '.center(79, '='))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('zip')
    args = parser.parse_args()

    _header('zip info')
    info = PyBI.parse(args.zip)
    print(info)

    with tempfile.TemporaryDirectory() as tmpdir:
        # TODO: replace this with python
        subprocess.check_call(('unzip', '-qq', '-d', tmpdir, args.zip))

        exe = os.path.join(tmpdir, 'bin', 'python')

        _header('--version --version')
        subprocess.check_call((exe, '--version', '--version'))

        _header(test_imports.__name__)
        test_imports(exe, info)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
