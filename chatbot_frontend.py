import streamlit as st
from chatbot_backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid

def generate_thread_id():
    return uuid.uuid4()


def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].insert(0, thread_id)


def reset_chat():
    thread_id = generate_thread_id()

    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []

    add_thread(thread_id)

    st.session_state['chat_created'] = True


def load_conversation(thread_id):
    state = chatbot.get_state(
        config={
            'configurable': {
                'thread_id': thread_id
            }
        }
    )

    return state.values.get("messages", [])


def generate_chat_name(message):
    return message[:30] + "..." if len(message) > 30 else message


if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []


if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()


if 'chat_names' not in st.session_state:
    st.session_state['chat_names'] = {}

    for thread_id in st.session_state['chat_threads']:

        messages = load_conversation(thread_id)

        for msg in messages:

            if msg.type == 'human':
                st.session_state['chat_names'][thread_id] = (
                    generate_chat_name(msg.content)
                )
                break


if 'thread_id' not in st.session_state:

    st.session_state['thread_id'] = generate_thread_id()

    st.session_state['chat_created'] = False

st.sidebar.title('GupShup AI')


if st.sidebar.button('New Chat'):

    reset_chat()

    st.rerun()


st.sidebar.header('My Conversations')


for thread_id in st.session_state['chat_threads']:

    chat_name = st.session_state['chat_names'].get(
        thread_id,
        "New Chat"
    )

    if st.sidebar.button(
        chat_name,
        key=str(thread_id)
    ):

        st.session_state['thread_id'] = thread_id

        messages = load_conversation(thread_id)

        temp_messages = []

        for msg in messages:

            if msg.type == 'human':
                role = 'user'
            else:
                role = 'assistant'

            temp_messages.append({
                'role': role,
                'content': msg.content
            })

        st.session_state['message_history'] = temp_messages

        st.session_state['chat_created'] = True

        st.rerun()



for message in st.session_state['message_history']:

    with st.chat_message(
        message.get('role', 'user')
    ):
        st.markdown(message['content'])


user_input = st.chat_input('Type here')


if user_input:

    thread_id = st.session_state['thread_id']

    if not st.session_state['chat_created']:

        add_thread(thread_id)

        st.session_state['chat_names'][thread_id] = (
            generate_chat_name(user_input)
        )

        st.session_state['chat_created'] = True



    elif thread_id not in st.session_state['chat_names']:

        st.session_state['chat_names'][thread_id] = (
            generate_chat_name(user_input)
        )


    st.session_state['message_history'].append({
        'role': 'user',
        'content': user_input
    })

    with st.chat_message('user'):
        st.markdown(user_input)


    config = {
        'configurable': {
            'thread_id': thread_id
        },
        'metadata': {
            'thread_id': thread_id
        },
        'run_name': 'chat_turn'
    }


    with st.chat_message('assistant'):

        ai_message = st.write_stream(
            message_chunk.content
            for message_chunk, metadata
            in chatbot.stream(
                {
                    'messages': [
                        HumanMessage(content=user_input)
                    ]
                },
                config=config,
                stream_mode='messages'
            )
        )


    st.session_state['message_history'].append({
        'role': 'assistant',
        'content': ai_message
    })


    st.rerun()