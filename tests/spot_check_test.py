import pytest
from packaging.version import Version
from packaging.markers import Marker
from packaging.specifiers import Specifier

from pythonbinary.spot_check import PyBI
from pythonbinary.spot_check import Module


@pytest.mark.parametrize(
    ('module', 'expected'),
    (
        (Module('m'), True),
        (Module('m', specifier=Specifier('>=3.9')), True),
        (Module('m', specifier=Specifier('<3.9')), False),
        (Module('m', marker=Marker('sys_platform=="win32"')), True),
        (Module('m', marker=Marker('sys_platform=="linux"')), False),
    ),
)
def test_module_satisfied(module, expected):
    info = PyBI(
        impl='cpython_unofficial',
        version=Version('3.9.2'),
        platform='win32',
    )
    assert module.is_satisfied(info) is expected
