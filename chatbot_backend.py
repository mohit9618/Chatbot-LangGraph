from langgraph.graph import StateGraph , START , END
from langchain_groq import ChatGroq
from typing import TypedDict, Literal, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage , HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from chatbot_tools import search_tool,get_stock_price,calculator
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv
import sqlite3
load_dotenv()

llm = ChatGroq(model = "openai/gpt-oss-120b" , temperature=0)
tools = [search_tool, get_stock_price, calculator]
llm_with_tools = llm.bind_tools(tools)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage],add_messages]


def chat_node(state:ChatState):
    """LLM node that may answer or request a tool call."""
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {'messages':[response]}

tool_node = ToolNode(tools)

conn = sqlite3.connect(database='chatbot.db' , check_same_thread=False)
checkpointer = SqliteSaver(conn = conn)


graph = StateGraph(ChatState)
graph.add_node('chat_node',chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START,'chat_node')
graph.add_conditional_edges("chat_node",tools_condition)
graph.add_edge('tools', 'chat_node')

chatbot = graph.compile(checkpointer=checkpointer)


def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)
