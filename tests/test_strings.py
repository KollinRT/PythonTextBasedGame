# test_strings.py

def test_singleWord_string_cap():
    name = "kollin"
    assert name.capitalize() == "Kollin"

def test_multiWord_string_cap():
    name = "kollin trujillo"
    assert name.capitalize() == "Kollin trujillo"

