import mono.dice as dc

def test_d6():
    for _ in range(36):
        assert dc.d6() in range(1,6+1)

def test_result():
    die0, die1 = 1,2
    assert dc.result(die0, die1) == (3, False)
    assert dc.result(die0, die0) == (2, True)
