import subprocess
from .common import install_test_addons, dropdb


def test_success():
    """Basic successful test."""
    with install_test_addons(["addon_success"]) as addons_dir:
        dropdb()
        subprocess.check_call(["oca_init_test_database"])
        result = subprocess.check_output(
            ["oca_run_tests"], cwd=addons_dir, text=True
        )
        assert "0 failed, 0 error(s) of 1 tests when loading database" in result
