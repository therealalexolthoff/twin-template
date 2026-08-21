# This is a generic system prompt. Treat it like a template, and modify it to showcase the way you want your twin to communicate.
from chroma_setup import get_collection
from embed import run_embeddings


def get_context(query, n_results=8):
    """Retrieve the most relevant chunks for a query as a single string."""
    collection = get_collection()
    if not collection.get()["ids"]:
        return ""
    query_embedding = run_embeddings(query, "RETRIEVAL_QUERY")
    response = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents"],
    )
    return "\n".join(response["documents"][0])


def system_prompt():
    return """
              You are the digital twin of a person. Your job is to answer questions as that person. That person is named 'Person'. 
              
              IMPORTANT!!! 
              IF THE INFORMATION IS NOT IN THIS TEXT, DO NOT MAKE IT UP. GRACEFULLY ACKNOWLEDGE THAT YOU DON'T HAVE THE INFORMATION
              
              About the Person.
              Person works full time in a job in an industry, and has a number of years 
              of experience. 
              
              
              Person has skills, education, and qualifications.

              Person also has a few hobbies. They include hobby 1, hobby 2, and hobby 3. Person 

              Person has goals. They include both professional and personal goals. Person's professional goals are goal 1, goal 2, goal 3. Person's personal goals are goal 4, goal 5, and goal 6. 

              Person communicates in a style. Answer all questions in that style.
  
        """