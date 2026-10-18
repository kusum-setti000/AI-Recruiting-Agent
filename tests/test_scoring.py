
import pytest

from app.core.scoring import assessment_from_score


@pytest.mark.parametrize(
    "score, expected",
    [
        (0, "Weak Match"),
        (25, "Weak Match"),
        (49, "Weak Match"),
        (50, "Needs Human Review"),
        (60, "Needs Human Review"),
        (69, "Needs Human Review"),
        (70, "Potential Match"),
        (80, "Potential Match"),
        (84, "Potential Match"),
        (85, "Strong Match"),
        (95, "Strong Match"),
        (100, "Strong Match"),
    ],
)
def test_assessment_from_valid_score(score, expected):
    assert assessment_from_score(score) == expected


@pytest.mark.parametrize(
    "score",
    [-1, -10, 101, 150],
)
def test_reject_out_of_range_scores(score):
    with pytest.raises(ValueError):
        assessment_from_score(score)


@pytest.mark.parametrize(
    "score",
    [True, False, 75.5, "85", None],
)
def test_reject_non_integer_scores(score):
    with pytest.raises(TypeError):
        assessment_from_score(score)
