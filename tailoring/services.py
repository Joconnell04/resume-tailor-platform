"""
Tailoring app services

AgentKit-like service for AI-powered resume tailoring without relying on the
hosted AgentKit runtime. This module orchestrates prompt construction,
experience matching, URL scraping, and OpenAI API calls.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential

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
        "python",
        "java",
        "javascript",
        "typescript",
        "c++",
        "c#",
        "sql",
        "nosql",
        "aws",
        "azure",
        "gcp",
        "react",
        "django",
        "flask",
        "docker",
        "kubernetes",
        "terraform",
        "linux",
        "git",
        "agile",
        "scrum",
        "ci/cd",
        "ml",
        "ai",
        "data",
        "analytics",
        "api",
        "microservices",
        "html",
        "css",
        "spark",
        "hadoop",
        "tableau",
        "powerbi",
        "salesforce",
        "sqlserver",
        "postgresql",
        "mongodb",
        "firebase",
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
            "gpt-4.1-mini",
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
            job_description: Combined text from raw description and scraped URL.
            experience_graph: User's experience data as a dictionary.
            parameters: Tailoring preferences supplied by the user.
            source_url: Optional URL where the job description originated.

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
            prompt=prompt, parameters=normalized_parameters
        )

        return {
            "title": result.title,
            "sections": result.sections,
            "bullets": result.bullets or self._flatten_sections(result.sections),
            "summary": result.summary,
            "suggestions": result.suggestions,
            "cover_letter": result.cover_letter,
            "token_usage": result.token_usage,
            "run_id": result.run_id,
            "debug": {
                "requirements": requirements,
                "selected_experiences": relevant_experiences,
                "parameters": normalized_parameters,
                "openai_response": result.debug.get("raw_payload"),
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

    def combine_job_content(self, raw_text: str, scraped_text: str) -> str:
        """
        Merge raw description text with scraped content, removing duplicates.
        """
        parts: List[str] = []
        for text in (raw_text, scraped_text):
            cleaned = self._clean_text(text)
            if not cleaned:
                continue

            replaced_existing = False
            for idx, existing in enumerate(parts):
                if cleaned in existing:
                    replaced_existing = True
                    break
                if existing in cleaned:
                    parts[idx] = cleaned
                    replaced_existing = True
                    break

            if not replaced_existing:
                parts.append(cleaned)
        return "\n\n".join(parts)

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
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9\+#\./-]{1,}", text)
        keywords: List[str] = []
        for token in tokens:
            token_clean = token.strip(" .,;:()[]{}").lower()
            if len(token_clean) < 2 or token_clean in STOPWORDS:
                continue
            if token_clean in self.TECH_KEYWORDS or token.istitle() or token.isupper():
                keywords.append(token_clean)
        return keywords

    def _extract_job_requirements(self, job_description: str) -> Dict[str, List[str]]:
        """
        Heuristically extract requirements, qualifications, and skills.
        """
        requirements = {
            "skills": [],
            "qualifications": [],
            "responsibilities": [],
            "keywords": [],
        }

        if not job_description:
            return requirements

        current_bucket = "responsibilities"
        skill_candidates: set[str] = set()
        keyword_candidates: List[str] = []

        for raw_line in job_description.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            lowered = line.lower()
            if "responsibil" in lowered or "duties" in lowered:
                current_bucket = "responsibilities"
                continue
            if "qualification" in lowered or "requirements" in lowered:
                current_bucket = "qualifications"
                continue
            if "skill" in lowered or "technolog" in lowered or "tools" in lowered:
                current_bucket = "skills"
                continue

            bullet = line.lstrip("-*•· ")

            if current_bucket == "skills":
                skill_candidates.update(self._extract_keywords(bullet))
            elif current_bucket == "qualifications":
                requirements["qualifications"].append(bullet)
                keyword_candidates.extend(self._extract_keywords(bullet))
            else:
                requirements["responsibilities"].append(bullet)
                keyword_candidates.extend(self._extract_keywords(bullet))

        requirements["skills"] = sorted(skill_candidates)
        requirements["keywords"] = sorted(set(keyword_candidates) | set(requirements["skills"]))
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

        prompt = f"""
You are an expert resume strategist. Tailor the candidate's experience to the job while emphasizing quantifiable impact.

JOB SOURCE URL: {source_url or "N/A"}

JOB DESCRIPTION:
{job_description}

