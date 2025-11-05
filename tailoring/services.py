"""
Tailoring app services

AgentKit-like service for AI-powered resume tailoring.
"""
import os
import re
from typing import Dict, List, Optional
# Uncomment when implementing OpenAI integration:
# from openai import OpenAI


class AgentKitTailoringService:
    """
    Service for AI-powered resume tailoring using OpenAI AgentKit pattern.
    
    This service analyzes job descriptions and matches them against
    user experience to generate tailored resume bullet points.
    
    Implementation Guide:
    1. Install OpenAI SDK: pip install openai
    2. Set OPENAI_API_KEY environment variable
    3. Uncomment OpenAI import above
    4. Implement the methods marked with TODO
    5. Test with sample job descriptions and experience graphs
    """
    
    def __init__(self):
        """Initialize service with API configuration."""
        self.api_key = os.environ.get('OPENAI_API_KEY', '')
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not set. AI tailoring will not work.")
        
        # Uncomment when implementing OpenAI:
        # self.client = OpenAI(api_key=self.api_key)
        # self.model = os.environ.get('OPENAI_MODEL', 'gpt-4-turbo-preview')
    
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
        # TODO: Remove this when implementing
        raise NotImplementedError(
            "AgentKit workflow not yet implemented. "
            "Please implement AI logic in tailoring/services.py"
        )
        
        # Implementation pattern (uncomment and adapt):
        """
        # Step 1: Extract job requirements
        requirements = self._extract_job_requirements(job_description)
        
        # Step 2: Match with user experience
        relevant_experiences = self._match_experiences(
            requirements, 
            experience_graph
        )
        
        # Step 3: Generate tailored content with AI
        result = self._generate_tailored_content(
            job_description,
            requirements,
            relevant_experiences
        )
        
        return result
        """
    
    def _extract_job_requirements(self, job_description: str) -> Dict[str, List[str]]:
        """
        Extract key requirements from job description.
        
        Args:
            job_description: Raw job posting text
        
        Returns:
            dict with:
                - skills: List of required skills
                - qualifications: List of qualifications
                - responsibilities: List of key responsibilities
        
        TODO: Implement using OpenAI or regex patterns
        """
        # Placeholder implementation
        return {
            'skills': [],
            'qualifications': [],
            'responsibilities': []
        }
        
        # Example OpenAI implementation:
        """
        prompt = f'''
        Analyze this job description and extract:
        1. Required technical skills
        2. Key qualifications
        3. Main responsibilities
        
        Job Description:
        {job_description}
        
        Return as JSON with keys: skills, qualifications, responsibilities
        '''
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a job analysis expert."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
        """
    
    def _match_experiences(
        self, 
        requirements: Dict[str, List[str]], 
        experience_graph: dict
    ) -> List[dict]:
        """
        Match user experiences to job requirements.
        
        Args:
            requirements: Extracted job requirements
            experience_graph: User's experience data
        
        Returns:
            List of relevant experience entries, sorted by relevance
        
        TODO: Implement matching algorithm
        """
        experiences = experience_graph.get('experiences', [])
        
        # Placeholder - return all experiences
        return experiences
        
        # Example implementation with scoring:
        """
        scored_experiences = []
        required_skills = set(s.lower() for s in requirements.get('skills', []))
        
        for exp in experiences:
            score = 0
            exp_skills = set(s.lower() for s in exp.get('skills', []))
            
            # Calculate skill overlap
            skill_overlap = len(required_skills & exp_skills)
            score += skill_overlap * 10
            
            # Keyword matching in achievements
            for achievement in exp.get('achievements', []):
                for keyword in requirements.get('responsibilities', []):
                    if keyword.lower() in achievement.lower():
                        score += 5
            
            if score > 0:
                scored_experiences.append({
                    'experience': exp,
                    'relevance_score': score
                })
        
        # Sort by relevance
        scored_experiences.sort(key=lambda x: x['relevance_score'], reverse=True)
        return [item['experience'] for item in scored_experiences[:5]]
        """
    
    def _generate_tailored_content(
        self,
        job_description: str,
        requirements: Dict[str, List[str]],
        relevant_experiences: List[dict]
    ) -> dict:
        """
        Generate tailored resume content using AI.
        
        Args:
            job_description: Original job posting
            requirements: Extracted requirements
            relevant_experiences: Matched user experiences
        
        Returns:
            dict with 'title' and 'bullets' keys
        
        TODO: Implement OpenAI call for content generation
        """
        # Placeholder
        return {
            'title': 'Relevant Position Title',
            'bullets': [
                'Bullet point 1 tailored to job requirements',
                'Bullet point 2 highlighting relevant experience',
                'Bullet point 3 showcasing measurable achievements'
            ]
        }
        
        # Example OpenAI implementation:
        """
        # Format experiences for prompt
        experience_text = self._format_experiences(relevant_experiences)
        
        prompt = f'''
        Create tailored resume content for this job application.
        
        Job Description:
        {job_description}
        
        Candidate's Relevant Experience:
        {experience_text}
        
        Generate:
        1. A recommended job title/header for the resume
        2. 3-5 powerful bullet points that:
           - Highlight relevant skills and experience
           - Use action verbs and quantifiable results
           - Align with job requirements
           - Follow STAR method (Situation, Task, Action, Result)
        
        Return as JSON with keys: title, bullets (array of strings)
        '''
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert resume writer who creates "
                               "compelling, achievement-focused content."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        return json.loads(response.choices[0].message.content)
        """
    
    def _format_experiences(self, experiences: List[dict]) -> str:
        """
        Format experience data for AI prompt.
        
        Args:
            experiences: List of experience dictionaries
        
        Returns:
            Formatted string representation of experiences
        """
        formatted = []
        for exp in experiences:
            exp_text = f"""
Title: {exp.get('title', 'N/A')}
Company: {exp.get('company', 'N/A')}
Duration: {exp.get('start', '')} to {exp.get('end', 'Present')}
Skills: {', '.join(exp.get('skills', []))}
Achievements:
"""
            for achievement in exp.get('achievements', []):
                exp_text += f"  - {achievement}\n"
            
            formatted.append(exp_text)
        
        return "\n".join(formatted)
    
    def scrape_job_url(self, url: str) -> str:
        """
        Scrape job description from URL.
        
        Args:
            url: Job posting URL
        
        Returns:
            Extracted job description text
        
        TODO: Implement web scraping
        Recommended libraries: BeautifulSoup4, requests, or Playwright
        """
        raise NotImplementedError(
            "URL scraping not yet implemented. "
            "Install beautifulsoup4 and requests, then implement this method."
        )
        
        # Example implementation:
        """
        import requests
        from bs4 import BeautifulSoup
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Common job posting selectors (adjust per site)
            job_text = soup.find('div', class_='job-description')
            if job_text:
                return job_text.get_text(strip=True)
            
            # Fallback: get all text
            return soup.get_text(strip=True)
            
        except Exception as e:
            raise ValueError(f"Failed to scrape URL: {str(e)}")
        """


