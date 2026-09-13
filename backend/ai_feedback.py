"""
Generates smart, personalized hydration feedback using LangChain + a
Hugging Face-hosted model via the HF Inference API.

Uses HuggingFaceEndpoint (calls HF's hosted API over HTTP) rather than
loading a model locally — no transformers/torch install required.
"""
import os
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
load_dotenv()

HF_MODEL = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")  # get a free token at huggingface.co/settings/tokens

_llm_endpoint = HuggingFaceEndpoint(
    repo_id=HF_MODEL,
    huggingfacehub_api_token=HF_TOKEN,
    task="conversational",
    max_new_tokens=200,
    temperature=0.7,
)
_chat_model = ChatHuggingFace(llm=_llm_endpoint)

_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a friendly, encouraging hydration coach embedded in a health app. "
     "Given a user's water intake data, give ONE short piece of feedback "
     "(2-3 sentences max). Be specific and actionable, not generic. "
     "If they're behind on their goal, gently nudge them. If they're on track "
     "or ahead, encourage them. If intake has been very uneven over recent days, "
     "point that out. Never sound robotic or clinical — sound like a supportive "
     "coach, not a medical professional. Do not give medical advice."),
    ("human",
     "Today's intake so far: {today_total_ml}ml. Daily goal: {goal_ml}ml "
     "({percent_of_goal}% of goal reached). "
     "Last 7 days of daily totals (ml, oldest to newest): {recent_history}. "
     "Give your feedback now."),
])

_chain = _prompt | _chat_model | StrOutputParser()


def generate_feedback(today_total_ml: int, goal_ml: int, recent_history: list[int]) -> str:
    percent = round((today_total_ml / goal_ml) * 100, 1) if goal_ml else 0
    return _chain.invoke({
        "today_total_ml": today_total_ml,
        "goal_ml": goal_ml,
        "percent_of_goal": percent,
        "recent_history": recent_history,
    })


# --- Embeddings (only needed if you later add semantic search / RAG) ---
# Not used anywhere yet — this app doesn't need embeddings for structured
# hydration data. Included here so it's ready if you add a feature like
# "find similar days" or a chat-with-your-history assistant later.
#
# from langchain_huggingface import HuggingFaceEndpointEmbeddings
#
# EMBEDDING_MODEL = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
#
# embeddings = HuggingFaceEndpointEmbeddings(
#     model=EMBEDDING_MODEL,
#     huggingfacehub_api_token=HF_TOKEN,
# )
# # Calls the HF Inference API for embeddings — no local model download,
# # no sentence-transformers/torch install required.
# vector = embeddings.embed_query("some text")
