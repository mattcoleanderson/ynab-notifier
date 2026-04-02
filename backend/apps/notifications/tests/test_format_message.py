from datetime import date
from decimal import Decimal

from apps.notifications.services.base import calculate_remaining, NotificationService
from apps.notifications.services.sms import SMSService
from apps.notifications.tests.factories import make_category


def service():
    return SMSService("", "", "")


# ── 2a: Remaining Calculation Tests ──────────────────────────────────────


def test_not_snoozed_goal_target_gt_budgeted():
    c = make_category(goal_target=500000, budgeted=0, activity=-200000, goal_snoozed_at=None)
    assert calculate_remaining(c) == Decimal("300.00")


def test_not_snoozed_budgeted_gt_goal_target():
    c = make_category(goal_target=500000, budgeted=600000, activity=-550000, goal_snoozed_at=None)
    assert calculate_remaining(c) == Decimal("50.00")


def test_not_snoozed_budgeted_eq_goal_target():
    c = make_category(goal_target=500000, budgeted=500000, activity=-200000, goal_snoozed_at=None)
    assert calculate_remaining(c) == Decimal("300.00")


def test_snoozed_budgeted_lt_goal_target():
    c = make_category(goal_target=200000, budgeted=150000, activity=0, goal_snoozed_at="2026-04-01")
    assert calculate_remaining(c) == Decimal("150.00")


def test_snoozed_budgeted_zero():
    c = make_category(goal_target=200000, budgeted=0, activity=0, goal_snoozed_at="2026-04-01")
    assert calculate_remaining(c) == Decimal("0.00")


def test_snoozed_with_activity():
    c = make_category(goal_target=200000, budgeted=100000, activity=-80000, goal_snoozed_at="2026-04-01")
    assert calculate_remaining(c) == Decimal("20.00")


def test_snoozed_budgeted_gt_goal_target():
    c = make_category(goal_target=200000, budgeted=300000, activity=-100000, goal_snoozed_at="2026-04-01")
    assert calculate_remaining(c) == Decimal("200.00")


def test_not_snoozed_goal_target_none():
    c = make_category(goal_target=None, budgeted=0, activity=-50000, goal_snoozed_at=None)
    assert calculate_remaining(c) == Decimal("-50.00")


def test_not_snoozed_goal_target_none_has_budgeted():
    c = make_category(goal_target=None, budgeted=100000, activity=-50000, goal_snoozed_at=None)
    assert calculate_remaining(c) == Decimal("50.00")


def test_not_snoozed_no_activity():
    c = make_category(goal_target=500000, budgeted=250000, activity=0, goal_snoozed_at=None)
    assert calculate_remaining(c) == Decimal("500.00")


def test_overspent_remaining_negative():
    c = make_category(goal_target=500000, budgeted=500000, activity=-600000, goal_snoozed_at=None)
    assert calculate_remaining(c) == Decimal("-100.00")


def test_exactly_zero_remaining():
    c = make_category(goal_target=500000, budgeted=500000, activity=-500000, goal_snoozed_at=None)
    assert calculate_remaining(c) == Decimal("0.00")


# ── 2b: Message Formatting — Section Separation Tests ────────────────────


def _header():
    today = date.today().strftime("%a, %b %d")
    return f"Budget Left ({today}):\n\n"


def test_all_positive_no_overspent_section():
    cats = [
        make_category(name="Groceries", goal_target=500000, budgeted=500000, activity=-200000),
        make_category(name="Dining", goal_target=200000, budgeted=200000, activity=-100000),
        make_category(name="Shopping", goal_target=100000, budgeted=100000, activity=-50000),
    ]
    result = service().format_message(cats)
    expected = (
        _header()
        + "Groceries:  $300.00\n"
        + "Dining:     $100.00\n"
        + "Shopping:   $ 50.00\n"
        + "────────────────────\n"
        + "Total:       $450.00"
    )
    assert result == expected


def test_all_zero_no_overspent_section():
    cats = [
        make_category(name="Groceries", goal_target=500000, budgeted=500000, activity=-500000),
        make_category(name="Dining", goal_target=200000, budgeted=200000, activity=-200000),
        make_category(name="Shopping", goal_target=100000, budgeted=100000, activity=-100000),
    ]
    result = service().format_message(cats)
    expected = (
        _header()
        + "Groceries:  $0.00\n"
        + "Dining:     $0.00\n"
        + "Shopping:   $0.00\n"
        + "──────────────────\n"
        + "Total:       $0.00"
    )
    assert result == expected


