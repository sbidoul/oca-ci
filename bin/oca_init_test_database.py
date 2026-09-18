#!/usr/bin/env python3

"""
Initialize the test database, with all direct dependencies of addons to test
installed. Use unbuffer to get a colored output.
"""

import shlex
import os
import re
import subprocess
import sys


def wait_for_postgres():
    """Wait for PostgreSQL to be ready."""
    subprocess.check_call(["oca_wait_for_postgres"])


def get_odoo_major_version() -> int:
    """Extract major version from ODOO_VERSION environment variable."""
    odoo_version = os.environ.get("ODOO_VERSION", "")
    match = re.match(r"^([0-9]+)\.([0-9]+)$", odoo_version)
    if not match:
        print(f"Invalid ODOO_VERSION format: {odoo_version!r}", file=sys.stderr)
        sys.exit(1)
    return int(match.group(1))


def get_addons_to_install() -> str:
    """Get a comma-separated list of addons dependencies to install using manifestoo."""
    include = os.environ.get("INCLUDE", "")
    exclude = os.environ.get("EXCLUDE", "")
    addons_dir = os.environ.get("ADDONS_DIR", ".")

    if include:
        cmd = [
            "manifestoo",
            "--select-include",
            include,
            "--select-exclude",
            exclude,
            "list-depends",
            "--separator=,",
        ]
    else:
        cmd = [
            "manifestoo",
            "--select-addons-dir",
            addons_dir,
            "--select-exclude",
            exclude,
            "list-depends",
            "--separator=,",
        ]

    return subprocess.check_output(cmd, text=True).strip() or "base"


def main():
    """Main function to initialize the test database."""
    wait_for_postgres()

    odoo_cmd = [
        "unbuffer",
        "odoo",
        "-d",
        os.environ["PGDATABASE"],
        "-i",
        get_addons_to_install(),
        "--http-interface=127.0.0.1",
        "--stop-after-init",
        "|",
        "oca_checklog_odoo",
    ]

    if get_odoo_major_version() >= 19:
        # Add --skip-auto-install for Odoo 19.0 and later
        # Since Odoo 19.0, already installed addons are not re-installed by --init,
        # and so their unit tests are not executed.
        # So, we let oca_install_addons explicitly install and test them.
        odoo_cmd.append("--skip-auto-install")

    # TODO: log commands like set -x did
    subprocess.check_call(["bash", "-o", "pipefail", "-c", shlex.join(odoo_cmd)])


if __name__ == "__main__":
    main()
