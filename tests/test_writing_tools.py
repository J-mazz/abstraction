from src.tools.writing_tools import (
    WordCounterTool,
    TextSummarizerTool,
    GrammarCheckerTool,
    TextFormatterTool,
)


def test_word_counter_metrics():
    tool = WordCounterTool()
    result = tool.execute("Hello world. Hello again!")
    assert result.success
    assert result.result["sentence_count"] == 2


def test_text_summarizer_extracts_sentences():
    tool = TextSummarizerTool()
    text = "Python is great. Testing is important. Coverage builds confidence."
    response = tool.execute(text, num_sentences=2)
    assert response.success
    assert response.result["summary_sentence_count"] == 2


def test_grammar_checker_detects_issues():
    tool = GrammarCheckerTool()
    result = tool.execute("This  sentence was written written poorly.")
    assert result.success
    assert result.result["issues_found"] >= 2


def test_text_formatter_cleans_text():
    tool = TextFormatterTool()
    output = tool.execute("hello ,world")
    assert output.success
    assert output.result["formatted_text"].startswith("Hello")
