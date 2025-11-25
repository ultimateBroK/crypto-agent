from agno.os import AgentOS
from agents.cryage import create_agent

cryage_agent = create_agent()
agent_os = AgentOS(agents=[cryage_agent])
app = agent_os.get_app()

def serve(reload: bool = True):
    agent_os.serve(app="cryage_agent:app", reload=reload)