def test_mix_positive_and_negative():
    cats = [
        make_category(name="Dining", goal_target=200000, budgeted=200000, activity=-100000),
        make_category(name="Shopping", goal_target=100000, budgeted=100000, activity=-50000),
        make_category(name="Groceries", goal_target=500000, budgeted=500000, activity=-600000),
    ]
    result = service().format_message(cats)
    expected = (
        _header()
        + "Dining:     $ 100.00\n"
        + "Shopping:   $  50.00\n"
        + "─────────────────────\n"
        + "Groceries:  $-100.00\n"
        + "─────────────────────\n"
        + "Total:       $  50.00"
    )
    assert result == expected


def test_all_negative_no_positive_section():
    cats = [
        make_category(name="Groceries", goal_target=500000, budgeted=500000, activity=-600000),
        make_category(name="Dining", goal_target=200000, budgeted=200000, activity=-250000),
        make_category(name="Shopping", goal_target=100000, budgeted=100000, activity=-150000),
    ]
    result = service().format_message(cats)
    expected = (
        _header()
        + "─────────────────────\n"
        + "Groceries:  $-100.00\n"
        + "Dining:     $ -50.00\n"
        + "Shopping:   $ -50.00\n"
        + "─────────────────────\n"
        + "Total:       $-200.00"
    )
    assert result == expected


def test_single_positive_category():
    cats = [
        make_category(name="Groceries", goal_target=500000, budgeted=500000, activity=-200000),
    ]
    result = service().format_message(cats)
    expected = (
        _header()
        + "Groceries:  $300.00\n"
        + "────────────────────\n"
        + "Total:       $300.00"
    )
    assert result == expected


def test_single_negative_category():
    cats = [
        make_category(name="Groceries", goal_target=500000, budgeted=500000, activity=-550000),
    ]
    result = service().format_message(cats)
    expected = (
        _header()
        + "────────────────────\n"
        + "Groceries:  $-50.00\n"
        + "────────────────────\n"
        + "Total:       $-50.00"
    )
    assert result == expected


def test_multiple_overspent_categories():
    cats = [
        make_category(name="Dining", goal_target=200000, budgeted=200000, activity=-100000),
        make_category(name="Groceries", goal_target=500000, budgeted=500000, activity=-600000),
        make_category(name="Shopping", goal_target=100000, budgeted=100000, activity=-150000),
    ]
    result = service().format_message(cats)
    expected = (
        _header()
        + "Dining:     $ 100.00\n"
        + "─────────────────────\n"
        + "Groceries:  $-100.00\n"
        + "Shopping:   $ -50.00\n"
        + "─────────────────────\n"
        + "Total:       $ -50.00"
    )
    assert result == expected


def test_negative_amount_not_clamped():
    cats = [
        make_category(name="Groceries", goal_target=500000, budgeted=500000, activity=-550000),
    ]
    result = service().format_message(cats)
    assert "$-50.00" in result


# ── 2c: Alignment Tests ──────────────────────────────────────────────────


def test_alignment_across_sections():
    cats = [
        make_category(name="Dining", goal_target=200000, budgeted=200000, activity=0),
        make_category(name="Groceries", goal_target=500000, budgeted=500000, activity=-550000),
    ]
    result = service().format_message(cats)
    lines = result.strip().split("\n")
    # Category lines (not Total) should align with each other
    cat_lines = [line for line in lines if "$" in line and not line.startswith("Total")]
    dollar_positions = [line.index("$") for line in cat_lines]
    assert len(set(dollar_positions)) == 1


def test_negative_amounts_dont_break_alignment():
    cats = [
        make_category(name="Dining", goal_target=200000, budgeted=200000, activity=0),
        make_category(name="Groceries", goal_target=500000, budgeted=500000, activity=-550000),
    ]
    result = service().format_message(cats)
    lines = result.strip().split("\n")
    cat_lines = [line for line in lines if "$" in line and not line.startswith("Total")]
    dollar_positions = [line.index("$") for line in cat_lines]
    assert len(set(dollar_positions)) == 1


def test_separator_width_accounts_for_both_sections():
    cats = [
        make_category(name="Dining", goal_target=200000, budgeted=200000, activity=0),
        make_category(name="Groceries", goal_target=500000, budgeted=500000, activity=-550000),
    ]
    result = service().format_message(cats)
    lines = result.strip().split("\n")
    separators = [line for line in lines if line.startswith("─")]
    content_lines = [line for line in lines if "$" in line]
    max_content_len = max(len(line) for line in content_lines)
    for sep in separators:
        assert len(sep) >= max_content_len


# ── 2d: Total Calculation Tests ──────────────────────────────────────────


