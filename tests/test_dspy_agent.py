import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def mock_dspy_calls():
    """
    Mocks the dspy.LM and dspy.Retrieve classes to prevent any real API
    or network calls during the test session.
    We REMOVED the patch on dspy.settings.configure as it's problematic
    and unnecessary.
    """
    with patch('dspy.LM', autospec=True) as mock_lm, \
         patch('dspy.Retrieve', autospec=True) as mock_retrieve:
        
        mock_lm.return_value = MagicMock()
        mock_retrieve.return_value = MagicMock()
        
        yield {
            "mock_lm": mock_lm,
            "mock_retrieve": mock_retrieve,
        }

def test_advanced_rag_initialization():
    """
    Tests that the AdvancedRAG class can be initialized correctly.
    """
    # Import the class to be tested
    from app.dspy_agent import AdvancedRAG

    # 1. Action: Initialize the agent with NO arguments, just like in your app code.
    try:
        # The __init__ of AdvancedRAG will now call the mocked dspy.Retrieve
        # without any issues.
        agent = AdvancedRAG(hops=2)
    except Exception as e:
        pytest.fail(f"AdvancedRAG initialization failed with an exception: {e}")

    # 2. Assert: Check that the agent and its components exist
    assert agent is not None
    assert agent.retrieve is not None
    assert agent.generate_query is not None
    assert agent.generate_answer is not None
    assert agent.hops == 2

def test_load_rag_agent_runs():
    """
    Tests that the main loading function can be called without crashing.
    """
    from app.dspy_agent import load_rag_agent
    from dspy.teleprompt import BootstrapFewShot

    # We patch the 'compile' method to prevent it from running and to control its output
    with patch.object(BootstrapFewShot, 'compile', return_value="compiled_agent") as mock_compile:
        
        # 1. Action: Call the function
        try:
            agent = load_rag_agent()
        except Exception as e:
            pytest.fail(f"load_rag_agent() failed with an exception: {e}")
            
        # 2. Assert: Check that we got the expected mock return value and compile was called
        mock_compile.assert_called_once()
        assert agent == "compiled_agent"