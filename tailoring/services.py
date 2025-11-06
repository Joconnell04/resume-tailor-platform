"""
Tailoring app services

AgentKit-like service for AI-powered resume tailoring without relying on the
hosted AgentKit runtime. This module orchestrates prompt construction,
experience matching, and OpenAI API calls with web search grounding.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from django.conf import settings

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled gracefully during runtime
    OpenAI = None

logger = logging.getLogger(__name__)


STOPWORDS = {
    "and",
    "the",
    "to",
    "of",
    "a",
    "for",
    "in",
    "on",
    "with",
    "an",
    "by",
    "is",
    "be",
    "as",
    "or",
    "at",
    "from",
    "into",
    "will",
    "that",
}


class TailoringPipelineError(Exception):
    """
    Domain-specific exception for tailoring failures.
    """


@dataclass
class TailoringResult:
    """
    Structured representation of the OpenAI response payload.
    """

    title: str = ""
    sections: List[Dict[str, List[str]]] = field(default_factory=list)
    bullets: List[str] = field(default_factory=list)
    summary: str = ""
    suggestions: List[str] = field(default_factory=list)
    cover_letter: str = ""
    token_usage: Dict[str, int] = field(default_factory=dict)
    run_id: str = ""
    debug: Dict[str, object] = field(default_factory=dict)

    @property
    def words_generated(self) -> int:
        """
        Count approximate number of words produced for usage reporting.
        """
        text_fragments = self.bullets[:]
        if self.summary:
            text_fragments.append(self.summary)
        if self.cover_letter:
            text_fragments.append(self.cover_letter)
        text = " ".join(text_fragments)
        return len(re.findall(r"\w+", text))


class AgentKitTailoringService:
    """
    Service for AI-powered resume tailoring using the OpenAI Responses API.
    """

    DEFAULT_PARAMETERS = {
        "sections": ["Professional Highlights"],
        "bullets_per_section": 3,
        "tone": "confident and metric-driven",
        "include_summary": True,
        "include_cover_letter": False,
        "temperature": 0.35,
        "max_output_tokens": 900,
    }

    TECH_KEYWORDS = {
        # Programming Languages
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "php", "swift",
        "kotlin", "go", "rust", "scala", "r", "matlab", "perl", "vb.net", "objective-c",
        # Databases
        "sql", "nosql", "mysql", "postgresql", "mongodb", "redis", "cassandra", "dynamodb",
        "oracle", "sqlserver", "mariadb", "sqlite", "elasticsearch", "neo4j", "couchdb",
        # Cloud Platforms
        "aws", "azure", "gcp", "heroku", "digitalocean", "linode", "cloudflare",
        "s3", "ec2", "lambda", "cloudformation", "cloudwatch", "rds", "sagemaker",
        # Frameworks & Libraries
        "react", "angular", "vue", "django", "flask", "fastapi", "spring", "express",
        "node.js", "nodejs", ".net", "asp.net", "rails", "laravel", "next.js", "gatsby",
        # DevOps & Tools
        "docker", "kubernetes", "terraform", "ansible", "jenkins", "gitlab", "github",
        "ci/cd", "git", "linux", "unix", "bash", "powershell", "nginx", "apache",
        # Data & Analytics
        "spark", "hadoop", "kafka", "airflow", "databricks", "snowflake", "redshift",
        "tableau", "powerbi", "looker", "qlik", "pandas", "numpy", "scipy",
        # AI/ML
        "ml", "ai", "tensorflow", "pytorch", "scikit-learn", "keras", "transformers",
        "nlp", "computer vision", "deep learning", "machine learning", "data science",
        # Methodologies
        "agile", "scrum", "kanban", "waterfall", "devops", "tdd", "bdd", "pair programming",
        # Business Tools
        "salesforce", "sap", "oracle", "workday", "servicenow", "jira", "confluence",
        "slack", "microsoft teams", "sharepoint", "excel", "powerpoint",
        # Other
        "api", "rest", "graphql", "microservices", "serverless", "etl", "data pipeline",
        "html", "css", "sass", "webpack", "babel", "typescript", "json", "xml", "yaml",
        "oauth", "jwt", "saml", "sso", "encryption", "security", "compliance", "gdpr",
    }
    
    # ATS-critical action verbs that show impact
    ATS_ACTION_VERBS = {
        # Leadership & Management
        "led", "managed", "directed", "supervised", "coordinated", "oversaw", "mentored",
        "coached", "trained", "guided", "delegated", "organized", "facilitated",
        # Achievement & Results
        "achieved", "improved", "increased", "decreased", "reduced", "accelerated",
        "optimized", "streamlined", "enhanced", "transformed", "exceeded", "delivered",
        # Innovation & Creation
        "developed", "created", "designed", "built", "engineered", "architected",
        "established", "launched", "pioneered", "innovated", "invented", "spearheaded",
        # Analysis & Strategy
        "analyzed", "evaluated", "assessed", "identified", "researched", "investigated",
        "diagnosed", "forecasted", "strategized", "planned", "recommended",
        # Collaboration & Communication
        "collaborated", "partnered", "communicated", "presented", "negotiated",
        "influenced", "persuaded", "consulted", "advised", "facilitated",
        # Implementation & Execution
        "implemented", "executed", "deployed", "integrated", "automated", "configured",
        "maintained", "operated", "administered", "monitored", "resolved",
    }
    
    # Soft skills that recruiters look for
    SOFT_SKILLS = {
        "leadership", "communication", "teamwork", "problem-solving", "critical thinking",
        "analytical", "strategic thinking", "creativity", "adaptability", "time management",
        "project management", "stakeholder management", "cross-functional", "collaboration",
        "presentation", "negotiation", "decision-making", "conflict resolution",
    }
    
    # Common certifications that boost ATS scores
    CERTIFICATIONS = {
        "aws certified", "azure certified", "gcp certified", "pmp", "cissp", "cism",
        "comptia", "ccna", "ccnp", "ccie", "cka", "ckad", "certified scrum master",
        "csm", "pmi", "itil", "six sigma", "cfa", "cpa", "mba", "ph.d", "phd",
    }

    def __init__(self):
        """
        Initialize service with API configuration.
        """
        self.api_key = os.environ.get("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")
        if not self.api_key:
            raise TailoringPipelineError("OPENAI_API_KEY is not configured.")
        if OpenAI is None:
            raise TailoringPipelineError(
                "openai package is not installed. Run `pip install openai` first."
            )

        self.model = os.environ.get("OPENAI_MODEL") or getattr(
            settings,
            "OPENAI_MODEL",
            "gpt-4o-mini",
        )
        self.client = OpenAI(api_key=self.api_key)

    # --------------------------------------------------------------------- #
    # Public helpers                                                        #
    # --------------------------------------------------------------------- #

    def run_workflow(
        self,
        job_description: str,
        experience_graph: dict,
        *,
        parameters: Optional[Dict[str, object]] = None,
        source_url: str = "",
    ) -> Dict[str, object]:
        """
        Analyze a job description and generate tailored resume content.

        Args:
            job_description: Text from raw description or user input.
            experience_graph: User's experience data as a dictionary.
            parameters: Tailoring preferences supplied by the user.
            source_url: Optional URL that OpenAI will fetch via web search grounding.

        Returns:
            Dict representing tailored resume content and metadata.
        """
        if not job_description and not source_url:
            raise TailoringPipelineError("Job description content is required.")

        normalized_parameters = self.normalize_parameters(parameters or {})
        cleaned_description = self._clean_text(job_description)
        requirements = self._extract_job_requirements(cleaned_description)
        relevant_experiences = self._match_experiences(requirements, experience_graph)

        prompt = self._build_prompt(
            job_description=cleaned_description,
            requirements=requirements,
            experiences=relevant_experiences,
            parameters=normalized_parameters,
            source_url=source_url,
        )

        result = self._generate_tailored_content(
            prompt=prompt, parameters=normalized_parameters, source_url=source_url
        )

        # Calculate ATS compatibility score
        all_bullets = result.bullets or self._flatten_sections(result.sections)
        optimizer = ResumeOptimizer()
        ats_score = optimizer.calculate_ats_score(
            bullet_points=all_bullets,
            job_keywords=requirements.get("keywords", []),
            required_skills=requirements.get("required_skills", []),
            preferred_skills=requirements.get("preferred_skills", []),
        )
        
        # Validate bullet points for quality
        bullet_validations = []
        for bullet in all_bullets[:10]:  # Validate first 10 bullets
            validation = optimizer.validate_bullet_point(bullet)
            if not validation["valid"] or validation.get("suggestions"):
                bullet_validations.append({
                    "bullet": bullet[:50] + "..." if len(bullet) > 50 else bullet,
                    "issues": validation.get("issues", []),
                    "suggestions": validation.get("suggestions", []),
                })
        
        # Enhance suggestions with ATS findings
        enhanced_suggestions = list(result.suggestions)
        if ats_score["missing_critical"]:
            enhanced_suggestions.insert(
                0, 
                f"Add required skills: {', '.join(ats_score['missing_critical'][:3])}"
            )
        if ats_score["overall_score"] < 70:
            enhanced_suggestions.insert(
                0,
                f"ATS Score: {ats_score['overall_score']}% - Improve keyword coverage"
            )

        return {
            "title": result.title,
            "sections": result.sections,
            "bullets": all_bullets,
            "summary": result.summary,
            "suggestions": enhanced_suggestions,
            "cover_letter": result.cover_letter,
            "token_usage": result.token_usage,
            "run_id": result.run_id,
            "ats_score": ats_score,
            "bullet_quality": {
                "total_bullets": len(all_bullets),
                "issues_found": len(bullet_validations),
                "validations": bullet_validations[:5],  # Top 5 issues
            },
            "debug": {
                "requirements": requirements,
                "selected_experiences": relevant_experiences,
                "parameters": normalized_parameters,
                "openai_response": result.debug.get("raw_payload"),
                "ats_analysis": ats_score,
            },
            "words_generated": result.words_generated,
        }

    @classmethod
    def normalize_parameters(cls, parameters: Dict[str, object]) -> Dict[str, object]:
        """
        Merge user-specified parameters with defaults and sanitize values.
        """
        merged = {**cls.DEFAULT_PARAMETERS, **parameters}

        sections = merged.get("sections")
        if isinstance(sections, str):
            raw_sections = re.split(r"[\n,]+", sections)
            sections = [section.strip() for section in raw_sections if section.strip()]
        elif isinstance(sections, Iterable):
            sections = [str(section).strip() for section in sections if str(section).strip()]
        else:
            sections = list(cls.DEFAULT_PARAMETERS["sections"])

        merged["sections"] = sections or list(cls.DEFAULT_PARAMETERS["sections"])

        try:
            merged["bullets_per_section"] = max(1, int(merged.get("bullets_per_section", 3)))
        except (TypeError, ValueError):
            merged["bullets_per_section"] = cls.DEFAULT_PARAMETERS["bullets_per_section"]

        try:
            merged["temperature"] = float(merged.get("temperature", cls.DEFAULT_PARAMETERS["temperature"]))
        except (TypeError, ValueError):
            merged["temperature"] = cls.DEFAULT_PARAMETERS["temperature"]

        try:
            merged["max_output_tokens"] = int(
                merged.get("max_output_tokens", cls.DEFAULT_PARAMETERS["max_output_tokens"])
            )
        except (TypeError, ValueError):
            merged["max_output_tokens"] = cls.DEFAULT_PARAMETERS["max_output_tokens"]

        merged["tone"] = (
            str(merged.get("tone", cls.DEFAULT_PARAMETERS["tone"])).strip()
            or cls.DEFAULT_PARAMETERS["tone"]
        )
        merged["include_summary"] = bool(merged.get("include_summary", True))
        merged["include_cover_letter"] = bool(merged.get("include_cover_letter", False))

        return merged

    # --------------------------------------------------------------------- #
    # Internal helpers                                                      #
    # --------------------------------------------------------------------- #

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"\r\n?", "\n", text)
        text = re.sub(r"\s+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract ATS-relevant keywords including tech terms, action verbs, and soft skills.
        """
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9\+#\./-]{1,}", text)
        keywords: List[str] = []
        text_lower = text.lower()
        
        # Check for multi-word certifications first
        for cert in self.CERTIFICATIONS:
            if cert in text_lower:
                keywords.append(cert)
        
        # Extract single tokens
        for token in tokens:
            token_clean = token.strip(" .,;:()[]{}").lower()
            if len(token_clean) < 2 or token_clean in STOPWORDS:
                continue
            
            # Include if it's a tech keyword, action verb, soft skill, or proper noun
            if (token_clean in self.TECH_KEYWORDS or 
                token_clean in self.ATS_ACTION_VERBS or
                token_clean in self.SOFT_SKILLS or
                token.istitle() or token.isupper()):
                keywords.append(token_clean)
        
        return keywords

    def _extract_job_requirements(self, job_description: str) -> Dict[str, List[str]]:
        """
        Enhanced extraction of requirements with ATS-critical categorization.
        Distinguishes between required/preferred, hard/soft skills, and certifications.
        """
        requirements = {
            "skills": [],
            "qualifications": [],
            "responsibilities": [],
            "keywords": [],
            "required_skills": [],  # Must-have skills
            "preferred_skills": [],  # Nice-to-have skills
            "certifications": [],
            "action_verbs": [],
            "years_experience": [],
            "education": [],
        }

        if not job_description:
            return requirements

        current_bucket = "responsibilities"
        is_required_section = False
        is_preferred_section = False
        skill_candidates: set[str] = set()
        keyword_candidates: List[str] = []
        text_lower = job_description.lower()

        # Extract years of experience requirements
        exp_patterns = [
            r"(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)",
            r"minimum\s+(?:of\s+)?(\d+)\s+(?:years?|yrs?)",
            r"at least\s+(\d+)\s+(?:years?|yrs?)",
        ]
        for pattern in exp_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                years = match.group(1)
                requirements["years_experience"].append(f"{years}+ years")

        # Extract education requirements
        education_keywords = ["bachelor", "master", "phd", "ph.d", "mba", "degree", "b.s.", "m.s."]
        for edu_kw in education_keywords:
            if edu_kw in text_lower:
                # Find the line containing this education requirement
                for line in job_description.splitlines():
                    if edu_kw in line.lower():
                        requirements["education"].append(line.strip().lstrip("-*•· "))
                        break

        # Process line by line
        for raw_line in job_description.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            lowered = line.lower()
            
            # Detect section headers
            if "responsibil" in lowered or "duties" in lowered or "you will" in lowered:
                current_bucket = "responsibilities"
                is_required_section = False
                is_preferred_section = False
                continue
            if "qualification" in lowered or "requirements" in lowered or "must have" in lowered:
                current_bucket = "qualifications"
                is_required_section = "required" in lowered or "must" in lowered
                is_preferred_section = "preferred" in lowered or "nice to have" in lowered
                continue
            if "skill" in lowered or "technolog" in lowered or "tools" in lowered or "proficienc" in lowered:
                current_bucket = "skills"
                is_required_section = "required" in lowered or "must" in lowered
                is_preferred_section = "preferred" in lowered or "nice to have" in lowered or "bonus" in lowered
                continue
            if "preferred" in lowered or "nice to have" in lowered or "bonus" in lowered or "plus" in lowered:
                is_preferred_section = True
                is_required_section = False
                continue

            bullet = line.lstrip("-*•· ")
            extracted_keywords = self._extract_keywords(bullet)

            # Check if this line indicates required vs preferred
            line_is_required = any(word in lowered for word in ["required", "must", "essential"])
            line_is_preferred = any(word in lowered for word in ["preferred", "nice to have", "bonus", "plus"])

            if current_bucket == "skills":
                skill_candidates.update(extracted_keywords)
                
                # Categorize as required or preferred
                if line_is_required or (is_required_section and not is_preferred_section):
                    requirements["required_skills"].extend(extracted_keywords)
                elif line_is_preferred or is_preferred_section:
                    requirements["preferred_skills"].extend(extracted_keywords)
                    
            elif current_bucket == "qualifications":
                requirements["qualifications"].append(bullet)
                keyword_candidates.extend(extracted_keywords)
                
                # Check for required qualifications
                if line_is_required or is_required_section:
                    requirements["required_skills"].extend(extracted_keywords)
                elif line_is_preferred or is_preferred_section:
                    requirements["preferred_skills"].extend(extracted_keywords)
            else:
                requirements["responsibilities"].append(bullet)
                keyword_candidates.extend(extracted_keywords)
                
                # Extract action verbs from responsibilities
                for verb in self.ATS_ACTION_VERBS:
                    if verb in lowered:
                        requirements["action_verbs"].append(verb)

        # Extract certifications from all keywords
        all_text_lower = job_description.lower()
        for cert in self.CERTIFICATIONS:
            if cert in all_text_lower:
                requirements["certifications"].append(cert)

        # Deduplicate and sort
        requirements["skills"] = sorted(skill_candidates)
        requirements["keywords"] = sorted(set(keyword_candidates) | set(requirements["skills"]))
        requirements["required_skills"] = sorted(set(requirements["required_skills"]))
        requirements["preferred_skills"] = sorted(set(requirements["preferred_skills"]))
        requirements["certifications"] = sorted(set(requirements["certifications"]))
        requirements["action_verbs"] = sorted(set(requirements["action_verbs"]))
        requirements["years_experience"] = sorted(set(requirements["years_experience"]))
        requirements["education"] = list(set(requirements["education"]))
        
        return requirements

    def _match_experiences(
        self,
        requirements: Dict[str, List[str]],
        experience_graph: dict,
        limit: int = 5,
    ) -> List[dict]:
        """
        Score and rank experiences against job requirements.
        """
        experiences = experience_graph.get("experiences", [])
        if not experiences:
            return []

        required_skills = {skill.lower() for skill in requirements.get("skills", [])}
        requirement_keywords = {kw.lower() for kw in requirements.get("keywords", [])}

        scored: List[Tuple[int, dict]] = []

        for exp in experiences:
            score = 0
            exp_skills = {skill.lower() for skill in exp.get("skills", [])}
            exp_achievements = exp.get("achievements", [])

            skill_overlap = len(required_skills & exp_skills)
            score += skill_overlap * 10

            for achievement in exp_achievements:
                lower_achievement = achievement.lower()
                for keyword in requirement_keywords:
                    if keyword and keyword in lower_achievement:
                        score += 4
                        break

            if exp.get("current"):
                score += 3

            if exp.get("type") == "work":
                score += 2

            scored.append((score, exp))

        scored.sort(key=lambda item: item[0], reverse=True)
        top_experiences = [self._trim_experience(experience) for score, experience in scored[:limit]]
        return top_experiences

    def _trim_experience(self, experience: dict) -> dict:
        """
        Reduce experience dictionary to essential keys for prompts.
        """
        keys = [
            "type",
            "title",
            "organization",
            "company",
            "location",
            "start",
            "start_date",
            "end",
            "end_date",
            "current",
            "skills",
            "achievements",
            "description",
        ]
        return {key: experience.get(key) for key in keys if key in experience}

    def _format_experiences(self, experiences: Sequence[dict]) -> str:
        """
        Format experiences for inclusion in the prompt.
        """
        formatted_lines: List[str] = []
        for exp in experiences:
            title = exp.get("title") or exp.get("organization") or "Untitled Experience"
            organization = exp.get("company") or exp.get("organization", "")
            date_range = f"{exp.get('start') or exp.get('start_date', '')} - {exp.get('end') or exp.get('end_date', 'Present')}"
            formatted_lines.append(f"Title: {title}")
            if organization:
                formatted_lines.append(f"Organization: {organization}")
            formatted_lines.append(f"Dates: {date_range}")
            skills = ", ".join(exp.get("skills", []))
            if skills:
                formatted_lines.append(f"Skills: {skills}")
            achievements = exp.get("achievements", [])
            if achievements:
                formatted_lines.append("Achievements:")
                for achievement in achievements:
                    formatted_lines.append(f"  - {achievement}")
            description = exp.get("description")
            if description:
                formatted_lines.append(f"Description: {description}")
            formatted_lines.append("")  # Blank line between entries
        return "\n".join(formatted_lines).strip()

    def _flatten_sections(self, sections: Sequence[Dict[str, List[str]]]) -> List[str]:
        bullets: List[str] = []
        for section in sections or []:
            bullets.extend(section.get("bullets", []))
        return bullets

    def _build_prompt(
        self,
        *,
        job_description: str,
        requirements: Dict[str, List[str]],
        experiences: Sequence[dict],
        parameters: Dict[str, object],
        source_url: str,
    ) -> str:
        """
        Compose the instruction prompt for the OpenAI Responses API.
        """
        requirements_json = json.dumps(requirements, indent=2)
        experiences_text = self._format_experiences(experiences) or "No structured experience provided."

        parameter_text = json.dumps(
            {
                "sections": parameters["sections"],
                "bullets_per_section": parameters["bullets_per_section"],
                "tone": parameters["tone"],
                "include_summary": parameters["include_summary"],
                "include_cover_letter": parameters["include_cover_letter"],
            },
            indent=2,
        )

        # Extract ATS-critical information for emphasis
        required_skills = requirements.get("required_skills", [])
        preferred_skills = requirements.get("preferred_skills", [])
        certifications = requirements.get("certifications", [])
        action_verbs = requirements.get("action_verbs", [])
        years_exp = requirements.get("years_experience", [])
        
        ats_emphasis = ""
        if required_skills:
            ats_emphasis += f"\n🎯 REQUIRED SKILLS (Must include): {', '.join(required_skills[:15])}"
        if certifications:
            ats_emphasis += f"\n📜 CERTIFICATIONS MENTIONED: {', '.join(certifications)}"
        if years_exp:
            ats_emphasis += f"\n⏱️ EXPERIENCE REQUIRED: {', '.join(years_exp)}"
        if preferred_skills:
            ats_emphasis += f"\n⭐ PREFERRED SKILLS (Bonus): {', '.join(preferred_skills[:10])}"
        if action_verbs:
            ats_emphasis += f"\n💪 KEY ACTION VERBS: {', '.join(action_verbs[:10])}"

        # Add web search instruction if URL provided
        web_search_note = ""
        if source_url:
            web_search_note = f"""
NOTE: You have web search enabled. Use it to fetch the complete job description from {source_url} 
and extract ALL requirements, qualifications, and details not present in the text below.
"""

        # Add custom section instructions if provided
        custom_instructions = ""
        section_instructions = parameters.get("section_instructions", "").strip()
        if section_instructions:
            custom_instructions = f"""

CUSTOM SECTION INSTRUCTIONS FROM USER:
{section_instructions}

NOTE: These instructions should GUIDE your content generation while maintaining all ATS optimization rules above. 
Balance user preferences with ATS requirements - never sacrifice keyword density or metrics for style preferences.
"""

        prompt = f"""
You are an expert ATS-optimized resume strategist. Your goal is to maximize both ATS compatibility (passing automated filters) and recruiter appeal (human interest).

JOB SOURCE URL: {source_url or "N/A"}
{web_search_note}

JOB DESCRIPTION:
{job_description}

DERIVED REQUIREMENTS (JSON):
{requirements_json}

{ats_emphasis}

CANDIDATE EXPERIENCE GRAPH:
{experiences_text}

TAILORING PARAMETERS (JSON):
{parameter_text}

CRITICAL ATS OPTIMIZATION RULES:
1. 🎯 KEYWORD DENSITY: Naturally incorporate ALL required skills from the job description
2. 💪 ACTION VERBS: Start EVERY bullet with a strong action verb (Led, Developed, Achieved, etc.)
3. 📊 QUANTIFY EVERYTHING: Include specific metrics (%, $, numbers) in at least 80% of bullets
4. 🎓 MIRROR JOB LANGUAGE: Use exact terminology from the job description when possible
5. 📏 LENGTH: Keep bullets 100-180 characters for optimal ATS parsing (no truncation)
6. 🏆 IMPACT FORMULA: Action Verb + Specific Task + Quantifiable Result + Business Impact

RECRUITER APPEAL RULES:
1. 🎤 STORYTELLING: Show career progression and increasing responsibility
2. 🎯 RELEVANCE: Prioritize experiences that directly match job requirements
3. 💎 UNIQUENESS: Highlight distinctive achievements that differentiate the candidate
4. 🔗 CONNECTIONS: Draw explicit links between past work and job requirements
5. 📈 GROWTH: Emphasize learning, leadership, and scalable impact

BULLET POINT FORMULA (USE THIS):
[Action Verb] + [Specific Activity] + [with X tool/skill] + [achieving Y% improvement] + [resulting in $Z impact/benefit]

Example: "Developed automated ETL pipeline using Python and Airflow, reducing data processing time by 65% and saving $120K annually in infrastructure costs"
{custom_instructions}

INSTRUCTIONS:
- Write in the candidate's authentic voice while optimizing for ATS
- Match tone: {parameters["tone"]}
- MANDATORY: Include required skills naturally throughout bullets
- MANDATORY: Start every bullet with a strong action verb
- MANDATORY: Add metrics to 80%+ of bullets
- Use industry-specific terminology from the job description
- Respect requested sections: {parameters["sections"]}
- Target {parameters["bullets_per_section"]} bullets per section
- If include_summary is true, write a compelling 2-sentence summary emphasizing ATS keywords and unique value
- If include_cover_letter is true, write a 150-200 word cover letter in 3 paragraphs (intro/body/closing) that naturally incorporates required skills
- Generate 5-10 actionable suggestions (5-10 words each) focusing on:
  * Missing required skills that should be added
  * Metrics that could strengthen bullets
  * Keywords to emphasize
  * Certifications to highlight
  * Formatting improvements

OUTPUT FORMAT (JSON):
{{
  "title": str (ATS-optimized job title),
  "summary": str (optional, keyword-rich 2 sentences),
  "sections": [{{"name": str, "bullets": [str, ...]}}],
  "bullets": [str, ...] (flat list if sections not needed),
  "cover_letter": str (optional, 3 paragraphs with \\n\\n separators),
  "suggestions": [str, ...] (concise, actionable, 5-10 words each)
}}

Return ONLY valid JSON, no markdown formatting.
"""
        return prompt.strip()

    def _generate_tailored_content(
        self,
        *,
        prompt: str,
        parameters: Dict[str, object],
        source_url: str = "",
    ) -> TailoringResult:
        """
        Execute the OpenAI Responses API call and parse the structured response.
        Uses OpenAI's web search (grounding) when a job URL is provided.
        """
        # Build the API request with grounding if URL provided
        request_params = {
            "model": self.model,
            "instructions": (
                "You are an expert resume strategist. Produce valid JSON only, "
                "matching the schema described in the user's request."
            ),
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        }
                    ],
                },
            ],
            "temperature": parameters["temperature"],
            "max_output_tokens": parameters["max_output_tokens"],
        }
        
        # Enable web search grounding if URL provided
        if source_url:
            request_params["grounding"] = {
                "type": "web_search",
                "web_search": {
                    "queries": [f"job posting {source_url}"],
                }
            }
        
        try:
            response = self.client.responses.create(**request_params)
        except Exception as exc:  # noqa: BLE001
            raise TailoringPipelineError(f"OpenAI request failed: {exc}") from exc

        output_text_parts: List[str] = []
        for item in response.output:
            # item is a ResponseOutputMessage (Pydantic object)
            content_blocks = getattr(item, "content", [])
            for block in content_blocks:
                # block is a ResponseOutputText (Pydantic object)
                if getattr(block, "type", None) == "output_text":
                    output_text_parts.append(getattr(block, "text", ""))

        raw_payload = "".join(output_text_parts).strip()
        
        # Remove markdown code fences if present
        if raw_payload.startswith("```json"):
            raw_payload = raw_payload[7:]  # Remove ```json
        if raw_payload.startswith("```"):
            raw_payload = raw_payload[3:]  # Remove ```
        if raw_payload.endswith("```"):
            raw_payload = raw_payload[:-3]  # Remove trailing ```
        raw_payload = raw_payload.strip()
        
        if not raw_payload:
            raise TailoringPipelineError("Received empty response from OpenAI.")

        if not raw_payload and hasattr(response, "output_text"):
            raw_payload = (response.output_text or "").strip()

        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            start = raw_payload.find("{")
            end = raw_payload.rfind("}")
            if start != -1 and end != -1:
                payload = json.loads(raw_payload[start : end + 1])
            else:
                raise TailoringPipelineError(
                    "Failed to parse OpenAI JSON payload."
                ) from None

        token_usage = {}
        if getattr(response, "usage", None):
            token_usage = {
                "prompt_tokens": getattr(response.usage, "input_tokens", 0),
                "completion_tokens": getattr(response.usage, "output_tokens", 0),
                "total_tokens": getattr(response.usage, "total_tokens", 0),
            }

        sections = payload.get("sections") or []
        if not isinstance(sections, list):
            sections = []

        bullets = payload.get("bullets")
        if bullets is None or not isinstance(bullets, list):
            bullets = []

        suggestions = payload.get("suggestions")
        if suggestions is None or not isinstance(suggestions, list):
            suggestions = []

        result = TailoringResult(
            title=str(payload.get("title", "")),
            summary=str(payload.get("summary", "")) if payload.get("summary") else "",
            sections=[
                {
                    "name": str(section.get("name", "Highlights")),
                    "bullets": [str(bullet) for bullet in section.get("bullets", [])],
                }
                for section in sections
            ],
            bullets=[str(bullet) for bullet in bullets],
            suggestions=[str(suggestion) for suggestion in suggestions],
            cover_letter=str(payload.get("cover_letter", "")) if payload.get("cover_letter") else "",
            token_usage=token_usage,
            run_id=getattr(response, "id", ""),
            debug={"raw_payload": payload},
        )
        return result




