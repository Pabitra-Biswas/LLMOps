import pytest
from unittest.mock import patch, MagicMock

# This fixture will now mock the modern dspy.LM and dspy.Retrieve classes
@pytest.fixture(autouse=True)
def mock_dspy_calls():
    """
    Mocks the dspy.LM and dspy.Retrieve classes to prevent any real API
    or network calls during the test session.
    """
    # We patch the specific classes that make external calls in your code.
    with patch('dspy.LM', autospec=True) as mock_lm, \
         patch('dspy.Retrieve', autospec=True) as mock_retrieve, \
         patch('dspy.settings.configure', autospec=True) as mock_configure:
        
        # Ensure that instantiating these classes returns a mock object
        mock_lm.return_value = MagicMock()
        mock_retrieve.return_value = MagicMock()
        
        yield {
            "mock_lm": mock_lm,
            "mock_retrieve": mock_retrieve,
            "mock_configure": mock_configure
        }

def test_advanced_rag_initialization():
    """
    Tests that the AdvancedRAG class can be initialized correctly.
    """
    # We can now import our agent code because the dependencies are mocked
    from app.dspy_agent import AdvancedRAG, dspy

    # Because dspy.Retrieve is mocked, this will return a MagicMock instance
    mock_retriever = dspy.Retrieve(k=3)

    # 1. Action: Initialize the agent
    try:
        # The __init__ of AdvancedRAG will use the mocked dspy.Retrieve
        agent = AdvancedRAG(retriever_module=mock_retriever)
    except Exception as e:
        pytest.fail(f"AdvancedRAG initialization failed with an exception: {e}")

    # 2. Assert: Check that the agent and its components exist
    assert agent is not None
    assert agent.retrieve is not None
    assert agent.generate_query is not None
    assert agent.generate_answer is not None

def test_load_rag_agent_runs():
    """
    Tests that the main loading function can be called without crashing.
    """
    # This import will now succeed
    from app.dspy_agent import load_rag_agent
    from dspy.teleprompt import BootstrapFewShot

    # We need to control what the mocked compiler does. We patch its 'compile' method.
    with patch.object(BootstrapFewShot, 'compile', return_value="compiled_agent") as mock_compile:
        
        # 1. Action: Call the function
        try:
            agent = load_rag_agent()
        except Exception as e:
            pytest.fail(f"load_rag_agent() failed with an exception: {e}")
            
        # 2. Assert: Check that we got the expected mock return value and compile was called
        mock_compile.assert_called_once()
        assert agent == "compiled_agent"