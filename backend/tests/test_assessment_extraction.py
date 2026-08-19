from app.ingestion.assessment_extraction_rules import extract_assessment_rule_based

BOTH_ONLINE_OPEN_BOOK = """Course Policies for CS 4347 - Database Systems

Attendance at weekly labs is mandatory; lecture attendance is optional. Grading Breakdown: Weekly lab assignments are worth 30%. A database design project is worth 25%. The midterm exam is worth 20% and the final exam is worth 25%.

Exam Format: Both exams are administered online through the course portal and are open-book, open-note. Students may reference course materials but may not collaborate with other students during the exam window.

Late Policy: Lab assignments lose 10% per day late, up to 3 days. The design project has a hard deadline with no late submissions accepted."""

ONLY_MIDTERM_ONLINE_NO_FINAL = """Course Policies for BUSN 4325 - Business Python Applications

Attendance is optional but recommended given the hands-on lab format. Grading Breakdown: Weekly lab exercises are worth 30%. A midterm exam is worth 20%. A capstone automation project is worth 35%. Class participation is worth 15%.

Exam Format: The midterm exam is administered online through the course portal and is open-book. There is no separate final exam; the capstone project serves as the final assessment.

Late Policy: Lab exercises are accepted up to 48 hours late with a 10% per day penalty. The capstone project has a firm deadline aligned with the final presentation day."""

NO_EXAMS_AT_ALL = """Course Policies for CS 3377 - Software Engineering

This course has no exams. Grading Breakdown: Students work in teams of four on a semester-long software project, delivered in three milestones worth 20% each (60% total). A final team presentation and demo is worth 20%.

Late Policy: Milestone deliverables submitted late lose 5% per day."""

IN_PERSON_CLOSED_BOOK_PROCTORED = """Course Policies for CS 4375 - Introduction to Machine Learning

Grading Breakdown: Homework assignments are worth 30% of the final grade. There is a midterm exam worth 20% and a comprehensive final exam worth 35%.

Exam Format: The midterm exam is administered online through the course portal and is open-book. The final exam is also online, proctored via Honorlock, and closed-book.

Late Policy: Late assignments are accepted up to 48 hours after the deadline."""


def test_both_exams_online_open_book():
    result = extract_assessment_rule_based(BOTH_ONLINE_OPEN_BOOK)
    assert result["midterm_format"] == "online"
    assert result["midterm_open_book"] is True
    assert result["final_format"] == "online"
    assert result["final_open_book"] is True


def test_midterm_present_final_absent():
    result = extract_assessment_rule_based(ONLY_MIDTERM_ONLINE_NO_FINAL)
    assert result["midterm_format"] == "online"
    assert result["midterm_open_book"] is True
    assert result["final_format"] == "none"


def test_no_exams_at_all_sets_both_none():
    result = extract_assessment_rule_based(NO_EXAMS_AT_ALL)
    assert result["midterm_format"] == "none"
    assert result["final_format"] == "none"
    assert result["has_group_project"] is True
    assert result["has_presentation"] is True


def test_proctoring_and_open_closed_book_per_exam():
    result = extract_assessment_rule_based(IN_PERSON_CLOSED_BOOK_PROCTORED)
    assert result["midterm_open_book"] is True
    assert result["final_open_book"] is False
    assert result["final_proctoring"] == "Honorlock"


def test_weight_extraction_does_not_cross_paragraph_breaks():
    result = extract_assessment_rule_based(BOTH_ONLINE_OPEN_BOOK)
    weights = result["weights"]
    assert weights.get("midterm exam") == 20.0
    assert weights.get("final exam") == 25.0
    # ensure no label accidentally spans into the previous paragraph
    assert all("\n" not in label for label in weights)


def test_confidence_and_extraction_method_are_set():
    result = extract_assessment_rule_based(BOTH_ONLINE_OPEN_BOOK)
    assert result["extraction_method"] == "rule_based"
    assert 0 < result["confidence"] <= 1
