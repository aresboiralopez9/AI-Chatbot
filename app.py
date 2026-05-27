import streamlit as st
from openai import OpenAI
from supabase import create_client
from datetime import datetime

openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

pid = st.query_params.get("pid", "missing")
condition = st.query_params.get("condition", "default")

if "pid" not in st.session_state or st.session_state.pid != pid:
    st.session_state.pid = pid
    st.session_state.messages = []
    st.session_state.turn_number = 0

st.title("AI Assistant")

st.write("Use this assistant while completing the task in the survey.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_prompt = st.chat_input("Message the AI assistant")

if user_prompt:
    st.session_state.turn_number += 1

    st.session_state.messages.append({
        "role": "user",
        "content": user_prompt
    })

    supabase.table("chat_logs").insert({
        "participant_id": pid,
        "condition": condition,
        "turn_number": st.session_state.turn_number,
        "role": "user",
        "message": user_prompt,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    response = openai_client.responses.create(
        model="gpt-4.1-mini",
        instructions="You are a helpful AI assistant for a research participant. Do not mention previous participants or prior conversations.",
        input=st.session_state.messages
    )

    ai_text = response.output_text

    st.session_state.messages.append({
        "role": "assistant",
        "content": ai_text
    })

    supabase.table("chat_logs").insert({
        "participant_id": pid,
        "condition": condition,
        "turn_number": st.session_state.turn_number,
        "role": "assistant",
        "message": ai_text,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    st.rerun()
