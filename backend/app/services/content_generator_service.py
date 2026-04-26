"""
Content Generator Service — produces ready-to-paste resume content for each
skill gap detected by the ATS analysis pipeline.

Two-mode approach:
    Mode A — Template Engine: Deterministic, instant, no LLM cost.
              Used for the ~80 canonical skills in SKILL_BULLET_TEMPLATES.
    Mode B — LLM Generation: Fallback for skills with no template.
              Calls llm_service.ask_llm() with a structured prompt.

Output for each skill:
    {
        "skill":          str  — canonical skill name
        "skills_entry":   str  — text to paste into Skills section
        "bullets":        list[str]  — 1-2 Experience/Projects bullets
        "placement":      str  — "Experience", "Projects", or "New Projects Section"
        "source":         str  — "template" | "llm" | "fallback"
    }
"""

import json
import re

from app.core.logger import logger

# ── Skill bullet templates ────────────────────────────────────────────────────
# Keys must be canonical skill names (same as SKILL_ALIASES values).
# Placeholders: {project} = first project hint, {tool} = related tool, {verb} = past verb
SKILL_BULLET_TEMPLATES: dict[str, dict] = {
    "Docker": {
        "skills_entry": "Docker, Docker Compose, Container Orchestration",
        "bullets": [
            "Containerized {project} application using Docker, authoring multi-stage Dockerfiles to standardize dev and production environments.",
            "Configured docker-compose for {project}, enabling one-command local setup and reducing onboarding time significantly.",
        ],
    },
    "Kubernetes": {
        "skills_entry": "Kubernetes, kubectl, Container Orchestration, Helm",
        "bullets": [
            "Deployed {project} to a Kubernetes cluster, configuring Deployments, Services, and HorizontalPodAutoscalers for traffic spikes.",
            "Managed Kubernetes rollouts for {project} with zero-downtime rolling updates and automated health checks.",
        ],
    },
    "CI/CD": {
        "skills_entry": "CI/CD, GitHub Actions, Automated Pipelines",
        "bullets": [
            "Built a CI/CD pipeline using GitHub Actions for {project}, automating lint, test, build, and deployment on every PR merge.",
            "Reduced manual deployment effort by setting up automated GitHub Actions workflows for {project}.",
        ],
    },
    "AWS": {
        "skills_entry": "AWS (EC2, S3, Lambda, RDS, CloudWatch)",
        "bullets": [
            "Deployed {project} on AWS using EC2 for compute, S3 for static assets, and RDS for the managed PostgreSQL database.",
            "Configured AWS CloudWatch alarms and Lambda functions for scheduled tasks in {project}.",
        ],
    },
    "GCP": {
        "skills_entry": "Google Cloud Platform (GCP), Cloud Run, Cloud Storage, BigQuery",
        "bullets": [
            "Hosted {project} on Google Cloud Run with auto-scaling containers, reducing idle compute costs.",
            "Used GCP Cloud Storage and BigQuery for data pipeline storage and analytics in {project}.",
        ],
    },
    "Azure": {
        "skills_entry": "Microsoft Azure, Azure App Service, Azure DevOps",
        "bullets": [
            "Deployed {project} using Azure App Service with integrated Azure DevOps pipelines for continuous delivery.",
        ],
    },
    "Redis": {
        "skills_entry": "Redis, Caching, Session Management, Pub/Sub",
        "bullets": [
            "Implemented Redis caching in {project} for frequently queried API responses, reducing average response time.",
            "Used Redis Pub/Sub for real-time event broadcasting between microservices in {project}.",
        ],
    },
    "PostgreSQL": {
        "skills_entry": "PostgreSQL, SQL, Database Design, Query Optimization",
        "bullets": [
            "Designed the PostgreSQL schema for {project}, including indexing strategies that improved query performance on high-traffic endpoints.",
            "Wrote optimized SQL queries and used EXPLAIN ANALYZE to tune slow queries in {project}.",
        ],
    },
    "MongoDB": {
        "skills_entry": "MongoDB, NoSQL, Mongoose, Aggregation Pipelines",
        "bullets": [
            "Designed MongoDB collections and aggregation pipelines for {project}, enabling flexible schema evolution without downtime.",
        ],
    },
    "GraphQL": {
        "skills_entry": "GraphQL, Apollo Server, Schema Design, Resolvers",
        "bullets": [
            "Built a GraphQL API for {project} using Apollo Server, replacing multiple REST endpoints with a single flexible query interface.",
            "Designed GraphQL resolvers and mutations for {project}, reducing over-fetching and improving frontend data efficiency.",
        ],
    },
    "REST API": {
        "skills_entry": "REST APIs, HTTP, API Design, JSON",
        "bullets": [
            "Designed and implemented RESTful APIs for {project} following OpenAPI specifications, with versioning and standardized error responses.",
        ],
    },
    "WebSockets": {
        "skills_entry": "WebSockets, Real-time Communication, Socket.IO",
        "bullets": [
            "Integrated WebSocket connections into {project} for real-time bidirectional communication between client and server.",
        ],
    },
    "React": {
        "skills_entry": "React, JSX, Hooks, Context API, Component Architecture",
        "bullets": [
            "Built the {project} frontend in React using functional components, custom hooks, and Context API for global state management.",
            "Developed reusable React component library for {project}, reducing UI development time across multiple pages.",
        ],
    },
    "Next.js": {
        "skills_entry": "Next.js, SSR, SSG, App Router, React Server Components",
        "bullets": [
            "Built {project} with Next.js using Server-Side Rendering (SSR) for dynamic pages and Static Site Generation (SSG) for content-heavy routes.",
            "Migrated {project} frontend to Next.js App Router, improving page load performance with React Server Components.",
        ],
    },
    "TypeScript": {
        "skills_entry": "TypeScript, Type Safety, Interfaces, Generics",
        "bullets": [
            "Refactored {project} codebase from JavaScript to TypeScript, adding strict type safety and eliminating a class of runtime errors.",
        ],
    },
    "Node.js": {
        "skills_entry": "Node.js, Express.js, Async/Await, npm",
        "bullets": [
            "Built the {project} backend API using Node.js and Express.js, handling concurrent requests with async/await patterns.",
        ],
    },
    "Python": {
        "skills_entry": "Python, OOP, Async Programming, Data Manipulation",
        "bullets": [
            "Implemented core business logic for {project} in Python, leveraging async/await for non-blocking I/O operations.",
        ],
    },
    "FastAPI": {
        "skills_entry": "FastAPI, Pydantic, Async Python, OpenAPI",
        "bullets": [
            "Built the {project} REST API with FastAPI, using Pydantic models for request validation and auto-generated OpenAPI documentation.",
        ],
    },
    "Django": {
        "skills_entry": "Django, Django REST Framework, ORM, Admin",
        "bullets": [
            "Developed {project} backend using Django with Django REST Framework, implementing authentication, serializers, and custom permissions.",
        ],
    },
    "Machine Learning": {
        "skills_entry": "Machine Learning, Scikit-learn, Model Training, Feature Engineering",
        "bullets": [
            "Built and trained a machine learning model for {project} using Scikit-learn, achieving measurable accuracy improvements over the baseline.",
        ],
    },
    "TensorFlow": {
        "skills_entry": "TensorFlow, Keras, Neural Networks, Model Training",
        "bullets": [
            "Trained a TensorFlow/Keras neural network for {project}, experimenting with architecture variants to optimize validation accuracy.",
        ],
    },
    "PyTorch": {
        "skills_entry": "PyTorch, Deep Learning, Custom Datasets, Model Evaluation",
        "bullets": [
            "Implemented a deep learning model for {project} in PyTorch, building custom Dataset classes and training loops.",
        ],
    },
    "NLP": {
        "skills_entry": "NLP, spaCy, NLTK, Text Processing, Named Entity Recognition",
        "bullets": [
            "Applied NLP techniques (tokenization, POS tagging, NER) using spaCy to extract structured information from unstructured text in {project}.",
        ],
    },
    "LLM": {
        "skills_entry": "LLMs, Prompt Engineering, RAG, LangChain",
        "bullets": [
            "Integrated a Large Language Model into {project} using LangChain, building a RAG pipeline over internal documents for contextual Q&A.",
        ],
    },
    "SSR": {
        "skills_entry": "Server-Side Rendering (SSR), Next.js, Performance Optimization",
        "bullets": [
            "Implemented Server-Side Rendering in {project} to improve initial page load and SEO performance for dynamic content routes.",
        ],
    },
    "Microservices": {
        "skills_entry": "Microservices Architecture, Service Decomposition, API Gateway",
        "bullets": [
            "Decomposed the {project} monolith into independent microservices, enabling teams to deploy and scale components independently.",
        ],
    },
    "Git": {
        "skills_entry": "Git, GitHub, Branch Strategy, Code Review",
        "bullets": [
            "Maintained version control for {project} using Git with a structured branching strategy (feature branches, PRs, and protected main).",
        ],
    },
    "Tailwind CSS": {
        "skills_entry": "Tailwind CSS, Responsive Design, Utility-First CSS",
        "bullets": [
            "Styled the {project} UI using Tailwind CSS, implementing a fully responsive layout across mobile and desktop breakpoints.",
        ],
    },
    "Agile": {
        "skills_entry": "Agile, Scrum, Sprint Planning, Jira",
        "bullets": [
            "Worked in a 2-week Agile sprint cycle on {project}, participating in daily standups, sprint planning, and retrospectives.",
        ],
    },
    "Unit Testing": {
        "skills_entry": "Unit Testing, Integration Testing, Jest, pytest",
        "bullets": [
            "Wrote unit and integration tests for {project} using pytest/Jest, maintaining test coverage above 80% across core modules.",
        ],
    },
}

