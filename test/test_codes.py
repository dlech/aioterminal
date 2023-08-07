from aioterminal.codes import CSI


def test_name():
    assert CSI.HPA().name == "HPA"


def test_repr():
    # default
    assert (
        repr(CSI("?", "1", " ", "X"))
        == "CSI(private='?', params='1', intermediate=' ', final='X')"
    )

    # named instances have special repr
    assert repr(CSI.HPA(1)) == "CSI.HPA('1')"
