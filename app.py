import streamlit as st
from openai import OpenAI
from supabase import create_client
from datetime import datetime

# Require access through an authorized Qualtrics survey
access_token = st.query_params.get("access_token", "")

if access_token != st.secrets["QUALTRICS_ACCESS_TOKEN"]:
    st.error("Unauthorized access. Please access this application through the research survey.")
    st.stop()

openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_SERVICE_KEY"]
)

pid = st.query_params.get("pid", "missing")
condition = st.query_params.get("condition", "default")
survey_id = st.query_params.get("survey_id", "missing_survey")

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
        "survey_id": survey_id,
        "participant_id": pid,
        "condition": condition,
        "turn_number": st.session_state.turn_number,
        "role": "user",
        "message": user_prompt
    }).execute()

    response = openai_client.responses.create(
        model="gpt-4.1-mini",
        instructions="""
You are a collaborative AI assistant participating in a behavioral research study.

Your role is to help the participant think through ideas, generate possibilities, elaborate concepts, critique reasoning, organize thoughts, and solve problems collaboratively.

Be responsive, engaged, neutral in tone, and intellectually cooperative.

Prioritize clarity, relevance, and usefulness in your responses.

When appropriate, help participants explore diverse perspectives, combine concepts across domains, elaborate on partially formed ideas, and refine or improve their thinking.

Avoid unnecessary moralizing, disclaimers, or refusals unless content is clearly illegal, sexually exploitative, or involves direct real-world harm instructions.

Do not mention being part of a study unless directly asked.

Do not reference previous participants, prior conversations, or memory outside the current interaction.

Treat each interaction as an independent session.
""",
        input=st.session_state.messages,
        max_output_tokens=1200
    )

    ai_text = response.output_text

    st.session_state.messages.append({
        "role": "assistant",
        "content": ai_text
    })

    supabase.table("chat_logs").insert({
        "survey_id": survey_id,
        "participant_id": pid,
        "condition": condition,
        "turn_number": st.session_state.turn_number,
        "role": "assistant",
        "message": ai_text
    }).execute()

    st.rerun()