_FALLBACK_BULLET = (
    "Applied {skill} in {project}, integrating it into the core workflow to improve "
    "reliability and maintainability of the system."
)

_LLM_PROMPT_TEMPLATE = """You are an expert resume writer specializing in ATS optimization.
The candidate's resume is missing the skill: "{skill}".
Their resume contains the following context from their experience section:
  Related tools: {related_tools}
  Project hints: {project_hints}
  Verbs used: {verbs_used}

Write exactly 2 resume bullet points that:
1. Naturally incorporate "{skill}"
2. Use past tense with a strong action verb
3. Include a quantified or specific outcome where possible
4. Are 15–25 words each
5. Sound like real work experience

Return ONLY a JSON array of 2 strings. No preamble, no explanation.
Example: ["Built X using {skill}, achieving Y.", "Implemented {skill} in Z, reducing W by N%."]
"""


def _fill_template(template: str, context: dict, skill: str) -> str:
    """Fill a bullet template with extracted resume context."""
    project = context.get("project_hints", ["the application"])[0] if context.get("project_hints") else "the application"
    tool = context.get("related_tools", ["the system"])[0] if context.get("related_tools") else "the system"
    verb = context.get("verbs_used", ["built"])[0] if context.get("verbs_used") else "built"
    return (
        template
        .replace("{project}", project)
        .replace("{tool}", tool)
        .replace("{verb}", verb)
        .replace("{skill}", skill)
    )