def test_total_includes_negatives():
    cats = [
        make_category(name="Dining", goal_target=200000, budgeted=200000, activity=-100000),
        make_category(name="Shopping", goal_target=100000, budgeted=100000, activity=-50000),
        make_category(name="Groceries", goal_target=500000, budgeted=500000, activity=-550000),
    ]
    result = service().format_message(cats)
    # 100 + 50 + (-50) = 100
    total_line = result.strip().split("\n")[-1]
    assert "$100.00" in total_line


def test_total_all_positive():
    cats = [
        make_category(name="Groceries", goal_target=500000, budgeted=500000, activity=-200000),
        make_category(name="Dining", goal_target=200000, budgeted=200000, activity=-100000),
    ]
    result = service().format_message(cats)
    total_line = result.strip().split("\n")[-1]
    assert "$400.00" in total_line


def test_total_all_negative():
    cats = [
        make_category(name="Groceries", goal_target=500000, budgeted=500000, activity=-600000),
        make_category(name="Dining", goal_target=200000, budgeted=200000, activity=-250000),
    ]
    result = service().format_message(cats)
    total_line = result.strip().split("\n")[-1]
    assert "$-150.00" in total_line


def test_total_zero_cancellation():
    cats = [
        make_category(name="Groceries", goal_target=100000, budgeted=100000, activity=0),
        make_category(name="Dining", goal_target=100000, budgeted=100000, activity=-200000),
    ]
    result = service().format_message(cats)
    total_line = result.strip().split("\n")[-1]
    assert "0.00" in total_line


# ── 2e: Integration Tests — Real Scenarios ───────────────────────────────


def test_user_hasnt_moved_money_yet():
    cats = [
        make_category(name="Groceries", goal_target=500000, budgeted=250000, activity=-550000),
        make_category(name="Dining", goal_target=200000, budgeted=100000, activity=0),
        make_category(name="Shopping", goal_target=100000, budgeted=50000, activity=-30000),
    ]
    result = service().format_message(cats)
    lines = result.strip().split("\n")

    # Find the separator positions
    sep_indices = [i for i, line in enumerate(lines) if line.startswith("─")]

    # Groceries should be in overspent section (after first separator)
    groceries_idx = next(i for i, l in enumerate(lines) if "Groceries" in l)
    assert groceries_idx > sep_indices[0]

    # Dining and Shopping should be before first separator
    dining_idx = next(i for i, l in enumerate(lines) if "Dining" in l)
    shopping_idx = next(i for i, l in enumerate(lines) if "Shopping" in l)
    assert dining_idx < sep_indices[0]
    assert shopping_idx < sep_indices[0]

    # Total should be $220.00
    total_line = lines[-1]
    assert "$220.00" in total_line


def test_user_moved_money_and_snoozed():
    cats = [
        make_category(name="Groceries", goal_target=500000, budgeted=550000, activity=-550000),
        make_category(name="Dining", goal_target=200000, budgeted=150000, activity=0, goal_snoozed_at="2026-04-01"),
        make_category(name="Shopping", goal_target=100000, budgeted=50000, activity=-30000),
    ]
    result = service().format_message(cats)
    lines = result.strip().split("\n")

    # Only one separator (no overspent section)
    sep_count = sum(1 for line in lines if line.startswith("─"))
    assert sep_count == 1

    total_line = lines[-1]
    assert "$220.00" in total_line


def test_partially_resolved():
    cats = [
        make_category(name="Groceries", goal_target=500000, budgeted=520000, activity=-550000),
        make_category(name="Dining", goal_target=200000, budgeted=180000, activity=0, goal_snoozed_at="2026-04-01"),
    ]
    result = service().format_message(cats)
    lines = result.strip().split("\n")

    # Groceries should be in overspent section
    sep_indices = [i for i, line in enumerate(lines) if line.startswith("─")]
    groceries_idx = next(i for i, l in enumerate(lines) if "Groceries" in l)
    assert groceries_idx > sep_indices[0]

    # Dining in positive section
    dining_idx = next(i for i, l in enumerate(lines) if "Dining" in l)
    assert dining_idx < sep_indices[0]

    total_line = lines[-1]
    assert "$150.00" in total_line


def test_no_goal_no_budget_pure_spending():
    cats = [
        make_category(name="Misc", goal_target=None, budgeted=0, activity=-25000),
    ]
    result = service().format_message(cats)
    lines = result.strip().split("\n")

    # Should be overspent
    sep_indices = [i for i, line in enumerate(lines) if line.startswith("─")]
    assert len(sep_indices) == 2  # two separators for all-overspent

    assert "$-25.00" in result
