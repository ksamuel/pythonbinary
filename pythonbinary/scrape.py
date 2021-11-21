from __future__ import annotations

import argparse
import functools
import hashlib
import html.parser
import os
import shutil
import sys
import tempfile
import urllib.parse
import urllib.request
from typing import NamedTuple

import httpx

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


def _do_build(link: Link, out_dir: str) -> str:
    pybi_name = os.path.basename(link.path)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_pybi = os.path.join(tmpdir, pybi_name)
        os.makedirs(os.path.join(tmpdir, 'out'))
        dest = os.path.join(tmpdir, 'out', pybi_name)

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

    return os.path.join(out_dir, pybi_name)


class Release(NamedTuple):
    tag: str
    upload_url: str
    assets: frozenset[PyBI]

    def upload_url_path(self, filename: str) -> str:
        expected_end = '{?name,label}'
        if not self.upload_url.endswith(expected_end):
            raise AssertionError(f'unexpected upload_url {self.upload_url=}')

        # TODO: removesuffix
        base = self.upload_url[:-1 * len(expected_end)]
        params = urllib.parse.urlencode({'name': filename})
        return f'{base}?{params}'


@functools.lru_cache
def _get_or_create_release(tag: str, *, token: str) -> Release:
    auth = {'Authorization': f'token {token}'}

    url = f'https://api.github.com/repos/ksamuel/pythonbinary/releases/tags/{tag}'  # noqa: E501
    release = httpx.get(url, headers=auth)

    try:
        release.raise_for_status()
    except httpx.HTTPStatusError:
        url = 'https://api.github.com/repos/ksamuel/pythonbinary/releases'
        data = {'tag_name': tag, 'name': tag}
        release = httpx.post(url, json=data, headers=auth)
        release.raise_for_status()

    json_response = release.json()

    assets = frozenset(
        PyBI.parse(asset['name'])
        for asset in json_response['assets']
    )
    return Release(tag, json_response['upload_url'], assets)


def _upload_artifact(release: Release, filename: str, *, token: str) -> None:
    with open(filename, 'rb') as f:
        httpx.post(
            release.upload_url_path(os.path.basename(filename)),
            headers={
                'Authorization': f'token {token}',
                'Content-Type': 'application/zip',
            },
            content=f.read(),
        )


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

    os.makedirs(args.out_dir, exist_ok=True)

    token = os.environ['GH_TOKEN']

    for link in href_parser.links:
        info = PyBI.parse(link.path)
        if info.platform not in platforms:
            continue

        release_tag = f'v{info.version}'
        release = _get_or_create_release(release_tag, token=token)

        if info not in release.assets:
            print(f'building {info}...')

            with tempfile.TemporaryDirectory() as tmpdir:
                filename = _do_build(link, tmpdir)
                _upload_artifact(release, filename, token=token)
        else:
            print(f'skipped {info}!')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
