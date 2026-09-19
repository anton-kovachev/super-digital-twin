import os
from dotenv import load_dotenv
from ctypes import cast

load_dotenv(override=True)

from agents import Agent, OpenAIChatCompletionsModel
from context import (
    DIGITAL_TWIN_SYSTEM_PROMPT,
    EMAIL_SENDER_SYSTEM_PROMPT,
    FRIENDLY_EMAIL_WRITER_INTRO_SYSTEM_PROMPT,
    PROFESSIONAL_EMAIL_WRITER_INTRO_SYSTEM_PROMPT,
    GITHUB_RESEARCH_AGENT_SYSTEM_PROMPT,
)
from openai import AsyncOpenAI
from tools import push_message, send_email, get_cv_pdf

from mcp_servers import github_mcp_server

# from mcp_tools import github_mcp_tool
from aws_bedrock_token_generator import provide_token

MODEL_NAME = os.getenv("LLM_MODEL_ID") or "openai.gpt-oss-120b"

async_aws_bedrock_client = AsyncOpenAI(
    api_key=provide_token(),
    base_url=os.getenv("AWS_BEDROCK_BASE_URL"),
    project=os.getenv("PROJECT_ID"),
)


model = OpenAIChatCompletionsModel(
    model=MODEL_NAME,
    openai_client=async_aws_bedrock_client,
)

professional_email_writer_agent = Agent(
    name="Professional Email Writer",
    instructions=PROFESSIONAL_EMAIL_WRITER_INTRO_SYSTEM_PROMPT,
    model=model,
)

friendly_email_writer_agent = Agent(
    name="Friendly Email Writer",
    instructions=FRIENDLY_EMAIL_WRITER_INTRO_SYSTEM_PROMPT,
    model=model,
)

email_sender_tools = [
    send_email,
    professional_email_writer_agent.as_tool(
        tool_name="professional_email_writer",
        tool_description="Use this tool to write professional emails.",
    ),
    friendly_email_writer_agent.as_tool(
        tool_name="friendly_email_writer",
        tool_description="Use this tool to write friendly and approachable emails.",
    ),
]

email_sender_agent = Agent(
    name="Email Sender",
    instructions=EMAIL_SENDER_SYSTEM_PROMPT,
    model=model,
    tools=email_sender_tools,
)

github_profile_researches = Agent(
    name="Github Profile Researcher",
    instructions=GITHUB_RESEARCH_AGENT_SYSTEM_PROMPT,
    model=model,
    mcp_servers=[github_mcp_server],
)


digital_twin_agent_tools = [
    push_message,
    get_cv_pdf,
    email_sender_agent.as_tool(
        tool_name="email_sender",
        tool_description="Use this tool to generate and send emails.",
    ),
    github_profile_researches.as_tool(
        tool_name="github_profile_researcher",
        tool_description="Use this tool to research GitHub profiles with web scrapping.",
        max_turns=200,
    ),
]

digital_twin_agent = Agent(
    name="Digital Twin CV assistant",
    instructions=DIGITAL_TWIN_SYSTEM_PROMPT,
    model=model,
    tools=digital_twin_agent_tools,
)
