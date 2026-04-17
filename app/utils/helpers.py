def get_age_group(age: int) -> str:
    """
    Returns an age group based on the given age.

    Age groups are as follows:
    * 0-12: child
    * 13-19: teenager
    * 20-59: adult
    * 60+: senior

    :param age: The age to determine the age group for
    :return: The age group as a string
    """
    if 0 <= age <= 12:
        return "child"
    if 13 <= age <= 19:
        return "teenager"
    if 20 <= age <= 59:
        return "adult"
    return "senior"
