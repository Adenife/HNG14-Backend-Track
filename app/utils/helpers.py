from typing import Dict, Any, Optional
import re
import pycountry


AGE_GROUPS: Dict[str, tuple[int, int]] = {
    "child": (0, 12),
    "teenager": (13, 19),
    "adult": (20, 59),
    "senior": (60, float("inf")),
}

COUNTRY_CODES: Dict[str, str] = {
    "nigeria": "NG",
    "angola": "AO",
    "kenya": "KE",
    # Add more as needed
}


def get_country_code(country_name: str):
    """
    Retrieves the ISO 3166-1 alpha-2 country code for a given country name.

    Parameters:
    - country_name: A string representing the full name of the country.

    Returns:
    - A string containing the 2-letter country code if found, otherwise None.
    """
    try:
        # Search for the country by name
        return pycountry.countries.lookup(country_name).alpha_2
    except LookupError:
        return None


def get_age_group(age: int) -> str:
    """
    Returns the age group for a given age.

    Age ranges:
    - child:     0 - 12
    - teenager: 13 - 19
    - adult:    20 - 59
    - senior:   60+

    :param age: Age as integer (>= 0)
    :return: Age group string
    :raises: TypeError if age is not int
    :raises: ValueError if age is negative
    """
    if not isinstance(age, int):
        raise TypeError(f"Age must be an integer, got {type(age).__name__}")

    if age < 0:
        raise ValueError(f"Age cannot be negative, got {age}")

    for group, (min_age, max_age) in AGE_GROUPS.items():
        if min_age <= age <= max_age:
            return group

    return "senior"


def parse_natural_query(q: str) -> Dict[str, Any]:
    """
    Parses plain English queries into filter parameters.

    Rules:
    - Rule-based parsing (Regex/String matching).
    - 'young' maps to 16-24 (does not use AGE_GROUPS).
    - Returns error dict if query is uninterpretable.
    """
    if not q or not isinstance(q, str):
        return {"status": "error", "message": "Unable to interpret query"}

    query = q.lower().strip()
    filters = {}

    is_female = "female" in query
    is_male = (
        "male" in query
        and "female" not in query[query.find("male") - 2 : query.find("male")]
    )

    if is_female and is_male:
        pass
    elif is_female:
        filters["gender"] = "female"
    elif is_male:
        filters["gender"] = "male"

    # handle Age Groups (including the "young" rule)
    if "young" in query:
        filters["min_age"] = 16
        filters["max_age"] = 24
    else:
        for group in AGE_GROUPS.keys():
            if group in query:
                filters["age_group"] = group
                break

    # handle Numeric Constraints (e.g., "above 30", "under 18")
    above_match = re.search(r"(?:above|over|older than)\s+(\d+)", query)
    if above_match:
        filters["min_age"] = int(above_match.group(1))

    below_match = re.search(r"(?:under|below|younger than)\s+(\d+)", query)
    if below_match:
        filters["max_age"] = int(below_match.group(1))

    # handle Country
    country_match = re.search(r"(?:from|in)\s+([a-zA-Z\s]{2,})", query)
    if country_match:
        country_name = country_match.group(1).strip()
        country_code = get_country_code(country_name)

        if country_code:
            filters["country_id"] = country_code

    # Final Interpretation Check
    # If the filters dict is still empty, we couldn't parse anything meaningful
    if not filters:
        return {"status": "error", "message": "Unable to interpret query"}

    return filters
