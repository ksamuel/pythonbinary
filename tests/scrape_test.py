import pytest

from pythonbinary.scrape import GetsAHrefs
from pythonbinary.scrape import Link


@pytest.mark.parametrize(
    ('s', 'expected'),
    (
        (
            '/url.pybi#sha256=deadbeef',
            Link('https://example.com/url.pybi', 'sha256', 'deadbeef'),
        ),
        (
            '/url.pybi#sha512=cafecafe',
            Link('https://example.com/url.pybi', 'sha512', 'cafecafe'),
        ),
    ),
)
def test_link_parse(s, expected):
    assert Link.parse('https://example.com/base', s) == expected


def test_gets_a_hrefs():
    html = '''\
<!DOCTYPE html><html><body>
<a href="/out.pybi#sha256=815bc888">
cpython_unofficial-3.10.0a1-macosx_10_9_x86_64.pybi
</a><br>
</body></html>
'''
    link_parser = GetsAHrefs('https://example.com/base/')
    link_parser.feed(html)

    assert link_parser.links == [
        Link('https://example.com/out.pybi', 'sha256', '815bc888'),
    ]
