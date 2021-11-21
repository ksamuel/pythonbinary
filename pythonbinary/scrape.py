from __future__ import annotations

import argparse
import html.parser
import json
import urllib.parse
import urllib.request
from typing import NamedTuple

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()

    resp = urllib.request.urlopen(URL)
    contents = resp.read().decode()

    href_parser = GetsAHrefs(URL)
    href_parser.feed(contents)

    as_json = [link._asdict() for link in href_parser.links]
    print(json.dumps(as_json, indent=2))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
