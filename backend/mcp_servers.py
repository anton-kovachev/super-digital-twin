from agents.mcp import (
    MCPServerStreamableHttp,
    MCPServerStreamableHttpParams,
    create_static_tool_filter,
)
from config import GITHUB_MCP_TOKEN

github_mcp_server = MCPServerStreamableHttp(
    params=MCPServerStreamableHttpParams(
        {
            "url": "https://api.githubcopilot.com/mcp",
            "headers": {
                "Authorization": f"Bearer {GITHUB_MCP_TOKEN}",
                "User-Agent": "super_twin",
            },
        }
    ),
    cache_tools_list=True,
    max_retry_attempts=3,
    retry_backoff_seconds_base=1.0,
    name="github_mcp_server",
    tool_filter=create_static_tool_filter(
        blocked_tool_names=[
            "add_comment_to_pending_review",
            "add_issue_comment",
            "add_reply_to_pull_request_comment",
            "assign_copilot_to_issue",
            "create_branch",
            "create_or_update_file",
            "create_pull_request",
            "create_pull_request_with_copilot",
            "create_repository",
            "delete_file",
            "fork_repository",
            "merge_pull_request",
            "sub_issue_write",
            "update_pull_request",
            "update_pull_request_branch",
        ]
    ),
)
