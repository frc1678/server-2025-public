def test_generate_random_value():
    from calculations import generate_random_value

    # test if function returns correct type
    assert isinstance(generate_random_value.generate_random_value("str"), str)
    assert isinstance(generate_random_value.generate_random_value("int"), int)
    assert isinstance(generate_random_value.generate_random_value("float"), float)
    assert isinstance(generate_random_value.generate_random_value("bool"), bool)

    # test all strings
    assert generate_random_value.generate_random_value("str", seed=254) == "xxxxxxxxxx"
    assert generate_random_value.generate_random_value("str", "team_number", seed=254) == "6141"

    # test int, float, bool
    assert generate_random_value.generate_random_value("int", seed=254) == 47

    assert generate_random_value.generate_random_value("float", seed=10) == 57.1403

    assert generate_random_value.generate_random_value("bool", seed=10) == False

    # test all lists
    assert not generate_random_value.generate_random_value("list", seed=254)
    assert generate_random_value.generate_random_value("list", "start_position", seed=254) == ["2"]
    assert generate_random_value.generate_random_value("list", "cage_level", seed=254) == ["S"]

    # test enum[int] and all enum[str]
    assert (
        generate_random_value.generate_random_value("enum[str]", "start_position", seed=254) == "2"
    )
    assert generate_random_value.generate_random_value("enum[int]", seed=254) == 1
