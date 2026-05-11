"""
Preprocessing Pipeline Module
Handles text cleaning, spam detection, language detection, and currency pair extraction
"""

import re
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from app.schemas import SourceType, ProcessedNewsItem, RawNewsItem


class LanguageCode(str, Enum):
    """ISO 639-1 language codes"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    UNKNOWN = "unknown"


@dataclass
class CurrencyPairMatch:
    """Represents a matched currency pair with context"""
    pair: str
    base_currency: str
    quote_currency: str
    confidence: float
    context: str


class TextCleaner:
    """Text cleaning and normalization utilities"""

    # Common abbreviations in financial news
    ABBREVIATIONS = {
        "fed": "federal reserve",
        "ecb": "european central bank",
        "boj": "bank of japan",
        "boe": "bank of england",
        "snb": "swiss national bank",
        "rba": "reserve bank of australia",
        "boc": "bank of canada",
        "rbnz": "reserve bank of new zealand",
        "cpi": "consumer price index",
        "gdp": "gross domestic product",
        "nfp": "non-farm payrolls",
        "pmi": "purchasing managers index",
        "yoy": "year over year",
        "qoq": "quarter over quarter",
        "mom": "month over month",
        "h1": "first half",
        "h2": "second half",
        "q1": "first quarter",
        "q2": "second quarter",
        "q3": "third quarter",
        "q4": "fourth quarter",
        "usd": "us dollar",
        "eur": "euro",
        "gbp": "british pound",
        "jpy": "japanese yen",
        "chf": "swiss franc",
        "aud": "australian dollar",
        "cad": "canadian dollar",
        "nzd": "new zealand dollar",
        "sgd": "singapore dollar",
    }

    # Financial jargon patterns
    FINANCIAL_PATTERNS = {
        r"\b(hawkish|dovish)\b": "monetary policy stance",
        r"\b(tapering|quantitative easing|qe)\b": "monetary policy action",
        r"\b(rate hike|rate cut|interest rate)\b": "interest rate change",
        r"\b(inflation|deflation)\b": "price level change",
        r"\b(recession|expansion)\b": "economic cycle",
    }

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text for analysis"""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', '', text)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)

        # Remove phone numbers
        text = re.sub(r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '', text)

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:]', '', text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    @staticmethod
    def expand_abbreviations(text: str) -> str:
        """Expand common financial abbreviations"""
        words = text.split()
        expanded = []

        for word in words:
            # Remove punctuation for matching
            clean_word = word.strip('.,!?;:')
            if clean_word in TextCleaner.ABBREVIATIONS:
                expanded.append(TextCleaner.ABBREVIATIONS[clean_word])
            else:
                expanded.append(word)

        return ' '.join(expanded)

    @staticmethod
    def remove_noise(text: str) -> str:
        """Remove noise from text (hashtags, mentions, etc.)"""
        # Remove hashtags (keep the text)
        text = re.sub(r'#(\w+)', r'\1', text)

        # Remove mentions
        text = re.sub(r'@\w+', '', text)

        # Remove excessive punctuation
        text = re.sub(r'([!?])\1+', r'\1', text)

        # Remove numbers that are likely dates or times
        text = re.sub(r'\b\d{1,2}:\d{2}\b', '', text)  # Times
        text = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '', text)  # Dates

        return text.strip()

    @staticmethod
    def normalize(text: str) -> str:
        """Complete normalization pipeline"""
        text = TextCleaner.clean_text(text)
        text = TextCleaner.expand_abbreviations(text)
        text = TextCleaner.remove_noise(text)
        return text


