import streamlit as st
from chatbot_backend import chatbot
from langchain_core.messages import BaseMessage, HumanMessage
import uuid 
# utility functions
def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(
        config={'configurable': {'thread_id': thread_id}}
    )
    return state.values.get("messages", [])

def generate_chat_name(message):
    return message[:30] + "..." if len(message) > 30 else message

# st.session_state -> dict
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []
add_thread(st.session_state['thread_id'])

if 'chat_names' not in st.session_state:
    st.session_state['chat_names'] = {}

# sidebar ui
st.sidebar.title('Chit-Chat')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(st.session_state['chat_names'].get(thread_id, str(thread_id))):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for msg in messages:
            if msg.type == 'human':
                role = 'user'
            else:
                role = 'assistant'

            temp_messages.append({'role':role , 'content':msg.content})
        st.session_state['message_history'] = temp_messages


# loading the past history
for message in st.session_state['message_history']:
    with st.chat_message(message.get('role', 'user')):
        st.markdown(message['content'])

user_input = st.chat_input('Type here')
if user_input:
    if st.session_state['thread_id'] not in st.session_state['chat_names']:
        st.session_state['chat_names'][st.session_state['thread_id']] = generate_chat_name(user_input)


    st.session_state['message_history'].append({'role':'user' , 'content':user_input})
    with st.chat_message('user'):
        st.text(user_input)

   

    # st.session_state['message_history'].append({'role':'assistant' , 'content':ai_message})
    config = {'configurable':{'thread_id':st.session_state['thread_id']}}
    with st.chat_message('assistant'):
       ai_message =  st.write_stream(
            message_chunk.content for message_chunk , metadata in chatbot.stream(
                {'messages':[HumanMessage(content=user_input)]},
                    config = config,
                    stream_mode="messages"
            )
        )
    st.session_state['message_history'].append({'role':'assistant' , 'content':ai_message})
