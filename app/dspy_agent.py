import dspy
from dspy.teleprompt import BootstrapFewShot
import os
# # Cell 1: Setup and Configuration
# import dspy
# import os

# --- Configuration ---
# IMPORTANT: Set your GCP Project ID here.
GCP_PROJECT_ID = "my-bigquery-test-466512"  # Replace with your actual project ID
os.environ["GCP_PROJECT_ID"] = GCP_PROJECT_ID

print(f"Using GCP Project: {os.getenv('GCP_PROJECT_ID')}")

# --- Initialize DSPy Modules ---
# For DSPy v3.0.3, use the LM class with vertex_ai prefix
gemini_model = dspy.LM(
    model='vertex_ai/gemini-2.0-flash',  # or 'vertex_ai/gemini-1.5-flash' for faster/cheaper
    project=GCP_PROJECT_ID,
    location='us-central1'
)

# Wikipedia-based Retriever (install with: pip install wikipedia-api)
import wikipedia

# Create a simple class to hold passage data
class Passage:
    def __init__(self, long_text, text, title, url):
        self.long_text = long_text
        self.text = text
        self.title = title
        self.url = url
    
    def __repr__(self):
        return f"Passage(title='{self.title}')"

class WikipediaRM(dspy.Retrieve):
    def __init__(self, k=3):
        super().__init__(k=k)
        self.k = k
    
    def forward(self, query_or_queries, k=None):
        """Retrieve passages from Wikipedia."""
        # Handle both single query and multiple queries
        queries = [query_or_queries] if isinstance(query_or_queries, str) else query_or_queries
        k = k if k is not None else self.k
        
        all_passages = []
        
        for query in queries:
            try:
                # Search Wikipedia
                search_results = wikipedia.search(query, results=k)
                
                for title in search_results[:k]:
                    try:
                        page = wikipedia.page(title, auto_suggest=False)
                        # Create a Passage object with the attributes DSPy expects
                        passage = Passage(
                            long_text=page.content[:800],  # Longer excerpt for better context
                            text=page.content[:500],       # Shorter version
                            title=title,
                            url=page.url
                        )
                        all_passages.append(passage)
                    except Exception as e:
                        print(f"Error fetching page '{title}': {e}")
                        continue
                
            except Exception as e:
                print(f"Wikipedia search error for query '{query}': {e}")
        
        # Return in the format DSPy expects
        return all_passages

# Configure the Retrieval Model
retriever_model = WikipediaRM(k=3)

# Configure DSPy with the LM and RM
dspy.configure(lm=gemini_model, rm=retriever_model)

print("DSPy configured successfully with Wikipedia retriever.")


# Cell 2: Define the Agent's Architecture
class GenerateSearchQuery(dspy.Signature):
    """Generate a specific, concise search query to find information about the question."""
    context = dspy.InputField(desc="Previous context for multi-hop reasoning. Can be empty.")
    question = dspy.InputField()
    query = dspy.OutputField(desc="A search query using keywords from the question.")


class GenerateAnswer(dspy.Signature):
    """Synthesize the provided context to give a comprehensive answer to the question."""
    context = dspy.InputField(desc="Relevant passages from a knowledge source.")
    question = dspy.InputField()
    answer = dspy.OutputField(desc="A detailed answer that directly addresses the question.")


class AdvancedRAG(dspy.Module):
    def __init__(self, hops=2):
        super().__init__()
        # Use the default retriever configured in dspy.configure
        self.retrieve = dspy.Retrieve(k=3)  # Retrieve top 3 passages per query
        self.generate_query = dspy.ChainOfThought(GenerateSearchQuery)
        self.generate_answer = dspy.ChainOfThought(GenerateAnswer)
        self.hops = hops
    
    def forward(self, question):
        full_context = []
        
        for i in range(self.hops):
            try:
                # 1. Generate a search query based on the question and any prior context.
                query = self.generate_query(context=full_context, question=question).query
                print(f"\n--- Hop {i+1} ---")
                print(f"Query: {query}")
                
                # 2. Retrieve relevant passages for that query.
                passages = self.retrieve(query).passages
                print(f"Retrieved {len(passages)} passages")
                
                # Display passage titles and preview
                for idx, passage in enumerate(passages):
                    title = getattr(passage, 'title', 'Unknown')
                    text_preview = getattr(passage, 'long_text', '')[:150]
                    print(f"  [{idx+1}] {title}")
                    print(f"      Preview: {text_preview}...")
                
                # 3. Add the new passages to our full context.
                # Extract the text content from passage objects
                for passage in passages:
                    if hasattr(passage, 'long_text'):
                        full_context.append(passage.long_text)
                    elif hasattr(passage, 'text'):
                        full_context.append(passage.text)
                        
            except Exception as e:
                print(f"Error at hop {i+1}: {e}")
                import traceback
                traceback.print_exc()
        
        # 4. Generate a final answer using the combined context from all hops.
        if not full_context:
            full_context = ["No external context retrieved. Please answer based on general knowledge."]
        
        print(f"\n--- Final Context ---")
        print(f"Total context passages: {len(full_context)}")
        print(f"Total context length: {sum(len(c) for c in full_context)} characters")
        
        prediction = self.generate_answer(context=full_context, question=question)
        
        return dspy.Prediction(answer=prediction.answer)


print("AdvancedRAG module defined.")


# # Cell 3: First Test Run
# # Instantiate our RAG agent
# uncompiled_rag = AdvancedRAG()

# # Define our test question
# my_question = "Which U.S. President signed the act that created NASA, and in what year was that act signed?"

# # Execute the agent
# prediction = uncompiled_rag(question=my_question)

# # Print the results
# print(f"\nQuestion: {my_question}")
# print(f"Predicted Answer: {prediction.answer}")

# Example of compiling the RAG agent
def compile_rag_agent():
    # Dummy data for demonstration
    trainset = [
        dspy.Example(question="What is the capital of France?", answer="Paris").with_inputs("question"),
        dspy.Example(question="Who wrote 'To Kill a Mockingbird'?", answer="Harper Lee").with_inputs("question"),
    ]

    # Define a metric for optimization
    def validate_answer(example, pred, trace=None):
        return example.answer.lower() in pred.answer.lower()

    # Compile the DSPy program
    teleprompter = BootstrapFewShot(metric=validate_answer)
    optimized_rag = teleprompter.compile(AdvancedRAG(), trainset=trainset)
    return optimized_rag



def load_rag_agent():
    """
    Creates, compiles, and returns an instance of the AdvancedRAG agent.
    This function will be called by our FastAPI server on startup.
    """
    # Dummy data for demonstration of the compilation process
    trainset = [
        dspy.Example(question="What is the capital of France?", answer="Paris").with_inputs("question"),
        dspy.Example(question="Who wrote 'To Kill a Mockingbird'?", answer="Harper Lee").with_inputs("question"),
    ]

    # Define a metric for the optimizer to use
    def validate_answer(example, pred, trace=None):
        return example.answer.lower() in pred.answer.lower()

    # Set up the teleprompter (optimizer)
    teleprompter = BootstrapFewShot(metric=validate_answer, max_bootstrapped_demos=2)

    # Compile the DSPy program. This will run a few calls to the LLM to build effective prompts.
    print("Compiling the RAG agent... (This may take a moment)")
    optimized_rag = teleprompter.compile(AdvancedRAG(), trainset=trainset)
    print("Agent compilation complete.")
    
    return optimized_rag