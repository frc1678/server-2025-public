import random
import string
import utils


def generate_random_value(
    value_type: str,
    value_name: str = "",
    value_value: dict = {},
    value_collection: str = "",
    seed=None,
):
    """Given a name of a type, return random data in that type.

    value_type: the name of the type as a string. The type will
    will be checked and the appropriate value will be generated.

    value_name: the name of the value, eg. team_number, preloaded_gamepiece

    seed: optional but will be used to set the random seed for tests.
    """
    if seed is not None:
        random.seed(seed)

    if type(value_type) is str:
        value_type = value_type.lower()
    else:
        raise TypeError('value_type must be a string (eg. "bool")')

    if value_type == "str":
        value = ""
        if value_collection == "categorical_actions":
            value = random.choice(value_value["list"])
        if value_name == "team_number":
            return str(random.randint(1, 10000))
        # if variable does not require a set of predefined constants, generate a random string
        # used for variables such as scout_name or other forgotten variables
        else:
            # Get the maximum length that the ascii_letters has for use to index it later
            max_length = len(string.ascii_letters) - 1
            # Repeat for a random amount of characters in a reasonable range
            for character in range(random.randint(5, 16)):
                # Also adds the seed if its defined, the random seed resets after use
                # this sets up the seed for each iteration
                if seed is not None:
                    random.seed(seed)
                # Get a random character from string.ascii_letters (a string of all ascii letters) and
                # add the char to the value, the final string
                value += string.ascii_letters[random.randint(0, max_length)]
        return value

    elif value_type == "int":
        return random.randint(0, 100)

    elif value_type == "float":
        return round(random.uniform(0, 100), 4)

    elif value_type == "bool":
        # Cast randint to bool
        return bool(random.randint(0, 1))

    elif value_type == "list":
        # For certain lists of strings, it is possible to generate a list of random specific enum values
        # generate random data for modes (which are lists) in calc_obj_team_schema
        obj_tim_schema = utils.read_schema("schema/calc_obj_tim_schema.yml")
        if value_name in obj_tim_schema["categorical_actions"].keys():
            return [random.choice(obj_tim_schema["categorical_actions"][value_name]["list"])]
        elif "mode" in value_name:
            return [
                random.choice(
                    obj_tim_schema["categorical_actions"][
                        value_value["tim_fields"][0].split(".")[1]
                    ]["list"]
                )
            ]
        # other (unknown) lists
        else:
            return []

    elif "enum" in value_type:
        # for string Enums, generate more specific data relevant to that Enum
        if value_type.lower() == "enum[str]":
            if "start_position" in value_name:
                return random.choice(["0", "1", "2", "3", "4", "5"])
        # for other integer Enums, return an int
        else:
            return 1
