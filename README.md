# Biomedical Literature Intelligence Tool

A Streamlit app that analyses PubMed abstracts using Hugging Face models.

## Features

- Fetches article titles and abstracts from PubMed
- Summarises biomedical abstracts in plain English
- Classifies papers into disease areas with zero-shot classification
- Extracts and displays biomedical entities such as diseases, medications, genes, and procedures

## Setup

Use Python 3.11 for best compatibility with the machine learning packages.

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Run

```powershell
python -m streamlit run app.py
```

Try PubMed IDs such as `33313405`, `33709421`, `36449413`, or `42167272`.
