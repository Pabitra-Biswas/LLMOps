import pytest
from unittest.mock import MagicMock, patch

# Mock the dspy and google modules before they are imported by our agent code
# This prevents the code from trying to make real API calls during tests
@pytest.fixture(autouse=True)
def mock_dspy_and_google():
    mock_dspy = MagicMock()
    mock_google = MagicMock()
    
    # Mock the VertexAI class
    mock_google.VertexAI.return_value = MagicMock()
    
    # Mock the ColBERTv2 class
    mock_dspy.ColBERTv2.return_value = MagicMock()
    
    # Mock the settings.configure method
    mock_dspy.settings.configure = MagicMock()

    modules = {
        'dspy': mock_dspy,
        'dspy.google': mock_google,
        'google.cloud': MagicMock()
    }
    with patch.dict('sys.modules', modules):
        yield

def test_advanced_rag_initialization():
    """
    Tests that the AdvancedRAG class can be initialized and
    that its sub-modules (retrieve, generate_query, etc.) are created.
    """
    # We can now import our agent code because the dependencies are mocked
    from app.dspy_agent import AdvancedRAG, dspy

    # Define a mock retriever module to pass to the agent
    mock_retriever = dspy.Retrieve(k=3)

    # 1. Action: Initialize the agent
    try:
        agent = AdvancedRAG(retriever_module=mock_retriever)
    except Exception as e:
        pytest.fail(f"AdvancedRAG initialization failed with an exception: {e}")

    # 2. Assert: Check that the agent and its components exist
    assert agent is not None, "Agent should not be None"
    assert agent.retrieve is not None, "Agent should have a 'retrieve' attribute"
    assert agent.generate_query is not None, "Agent should have a 'generate_query' attribute"
    assert agent.generate_answer is not None, "Agent should have a 'generate_answer' attribute"
    
    # You can even check the class of the sub-modules
    assert isinstance(agent.retrieve, type(dspy.Retrieve.return_value))

def test_load_rag_agent_runs():
    """
    Tests that the main loading function can be called without crashing.
    This is a simple smoke test.
    """
    # Import the function we want to test
    from app.dspy_agent import load_rag_agent, dspy
    
    # Mock the BootstrapFewShot compiler
    dspy.teleprompt.BootstrapFewShot.return_value.compile.return_value = "compiled_agent"
    
    # 1. Action: Call the function
    try:
        agent = load_rag_agent()
    except Exception as e:
        pytest.fail(f"load_rag_agent() failed with an exception: {e}")
        
    # 2. Assert: Check that we got the expected mock return value
    assert agent == "compiled_agent", "The compiled agent should be returned"