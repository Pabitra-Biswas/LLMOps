import pytest
from unittest.mock import patch
from app.dspy_agent import AdvancedRAG

# Mock dspy settings to avoid actual API calls during tests
@patch('dspy.settings.configure')
def test_advanced_rag_initialization(mock_configure):
    """
    Tests if the AdvancedRAG agent initializes without errors.
    """
    try:
        agent = AdvancedRAG(num_passages=3, hops=2)
        assert agent is not None, "Agent should not be None"
        assert agent.hops == 2, "Hops should be set to 2"
        assert agent.retrieve.k == 3, "Number of passages for retrieval should be 3"
    except Exception as e:
        pytest.fail(f"AdvancedRAG initialization failed with an exception: {e}")