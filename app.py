from __future__ import annotations

import os
import streamlit as st
from dotenv import load_dotenv

from utils.pdf_reader import extract_text_from_pdf
from utils.summarizer import summarize_text
from utils.qa import answer_question
from utils.quiz_generator import generate_mcqs
from utils.flashcards import generate_flashcards

from utils.groq_client import (
    GroqInvalidAPIKeyError,
    GroqQuotaError,
    GroqEmptyResponseError,
)



# -------------------------
# App configuration

# -------------------------
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="🧠",
    layout="wide",
)

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# We keep `client` for backward compatibility with the existing utils signatures,
# but Groq calls are done inside utils/groq_client.py.
client = object()


# -------------------------
# Validate key early (better UX)
# -------------------------
# Validate key early (better UX)
try:
    if not GROQ_API_KEY:
        raise GroqInvalidAPIKeyError(
            "Missing GROQ_API_KEY. Create a `.env` file and add your Groq key."
        )
except GroqInvalidAPIKeyError as e:
    st.error(str(e))
except (GroqQuotaError, GroqEmptyResponseError) as e:
    st.error(f"Groq init failed: {e}")
except Exception as e:
    st.error(f"Failed to initialize Groq client: {e}")





# -------------------------
# Session state
# -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "notes_text" not in st.session_state:
    st.session_state.notes_text = ""

if "summary" not in st.session_state:
    st.session_state.summary = ""

if "mcqs" not in st.session_state:
    st.session_state.mcqs = []

if "flashcards" not in st.session_state:
    st.session_state.flashcards = []


# -------------------------
# Helper functions
# -------------------------
def require_client():
    # Keep UI unchanged; backend calls rely on GEMINI_API_KEY inside utils/gemini_client.py.
    # If the key is missing, we already show an error during initialization.
    return True



def reset_generated_outputs():
    st.session_state.summary = ""
    st.session_state.mcqs = []
    st.session_state.flashcards = []
    st.session_state.messages = []


# -------------------------
# Sidebar
# -------------------------
with st.sidebar:
    st.title("🧠 AI Study Assistant")
    st.caption("PDF → Summary → Q&A → Quiz → Flashcards")

    section = st.radio(
        "Navigation",
        [
            "1) Upload PDF",
            "2) Summary",
            "3) Ask Questions",
            "4) Quiz Generator",
            "5) Flashcards",
        ],
    )

    if st.button("🔄 Clear Session"):
        st.session_state.messages = []
        st.session_state.notes_text = ""
        reset_generated_outputs()
        st.success("Session cleared.")

    st.divider()

    st.info(
        "Tip: Ask questions using keywords from your notes for best results."
    )


# -------------------------
# Main UI
# -------------------------
st.title("AI Study Assistant")


# =========================================================
# 1) Upload PDF
# =========================================================
if section == "1) Upload PDF":

    st.subheader("Upload your study notes (PDF)")

    uploaded = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
    )

    if uploaded is not None:

        if not require_client():
            st.stop()

        try:
            with st.spinner("Extracting text from PDF..."):

                file_bytes = uploaded.read()

                extracted = extract_text_from_pdf(
                    file_bytes,
                    max_pages=25
                )

            if not extracted.strip():
                st.error("No text found in PDF.")
                st.stop()

            st.session_state.notes_text = extracted

            reset_generated_outputs()

            st.success("PDF uploaded successfully!")

            preview = extracted[:1500]

            with st.expander("Preview Extracted Text"):

                st.text_area(
                    "Preview",
                    value=preview,
                    height=250,
                )

        except Exception as e:
            st.error(f"PDF extraction failed: {e}")


# =========================================================
# 2) Summary
# =========================================================
elif section == "2) Summary":

    st.subheader("AI Summary")

    if not st.session_state.notes_text:
        st.warning("Upload a PDF first.")

    else:

        if st.button("✨ Generate Summary"):

            if not require_client():
                st.stop()

            try:
                with st.spinner("Generating summary..."):

                    result = summarize_text(
                        client,
                        st.session_state.notes_text
                    )

                st.session_state.summary = result.summary

                st.success("Summary generated!")

            except Exception as e:
                st.error(f"Summary failed: {e}")

        if st.session_state.summary:

            st.download_button(
                "⬇️ Download Summary",
                data=st.session_state.summary,
                file_name="study_summary.txt",
                mime="text/plain",
            )

            with st.expander("Summary", expanded=True):
                st.markdown(st.session_state.summary)


# =========================================================
# 3) Ask Questions
# =========================================================
elif section == "3) Ask Questions":

    st.subheader("Ask Questions")

    if not st.session_state.notes_text:
        st.warning("Upload a PDF first.")

    else:

        for msg in st.session_state.messages:

            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        question = st.chat_input(
            "Ask something from your notes..."
        )

        if question:

            if not require_client():
                st.stop()

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": question,
                }
            )

            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):

                with st.spinner("Thinking..."):

                    try:

                        qa_result = answer_question(
                            client,
                            st.session_state.notes_text,
                            question
                        )

                        answer = qa_result.answer

                        st.markdown(answer)

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": answer,
                            }
                        )

                    except Exception as e:
                        st.error(f"Q&A failed: {e}")


# =========================================================
# 4) Quiz Generator
# =========================================================
elif section == "4) Quiz Generator":

    st.subheader("Quiz Generator")

    if not st.session_state.notes_text:
        st.warning("Upload a PDF first.")

    else:

        if st.button("🎯 Generate Quiz"):

            if not require_client():
                st.stop()

            try:

                with st.spinner("Generating MCQs..."):

                    quiz = generate_mcqs(
                        client,
                        st.session_state.notes_text,
                        num_questions=5
                    )

                st.session_state.mcqs = quiz.mcqs

                st.success("Quiz generated!")

            except Exception as e:
                st.error(f"Quiz generation failed: {e}")

        if st.session_state.mcqs:

            for i, mcq in enumerate(
                st.session_state.mcqs,
                start=1
            ):

                with st.expander(
                    f"Q{i}: {mcq.question}"
                ):

                    choice = st.radio(
                        "Choose answer",
                        mcq.options,
                        key=f"quiz_{i}"
                    )

                    if choice:
                        st.success(
                            f"Correct Answer: {mcq.correct_answer}"
                        )


# =========================================================
# 5) Flashcards
# =========================================================
elif section == "5) Flashcards":

    st.subheader("Flashcards")

    if not st.session_state.notes_text:
        st.warning("Upload a PDF first.")

    else:

        num = st.selectbox(
            "Number of flashcards",
            [5, 10, 15],
            index=1
        )

        if st.button("🗂️ Generate Flashcards"):

            if not require_client():
                st.stop()

            try:

                with st.spinner(
                    "Generating flashcards..."
                ):

                    cards = generate_flashcards(
                        client,
                        st.session_state.notes_text,
                        num_cards=int(num)
                    )

                st.session_state.flashcards = cards.cards

                st.success("Flashcards generated!")

            except Exception as e:
                st.error(f"Flashcard generation failed: {e}")

        if st.session_state.flashcards:

            for idx, card in enumerate(
                st.session_state.flashcards,
                start=1
            ):

                with st.expander(
                    f"Card {idx}: {card.question}"
                ):

                    st.write(card.answer)