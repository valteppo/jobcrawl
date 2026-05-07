import os
from netparser import Netparser

AI_AGENT_LIGHT = os.environ.get('AI_AGENT_LIGHT')
AI_AGENT_HEAVY= os.environ.get('AI_AGENT_HEAVY')

if __name__ == "__main__":
    p = Netparser()
    p.update_database()