class SpamDetector:
    """Detect spam and bot-generated content"""

    # Spam patterns
    SPAM_PATTERNS = [
        r'\b(buy now|click here|free money|guaranteed|instant profit|100% win)\b',
        r'\b(\d{1,3}%\s*(bonus|profit|return|gain))\b',
        r'\b(bitcoin|crypto|crypto currency)\s+(mining|investment|trading)\b',
        r'\b(scam|fraud|fake|ponzi)\b',
    ]

    # Bot account patterns
    BOT_PATTERNS = [
        r'\d{6,}',  # Accounts with only numbers
        r'bot\d*',  # Accounts with "bot" in name
        r'auto\d*',  # Accounts with "auto" in name
    ]

    @staticmethod
    def is_spam(text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Check if content is spam"""
        if not text:
            return True

        text_lower = text.lower()

        # Check for spam patterns
        for pattern in SpamDetector.SPAM_PATTERNS:
            if re.search(pattern, text_lower):
                return True

        # Check for excessive capitalization
        uppercase_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if uppercase_ratio > 0.7:
            return True

        # Check for excessive repetition
        words = text.split()
        if len(words) > 0:
            unique_words = len(set(words))
            repetition_ratio = 1 - (unique_words / len(words))
            if repetition_ratio > 0.6:
                return True

        return False

    @staticmethod
    def is_bot(author: Optional[str], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Check if content is from a bot account"""
        if not author:
            return False

        author_lower = author.lower()

        # Check for bot patterns in author name
        for pattern in SpamDetector.BOT_PATTERNS:
            if re.search(pattern, author_lower):
                return True

        # Check metadata for bot indicators
        if metadata:
            # Check for suspicious follower/following ratios
            followers = metadata.get('followers_count', 0)
            following = metadata.get('following_count', 0)

            if followers > 0 and following > 0:
                ratio = followers / following
                # Very high follower-to-following ratio can indicate bots
                if ratio > 100:
                    return True

            # Check for verified status (some bots are verified)
            if metadata.get('verified', False):
                # Additional checks for verified accounts
                pass

        return False


class LanguageDetector:
    """Simple language detection (can be enhanced with proper NLP library)"""

    # Common words for major languages
    LANGUAGE_INDICATORS = {
        LanguageCode.ENGLISH: ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i'],
        LanguageCode.SPANISH: ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se'],
        LanguageCode.FRENCH: ['le', 'de', 'et', 'à', 'un', 'il', 'avoir', 'ne', 'je', 'son'],
        LanguageCode.GERMAN: ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich'],
        LanguageCode.ITALIAN: ['il', 'di', 'che', 'e', 'la', 'un', 'a', 'per', 'in', 'è'],
        LanguageCode.PORTUGUESE: ['o', 'de', 'a', 'e', 'do', 'da', 'em', 'um', 'para', 'é'],
        LanguageCode.RUSSIAN: ['и', 'в', 'не', 'на', 'я', 'то', 'с', 'что', 'а', 'по'],
        LanguageCode.CHINESE: ['的', '一', '是', '在', '不', '了', '有', '和', '人', '这'],
        LanguageCode.JAPANESE: ['の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と', 'し'],
        LanguageCode.KOREAN: ['이', '그', '저', '것', '의', '가', '에', '를', '은', '는'],
    }

    @staticmethod
    def detect(text: str) -> LanguageCode:
        """Detect the language of the text"""
        if not text:
            return LanguageCode.UNKNOWN

        text_lower = text.lower()
        words = text_lower.split()

        if len(words) < 3:
            return LanguageCode.UNKNOWN

        # Count matches for each language
        language_scores = {}

        for language, indicators in LanguageDetector.LANGUAGE_INDICATORS.items():
            score = 0
            for word in words:
                if word in indicators:
                    score += 1
            language_scores[language] = score

        # Find the language with the highest score
        max_score = max(language_scores.values())

        if max_score == 0:
            return LanguageCode.UNKNOWN

        # Get the language with the highest score
        detected_language = max(language_scores, key=language_scores.get)

        # Only return if we have enough confidence
        if max_score >= 2:
            return detected_language

        return LanguageCode.UNKNOWN

    @staticmethod
    def is_english(text: str) -> bool:
        """Check if text is in English"""
        return LanguageDetector.detect(text) == LanguageCode.ENGLISH


class CurrencyPairExtractor:
    """Extract currency pairs from text using NLP"""

    # Standard currency pairs
    STANDARD_PAIRS = {
        "EUR/USD": ["eur/usd", "eurusd", "euro dollar", "euro usd"],
        "GBP/USD": ["gbp/usd", "gbpusd", "pound dollar", "cable"],
        "USD/JPY": ["usd/jpy", "usdjpy", "dollar yen", "dollar jpy"],
        "USD/CHF": ["usd/chf", "usdchf", "dollar franc", "dollar chf"],
        "AUD/USD": ["aud/usd", "audusd", "aussie", "australian dollar"],
        "USD/CAD": ["usd/cad", "usdcad", "loonie", "dollar cad"],
        "NZD/USD": ["nzd/usd", "nzdusd", "kiwi", "new zealand dollar"],
        "USD/SGD": ["usd/sgd", "usdsgd", "sing dollar", "singapore dollar"],
    }

    # Individual currencies
    CURRENCIES = {
        "USD": ["usd", "dollar", "greenback", "buck"],
        "EUR": ["eur", "euro", "single currency"],
        "GBP": ["gbp", "pound", "sterling", "quid"],
        "JPY": ["jpy", "yen", "japanese yen"],
        "CHF": ["chf", "franc", "swiss franc"],
        "AUD": ["aud", "australian dollar", "aussie"],
        "CAD": ["cad", "canadian dollar", "loonie"],
        "NZD": ["nzd", "new zealand dollar", "kiwi"],
        "SGD": ["sgd", "singapore dollar"],
    }

    # Central bank references
    CENTRAL_BANKS = {
        "USD": ["federal reserve", "fed", "jerome powell"],
        "EUR": ["european central bank", "ecb", "christine lagarde"],
        "GBP": ["bank of england", "boe", "andrew bailey"],
        "JPY": ["bank of japan", "boj", "kazuo ueda"],
        "CHF": ["swiss national bank", "snb", "thomas jordan"],
        "AUD": ["reserve bank of australia", "rba", "michele bullock"],
        "CAD": ["bank of canada", "boc", "tif macklem"],
        "NZD": ["reserve bank of new zealand", "rbnz", "adrian orr"],
        "SGD": ["monetary authority of singapore", "mas"],
    }

    @staticmethod
    def extract_pairs(text: str) -> List[str]:
        """Extract currency pairs from text"""
        if not text:
            return []

        text_lower = text.lower()
        found_pairs = []

        # Check for standard pair notations
        for pair, variations in CurrencyPairExtractor.STANDARD_PAIRS.items():
            for variation in variations:
                if variation in text_lower:
                    if pair not in found_pairs:
                        found_pairs.append(pair)
                    break

        # Check for individual currency mentions
        mentioned_currencies = CurrencyPairExtractor._find_mentioned_currencies(text_lower)

        # Generate potential pairs from mentioned currencies
        if len(mentioned_currencies) >= 2:
            for i, curr1 in enumerate(mentioned_currencies):
                for curr2 in mentioned_currencies[i+1:]:
                    # Try both orderings
                    pair1 = f"{curr1}/{curr2}"
                    pair2 = f"{curr2}/{curr1}"

                    if pair1 in CurrencyPairExtractor.STANDARD_PAIRS:
                        if pair1 not in found_pairs:
                            found_pairs.append(pair1)
                    elif pair2 in CurrencyPairExtractor.STANDARD_PAIRS:
                        if pair2 not in found_pairs:
                            found_pairs.append(pair2)

        return found_pairs

    @staticmethod
    def _find_mentioned_currencies(text: str) -> List[str]:
        """Find which currencies are mentioned in the text"""
        mentioned = []

        for currency, variations in CurrencyPairExtractor.CURRENCIES.items():
            for variation in variations:
                if variation in text:
                    if currency not in mentioned:
                        mentioned.append(currency)
                    break

        return mentioned

    @staticmethod
    def extract_with_context(text: str) -> List[CurrencyPairMatch]:
        """Extract currency pairs with context and confidence"""
        if not text:
            return []

        text_lower = text.lower()
        matches = []

        for pair, variations in CurrencyPairExtractor.STANDARD_PAIRS.items():
            for variation in variations:
                if variation in text_lower:
                    # Find the context around the match
                    index = text_lower.find(variation)
                    start = max(0, index - 50)
                    end = min(len(text), index + len(variation) + 50)
                    context = text[start:end].strip()

                    # Calculate confidence based on match type
                    confidence = 1.0 if "/" in variation else 0.7

                    # Parse base and quote currencies
                    parts = pair.split("/")
                    base_currency = parts[0] if len(parts) > 0 else ""
                    quote_currency = parts[1] if len(parts) > 1 else ""

                    matches.append(CurrencyPairMatch(
                        pair=pair,
                        base_currency=base_currency,
                        quote_currency=quote_currency,
                        confidence=confidence,
                        context=context
                    ))
                    break

        return matches


class Deduplicator:
    """Handle content deduplication across platforms"""

    @staticmethod
    def generate_hash(content: str, source: SourceType, source_id: str) -> str:
        """Generate a unique hash for deduplication"""
        hash_input = f"{source.value}:{source_id}:{content}"
        return hashlib.sha256(hash_input.encode()).hexdigest()

    @staticmethod
    def is_duplicate(
        content_hash: str,
        existing_hashes: set
    ) -> bool:
        """Check if content is a duplicate"""
        return content_hash in existing_hashes

    @staticmethod
    def find_similar(
        content: str,
        existing_contents: List[str],
        threshold: float = 0.8
    ) -> Optional[str]:
        """Find similar content using simple similarity"""
        # This is a simplified implementation
        # In production, use proper text similarity algorithms

        content_words = set(content.lower().split())

        for existing in existing_contents:
            existing_words = set(existing.lower().split())

            if not content_words or not existing_words:
                continue

            # Jaccard similarity
            intersection = len(content_words & existing_words)
            union = len(content_words | existing_words)

            if union > 0:
                similarity = intersection / union
                if similarity >= threshold:
                    return existing

        return None


class PreprocessingPipeline:
    """Main preprocessing pipeline"""

    def __init__(self):
        self.cleaner = TextCleaner()
        self.spam_detector = SpamDetector()
        self.language_detector = LanguageDetector()
        self.currency_extractor = CurrencyPairExtractor()
        self.deduplicator = Deduplicator()

    def process(
        self,
        raw_item: RawNewsItem,
        existing_hashes: Optional[set] = None
    ) -> Optional[ProcessedNewsItem]:
        """Process a raw news item through the pipeline"""
        if existing_hashes is None:
            existing_hashes = set()

        # Step 1: Check for duplicates
        content_hash = self.deduplicator.generate_hash(
            raw_item.content,
            raw_item.source,
            raw_item.source_id
        )

        if self.deduplicator.is_duplicate(content_hash, existing_hashes):
            return None

        # Step 2: Clean text
        cleaned_content = self.cleaner.normalize(raw_item.content)

        if not cleaned_content or len(cleaned_content) < 10:
            return None

        # Step 3: Detect spam
        is_spam = self.spam_detector.is_spam(
            cleaned_content,
            raw_item.metadata
        )

        if is_spam:
            return None

        # Step 4: Detect bot content
        is_bot = self.spam_detector.is_bot(
            raw_item.author,
            raw_item.metadata
        )

        # Step 5: Detect language
        language = self.language_detector.detect(cleaned_content)

        # Filter non-English content
        if language != LanguageCode.ENGLISH:
            return None

        # Step 6: Extract currency pairs
        currency_pairs = self.currency_extractor.extract_pairs(cleaned_content)

        # Step 7: Create processed item
        processed_item = ProcessedNewsItem(
            source=raw_item.source,
            source_id=raw_item.source_id,
            original_content=raw_item.content,
            cleaned_content=cleaned_content,
            title=raw_item.title,
            author=raw_item.author,
            url=raw_item.url,
            timestamp=raw_item.timestamp,
            currency_pairs=currency_pairs,
            language=language.value,
            is_spam=is_spam,
            is_bot=is_bot,
            metadata=raw_item.metadata,
            content_hash=content_hash
        )

        return processed_item

    def process_batch(
        self,
        raw_items: List[RawNewsItem]
    ) -> List[ProcessedNewsItem]:
        """Process a batch of raw news items"""
        processed_items = []
        existing_hashes = set()

        for raw_item in raw_items:
            processed = self.process(raw_item, existing_hashes)
            if processed:
                processed_items.append(processed)
                existing_hashes.add(processed.content_hash)

        return processed_items
