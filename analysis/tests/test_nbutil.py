from src.nbutil import indian_group, inr


def test_indian_grouping():
    assert indian_group(999) == "999"
    assert indian_group(1000) == "1,000"
    assert indian_group(150000) == "1,50,000"
    assert indian_group(12345678) == "1,23,45,678"


def test_inr_units():
    assert inr(45000) == "₹45,000"
    assert inr(1818317) == "₹18.18 lakh"
    assert inr(255000000) == "₹25.50 crore"
    assert inr(-150000) == "-₹1.50 lakh"
