from resources import linkedin, summary, facts, style
from pypdf import PdfReader
from pathlib import Path
import datetime

cv = ""


def read_cv_pdf(file_path):
    reader = PdfReader(file_path)
    cv_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            cv_text += text
    return cv_text


def read_prompt_file(filename):
    """Read a prompt from a markdown file in the prompts directory."""
    prompt_path = Path(__file__).parent / "prompts" / filename
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


cv += read_cv_pdf("./public/cv_version_1.pdf")
cv += read_cv_pdf("./public/cv_version_2.pdf")
cv += read_cv_pdf("./public/cv_version_3.pdf")
cv += read_cv_pdf("./public/anton_kovachev_cv.pdf")

with open("./data/summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()

# Load system prompts from markdown files
DIGITAL_TWIN_GREETING_SYSTEM_PROMPT = read_prompt_file(
    "digital_twin_greeting_system_prompt.md"
).format(
    name=facts["name"],
    full_name=facts["full_name"],
    facts=facts,
    summary=summary,
    style=style,
    datetime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
)
digital_twin_template = read_prompt_file("digital_twin_system_prompt.md")
DIGITAL_TWIN_SYSTEM_PROMPT = digital_twin_template.format(
    name=facts["name"],
    full_name=facts["full_name"],
    phone_number=facts["phone_number"],
    facts=facts,
    summary=summary,
    style=style,
    cv=cv,
    github_profile=facts["github"],
    datetime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
)

EMAIL_WRITER_INTRO_SYSTEM_PROMPT = read_prompt_file(
    "email_writer_intro_system_prompt.md"
)

PROFESSIONAL_EMAIL_WRITER_INTRO_SYSTEM_PROMPT = (
    EMAIL_WRITER_INTRO_SYSTEM_PROMPT
    + "\n"
    + read_prompt_file("professional_email_writer_extension.md")
)

FRIENDLY_EMAIL_WRITER_INTRO_SYSTEM_PROMPT = (
    EMAIL_WRITER_INTRO_SYSTEM_PROMPT
    + "\n"
    + read_prompt_file("friendly_email_writer_extension.md")
)

EMAIL_SENDER_SYSTEM_PROMPT = read_prompt_file("email_sender_system_prompt.md")

GITHUB_RESEARCH_AGENT_SYSTEM_PROMPT = read_prompt_file(
    "github_research_agent_system_prompt.md"
)

EXAMPLES = [
    "Tell me about your background and experience.",
    "What kinds of projects are you working on now?",
    "What kinds of projects did you worked on in the past?",
    "What are your strongest technical skills?",
    "Do you have any experience in leading a team and mentoring people?",
    "When and where did you study?",
    "What professional certifications do you hold?",
    "How can I get in touch with you?",
    "What kind of projects are you interested in?",
    "Can I review your CV?",
    "What is the weather today?",
    "Contacts",
]
