from pydantic import TypeAdapter

from src.modelAccessors.mock_accessor import MockAccessor
from src.dataModel.model_response import (
    FollowUpResponse,
    FailedResponse,
    ClarifierResponse,
)


def test_mock_accessor_follow_up_response():
    accessor = MockAccessor()
    adapter = TypeAdapter(ClarifierResponse)
    schema = adapter.json_schema()
    response = accessor.call_model(
        "mock_follow_up", adapter=adapter, schema=schema, model="mock-model"
    )
    assert isinstance(response, FollowUpResponse)
    assert response.follow_up_ask.description


def test_mock_accessor_failed_response():
    accessor = MockAccessor()
    adapter = TypeAdapter(FailedResponse)
    schema = adapter.json_schema()
    response = accessor.call_model(
        "mock_fail", adapter=adapter, schema=schema, model="mock-model"
    )
    assert isinstance(response, FailedResponse)
    assert response.error_message
