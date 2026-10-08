from langgraph.graph import StateGraph , START , END
from langchain_groq import ChatGroq
from typing import TypedDict, Literal, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage , HumanMessage
from langgraph.checkpoint.sqlite import AsyncSqliteSaver
from chatbot_tools import search_tool,get_stock_price,calculator
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import tool,BaseTool
from dotenv import load_dotenv
import sqlite3
import asyncio
import aiosqlite
import threading
load_dotenv()

_ASYNC_LOOP = asyncio.new_event_loop()
_ASYNC_THREAD = threading.Thread(target=_ASYNC_LOOP.run_forever, daemon=True)
_ASYNC_THREAD.start()

def _submit_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, _ASYNC_LOOP)


def run_async(coro):
    return _submit_async(coro).result()


def submit_async_task(coro):
    """Schedule a coroutine on the backend event loop."""
    return _submit_async(coro)


llm = ChatGroq(model = "openai/gpt-oss-120b" , temperature=0)

client = MultiServerMCPClient(
    {
        "arith": {
            "transport": "stdio",
            "command": "python3",
            "args": ["/Users/nitish/Desktop/mcp-math-server/main.py"],
        },
        "expense": {
            "transport": "streamable_http",  # if this fails, try "sse"
            "url": "https://splendid-gold-dingo.fastmcp.app/mcp"
        }
    }
)

def load_mcp_tools() -> list[BaseTool]:
    try:
        return run_async(client.get_tools())
    except Exception:
        return []


mcp_tools = load_mcp_tools()


tools = [search_tool, get_stock_price, calculator]
llm_with_tools = llm.bind_tools(tools) if tools else llm

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage],add_messages]


async def chat_node(state:ChatState):
    """LLM node that may answer or request a tool call."""
    messages = state['messages']
    response = await llm_with_tools.ainvoke(messages)
    return {'messages':[response]}

tool_node = ToolNode(tools) if tools else None

async def _init_checkpointer():
    conn = await aiosqlite.connect(database='chatbot.db' , check_same_thread=False)
    return AsyncSqliteSaver(conn)

checkpointer = run_async(_init_checkpointer())


graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")

if tool_node:
    graph.add_node("tools", tool_node)
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")
else:
    graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)


async def _alist_threads():
    all_threads = set()
    async for checkpoint in checkpointer.alist(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)


def retrieve_all_threads():
    return run_async(_alist_threads())
