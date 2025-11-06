from location_not_found.foo import foo


def test_foo():
    assert foo("foo") == "foo"
