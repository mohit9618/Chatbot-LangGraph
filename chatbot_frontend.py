import streamlit as st
from chatbot_backend import chatbot
from langchain_core.messages import BaseMessage, HumanMessage
# st.session_state -> dict

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []


# loading the past history
for message in st.session_state['message_history']:
    with st.chat_message(message.get('role', 'user')):
        st.text(message['content'])

user_input = st.chat_input('Type here')


if user_input:
    st.session_state['message_history'].append({'role':'user' , 'content':user_input})
    with st.chat_message('user'):
        st.text(user_input)

   

    # st.session_state['message_history'].append({'role':'assistant' , 'content':ai_message})

    thread_id  = 1
    config = {'configurable':{'thread_id':thread_id}}
    with st.chat_message('assistant'):
       ai_message =  st.write_stream(
            message_chunk.content for message_chunk , metadata in chatbot.stream(
                {'messages':[HumanMessage(content=user_input)]},
                    config = config,
                    stream_mode="messages"
            )
        )
    st.session_state['message_history'].append({'role':'assistant' , 'content':ai_message})
