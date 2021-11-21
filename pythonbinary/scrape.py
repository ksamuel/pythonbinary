from __future__ import annotations

import argparse
import hashlib
import html.parser
import os
import shutil
import sys
import tempfile
import urllib.parse
import urllib.request
from typing import NamedTuple

from pythonbinary import add_pip
from pythonbinary import spot_check
from pythonbinary.pybi import PyBI
from pythonbinary.spot_check import PLATFORM_TAG_TO_SYS_PLATFORM

URL = 'https://pybi.vorpus.org/cpython_unofficial/'


class Link(NamedTuple):
    path: str
    hash_algorithm: str
    hash_value: str

    @classmethod
    def parse(cls, base: str, href: str) -> Link:
        parsed = urllib.parse.urlsplit(href)
        hashes = urllib.parse.parse_qsl(parsed.fragment)
        if len(hashes) != 1:
            raise AssertionError(f'unexpected hashes: {href=}')

        path = urllib.parse.urljoin(base, parsed.path)
        (algorithm, value), = hashes
        return cls(path, algorithm, value)


class GetsAHrefs(html.parser.HTMLParser):
    def __init__(self, base: str) -> None:
        super().__init__()
        self.base = base
        self.links: list[Link] = []

    def handle_starttag(
            self,
            tag: str,
            attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag == 'a':
            attrs_d = dict(attrs)
            href = attrs_d.get('href')

            if href is None or '#' not in href:
                raise AssertionError(f'unexpected <a>: {tag=} {attrs=}')

            self.links.append(Link.parse(self.base, href))


def _do_build(link: Link, out_dir: str) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_pybi = os.path.join(tmpdir, os.path.basename(link.path))
        os.makedirs(os.path.join(tmpdir, 'out'))
        dest = os.path.join(tmpdir, 'out', os.path.basename(link.path))

        print('==> downloading...')
        resp = urllib.request.urlopen(link.path)

        with open(tmp_pybi, 'wb') as f:
            shutil.copyfileobj(resp, f)

        h = hashlib.new(link.hash_algorithm)
        with open(tmp_pybi, 'rb') as f:
            while (bts := f.read()):
                h.update(bts)

        if h.hexdigest() != link.hash_value:
            raise AssertionError(f'hash mismatch {h.hexdigest()} {link=}')

        print('==> updating...')
        add_pip.main((tmp_pybi, dest))

        print('==> testing...')
        spot_check.main((dest,))

        shutil.copy(dest, out_dir)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('out_dir')
    args = parser.parse_args()

    # slightly imprecise, should do better platform detection
    platforms = {
        k
        for k, v in PLATFORM_TAG_TO_SYS_PLATFORM.items()
        if v == sys.platform
    }

    resp = urllib.request.urlopen(URL)
    contents = resp.read().decode()

    href_parser = GetsAHrefs(URL)
    href_parser.feed(contents)

    # simulate an incremental update
    # del href_parser.links[58:]

    os.makedirs(args.out_dir, exist_ok=True)
    already_built = {PyBI.parse(s) for s in os.listdir(args.out_dir)}

    for link in href_parser.links:
        info = PyBI.parse(link.path)
        if info.platform not in platforms:
            continue

        if info not in already_built:
            print(f'building {info}...')

            _do_build(link, args.out_dir)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
