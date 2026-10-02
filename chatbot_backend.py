from langgraph.graph import StateGraph , START , END
from langchain_groq import ChatGroq
from typing import TypedDict, Literal, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
load_dotenv()

model = ChatGroq(model = "openai/gpt-oss-120b" , temperature=0)

class ChatState(TypedDict):

    messages: Annotated[list[BaseMessage],add_messages]


def chat_node(state:ChatState):
    messages = state['messages']
    response = model.invoke(messages).content
    return {'messages':[response]}

checkpointer = MemorySaver()
graph = StateGraph(ChatState)
graph.add_node('chat_node',chat_node)

graph.add_edge(START,'chat_node')
graph.add_edge('chat_node',END)

chatbot = graph.compile(checkpointer=checkpointer)




