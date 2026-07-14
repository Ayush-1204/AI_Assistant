from app.services.ai.planner.agents.swarm.base import SwarmAgent

# Forward declarations for tools
def transfer_to_reviewer() -> SwarmAgent:
    """Hands off code execution results or generated scripts to the Reviewer Agent for validation."""
    return reviewer_agent

def transfer_to_coder() -> SwarmAgent:
    """Hands off task logic to the Coder Agent when python scripting or execution is required."""
    return coder_agent

# Agent Definitions
coder_agent = SwarmAgent(
    name="CoderAgent",
    instructions="""You are an expert Python engineering agent.
Your primary role is to emit python script architectures and logic when delegated to by the Router.
If you believe your code needs to be verified for syntax errors or traceback hallucinations, immediately call `<tool_call><name>transfer_to_reviewer</name></tool_call>`.""",
    tools=[transfer_to_reviewer]
)

reviewer_agent = SwarmAgent(
    name="ReviewerAgent",
    instructions="""You are a strict QA and Security engineering agent.
You analyze python code for edge cases, memory leaks, security flaws, and syntax errors.
If the code is flawless, output the final result. If the code requires modifications, immediately call `<tool_call><name>transfer_to_coder</name></tool_call>` and outline exactly what they need to fix.""",
    tools=[transfer_to_coder]
)

router_agent = SwarmAgent(
    name="RouterAgent",
    instructions="""You are the Swarm Intelligence Router.
Analyze the user's intent. If they are asking for code, programming, or script execution, invoke `<tool_call><name>transfer_to_coder</name></tool_call>`.
If it is a general question, answer it directly.""",
    tools=[transfer_to_coder]
)
