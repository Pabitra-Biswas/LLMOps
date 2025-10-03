import pytest
from unittest.mock import patch, MagicMock

# This fixture will now mock only the specific external classes and functions
@pytest.fixture(autouse=True)
def mock_dspy_externals():
    """
    Mocks the external-facing parts of DSPy so we don't make real API calls,
    but allows the internal structure (like dspy.teleprompt) to be imported.
    """
    # Mock the VertexAI class directly at its source
    with patch('dspy.google.VertexAI', autospec=True) as mock_vertex_ai, \
         patch('dspy.ColBERTv2', autospec=True) as mock_colbert, \
         patch('dspy.settings.configure', autospec=True) as mock_configure:
        
        # Ensure the mocked classes can still be instantiated
        mock_vertex_ai.return_value = MagicMock()
        mock_colbert.return_value = MagicMock()
        
        yield {
            "mock_vertex_ai": mock_vertex_ai,
            "mock_colbert": mock_colbert,
            "mock_configure": mock_configure
        }


def test_advanced_rag_initialization():
    """
    Tests that the AdvancedRAG class can be initialized and
    that its sub-modules (retrieve, generate_query, etc.) are created.
    """
    # Because of our fixture, the import will now succeed
    from app.dspy_agent import AdvancedRAG
    import dspy # We can import the real dspy now

    # Define a mock retriever module to pass to the agent
    mock_retriever = dspy.Retrieve(k=3)

    # 1. Action: Initialize the agent
    try:
        agent = AdvancedRAG(retriever_module=mock_retriever)
    except Exception as e:
        pytest.fail(f"AdvancedRAG initialization failed with an exception: {e}")

    # 2. Assert: Check that the agent and its components exist
    assert agent is not None
    assert agent.retrieve is not None
    assert agent.generate_query is not None
    assert agent.generate_answer is not None
    # We can check the actual type now
    assert isinstance(agent.retrieve, dspy.Retrieve)


def test_load_rag_agent_runs():
    """
    Tests that the main loading function can be called without crashing.
    """
    # This import will now succeed
    from app.dspy_agent import load_rag_agent
    from dspy.teleprompt import BootstrapFewShot

    # We need to control what the mocked compiler does
    with patch.object(BootstrapFewShot, 'compile', return_value="compiled_agent") as mock_compile:
        
        # 1. Action: Call the function
        try:
            agent = load_rag_agent()
        except Exception as e:
            pytest.fail(f"load_rag_agent() failed with an exception: {e}")
            
        # 2. Assert: Check that we got the expected mock return value and compile was called
        mock_compile.assert_called_once()
        assert agent == "compiled_agent"