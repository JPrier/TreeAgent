from src.modelAccessors.mock_accessor import MockAccessor
from src.dataModel.model_response import FollowUpResponse, FailedResponse


def test_mock_accessor_follow_up_response():
    accessor = MockAccessor()
    response = accessor.prompt_model(
        "mock-model", "", "irrelevant", FollowUpResponse
    )
    assert isinstance(response, FollowUpResponse)
    assert response.follow_up_ask.description


def test_mock_accessor_failed_response():
    accessor = MockAccessor()
    response = accessor.prompt_model(
        "mock-model", "", "irrelevant", FailedResponse
    )
    assert isinstance(response, FailedResponse)
    assert response.error_message
