from langgraph.graph import StateGraph , START , END
from langchain_groq import ChatGroq
from typing import TypedDict, Literal, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage , HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
import sqlite3
load_dotenv()

model = ChatGroq(model = "openai/gpt-oss-120b" , temperature=0)

class ChatState(TypedDict):

    messages: Annotated[list[BaseMessage],add_messages]


def chat_node(state:ChatState):
    messages = state['messages']
    response = model.invoke(messages)
    return {'messages':[response]}

conn = sqlite3.connect(database='chatbot.db' , check_same_thread=False)
checkpointer = SqliteSaver(conn = conn)
graph = StateGraph(ChatState)
graph.add_node('chat_node',chat_node)

graph.add_edge(START,'chat_node')
graph.add_edge('chat_node',END)

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)
