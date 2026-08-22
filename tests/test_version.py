import releasenote_tool


def test_package_exposes_a_version():
    assert releasenote_tool.__version__
