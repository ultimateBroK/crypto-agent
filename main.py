from server.app import app, agent_os

if __name__ == "__main__":
    agent_os.serve(app="main:app", reload=True)