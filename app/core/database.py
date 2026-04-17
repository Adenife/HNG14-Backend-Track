from typing import Dict

# Primary storage: id -> profile data
profiles_db: Dict[str, dict] = {}

# Secondary index: name (lowercase) -> id
# Kept in sync with profiles_db for O(1) duplicate lookups
profiles_name_index: Dict[str, str] = {}
