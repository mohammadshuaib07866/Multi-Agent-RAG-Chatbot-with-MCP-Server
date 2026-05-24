import streamlit as st
from chatbot import chatbot
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# **************************************** utility functions *************************

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
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    # Check if messages key exists in state values, return empty list if not
    return state.values.get('messages', [])

def get_message_preview(thread_id, max_length=50):
    """Get a preview of the first user message from a conversation"""
    messages = load_conversation(thread_id)
    if messages:
        for msg in messages:
            if isinstance(msg, HumanMessage):
                preview = msg.content[:max_length]
                if len(msg.content) > max_length:
                    preview += "..."
                return preview
    return "New Chat"


# **************************************** Session Setup ******************************
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

add_thread(st.session_state['thread_id'])


# **************************************** Sidebar UI *********************************

st.sidebar.title('💬 LangGraph Chatbot')

# New Chat Button
col1, col2 = st.sidebar.columns([3, 1])
with col1:
    if st.sidebar.button('➕ New Chat', use_container_width=True):
        reset_chat()
        st.rerun()

st.sidebar.divider()

st.sidebar.header('📚 My Conversations')

# Filter threads with messages to avoid duplicate "New Chat" display
conversations_with_messages = []
for thread_id in st.session_state['chat_threads'][::-1]:
    messages = load_conversation(thread_id)
    if messages:  # Only show conversations with messages
        conversations_with_messages.append(thread_id)

if conversations_with_messages:
    for thread_id in conversations_with_messages:
        message_preview = get_message_preview(thread_id, max_length=40)
        
        # Highlight current conversation
        is_current = thread_id == st.session_state['thread_id']
        button_label = f"{'✓' if is_current else '•'} {message_preview}"
        
        if st.sidebar.button(button_label, use_container_width=True, key=str(thread_id)):
            st.session_state['thread_id'] = thread_id
            messages = load_conversation(thread_id)

            temp_messages = []

            for msg in messages:
                if isinstance(msg, HumanMessage):
                    role='user'
                else:
                    role='assistant'
                temp_messages.append({'role': role, 'content': msg.content})

            st.session_state['message_history'] = temp_messages
            st.rerun()
else:
    st.sidebar.info("💡 Start a new chat to begin!")



# **************************************** Main UI ************************************

st.title('Chatbot with Stream and Resume Chat')

# loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:

    # first add the message to message_history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

     # first add the message to message_history
    with st.chat_message("assistant"):
        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            ):
                if isinstance(message_chunk, AIMessage):
                    # yield only assistant tokens
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})