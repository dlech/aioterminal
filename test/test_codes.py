from aioterminal.codes import CSI


def test_name():
    assert CSI.HPA().name == "HPA"
