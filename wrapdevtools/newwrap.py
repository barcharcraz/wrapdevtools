# newwrap.py
#
# Copyright 2018 Charles Barto <barto.charlie@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later


"""newwrap.

Initialize a new wrap from an upstream tarball. 

Newwrap will download the tarball (with curl) saving it under the
packagecache directory.  It will use the filename supplied by the
server, or, if the server doesn't supply a filename it will use the
end of the url (This is the ``-O -J`` option for curl). After downloading
it will take the sha256 hash of the tarball, and output a wrap file.

Todo:
    * handle tarballs without a root directory
"""
from pathlib import Path
import argparse
import subprocess
import hashlib
import shutil
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--wrapdev-tree',
                        help='Project tree. Should be the root of a meson project',
                        required=True)
parser.add_argument('url',
                    help='URL of the upstream tarball')

wrapfile = """
[wrap-file]
directory={unpack_directory}

source_url={source_url}
source_filename={source_filename}
source_hash={source_hash}
"""

def main():
    args = parser.parse_args()
    wrapdev_path = Path(args.wrapdev_tree)
    subprojects_path = wrapdev_path / "subprojects"
    packagecache_path = subprojects_path / "packagecache"
    subprojects_path.mkdir(exist_ok=True)
    packagecache_path.mkdir(exist_ok=True)

    # this here is a race
    cache_cts = set(packagecache_path.iterdir())
    subprocess.run(['curl', '-O', '-J', args.url], cwd=packagecache_path)
    new_cache_cts = set(packagecache_path.iterdir())
    downloaded_items = new_cache_cts - cache_cts
    if len(downloaded_items) != 1:
        raise AssertionError("Didn't download any items, or downloaded more than one item")
    print("hashing file {}".format(downloaded_items))
    source_tarball = downloaded_items[0]
    source_hash = hashlib.sha256(source_tarball.read_bytes()).hexdigest()

    cache_cts = set(subprojects_path.iterdir())
    shutil.unpack_archive(source_tarball, subprojects_path)
    new_cache_cts = set(packagecache_path.iterdir())
    extracted_folders = new_cache_cts - cache_cts
    if len(extracted_folders) != 1:
        raise AssertionError("Didn't find any new extracted folders")
    unpack_directory = extracted_folders[0]
    wrap_file_str = wrapfile.format(unpack_directory=str(unpack_directory),
                                    source_url=args.url,
                                    source_filename=str(source_tarball),
                                    source_hash=source_hash)
    print(wrap_file_str)

if __name__ == "__main__":
    main()
