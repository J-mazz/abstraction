"""
Tools for writing and text processing tasks.
"""
import re
from typing import Optional, List
from collections import Counter
from .base import BaseTool, ToolCategory, ToolOutput


class WordCounterTool(BaseTool):
    """Count words, characters, and sentences in text."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WRITING

    @property
    def requires_approval(self) -> bool:
        return False  # Read-only operation

    def execute(self, text: str) -> ToolOutput:
        """
        Count words, characters, and sentences.

        Args:
            text: Text to analyze

        Returns:
            ToolOutput with text statistics
        """
        try:
            # Word count
            words = text.split()
            word_count = len(words)

            # Character count
            char_count = len(text)
            char_count_no_spaces = len(text.replace(' ', ''))

            # Sentence count
            sentences = re.split(r'[.!?]+', text)
            sentence_count = len([s for s in sentences if s.strip()])

            # Paragraph count
            paragraphs = text.split('\n\n')
            paragraph_count = len([p for p in paragraphs if p.strip()])

            # Average word length
            avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0

            result = {
                "word_count": word_count,
                "character_count": char_count,
                "character_count_no_spaces": char_count_no_spaces,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count,
                "avg_word_length": round(avg_word_length, 2)
            }

            return ToolOutput(success=True, result=result)

        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))


class TextSummarizerTool(BaseTool):
    """Summarize text by extracting key sentences."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WRITING

    @property
    def requires_approval(self) -> bool:
        return False  # Read-only operation

    def execute(self, text: str, num_sentences: int = 3) -> ToolOutput:
        """
        Summarize text by extracting key sentences.

        Args:
            text: Text to summarize
            num_sentences: Number of sentences to extract

        Returns:
            ToolOutput with summary
        """
        try:
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]

            if len(sentences) <= num_sentences:
                summary = ' '.join(sentences)
            else:
                # Simple extractive summarization: use first and last sentences
                # plus sentences with most common words
                words = text.lower().split()
                word_freq = Counter(words)

                # Score sentences by word frequency
                sentence_scores = []
                for sent in sentences:
                    score = sum(word_freq.get(word.lower(), 0) for word in sent.split())
                    sentence_scores.append((sent, score))

                # Sort by score and take top sentences
                top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:num_sentences]

                # Maintain original order
                summary = '. '.join([sent for sent, _ in top_sentences]) + '.'

            result = {
                "summary": summary,
                "original_sentence_count": len(sentences),
                "summary_sentence_count": num_sentences
            }

            return ToolOutput(success=True, result=result)

        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))


class GrammarCheckerTool(BaseTool):
    """Basic grammar and style checking."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WRITING

    @property
    def requires_approval(self) -> bool:
        return False  # Read-only operation

    def execute(self, text: str) -> ToolOutput:
        """
        Check for basic grammar and style issues.

        Args:
            text: Text to check

        Returns:
            ToolOutput with issues found
        """
        try:
            issues = []

            # Check for double spaces
            if '  ' in text:
                issues.append({
                    "type": "spacing",
                    "message": "Found double spaces",
                    "severity": "low"
                })

            # Check for repeated words
            words = text.lower().split()
            for i in range(len(words) - 1):
                if words[i] == words[i + 1]:
                    issues.append({
                        "type": "repetition",
                        "message": f"Repeated word: '{words[i]}'",
                        "severity": "medium"
                    })

            # Check for passive voice indicators
            passive_indicators = ['was', 'were', 'been', 'being']
            for indicator in passive_indicators:
                if f' {indicator} ' in text.lower():
                    issues.append({
                        "type": "style",
                        "message": f"Possible passive voice (contains '{indicator}')",
                        "severity": "low"
                    })
                    break

            # Check for sentence length
            sentences = re.split(r'[.!?]+', text)
            for sent in sentences:
                if len(sent.split()) > 30:
                    issues.append({
                        "type": "readability",
                        "message": "Long sentence detected (>30 words)",
                        "severity": "low"
                    })

            result = {
                "issues_found": len(issues),
                "issues": issues,
                "clean": len(issues) == 0
            }

            return ToolOutput(success=True, result=result)

        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))


class TextFormatterTool(BaseTool):
    """Format and clean text."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WRITING

    @property
    def requires_approval(self) -> bool:
        return False  # Read-only operation

    def execute(
        self,
        text: str,
        remove_extra_spaces: bool = True,
        fix_punctuation_spacing: bool = True,
        capitalize_sentences: bool = True
    ) -> ToolOutput:
        """
        Format and clean text.

        Args:
            text: Text to format
            remove_extra_spaces: Remove extra spaces
            fix_punctuation_spacing: Fix spacing around punctuation
            capitalize_sentences: Capitalize first letter of sentences

        Returns:
            ToolOutput with formatted text
        """
        try:
            formatted = text

            if remove_extra_spaces:
                formatted = re.sub(r'\s+', ' ', formatted)

            if fix_punctuation_spacing:
                # Remove spaces before punctuation
                formatted = re.sub(r'\s+([.,!?;:])', r'\1', formatted)
                # Add space after punctuation if missing
                formatted = re.sub(r'([.,!?;:])(\w)', r'\1 \2', formatted)

            if capitalize_sentences:
                # Capitalize after sentence-ending punctuation
                sentences = re.split(r'([.!?]+)', formatted)
                formatted = ''
                for i, part in enumerate(sentences):
                    if i % 2 == 0 and part.strip():
                        formatted += part.strip().capitalize()
                    else:
                        formatted += part
                    if i < len(sentences) - 1:
                        formatted += ' '

            result = {
                "formatted_text": formatted.strip(),
                "original_length": len(text),
                "formatted_length": len(formatted.strip())
            }

            return ToolOutput(success=True, result=result)

        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))
