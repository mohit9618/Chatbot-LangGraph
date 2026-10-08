import streamlit as st
from chatbot_backend import chatbot, retrieve_all_threads,ingest_pdf
from langchain_core.messages import HumanMessage
import uuid

# IMPORTANT:
# Import ingest_pdf from wherever you have defined it.
# Example:
# from pdf_ingestion import ingest_pdf


def generate_thread_id():
    return uuid.uuid4()


def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].insert(0, thread_id)


def reset_chat():
    thread_id = generate_thread_id()

    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []

    # Reset PDFs for the new chat
    st.session_state['thread_docs'] = {}

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


# -----------------------------
# SESSION STATE
# -----------------------------

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


# PDF storage for current chat
if 'thread_docs' not in st.session_state:
    st.session_state['thread_docs'] = {}


# Short variable so the PDF code is easier to read
thread_id = st.session_state['thread_id']
thread_docs = st.session_state['thread_docs']


# -----------------------------
# SIDEBAR
# -----------------------------

st.sidebar.title('GupShup AI')


if st.sidebar.button('New Chat'):

    reset_chat()

    st.rerun()


# -----------------------------
# PDF UPLOAD
# -----------------------------

uploaded_pdf = st.sidebar.file_uploader(
    "Upload a PDF for this chat",
    type=["pdf"]
)


if uploaded_pdf:

    if uploaded_pdf.name in thread_docs:

        st.sidebar.info(
            f"`{uploaded_pdf.name}` already processed for this chat."
        )

    else:

        with st.sidebar.status(
            "Indexing PDF…",
            expanded=True
        ) as status_box:

            summary = ingest_pdf(
                uploaded_pdf.getvalue(),
                thread_id=thread_id,
                filename=uploaded_pdf.name
            )

            thread_docs[uploaded_pdf.name] = summary

            status_box.update(
                label="✅ PDF indexed",
                state="complete",
                expanded=False
            )


# Show current PDF
if thread_docs:

    latest_doc = list(thread_docs.values())[-1]

    st.sidebar.success(
        f"Using `{latest_doc.get('filename')}` "
        f"({latest_doc.get('chunks')} chunks from "
        f"{latest_doc.get('documents')} pages)"
    )

else:

    st.sidebar.info("No PDF indexed yet.")


# -----------------------------
# EXISTING CONVERSATIONS
# -----------------------------

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

        # Reset PDF UI when switching chats
        st.session_state['thread_docs'] = {}

        st.session_state['chat_created'] = True

        st.rerun()


# -----------------------------
# DISPLAY CHAT
# -----------------------------

for message in st.session_state['message_history']:

    with st.chat_message(
        message.get('role', 'user')
    ):
        st.markdown(message['content'])


# -----------------------------
# CHAT INPUT
# -----------------------------

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

        def generate_response():

            shown_tools = set()

            for message_chunk, metadata in chatbot.stream(
                {
                    'messages': [
                        HumanMessage(content=user_input)
                    ]
                },
                config=config,
                stream_mode='messages'
            ):

                if message_chunk.type == "AIMessageChunk":

                    tool_calls = getattr(
                        message_chunk,
                        "tool_call_chunks",
                        []
                    )

                    for tool_call in tool_calls:

                        tool_name = tool_call.get("name")

                        if tool_name and tool_name not in shown_tools:

                            st.caption(
                                f"🔧 Using `{tool_name}`..."
                            )

                            shown_tools.add(tool_name)

                    if message_chunk.content:
                        yield message_chunk.content


                elif message_chunk.type == "tool":
                    continue


        ai_message = st.write_stream(
            generate_response()
        )


    st.session_state['message_history'].append({
        'role': 'assistant',
        'content': ai_message
    })


    st.rerun()