# AI Study Assistant (Streamlit + Groq + PyPDF2)

A beginner-friendly web app that:

- Uploads a PDF
- Extracts text (PyPDF2)
- Generates a summary (Gemini)
- Answers questions from the notes (Gemini)
- Creates a 5-question MCQ quiz (Gemini)
- Generates flashcards (Gemini)


## Project Structure
- `app.py` - Streamlit UI
- `utils/` - modular backend functions
- `uploads/` - saved uploaded PDFs (optional)

## Setup
1. Open a terminal in the `ai-study-assistant` folder.
2. (Recommended) Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create your `.env` file:
   - Copy `.env.example` to `.env`
   - Add your Gemini API key:
     ```env
     GROQ_API_KEY=your_groq_key_here

     ```


## Run
```bash
streamlit run app.py
```

## Notes
- Large PDFs may be truncated to keep prompts manageable.
- If the model says it can't find the answer, try asking using wording that appears in your notes.


