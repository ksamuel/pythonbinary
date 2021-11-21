from __future__ import annotations

import os.path
from typing import NamedTuple

from packaging.version import Version


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

    @property
    def bin_dir(self) -> str:
        if self.platform in {'win32', 'win_amd64'}:
            return 'Scripts'
        elif self.platform.startswith('macosx'):
            py_minor = f'{self.version.major}.{self.version.minor}'
            return f'Python.framework/Versions/{py_minor}/bin'
        else:
            return 'bin'

    def exe(self, s: str) -> str:
        if self.platform in {'win32', 'win_amd64'}:
            return f'{s}.exe'
        else:
            return s

    def python(self, root: str) -> str:
        return os.path.join(root, self.bin_dir, self.exe('python'))
