from Bio import Entrez

Entrez.email = "shlokdhama0@gmail.com"


def fetch_abstract(pubmed_id):
    handle = Entrez.efetch(
        db="pubmed",
        id=pubmed_id,
        rettype="abstract",
        retmode="text",
    )
    abstract = handle.read()
    handle.close()
    return abstract


def search_pubmed(query, max_results=5):
    handle = Entrez.esearch(
        db="pubmed",
        term=query,
        retmax=max_results,
    )
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]


def fetch_abstract_clean(pubmed_id):
    handle = Entrez.efetch(
        db="pubmed",
        id=pubmed_id,
        rettype="xml",
        retmode="xml",
    )
    records = Entrez.read(handle)
    handle.close()

    try:
        article = records["PubmedArticle"][0]["MedlineCitation"]["Article"]
        title = article["ArticleTitle"]
        abstract_parts = article["Abstract"]["AbstractText"]
        abstract_text = " ".join(str(part) for part in abstract_parts)

        return {
            "title": str(title),
            "abstract": abstract_text,
            "id": pubmed_id,
        }
    except (KeyError, IndexError):
        return None


if __name__ == "__main__":
    ids = search_pubmed("BRCA1 breast cancer machine learning")
    print("Found IDs:", ids)

    for pubmed_id in ids[:3]:
        print(f"\n--- Abstract {pubmed_id} ---")
        print(fetch_abstract(pubmed_id))

    result = fetch_abstract_clean("33577785")
    if result:
        print(result["title"])
        print(result["abstract"])
