from timeflip_tracker import run_main


def test_package_exports_run_main():
    assert callable(run_main)