class ResumeOptimizer:
    """
    Helper class for resume optimization utilities.
    
    Provides additional functionality for resume enhancement,
    ATS optimization, and formatting.
    """
    
    @staticmethod
    def calculate_ats_score(bullet_points: List[str], job_keywords: List[str]) -> float:
        """
        Calculate ATS (Applicant Tracking System) compatibility score.
        
        Args:
            bullet_points: List of resume bullet points
            job_keywords: Keywords from job description
        
        Returns:
            Score from 0-100 indicating ATS compatibility
        """
        if not job_keywords or not bullet_points:
            return 0.0
        
        # Combine all bullet text
        resume_text = ' '.join(bullet_points).lower()
        
        # Count keyword matches
        matches = sum(1 for keyword in job_keywords if keyword.lower() in resume_text)
        
        # Calculate score
        score = (matches / len(job_keywords)) * 100
        return min(score, 100.0)
    
    @staticmethod
    def enhance_bullet_with_metrics(bullet: str) -> str:
        """
        Enhance a bullet point by emphasizing metrics and results.
        
        Args:
            bullet: Original bullet point text
        
        Returns:
            Enhanced bullet point
        """
        # Check if bullet already has metrics
        has_number = bool(re.search(r'\d+', bullet))
        has_percent = bool(re.search(r'\d+%', bullet))
        
        if has_number or has_percent:
            return bullet  # Already has metrics
        
        # Add suggestion for metrics
        return f"{bullet} [Add metrics: X%, $Y, Z units]"
    
    @staticmethod
    def validate_bullet_point(bullet: str) -> Dict[str, any]:
        """
        Validate bullet point against best practices.
        
        Args:
            bullet: Bullet point text to validate
        
        Returns:
            dict with validation results:
                - valid: bool
                - issues: List[str]
                - suggestions: List[str]
        """
        issues = []
        suggestions = []
        
        # Check length
        if len(bullet) < 30:
            issues.append("Too short - add more detail")
        if len(bullet) > 150:
            issues.append("Too long - aim for 1-2 lines")
        
        # Check for action verb
        action_verbs = ['led', 'developed', 'created', 'managed', 'improved', 
                       'increased', 'decreased', 'achieved', 'implemented']
        starts_with_action = any(bullet.lower().startswith(verb) for verb in action_verbs)
        if not starts_with_action:
            suggestions.append("Start with a strong action verb")
        
        # Check for metrics
        has_metrics = bool(re.search(r'\d+', bullet))
        if not has_metrics:
            suggestions.append("Add quantifiable metrics or results")
        
        # Check for passive voice
        passive_indicators = ['was', 'were', 'been', 'being']
        if any(word in bullet.lower().split() for word in passive_indicators):
            suggestions.append("Consider using active voice")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'suggestions': suggestions
        }