def _determine_placement(context: dict) -> str:
    """Determine best section for the suggested bullet."""
    if context.get("has_projects_section"):
        return "Projects"
    if context.get("has_experience_section"):
        return "Experience"
    return "New Projects Section"


def generate_content_for_skill(
    skill: str,
    context: dict,
    use_llm: bool = True,
) -> dict:
    """
    Generate ready-to-paste resume content for a single missing skill.

    Args:
        skill: Canonical skill name (e.g. "Docker", "Next.js")
        context: Output of nlp_service.extract_experience_context()
        use_llm: If True, fall back to LLM when no template exists

    Returns:
        {
            "skill": str,
            "skills_entry": str,
            "bullets": list[str],
            "placement": str,
            "source": "template" | "llm" | "fallback",
        }
    """
    placement = _determine_placement(context)
    template_data = SKILL_BULLET_TEMPLATES.get(skill)

    # ── Mode A: Template ──────────────────────────────────────────────────────
    if template_data:
        filled_bullets = [
            _fill_template(b, context, skill)
            for b in template_data["bullets"]
        ]
        return {
            "skill": skill,
            "skills_entry": template_data["skills_entry"],
            "bullets": filled_bullets,
            "placement": placement,
            "source": "template",
        }

    # ── Mode B: LLM ───────────────────────────────────────────────────────────
    if use_llm:
        try:
            from app.services.llm_service import ask_llm

            prompt = _LLM_PROMPT_TEMPLATE.format(
                skill=skill,
                related_tools=", ".join(context.get("related_tools", [])) or "various tools",
                project_hints=", ".join(context.get("project_hints", [])) or "various projects",
                verbs_used=", ".join(context.get("verbs_used", [])) or "built, developed",
            )
            raw = ask_llm(prompt, temperature=0.4)

            # Parse the JSON array returned by the LLM
            match = re.search(r"\[.*?\]", raw, re.DOTALL)
            if match:
                bullets = json.loads(match.group())
                if isinstance(bullets, list) and len(bullets) >= 1:
                    return {
                        "skill": skill,
                        "skills_entry": skill,
                        "bullets": bullets[:2],
                        "placement": placement,
                        "source": "llm",
                    }
        except Exception as e:
            logger.warning(f"LLM bullet generation failed for '{skill}': {e}")

    # ── Fallback: Generic ──────────────────────────────────────────────────────
    project = context.get("project_hints", ["the application"])[0] if context.get("project_hints") else "the application"
    bullet = _FALLBACK_BULLET.replace("{skill}", skill).replace("{project}", project)
    return {
        "skill": skill,
        "skills_entry": skill,
        "bullets": [bullet],
        "placement": placement,
        "source": "fallback",
    }


def generate_content_for_gaps(
    skill_gaps: list[str],
    sections: dict,
    max_skills: int = 6,
    use_llm: bool = True,
) -> list[dict]:
    """
    Generate suggested content for the top N skill gaps.

    Args:
        skill_gaps: List of missing canonical skill names (from improvement_service)
        sections: Dict from nlp_service.parse_sections()
        max_skills: Cap to avoid overwhelming the user (default 6)
        use_llm: Whether to use LLM for skills with no template

    Returns:
        List of content dicts, one per skill gap processed.
    """
    results = []
    for skill in skill_gaps[:max_skills]:
        context = __import__(
            "app.services.nlp_service", fromlist=["extract_experience_context"]
        ).extract_experience_context(sections, skill)
        content = generate_content_for_skill(skill, context, use_llm=use_llm)
        results.append(content)
    return results
