from __future__ import annotations

import argparse
import os.path
import subprocess
import tempfile

from pythonbinary.pybi import PyBI


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('zip')
    parser.add_argument('out')
    args = parser.parse_args()

    # ensure our output is an absolute path
    args.out = os.path.abspath(args.out)

    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

    info = PyBI.parse(args.zip)

    with tempfile.TemporaryDirectory() as tmpdir:
        # TODO: use a python unzip instead
        subprocess.check_call(('unzip', '-qq', '-d', tmpdir, args.zip))

        py = os.path.join(tmpdir, info.bin_dir, info.exe('python'))
        subprocess.check_call((py, '-mensurepip'), stdout=subprocess.DEVNULL)

        # TODO: on posixlikes: fix up the shebangs in bin/pip*
        # TODO: on posixlikes: symlink 'bin/pip' -> 'bin/pip3'
        # TODO: on windows: copy bin/pip3.exe to bin/pip.exe

        # TODO: on windows: ship an idle.exe (or .cmd, or whatever)

        # TODO: use a python zip instead
        # TODO: use reproducible zip / tar
        cmd = ('zip', '--symlinks', '-qq', '-r', args.out, '.')
        subprocess.check_call(cmd, cwd=tmpdir)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
