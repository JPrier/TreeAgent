import pytest

from src.dataModel.validation_result import ValidationResult


def test_validation_result_valid_with_no_errors():
    """Test creating a valid ValidationResult with no errors."""
    result = ValidationResult(is_valid=True, errors=None)
    assert result.is_valid is True
    assert result.errors is None


def test_validation_result_valid_with_empty_errors():
    """Test creating a valid ValidationResult with empty errors list."""
    result = ValidationResult(is_valid=True, errors=[])
    assert result.is_valid is True
    assert result.errors == []


def test_validation_result_invalid_with_errors():
    """Test creating an invalid ValidationResult with errors."""
    errors = ["Error 1", "Error 2"]
    result = ValidationResult(is_valid=False, errors=errors)
    assert result.is_valid is False
    assert result.errors == errors


def test_validation_result_invalid_with_single_error():
    """Test creating an invalid ValidationResult with a single error."""
    error = ["Single error"]
    result = ValidationResult(is_valid=False, errors=error)
    assert result.is_valid is False
    assert result.errors == error


def test_validation_result_invalid_valid_true_with_errors_raises_error():
    """Test that ValidationResult raises error when is_valid=True but errors are present."""
    with pytest.raises(ValueError, match="Cannot have both is_valid=True and an error_message"):
        ValidationResult(is_valid=True, errors=["Some error"])


def test_validation_result_invalid_valid_false_with_no_errors_raises_error():
    """Test that ValidationResult raises error when is_valid=False but no errors provided."""
    with pytest.raises(ValueError, match="Must provide an error_message when is_valid=False"):
        ValidationResult(is_valid=False, errors=None)


def test_validation_result_invalid_valid_false_with_empty_errors_raises_error():
    """Test that ValidationResult raises error when is_valid=False but empty errors provided."""
    with pytest.raises(ValueError, match="Must provide an error_message when is_valid=False"):
        ValidationResult(is_valid=False, errors=[])