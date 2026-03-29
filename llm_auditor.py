import os
import json
from pydantic import BaseModel, Field
try:
    from google import genai
    from google.genai import types
    _CLIENT = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
except ImportError:
    # Fallback to the older SDK if the new one fails to import
    import google.generativeai as genai
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    _CLIENT = None

class Vulnerability(BaseModel):
    severity: str = Field(description="Critical, High, Medium, or Low")
    type: str = Field(description="E.g., XSS, Missing Component, API Key Exposure")
    description: str = Field(description="Detailed explanation of the issue")
    location: str = Field(description="URL, Header, or File where the issue was found")

class Recommendation(BaseModel):
    actionable_step: str = Field(description="Actionable step to resolve the vulnerability")
    ai_prompt: str = Field(description="Exact AI prompt the user can provide to an LLM assistant verbatim to fix the issue in their codebase")

class SecurityReport(BaseModel):
    security_score: int = Field(description="Security score from 0-100. IMPORTANT: If 'unsafe-inline' is in CSP or CSP is missing entirely, score MUST be below 60.")
    vulnerabilities: list[Vulnerability] = Field(description="List of identified vulnerabilities")
    recommendations: list[Recommendation] = Field(description="List of recommendations paired with AI fix prompts")
    svg_chart: str = Field(description="Valid raw SVG code of a radar chart visualizing security posture (Categories: Authentication, Injection, Privacy, Infrastructure, Headers). Use vibrant, dynamic, modern styles. Width/Height 400x400.")

DISCLAIMER = (
    "DISCLAIMER: This is a static/recon analysis tool utilizing automated and heuristic logic. "
    "It is NOT a replacement for professional penetration testing. Findings should be manually verified."
)

async def generate_audit_report(context_data: dict) -> dict:
    prompt = f"""
    You are a Senior DevSecOps Engineer & Red Team Auditor. 
    Analyze the following reconnaissance data and formulate a professional security assessment.
    
    Data:
    {json.dumps(context_data, indent=2)}
    
    Ensure your generated SVG radar chart represents realistic scores for the given findings.
    """
    
    if _CLIENT:
        # Using the new google-genai SDK
        response = _CLIENT.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SecurityReport,
            ),
        )
        report_data = json.loads(response.text)
    else:
        # Using the legacy google.generativeai SDK
        model = genai.GenerativeModel('gemini-3-flash-preview')
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                # The legacy SDK requires either a dictionary schema or `response_schema=SecurityReport` if supported in the specific version
                response_schema=SecurityReport
            )
        )
        report_data = json.loads(response.text)

    return {
        "status": "success",
        "disclaimer": DISCLAIMER,
        "report": report_data
    }
