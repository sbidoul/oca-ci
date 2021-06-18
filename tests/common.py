import ast
import contextlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ODOO_VENV = "/opt/odoo-venv"

test_addons_dir = Path(__file__).parent / "data" / "addons"

odoo_version_info = tuple(map(int, os.environ["ODOO_VERSION"].split(".")))

if odoo_version_info < (10, 0):
    odoo_bin = "openerp-server"
else:
    odoo_bin = "odoo"


@contextlib.contextmanager
def preserve_odoo_rc():
    odoo_rc_path = Path(os.environ["ODOO_RC"])
    odoo_rc = odoo_rc_path.read_bytes()
    try:
        yield
    finally:
        odoo_rc_path.write_bytes(odoo_rc)


@contextlib.contextmanager
def preserve_odoo_venv():
    subprocess.check_call(["cp", "-arl", ODOO_VENV, ODOO_VENV + ".org"])
    try:
        yield
    finally:
        subprocess.check_call(["rm", "-r", ODOO_VENV])
        subprocess.check_call(["mv", ODOO_VENV + ".org", ODOO_VENV])


@contextlib.contextmanager
def make_addons_dir(test_addons):
    """Copy test addons to a temporary directory.

    Adjust the addons version to match the Odoo version being tested.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        for addon_name in test_addons:
            shutil.copytree(test_addons_dir / addon_name, tmppath / addon_name)
            # prefix Odoo version
            manifest_path = tmppath / addon_name / "__manifest__.py"
            manifest = ast.literal_eval(manifest_path.read_text())
            manifest["version"] = os.environ["ODOO_VERSION"] + "." + manifest["version"]
            manifest_path.write_text(repr(manifest))
        yield tmppath


@contextlib.contextmanager
def install_test_addons(test_addons):
    with preserve_odoo_rc(), preserve_odoo_venv(), make_addons_dir(
        test_addons
    ) as addons_dir:
        subprocess.check_call(["oca_install_addons"], cwd=addons_dir)
        yield addons_dir


def dropdb():
    subprocess.check_call(["dropdb", "--if-exists", os.environ["PGDATABASE"]])
