"""Seed database with starter templates for common use cases."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.pg_database import postgres_conn
from app.template_store import template_store, Template
import uuid


SEED_TEMPLATES = [
    {
        "name": "Code Review - Python",
        "description": "Comprehensive code review for Python code focusing on bugs, security, performance, and best practices",
        "system_template": "You are an expert Python developer and code reviewer. Provide detailed, actionable feedback on code quality, bugs, security vulnerabilities, performance issues, and adherence to Python best practices (PEP 8, type hints, etc.).",
        "user_template": "Review the following {language} code and focus on {focus_areas}. Provide {detail_level} analysis.\n\nCode:\n{code}\n\nPlease provide:\n1. Critical issues that must be fixed\n2. Suggestions for improvement\n3. Best practices recommendations\n4. Overall code quality assessment",
        "required_args": [
            {"name": "code", "type": "string", "description": "The code to review", "required": True},
            {"name": "language", "type": "enum", "description": "Programming language", "required": True, "enum_values": ["python", "javascript", "typescript", "java", "go", "rust"]},
        ],
        "optional_args": [
            {"name": "focus_areas", "type": "array", "description": "Specific areas to focus on", "required": False, "default": ["bugs", "security", "performance"]},
            {"name": "detail_level", "type": "enum", "description": "Level of detail in review", "required": False, "default": "medium", "enum_values": ["brief", "medium", "detailed"]},
        ],
        "keywords": ["code", "review", "python", "bugs", "security", "quality"],
        "category": "code_review",
        "tags": ["python", "code-quality", "security"],
    },
    {
        "name": "Code Generation - React Component",
        "description": "Generate modern React component with TypeScript, hooks, and best practices",
        "system_template": "You are an expert React developer specializing in modern React development with TypeScript, hooks, and best practices. Generate clean, type-safe, production-ready code with proper error handling and accessibility.",
        "user_template": "Create a React component for {component_purpose}.\n\nRequirements:\n- Use {typescript_enabled} for type safety\n- Implement using {hooks_to_use}\n- Follow these style guidelines: {style_approach}\n- Include {accessibility_level} accessibility features\n\nProvide:\n1. Complete component code\n2. PropTypes or TypeScript interfaces\n3. Usage example\n4. Any necessary dependencies",
        "required_args": [
            {"name": "component_purpose", "type": "string", "description": "What the component should do", "required": True},
        ],
        "optional_args": [
            {"name": "typescript_enabled", "type": "enum", "description": "Use TypeScript", "required": False, "default": "TypeScript", "enum_values": ["TypeScript", "JavaScript"]},
            {"name": "hooks_to_use", "type": "array", "description": "React hooks to use", "required": False, "default": ["useState", "useEffect"]},
            {"name": "style_approach", "type": "enum", "description": "Styling method", "required": False, "default": "CSS modules", "enum_values": ["CSS modules", "styled-components", "Tailwind", "inline styles"]},
            {"name": "accessibility_level", "type": "enum", "description": "Accessibility compliance", "required": False, "default": "basic", "enum_values": ["basic", "WCAG AA", "WCAG AAA"]},
        ],
        "keywords": ["react", "component", "typescript", "hooks", "frontend"],
        "category": "code_generation",
        "tags": ["react", "typescript", "frontend"],
    },
    {
        "name": "Blog Post Writer",
        "description": "Write engaging, SEO-optimized blog posts on any topic",
        "system_template": "You are an expert content writer and SEO specialist. Write engaging, well-researched blog posts that are optimized for search engines while being valuable and readable for humans. Use proper headings, bullet points, and formatting.",
        "user_template": "Write a {tone} blog post about {topic} for {target_audience}.\n\nLength: {word_count} words\nSEO focus keyword: {seo_keyword}\n\nThe post should:\n1. Have an engaging introduction\n2. Include {sections_count} main sections with H2 headings\n3. Use bullet points and examples where appropriate\n4. Include a strong call-to-action\n5. Be optimized for the keyword '{seo_keyword}'\n\nAdditional requirements: {additional_requirements}",
        "required_args": [
            {"name": "topic", "type": "string", "description": "Main topic of the blog post", "required": True},
            {"name": "seo_keyword", "type": "string", "description": "Primary SEO keyword to target", "required": True},
        ],
        "optional_args": [
            {"name": "tone", "type": "enum", "description": "Writing tone", "required": False, "default": "professional", "enum_values": ["casual", "professional", "technical", "friendly", "authoritative"]},
            {"name": "target_audience", "type": "string", "description": "Target audience", "required": False, "default": "general readers"},
            {"name": "word_count", "type": "number", "description": "Target word count", "required": False, "default": 1000},
            {"name": "sections_count", "type": "number", "description": "Number of main sections", "required": False, "default": 4},
            {"name": "additional_requirements", "type": "string", "description": "Any additional requirements", "required": False, "default": "none"},
        ],
        "keywords": ["blog", "content", "writing", "seo", "article"],
        "category": "content_writing",
        "tags": ["content", "seo", "blog"],
    },
    {
        "name": "SQL Query Generator",
        "description": "Generate optimized SQL queries with explanations",
        "system_template": "You are a database expert specializing in SQL query optimization. Generate efficient, well-structured SQL queries with proper indexing considerations and explanations. Consider performance, readability, and best practices.",
        "user_template": "Generate a SQL query for {database_type} to {query_purpose}.\n\nDatabase schema:\n{schema}\n\nRequirements:\n- Optimize for {optimization_goal}\n- {include_explanation}\n- Handle edge cases like null values\n\nProvide:\n1. The SQL query\n2. Explanation of the query logic\n3. Performance considerations\n4. Suggested indexes (if applicable)",
        "required_args": [
            {"name": "query_purpose", "type": "string", "description": "What the query should accomplish", "required": True},
            {"name": "schema", "type": "string", "description": "Database schema description", "required": True},
        ],
        "optional_args": [
            {"name": "database_type", "type": "enum", "description": "Database system", "required": False, "default": "PostgreSQL", "enum_values": ["PostgreSQL", "MySQL", "SQL Server", "Oracle", "SQLite"]},
            {"name": "optimization_goal", "type": "enum", "description": "Optimization focus", "required": False, "default": "speed", "enum_values": ["speed", "readability", "maintainability"]},
            {"name": "include_explanation", "type": "enum", "description": "Include explanation", "required": False, "default": "Include detailed explanation", "enum_values": ["Include detailed explanation", "Query only"]},
        ],
        "keywords": ["sql", "query", "database", "optimization"],
        "category": "data_analysis",
        "tags": ["sql", "database", "data"],
    },
    {
        "name": "Bug Investigation Assistant",
        "description": "Analyze error messages and suggest debugging steps",
        "system_template": "You are a senior software engineer specializing in debugging and troubleshooting. Analyze error messages, stack traces, and code context to identify root causes and suggest systematic debugging approaches.",
        "user_template": "Help me debug this {error_type} error in {language}:\n\nError message:\n{error_message}\n\nCode context:\n{code_context}\n\nWhat I've tried:\n{attempted_solutions}\n\nPlease provide:\n1. Root cause analysis\n2. Step-by-step debugging approach\n3. Potential solutions ranked by likelihood\n4. Prevention strategies for the future",
        "required_args": [
            {"name": "error_message", "type": "string", "description": "The error message or stack trace", "required": True},
            {"name": "code_context", "type": "string", "description": "Relevant code snippet", "required": True},
        ],
        "optional_args": [
            {"name": "error_type", "type": "enum", "description": "Type of error", "required": False, "default": "runtime", "enum_values": ["runtime", "compilation", "logical", "performance", "memory"]},
            {"name": "language", "type": "enum", "description": "Programming language", "required": False, "default": "Python", "enum_values": ["Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust"]},
            {"name": "attempted_solutions", "type": "string", "description": "What has been tried", "required": False, "default": "none yet"},
        ],
        "keywords": ["debug", "error", "bug", "troubleshoot", "fix"],
        "category": "debugging",
        "tags": ["debugging", "troubleshooting", "errors"],
    },
    {
        "name": "API Design Review",
        "description": "Review REST API design for consistency, best practices, and usability",
        "system_template": "You are an API design expert with deep knowledge of REST principles, HTTP standards, and API best practices. Review API designs for consistency, scalability, security, and developer experience.",
        "user_template": "Review this API design for {api_purpose}:\n\nEndpoints:\n{endpoints}\n\nData models:\n{data_models}\n\nFocus on:\n- {api_style} best practices\n- {security_level} security requirements\n- Consistency and naming conventions\n- Error handling and status codes\n- Documentation completeness\n\nProvide:\n1. Critical issues to fix\n2. Suggested improvements\n3. Best practices recommendations\n4. Example request/response for key endpoints",
        "required_args": [
            {"name": "api_purpose", "type": "string", "description": "Purpose of the API", "required": True},
            {"name": "endpoints", "type": "string", "description": "List of API endpoints", "required": True},
        ],
        "optional_args": [
            {"name": "data_models", "type": "string", "description": "Data models/schemas", "required": False, "default": "not provided"},
            {"name": "api_style", "type": "enum", "description": "API architecture style", "required": False, "default": "REST", "enum_values": ["REST", "GraphQL", "gRPC", "WebSocket"]},
            {"name": "security_level", "type": "enum", "description": "Security requirements", "required": False, "default": "standard", "enum_values": ["basic", "standard", "high", "critical"]},
        ],
        "keywords": ["api", "rest", "design", "review", "architecture"],
        "category": "api_design",
        "tags": ["api", "rest", "architecture"],
    },
    {
        "name": "Documentation Generator",
        "description": "Generate comprehensive documentation from code or specifications",
        "system_template": "You are a technical writer specializing in developer documentation. Create clear, comprehensive documentation that helps developers understand and use code effectively. Include examples, edge cases, and best practices.",
        "user_template": "Generate {doc_type} documentation for:\n\n{code_or_spec}\n\nTarget audience: {audience}\nFormat: {format}\n\nInclude:\n1. Overview and purpose\n2. {include_examples}\n3. Parameters and return values (if applicable)\n4. Usage guidelines and best practices\n5. Edge cases and error handling\n6. Related resources",
        "required_args": [
            {"name": "code_or_spec", "type": "string", "description": "Code or specification to document", "required": True},
        ],
        "optional_args": [
            {"name": "doc_type", "type": "enum", "description": "Type of documentation", "required": False, "default": "API reference", "enum_values": ["API reference", "README", "Tutorial", "How-to guide", "Architecture doc"]},
            {"name": "audience", "type": "enum", "description": "Target audience", "required": False, "default": "developers", "enum_values": ["beginners", "developers", "architects", "end-users"]},
            {"name": "format", "type": "enum", "description": "Documentation format", "required": False, "default": "Markdown", "enum_values": ["Markdown", "reStructuredText", "HTML", "Plain text"]},
            {"name": "include_examples", "type": "enum", "description": "Include code examples", "required": False, "default": "Multiple examples", "enum_values": ["One example", "Multiple examples", "No examples"]},
        ],
        "keywords": ["documentation", "docs", "readme", "guide"],
        "category": "documentation",
        "tags": ["documentation", "technical-writing"],
    },
    {
        "name": "Test Case Generator",
        "description": "Generate comprehensive test cases for code",
        "system_template": "You are a QA engineer and testing expert. Generate comprehensive test cases that cover happy paths, edge cases, error conditions, and boundary values. Follow testing best practices and use appropriate testing frameworks.",
        "user_template": "Generate {test_type} tests for {testing_framework}:\n\nCode to test:\n{code}\n\nCoverage requirements:\n- Happy path scenarios\n- Edge cases: {edge_cases}\n- Error conditions\n- {coverage_level} code coverage\n\nProvide:\n1. Test suite structure\n2. Individual test cases with assertions\n3. Test data/fixtures\n4. Setup and teardown logic (if needed)",
        "required_args": [
            {"name": "code", "type": "string", "description": "Code to generate tests for", "required": True},
        ],
        "optional_args": [
            {"name": "test_type", "type": "enum", "description": "Type of tests", "required": False, "default": "unit", "enum_values": ["unit", "integration", "e2e", "performance"]},
            {"name": "testing_framework", "type": "enum", "description": "Testing framework", "required": False, "default": "pytest", "enum_values": ["pytest", "jest", "mocha", "JUnit", "go test"]},
            {"name": "edge_cases", "type": "string", "description": "Specific edge cases to test", "required": False, "default": "null values, empty arrays, boundary values"},
            {"name": "coverage_level", "type": "enum", "description": "Target coverage", "required": False, "default": "80%", "enum_values": ["60%", "80%", "90%", "100%"]},
        ],
        "keywords": ["test", "testing", "unit-test", "qa"],
        "category": "testing",
        "tags": ["testing", "qa", "unit-tests"],
    },
]


async def seed_templates():
    """Seed database with starter templates."""
    try:
        # Connect to PostgreSQL
        await postgres_conn.connect()
        await postgres_conn.init_tables()

        print("Seeding templates...")

        for template_data in SEED_TEMPLATES:
            template = Template(
                id=str(uuid.uuid4()),
                name=template_data["name"],
                description=template_data["description"],
                system_template=template_data["system_template"],
                user_template=template_data["user_template"],
                required_args=template_data["required_args"],
                optional_args=template_data["optional_args"],
                keywords=template_data["keywords"],
                category=template_data["category"],
                tags=template_data["tags"],
                created_by="system",
            )

            template_id = await template_store.save(template)
            print(f"  ✓ Created: {template.name} ({template_id})")

        print(f"\n✅ Successfully seeded {len(SEED_TEMPLATES)} templates")

        # Disconnect
        await postgres_conn.disconnect()

    except Exception as e:
        print(f"❌ Error seeding templates: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(seed_templates())
