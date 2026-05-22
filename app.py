import html

import streamlit as st

from pipeline import run_pipeline

st.set_page_config(
    page_title="Biomedical Literature Intelligence Tool",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }

        .app-title {
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }

        .app-subtitle {
            color: #9ca3af;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        .result-title {
            font-size: 1.55rem;
            font-weight: 750;
            line-height: 1.25;
            margin-top: 1.2rem;
            margin-bottom: 1rem;
        }

        .metric-panel {
            border: 1px solid rgba(148, 163, 184, 0.22);
            background: rgba(15, 23, 42, 0.55);
            padding: 1rem 1.1rem;
            border-radius: 8px;
            min-height: 112px;
        }

        .metric-label {
            color: #9ca3af;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.35rem;
        }

        .metric-value {
            font-size: 1.55rem;
            font-weight: 800;
            line-height: 1.15;
        }

        .confidence-track {
            height: 8px;
            background: rgba(148, 163, 184, 0.25);
            border-radius: 999px;
            overflow: hidden;
            margin-top: 0.8rem;
        }

        .confidence-fill {
            height: 8px;
            background: linear-gradient(90deg, #22c55e, #14b8a6);
            border-radius: 999px;
        }

        .section-title {
            font-size: 1.05rem;
            font-weight: 800;
            margin-top: 1.5rem;
            margin-bottom: 0.7rem;
        }

        .summary-box {
            border-left: 4px solid #14b8a6;
            background: rgba(20, 184, 166, 0.08);
            padding: 1rem 1.1rem;
            border-radius: 6px;
            line-height: 1.65;
            font-size: 1rem;
        }

        .entity-block {
            margin-bottom: 1rem;
        }

        .entity-heading {
            color: #d1d5db;
            font-size: 0.82rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.45rem;
        }

        .chip {
            display: inline-block;
            padding: 0.28rem 0.62rem;
            margin: 0.18rem 0.22rem 0.18rem 0;
            border-radius: 999px;
            font-size: 0.86rem;
            font-weight: 650;
            border: 1px solid rgba(255, 255, 255, 0.14);
        }

        .empty-state {
            color: #9ca3af;
            padding: 1rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

ENTITY_COLORS = {
    "Disease_disorder": ("#7f1d1d", "#fecaca"),
    "Medication": ("#134e4a", "#99f6e4"),
    "Sign_symptom": ("#713f12", "#fde68a"),
    "Therapeutic_procedure": ("#374151", "#e5e7eb"),
    "Diagnostic_procedure": ("#4c1d95", "#ddd6fe"),
    "Biological_structure": ("#14532d", "#bbf7d0"),
    "Gene_or_gene_product": ("#1e3a8a", "#bfdbfe"),
}


def title_case_entity_group(group):
    return group.replace("_", " ").title()


def render_metric(label, value, confidence=None):
    bar_html = ""

    if confidence is not None:
        width = max(0, min(confidence * 100, 100))
        bar_html = (
            f'<div class="confidence-track">'
            f'<div class="confidence-fill" style="width:{width:.1f}%"></div>'
            f"</div>"
        )

    metric_html = (
        f'<div class="metric-panel">'
        f'<div class="metric-label">{html.escape(label)}</div>'
        f'<div class="metric-value">{html.escape(value)}</div>'
        f"{bar_html}"
        f"</div>"
    )

    st.markdown(metric_html, unsafe_allow_html=True)


def render_entities(entities):
    entity_groups = {}

    for entity in entities:
        group = entity["entity_group"]
        word = entity["word"].strip()

        if not word:
            continue

        entity_groups.setdefault(group, set()).add(word)

    if not entity_groups:
        st.markdown(
            '<div class="empty-state">No clean biomedical entities found.</div>',
            unsafe_allow_html=True,
        )
        return

    for group, items in entity_groups.items():
        bg_color, text_color = ENTITY_COLORS.get(group, ("#374151", "#f9fafb"))

        chips = ""
        for item in sorted(items, key=str.lower):
            chips += (
                f'<span class="chip" style="background:{bg_color}; color:{text_color};">'
                f"{html.escape(item)}"
                f"</span>"
            )

        st.markdown(
            f"""
            <div class="entity-block">
                <div class="entity-heading">{html.escape(title_case_entity_group(group))}</div>
                <div>{chips}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


st.markdown(
    '<div class="app-title">Biomedical Literature Intelligence Tool</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="app-subtitle">Analyse PubMed abstracts with summarisation, disease-area classification, and biomedical entity extraction.</div>',
    unsafe_allow_html=True,
)

with st.form("pubmed_form"):
    left, right = st.columns([4, 1])

    with left:
        pubmed_id = st.text_input(
            "PubMed ID",
            placeholder="Try 33313405, 33709421, 36449413, 31679946",
            label_visibility="collapsed",
        )

    with right:
        submitted = st.form_submit_button("Analyse", use_container_width=True)

if submitted:
    if not pubmed_id.strip():
        st.warning("Enter a PubMed ID first.")
    else:
        with st.spinner("Fetching and analysing abstract..."):
            result = run_pipeline(pubmed_id.strip())

        if "error" in result:
            st.error(result["error"])
        else:
            st.markdown(
                f'<div class="result-title">{html.escape(result["title"])}</div>',
                unsafe_allow_html=True,
            )

            col1, col2, col3 = st.columns([1.5, 1, 1])

            with col1:
                render_metric("Disease Area", result["disease_area"].title())

            with col2:
                confidence_text = f"{result['disease_confidence'] * 100:.1f}%"
                render_metric("Confidence", confidence_text, result["disease_confidence"])

            with col3:
                render_metric("PubMed ID", result["pubmed_id"])

            with st.expander("View full abstract"):
                st.write(result.get("abstract", "Abstract not available."))

            st.markdown(
                '<div class="section-title">Plain English Summary</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="summary-box">{html.escape(result["summary"])}</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="section-title">Extracted Biomedical Entities</div>',
                unsafe_allow_html=True,
            )
            render_entities(result["entities"])
