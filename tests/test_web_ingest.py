from local_gate_agent.ingestion.web_ingest import chunk_text, extract_html_text


def test_extract_html_text_ignores_non_content_tags():
    html = "<html><head><style>hidden</style><script>ignored()</script></head><body><h1>Flight status</h1><p>Gate update</p></body></html>"

    assert extract_html_text(html) == "Flight status gate update"


def test_chunk_text_preserves_all_words_within_limit():
    chunks = chunk_text("one two three four", chunk_size=8)

    assert chunks == ["one two", "three", "four"]