class ResumeOptimizer:
    """
    Helper class for ATS optimization and resume quality validation.
    """

    @staticmethod
    def calculate_ats_score(
        bullet_points: List[str], 
        job_keywords: List[str],
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
    ) -> Dict[str, object]:
        """
        Calculate comprehensive ATS compatibility score with detailed breakdown.
        
        Returns:
            - overall_score: 0-100 weighted score
            - keyword_match: % of job keywords found
            - required_skills_match: % of required skills found
            - preferred_skills_match: % of preferred skills found
            - missing_critical: List of missing required keywords
            - missing_preferred: List of missing preferred keywords
            - suggestions: Actionable recommendations
        """
        if not job_keywords and not required_skills:
            return {
                "overall_score": 0.0,
                "keyword_match": 0.0,
                "required_skills_match": 0.0,
                "preferred_skills_match": 0.0,
                "missing_critical": [],
                "missing_preferred": [],
                "suggestions": ["No job requirements provided for analysis"],
            }

        resume_text = " ".join(bullet_points).lower()
        
        # Calculate keyword match
        keyword_matches = 0
        if job_keywords:
            keyword_matches = sum(1 for kw in job_keywords if kw.lower() in resume_text)
            keyword_match_pct = (keyword_matches / len(job_keywords)) * 100
        else:
            keyword_match_pct = 0.0
        
        # Calculate required skills match (weighted heavily)
        required_matches = 0
        missing_required = []
        if required_skills:
            for skill in required_skills:
                if skill.lower() in resume_text:
                    required_matches += 1
                else:
                    missing_required.append(skill)
            required_match_pct = (required_matches / len(required_skills)) * 100
        else:
            required_match_pct = 100.0  # No requirements = perfect score
        
        # Calculate preferred skills match (bonus points)
        preferred_matches = 0
        missing_preferred = []
        if preferred_skills:
            for skill in preferred_skills:
                if skill.lower() in resume_text:
                    preferred_matches += 1
                else:
                    missing_preferred.append(skill)
            preferred_match_pct = (preferred_matches / len(preferred_skills)) * 100
        else:
            preferred_match_pct = 0.0
        
        # Weighted overall score
        # Required skills: 60%, Keyword match: 30%, Preferred skills: 10%
        overall_score = (
            (required_match_pct * 0.60) +
            (keyword_match_pct * 0.30) +
            (preferred_match_pct * 0.10)
        )
        
        # Generate suggestions
        suggestions = []
        if missing_required:
            suggestions.append(
                f"CRITICAL: Add these required skills: {', '.join(missing_required[:5])}"
            )
        if required_match_pct < 80:
            suggestions.append(
                "Include more required skills throughout your bullets"
            )
        if keyword_match_pct < 60:
            suggestions.append(
                "Incorporate more job-specific keywords naturally"
            )
        if missing_preferred and preferred_match_pct < 50:
            suggestions.append(
                f"Consider adding preferred skills: {', '.join(missing_preferred[:3])}"
            )
        if overall_score >= 85:
            suggestions.append(
                "Excellent ATS compatibility! Your resume should pass most ATS filters."
            )
        elif overall_score >= 70:
            suggestions.append(
                "Good ATS compatibility. Minor improvements could boost your score."
            )
        else:
            suggestions.append(
                "ATS compatibility needs improvement. Focus on required skills first."
            )
        
        return {
            "overall_score": round(overall_score, 1),
            "keyword_match": round(keyword_match_pct, 1),
            "required_skills_match": round(required_match_pct, 1),
            "preferred_skills_match": round(preferred_match_pct, 1),
            "missing_critical": missing_required[:10],  # Limit to top 10
            "missing_preferred": missing_preferred[:10],
            "suggestions": suggestions,
        }

    @staticmethod
    def enhance_bullet_with_metrics(bullet: str) -> str:
        """
        Enhance a bullet point by emphasizing metrics and results.
        """
        has_number = bool(re.search(r"\d+", bullet))
        has_percent = bool(re.search(r"\d+%", bullet))

        if has_number or has_percent:
            return bullet

        return f"{bullet} [Add metrics: X%, $Y, Z units]"

    @staticmethod
    def validate_bullet_point(bullet: str) -> Dict[str, object]:
        """
        Validate bullet point against ATS and recruiter best practices.
        """
        issues = []
        suggestions = []
        
        # ATS-critical checks
        action_verbs = {
            "led", "managed", "developed", "created", "improved", "increased",
            "reduced", "achieved", "delivered", "built", "designed", "implemented",
            "analyzed", "optimized", "launched", "coordinated", "established",
        }
        
        first_word = bullet.split()[0].lower().rstrip(".,;:") if bullet else ""
        
        # Length check (ATS systems may truncate)
        if len(bullet) > 220:
            issues.append("Bullet exceeds 220 characters - may be truncated by ATS")
            suggestions.append("Aim for 100-180 characters for optimal ATS parsing")
        elif len(bullet) < 50:
            issues.append("Bullet is too short - may lack detail")
            suggestions.append("Expand with specific metrics and outcomes")

        # Action verb check (critical for ATS)
        if not re.match(r"^[A-Z]", bullet):
            issues.append("Must start with capital letter for ATS parsing")
            suggestions.append("Capitalize the first word")
        
        if first_word not in action_verbs:
            issues.append("Should start with strong action verb for ATS scoring")
            suggestions.append(
                f"Start with: {', '.join(list(action_verbs)[:5])}, etc."
            )

        # Metrics check (recruiter appeal)
        has_number = bool(re.search(r"\d+", bullet))
        has_percent = bool(re.search(r"\d+%", bullet))
        has_dollar = bool(re.search(r"\$[\d,]+", bullet))
        
        if not (has_number or has_percent or has_dollar):
            suggestions.append("Add quantifiable metrics (%, $, numbers)")
        
        # Keyword density check
        if len(bullet.split()) < 10:
            suggestions.append("Add more context and keywords")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "has_metrics": has_number or has_percent or has_dollar,
            "starts_with_action_verb": first_word in action_verbs,
            "character_count": len(bullet),
        }
