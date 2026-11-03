import json


class CustomDBSchema:
    """Custom database schema."""

    @staticmethod
    def get_table_info(table_names=None):
        """Returns the database schema as a list of dictionaries."""
        schema = [
            {
                "table_name": "crime_scene_report",
                "description": "One row is one reported crime in one city on one date. Use this table for crime, murder, case, report, witness clue, city, or crime-date questions.",
                "row_meaning": "One police report; description contains narrative clues and witness instructions.",
                "primary_key": None,
                "join_hints": [
                    "No direct person_id exists; connect to people only through clues written in description."
                ],
                "columns": [
                    {
                        "name": "date",
                        "type": "INTEGER",
                        "format": "YYYYMMDD (8-digit integer)",
                        "description": "Date of the reported crime as an 8-digit YYYYMMDD integer. Convert a dotted or dashed date before comparing, without quotes.",
                        "foreign_key": None,
                    },
                    {
                        "name": "type",
                        "type": "TEXT",
                        "description": "Crime category. For the case, murder is exactly 'murder'; use type = 'murder'.",
                        "variants": [
                            "arson",
                            "assault",
                            "blackmail",
                            "bribery",
                            "fraud",
                            "murder",
                            "robbery",
                            "smuggling",
                            "theft",
                        ],
                        "foreign_key": None,
                    },
                    {
                        "name": "description",
                        "type": "TEXT",
                        "description": "Free-text report narrative. Search clues with description LIKE '%text%'.",
                        "foreign_key": None,
                    },
                    {
                        "name": "city",
                        "type": "TEXT",
                        "description": "City where the crime occurred. Use the city supplied by the user as an exact TEXT value.",
                        "foreign_key": None,
                    },
                ],
                "relationships": [],
            },
            {
                "table_name": "drivers_license",
                "description": "One row is one driver's license. Contains physical description and vehicle data, not a person's name.",
                "row_meaning": "One license record belonging to zero or one person.",
                "primary_key": "id",
                "join_hints": ["Join to person with person.license_id = drivers_license.id."],
                "columns": [
                    {
                        "name": "id",
                        "type": "INTEGER",
                        "description": "Unique license ID. Match it to person.license_id.",
                        "foreign_key": None,
                    },
                    {
                        "name": "age",
                        "type": "INTEGER",
                        "description": "Age of the license holder",
                        "foreign_key": None,
                    },
                    {
                        "name": "height",
                        "type": "INTEGER",
                        "description": "License holder's height in inches",
                        "foreign_key": None,
                    },
                    {
                        "name": "eye_color",
                        "type": "TEXT",
                        "description": "License holder's eye color",
                        "foreign_key": None,
                    },
                    {
                        "name": "hair_color",
                        "type": "TEXT",
                        "description": "License holder's hair color",
                        "foreign_key": None,
                    },
                    {
                        "name": "gender",
                        "type": "TEXT",
                        "description": "Gender of the license holder",
                        "foreign_key": None,
                    },
                    {
                        "name": "plate_number",
                        "type": "TEXT",
                        "description": "Vehicle plate number. Six alphanumeric characters; search as TEXT.",
                        "foreign_key": None,
                    },
                    {
                        "name": "car_make",
                        "type": "TEXT",
                        "description": "Make of License holder's car",
                        "foreign_key": None,
                    },
                    {
                        "name": "car_model",
                        "type": "TEXT",
                        "description": "Model of License holder's car",
                        "foreign_key": None,
                    },
                ],
                "relationships": [
                    {
                        "type": "referenced_by",
                        "source_table": "person",
                        "source_column": "license_id",
                        "target_column": "id",
                    }
                ],
            },
            {
                "table_name": "facebook_event_checkin",
                "description": "One row is one person's attendance at one Facebook event on one date. Use for event, Facebook, or checked-in questions.",
                "row_meaning": "One event check-in by one person.",
                "primary_key": None,
                "join_hints": ["Join to person with facebook_event_checkin.person_id = person.id."],
                "columns": [
                    {
                        "name": "person_id",
                        "type": "INTEGER",
                        "description": "ID of the person who attended. Join to person.id.",
                        "foreign_key": "person.id",
                    },
                    {
                        "name": "event_id",
                        "type": "INTEGER",
                        "description": "Identifier of the event. It is not a person ID.",
                        "foreign_key": None,
                    },
                    {"name": "event_name", "type": "TEXT", "description": "Name of the event", "foreign_key": None},
                    {
                        "name": "date",
                        "type": "INTEGER",
                        "format": "YYYYMMDD  (8-number integer)",
                        "description": "Date of event attendance as YYYYMMDD integer.",
                        "foreign_key": None,
                    },
                ],
                "relationships": [
                    {
                        "type": "foreign_key",
                        "source_column": "person_id",
                        "target_table": "person",
                        "target_column": "id",
                    }
                ],
            },
            {
                "table_name": "get_fit_now_check_in",
                "description": "One row is one gym visit by one member. Use for gym visits, check-in times, or alibis.",
                "row_meaning": "One visit; the same member can have many rows.",
                "primary_key": None,
                "join_hints": [
                    "Join to get_fit_now_member with get_fit_now_check_in.membership_id = get_fit_now_member.id, then to person using person_id."
                ],
                "columns": [
                    {
                        "name": "membership_id",
                        "type": "TEXT",
                        "description": "Gym membership identifier, usually 5 alphanumeric characters such as NL318. Join to get_fit_now_member.id.",
                        "foreign_key": "get_fit_now_member.id",
                    },
                    {
                        "name": "check_in_date",
                        "type": "INTEGER",
                        "format": "YYYYMMDD  (8-digit integer)",
                        "description": "Date of the gym visit as YYYYMMDD integer.",
                        "foreign_key": None,
                    },
                    {
                        "name": "check_in_time",
                        "type": "INTEGER",
                        "format": "minutes passed since midnight",
                        "description": "Minutes after midnight, not HHMM. 329 means 05:29. Compare numerically.",
                        "foreign_key": None,
                    },
                    {
                        "name": "check_out_time",
                        "type": "INTEGER",
                        "format": "minutes passed since midnight",
                        "description": "Minutes after midnight, not HHMM. NULL means no recorded checkout.",
                        "foreign_key": None,
                    },
                ],
                "relationships": [
                    {
                        "type": "foreign_key",
                        "source_column": "membership_id",
                        "target_table": "get_fit_now_member",
                        "target_column": "id",
                    }
                ],
            },
            {
                "table_name": "get_fit_now_member",
                "description": "One row is one gym membership. Use for gym member names, membership status, or membership start dates.",
                "row_meaning": "One membership belonging to one person.",
                "primary_key": "id",
                "join_hints": [
                    "Join to person with get_fit_now_member.person_id = person.id. Join visits through get_fit_now_check_in.membership_id = get_fit_now_member.id."
                ],
                "columns": [
                    {
                        "name": "id",
                        "type": "TEXT",
                        "description": "Unique gym membership ID, typically 5 alphanumeric characters such as NL318. Do not treat it as an integer.",
                        "foreign_key": None,
                    },
                    {
                        "name": "person_id",
                        "type": "INTEGER",
                        "description": "Person ID associated with this membership. Join to person.id.",
                        "foreign_key": "person.id",
                    },
                    {"name": "name", "type": "TEXT", "description": "Name of the gym member", "foreign_key": None},
                    {
                        "name": "membership_start_date",
                        "type": "INTEGER",
                        "format": "YYYYMMDD  (8-digit integer)",
                        "description": "Start date of the membership",
                        "foreign_key": None,
                    },
                    {
                        "name": "membership_status",
                        "type": "TEXT",
                        "description": "Membership tier. Known values are gold, silver, and regular.",
                        "variants": ["gold", "regular", "silver"],
                        "foreign_key": None,
                    },
                ],
                "relationships": [
                    {
                        "type": "foreign_key",
                        "source_column": "person_id",
                        "target_table": "person",
                        "target_column": "id",
                    },
                    {
                        "type": "referenced_by",
                        "source_table": "get_fit_now_check_in",
                        "source_column": "membership_id",
                        "target_column": "id",
                    },
                ],
            },
            {
                "table_name": "income",
                "description": "One row is annual income for one person. There is no person_id; match this table to person using SSN.",
                "row_meaning": "One income record identified by a social security number.",
                "primary_key": "ssn",
                "join_hints": ["Logical join only: income.ssn = person.ssn. Do not join income through person.id."],
                "columns": [
                    {
                        "name": "ssn",
                        "type": "INTEGER",
                        "format": "9-digit integer",
                        "description": "Unique 9-digit social security number. Match exactly to person.ssn.",
                        "foreign_key": None,
                    },
                    {
                        "name": "annual_income",
                        "type": "INTEGER",
                        "format": "Integer amount in USD",
                        "description": "Annual income in US dollars. It may have 5 or 6 digits; do not assume a fixed length.",
                        "foreign_key": None,
                    },
                ],
                "relationships": [
                    {"type": "logical_link", "source_column": "ssn", "target_table": "person", "target_column": "ssn"}
                ],
            },
            {
                "table_name": "interview",
                "description": "One row is one interview transcript for one person. Use for statements, clues, witnesses, or confessions.",
                "row_meaning": "One interview belonging to one person.",
                "primary_key": None,
                "join_hints": [
                    "Join to person with interview.person_id = person.id. Search transcript with transcript LIKE '%text%'."
                ],
                "columns": [
                    {
                        "name": "person_id",
                        "type": "INTEGER",
                        "description": "ID of the interviewed person. Join to person.id.",
                        "foreign_key": "person.id",
                    },
                    {
                        "name": "transcript",
                        "type": "TEXT",
                        "description": "Full free-text interview. Search it with LIKE; it is not a structured clue field.",
                        "foreign_key": None,
                    },
                ],
                "relationships": [
                    {
                        "type": "foreign_key",
                        "source_column": "person_id",
                        "target_table": "person",
                        "target_column": "id",
                    }
                ],
            },
            {
                "table_name": "solution",
                "description": "Internal game-answer table. It is empty in the investigation database and must never be queried for clues or suspects.",
                "row_meaning": "No investigation records; zero rows.",
                "primary_key": None,
                "join_hints": [],
                "columns": [
                    {
                        "name": "user",
                        "type": "TEXT",
                        "description": "Internal solution metadata; do not use.",
                        "foreign_key": None,
                    },
                    {
                        "name": "value",
                        "type": "TEXT",
                        "description": "Internal solution metadata; do not use.",
                        "foreign_key": None,
                    },
                ],
                "relationships": [],
            },
            {
                "table_name": "person",
                "description": "One row is one person. This is the central table for names, addresses, IDs, interviews, gym memberships, events, licenses, and income.",
                "row_meaning": "One person; use person.id as the bridge to most other tables.",
                "primary_key": "id",
                "join_hints": [
                    "person.id joins to interview.person_id, facebook_event_checkin.person_id, and get_fit_now_member.person_id. person.license_id joins to drivers_license.id. person.ssn joins logically to income.ssn."
                ],
                "columns": [
                    {
                        "name": "id",
                        "type": "INTEGER",
                        "format": "5-digit integer",
                        "description": "Unique person identifier. This is the main join key for a person.",
                        "foreign_key": None,
                    },
                    {
                        "name": "name",
                        "type": "TEXT",
                        "format": "2-word string, first name and surname",
                        "description": "Full name, usually first name plus surname. For a partial name use name LIKE '%fragment%'.",
                        "foreign_key": None,
                    },
                    {
                        "name": "license_id",
                        "type": "INTEGER",
                        "format": "6-digit integer",
                        "description": "License ID. Join to drivers_license.id; do not confuse it with person.id.",
                        "foreign_key": "drivers_license.id",
                    },
                    {
                        "name": "address_number",
                        "type": "INTEGER",
                        "format": "4 or less digits",
                        "description": "House number. It is numeric, so use MAX/MIN or ORDER BY address_number for last/first house.",
                        "foreign_key": None,
                    },
                    {
                        "name": "address_street_name",
                        "type": "TEXT",
                        "description": "Street name without the house number. Filter exact names such as 'Franklin Ave' or 'Northwestern Dr'.",
                        "foreign_key": None,
                    },
                    {
                        "name": "ssn",
                        "type": "INTEGER",
                        "format": "9-digit integer",
                        "description": "9-digit social security number. Logical join to income.ssn; not a foreign key in SQLite.",
                        "foreign_key": None,
                    },
                ],
                "relationships": [
                    {
                        "type": "foreign_key",
                        "source_column": "license_id",
                        "target_table": "drivers_license",
                        "target_column": "id",
                    },
                    {
                        "type": "referenced_by",
                        "source_table": "facebook_event_checkin",
                        "source_column": "person_id",
                        "target_column": "id",
                    },
                    {
                        "type": "referenced_by",
                        "source_table": "get_fit_now_member",
                        "source_column": "person_id",
                        "target_column": "id",
                    },
                    {
                        "type": "referenced_by",
                        "source_table": "interview",
                        "source_column": "person_id",
                        "target_column": "id",
                    },
                    {"type": "logical_link", "source_column": "ssn", "target_table": "income", "target_column": "ssn"},
                ],
            },
        ]
        return json.dumps(schema, separators=(",", ":"))
