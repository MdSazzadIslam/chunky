from app.ingest.chunking import chunk_pages


def test_short_page_stays_one_chunk() -> None:
    chunks = chunk_pages([(1, "hello world")], chunk_size=100, overlap=20)
    assert len(chunks) == 1
    assert chunks[0].page == 1
    assert chunks[0].text == "hello world"


def test_prefers_sentence_boundary() -> None:
    text = "First sentence ends here. Second sentence continues after that point for a while."
    chunks = chunk_pages([(1, text)], chunk_size=40, overlap=5)
    assert chunks[0].text.endswith("here.")


def test_long_text_without_spaces_still_splits() -> None:
    text = "abcdefghij" * 20
    chunks = chunk_pages([(1, text)], chunk_size=50, overlap=10)
    assert len(chunks) > 1
    assert chunks[0].index == 0


