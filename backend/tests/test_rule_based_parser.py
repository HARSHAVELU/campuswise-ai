from app.agents.rule_based_parser import parse_requirement_rule_based


def test_extracts_topic_and_rating_and_time_window():
    query = (
        "I want to take a Python course next semester. I prefer online or hybrid classes, "
        "exams should preferably be online, I do not want classes before 11 AM, "
        "I want a professor rated above 4, and I want someone with historically good grades."
    )
    parsed = parse_requirement_rule_based(query)

    assert parsed.topic == "python"
    assert parsed.hard_constraints.earliest_start_time == "11:00"
    assert parsed.hard_constraints.minimum_professor_rating == 4.0
    assert set(parsed.soft_preferences.prefer_delivery_modes or []) == {"online", "hybrid"}
    assert parsed.soft_preferences.prefer_online_exams is True
    assert parsed.soft_preferences.prefer_easier_grading is True
    assert parsed.soft_preferences.prefer_higher_rated_professor is True
    assert parsed.parser_source == "rule_based"


def test_bare_topic_query():
    parsed = parse_requirement_rule_based("Find me a Python class.")
    assert parsed.topic == "python"
    assert parsed.hard_constraints == parsed.hard_constraints.__class__()


def test_online_graduate_courses_is_hard_constraint():
    parsed = parse_requirement_rule_based("Show online graduate courses.")
    assert parsed.hard_constraints.delivery_modes == ["online"]
    assert parsed.hard_constraints.level == "graduate"


def test_after_time_sets_earliest_start():
    parsed = parse_requirement_rule_based("I need a class after 4 PM.")
    assert parsed.hard_constraints.earliest_start_time == "16:00"


def test_before_time_without_negation_sets_latest_start():
    parsed = parse_requirement_rule_based("I need a class before 3 PM.")
    assert parsed.hard_constraints.latest_start_time == "15:00"


def test_no_friday_excludes_friday():
    parsed = parse_requirement_rule_based("Find me a course without Friday meetings.")
    assert parsed.hard_constraints.exclude_days == ["friday"]


def test_online_course_with_online_exams():
    parsed = parse_requirement_rule_based("I want an online course with online exams.")
    assert parsed.hard_constraints.delivery_modes == ["online"]
    assert parsed.soft_preferences.prefer_online_exams is True


def test_undergraduate_is_not_misdetected_as_graduate():
    parsed = parse_requirement_rule_based("I want an undergraduate database course.")
    assert parsed.hard_constraints.level == "undergraduate"


def test_online_exams_does_not_imply_online_delivery_mode():
    parsed = parse_requirement_rule_based("I want a database course with online exams.")
    assert parsed.soft_preferences.prefer_online_exams is True
    assert parsed.hard_constraints.delivery_modes is None


def test_online_course_and_online_exams_both_detected_independently():
    parsed = parse_requirement_rule_based("I want an online course with online exams.")
    assert parsed.hard_constraints.delivery_modes == ["online"]
    assert parsed.soft_preferences.prefer_online_exams is True
