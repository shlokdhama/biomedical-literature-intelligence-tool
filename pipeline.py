from transformers import pipeline
from pubmed_fetch import fetch_abstract_clean

# Load models once at the top, not inside the function.
bio_ner = pipeline(
    "ner",
    model="d4data/biomedical-ner-all",
    aggregation_strategy="first",
)

summarizer = pipeline(
    "summarization",
    model="sshleifer/distilbart-cnn-12-6",
)

classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli",
)

DISEASE_LABELS = [
    "mental health and psychiatric disorders",
    "neurology and brain disorders",
    "cancer and oncology",
    "cardiovascular disease",
    "infectious disease",
    "metabolic and endocrine disorders",
    "respiratory disease",
    "rare genetic disorders",
    "public health and epidemiology",
]

USEFUL_ENTITY_GROUPS = {
    "Disease_disorder",
    "Medication",
    "Therapeutic_procedure",
    "Biological_structure",
    "Gene_or_gene_product",
}

BLOCKED_ENTITY_WORDS = {
    "aes",
    "impairment",
    "burden",
    "anti",
    "disease",
    "disorder",
    "therapy",
    "mono",
    "meta",
    "orr",
    "boxes",
    "scale",
    "sum",
    "placebo",
    "random",
    "adverse events",
    "therapeutic agents",
    "mtb",
    "lecan",
    "mel",
    "mel ano",
    "uma",
    "izuma",
    "ili mumab",
    "loid",
}

FORCE_ENTITY_FIXES = {
    "alzheimer ' s disease": ("Alzheimer's disease", "Disease_disorder"),
    "alzheimer's disease": ("Alzheimer's disease", "Disease_disorder"),
    "pembrolizumab ipilimumab": ("pembrolizumab + ipilimumab", "Medication"),
    "ipilimumab": ("ipilimumab", "Medication"),
    "alzheimer": ("Alzheimer's disease", "Disease_disorder"),
    "alzheimer disease": ("Alzheimer's disease", "Disease_disorder"),
    "early alzheimer's disease": ("early Alzheimer's disease", "Disease_disorder"),
    "cognitive impairment": ("cognitive impairment", "Disease_disorder"),
    "melanoma": ("melanoma", "Disease_disorder"),
    "pembrolizumab": ("pembrolizumab", "Medication"),
    "lecanemab": ("lecanemab", "Medication"),
    "remdesivir": ("remdesivir", "Medication"),
    "covid-19": ("COVID-19", "Disease_disorder"),
    "coronavirus disease": ("coronavirus disease", "Disease_disorder"),
    "mycobacterium tuberculosis": ("Mycobacterium tuberculosis", "Disease_disorder"),
    "tuberculosis": ("tuberculosis", "Disease_disorder"),
    "bcg": ("BCG vaccine", "Medication"),
}


def clean_entity_word(word):
    word = word.replace(" ##", "")
    word = word.replace("##", "")
    word = word.replace(" ' s", "'s")
    word = word.replace(" 's", "'s")
    word = word.replace(" '", "'")
    word = word.replace(" - ", "-")
    word = word.replace(" -", "-")
    word = word.replace("- ", "-")
    word = word.strip(" ,.;:()[]{}")
    return word.strip()


def merge_entities(entities, threshold=0.75):
    filtered = []

    for entity in entities:
        if entity["score"] < threshold:
            continue

        word = clean_entity_word(entity["word"])
        group = entity["entity_group"]

        if not word or len(word) <= 2:
            continue

        normalized = word.lower()

        if normalized in BLOCKED_ENTITY_WORDS:
            continue

        if normalized in FORCE_ENTITY_FIXES:
            fixed_word, fixed_group = FORCE_ENTITY_FIXES[normalized]
            entity = entity.copy()
            entity["word"] = fixed_word
            entity["entity_group"] = fixed_group
            filtered.append(entity)
            continue

        if group not in USEFUL_ENTITY_GROUPS:
            continue

        entity = entity.copy()
        entity["word"] = word
        filtered.append(entity)

    if not filtered:
        return []

    merged = [filtered[0]]

    for current in filtered[1:]:
        previous = merged[-1]

        same_group = current["entity_group"] == previous["entity_group"]
        adjacent = current.get("start", 999999) - previous.get("end", -999999) <= 2
        current_word = current["word"]
        is_fragment = current_word.startswith("##") or len(current_word) <= 3

        if same_group and (adjacent or is_fragment):
            previous["word"] = clean_entity_word(previous["word"] + " " + current_word)
            previous["end"] = current.get("end", previous.get("end"))
            previous["score"] = max(previous["score"], current["score"])
        else:
            merged.append(current)

    unique = {}

    for entity in merged:
        word = clean_entity_word(entity["word"])
        normalized = word.lower()

        if normalized in BLOCKED_ENTITY_WORDS:
            continue

        if normalized in FORCE_ENTITY_FIXES:
            word, group = FORCE_ENTITY_FIXES[normalized]
            entity["word"] = word
            entity["entity_group"] = group

        key = (entity["entity_group"], entity["word"].lower())

        if key not in unique or entity["score"] > unique[key]["score"]:
            unique[key] = entity

    return sorted(
        unique.values(),
        key=lambda e: (e["entity_group"], e["word"].lower()),
    )


def run_pipeline(pubmed_id):
    paper = fetch_abstract_clean(pubmed_id)

    if not paper:
        return {"error": "Abstract not found for this PubMed ID"}

    abstract = paper["abstract"]
    title = paper["title"]

    ner_text = f"{title}. {abstract}"
    raw_entities = bio_ner(ner_text)
    entities = merge_entities(raw_entities)

    summary = summarizer(
        abstract[:2500],
        max_length=140,
        min_length=50,
        do_sample=False,
    )[0]["summary_text"]

    classification_text = f"{title}. {abstract[:1500]}"

    classification = classifier(
        classification_text,
        candidate_labels=DISEASE_LABELS,
        multi_label=True,
    )

    top_label = classification["labels"][0]
    top_score = classification["scores"][0]

    return {
        "title": title,
        "pubmed_id": pubmed_id,
        "abstract": abstract,
        "disease_area": top_label,
        "disease_confidence": round(top_score, 3),
        "summary": summary,
        "entities": entities,
    }


if __name__ == "__main__":
    result = run_pipeline("33577785")

    if "error" in result:
        print(result["error"])
    else:
        print("Title:", result["title"])
        print("Disease area:", result["disease_area"], f"({result['disease_confidence']})")
        print("Summary:", result["summary"])
        print("\nEntities:")

        for entity in result["entities"]:
            print(f"  {entity['entity_group']}: {entity['word']} ({entity['score']:.2f})")
