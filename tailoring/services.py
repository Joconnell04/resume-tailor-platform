"""
Tailoring app services

AgentKit-like service for AI-powered resume tailoring.
"""
import os


class AgentKitTailoringService:
    """
    Stub for calling OpenAI AgentKit or similar AI workflow.
    
    This service analyzes job descriptions and matches them against
    user experience to generate tailored resume bullet points.
    
    TODO: Implement actual OpenAI AgentKit integration
    - Set up OpenAI client with API key from settings
    - Implement prompt engineering for job analysis
    - Implement experience matching logic
    - Handle URL scraping if source_url is present and raw_description is empty
    - Generate 3-5 targeted bullet points
    - Generate recommended role title
    """
    
    def __init__(self):
        """Initialize service with API configuration."""
        self.api_key = os.environ.get('OPENAI_API_KEY', '')
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not set. AI tailoring will not work.")
    
    def run_workflow(self, job_description: str, experience_graph: dict) -> dict:
        """
        Analyze job description and generate tailored resume content.
        
        Args:
            job_description: Raw text of job posting
            experience_graph: User's experience data as dict
        
        Returns:
            dict with keys:
                - title: Recommended role fit (str)
                - bullets: List of 3-5 tailored bullet points (list[str])
        
        Raises:
            NotImplementedError: This is a stub awaiting implementation
        
        Example return value:
        {
            "title": "Operations Analyst",
            "bullets": [
                "Automated ETL pipelines reducing processing time by 40%",
                "Analyzed flight delay data to improve reporting accuracy",
                "Collaborated with cross-functional teams on data projects"
            ]
        }
        """
        # TODO: Implement actual workflow
        # 1. Parse job_description for key requirements
        # 2. Extract relevant experiences from experience_graph
        # 3. Match skills and achievements to job requirements
        # 4. Generate targeted bullet points using AI
        # 5. Suggest appropriate title
        
        raise NotImplementedError(
            "AgentKit workflow not yet implemented. "
            "Please implement AI logic in tailoring/services.py"
        )
