import pytest

from src.utils.sample import get_stratified_sample


# Mock data to use across tests
@pytest.fixture
def get_labels():
    records = [
        {"feedback_record_id": 1, "labels": ["A"]},
        {"feedback_record_id": 2, "labels": ["A", "B"]},
        {"feedback_record_id": 3, "labels": ["B"]},
        {"feedback_record_id": 4, "labels": ["C"]},
        {"feedback_record_id": 5, "labels": ["A", "C"]},
        {"feedback_record_id": 6, "labels": ["B", "C"]},
    ]
    return records


def test_sample_size(get_labels):
    """Test that the function returns the correct number of samples."""
    sample_size = 4
    samples = get_stratified_sample(get_labels, sample_size)
    assert len(samples) == sample_size, "Sample size does not match requested size."