DERIVED REQUIREMENTS (JSON):
{requirements_json}

CANDIDATE EXPERIENCE GRAPH:
{experiences_text}

TAILORING PARAMETERS (JSON):
{parameter_text}

INSTRUCTIONS:
- Produce concise, achievement-driven bullet points written in the candidate's voice.
- Match the specified tone: {parameters["tone"]}.
- Respect the requested sections and bullet counts. If you cannot fill a section, provide your best effort and briefly note the gap in suggestions.
- Use strong action verbs, quantify impact where possible, and align to the derived requirements.
- If include_summary is true, provide a brief summary paragraph (2 sentences max) highlighting the candidate's fit.
- If include_cover_letter is true, include a concise cover letter (<= 180 words) addressing the hiring manager.
- Provide actionable suggestions (array of strings) for the candidate to further customize their resume.
- Return a JSON object with the following structure:
  {{
    "title": str,
    "summary": str (optional),
    "sections": [{{"name": str, "bullets": [str, ...]}}],
    "bullets": [str, ...] (optional flat list),
    "cover_letter": str (optional),
    "suggestions": [str, ...]
  }}
- Do not include markdown outside the JSON payload.
"""
        return prompt.strip()

    def _generate_tailored_content(
        self,
        *,
        prompt: str,
        parameters: Dict[str, object],
    ) -> TailoringResult:
        """
        Execute the OpenAI Responses API call and parse the structured response.
        """
        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": "You are an expert resume strategist that produces structured JSON output.",
                            }
                        ],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}],
                    },
                ],
                response_format={"type": "json_object"},
                temperature=parameters["temperature"],
                max_output_tokens=parameters["max_output_tokens"],
            )
        except Exception as exc:  # noqa: BLE001
            raise TailoringPipelineError(f"OpenAI request failed: {exc}") from exc

        output_text_parts: List[str] = []
        for item in response.output:
            for block in item.get("content", []):
                if block.get("type") in {"output_text", "text"}:
                    output_text_parts.append(block.get("text", ""))

        raw_payload = "".join(output_text_parts).strip()
        if not raw_payload:
            raise TailoringPipelineError("Received empty response from OpenAI.")

        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            raise TailoringPipelineError(f"Failed to parse OpenAI JSON payload: {exc}") from exc

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

    # ------------------------------------------------------------------ #
    # Scraping                                                           #
    # ------------------------------------------------------------------ #

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    def scrape_job_url(self, url: str) -> str:
        """
        Scrape job description text from a URL.
        """
        if not url:
            return ""

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
            )
        }
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise TailoringPipelineError(f"Failed to fetch job URL: {exc}") from exc

        soup = BeautifulSoup(response.text, "html.parser")

        # Prefer common job description containers
        selectors = [
            {"name": "section", "attrs": {"id": "jobDescriptionText"}},
            {"name": "div", "attrs": {"class": re.compile("job[-_]description", re.I)}},
            {"name": "div", "attrs": {"class": re.compile("description", re.I)}},
            {"name": "article", "attrs": {}},
        ]

        for selector in selectors:
            node = soup.find(selector["name"], attrs=selector.get("attrs"))
            if node:
                text = self._clean_text(node.get_text(" ", strip=True))
                if text:
                    return text

        # Fallback to all text if no specific container found.
        return self._clean_text(soup.get_text(" ", strip=True))


class ResumeOptimizer:
    """
    Helper class for resume optimization utilities.
    """

    @staticmethod
    def calculate_ats_score(bullet_points: List[str], job_keywords: List[str]) -> float:
        """
        Calculate ATS (Applicant Tracking System) compatibility score.
        """
        if not job_keywords or not bullet_points:
            return 0.0

        resume_text = " ".join(bullet_points).lower()
        matches = sum(1 for keyword in job_keywords if keyword.lower() in resume_text)
        score = (matches / len(job_keywords)) * 100
        return min(score, 100.0)

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
        Validate bullet point against best practices.
        """
        issues = []
        suggestions = []

        if len(bullet) > 220:
            issues.append("Bullet is lengthy. Consider splitting into two sentences.")
            suggestions.append("Aim for 25-35 words for readability.")

        if not re.match(r"^[A-Z]", bullet):
            issues.append("Bullet should start with a strong action verb.")
            suggestions.append("Capitalize the first word and use an action verb.")

        if not re.search(r"\d", bullet):
            suggestions.append("Include metrics to quantify impact.")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
        }
