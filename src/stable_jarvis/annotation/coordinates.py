"""
PDF coordinate extraction using PyMuPDF.
Handles text search and bounding box extraction with multiple fallback strategies.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import pymupdf
import pymupdf4llm


# Math symbol normalization mapping (bidirectional where sensible)
# Maps special characters to ASCII equivalents for robust text matching
MATH_NORMALIZE_MAP: dict[str, str] = {
    # Greek letters (lowercase)
    "ω": "omega", "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta",
    "ε": "epsilon", "ζ": "zeta", "η": "eta", "θ": "theta", "ι": "iota",
    "κ": "kappa", "λ": "lambda", "μ": "mu", "ν": "nu", "ξ": "xi",
    "π": "pi", "ρ": "rho", "σ": "sigma", "τ": "tau", "υ": "upsilon",
    "φ": "phi", "χ": "chi", "ψ": "psi",
    # Greek letters (uppercase)
    "Ω": "Omega", "Α": "Alpha", "Β": "Beta", "Γ": "Gamma", "Δ": "Delta",
    "Θ": "Theta", "Λ": "Lambda", "Π": "Pi", "Σ": "Sigma", "Φ": "Phi",
    "Ψ": "Psi",
    # Additional math symbols
    "∂": "d", "∇": "nabla", "∈": "in", "∉": "not in", "∀": "forall",
    "∃": "exists", "∧": "and", "∨": "or", "¬": "not", "→": "->",
    "←": "<-", "↔": "<->", "⇒": "=>", "⇐": "<=", "⇔": "<=>",
    "∑": "sum", "∏": "prod", "∫": "int", "∮": "oint",
    "√": "sqrt", "∝": "propto", "∼": "~", "≡": "==", "⊂": "subset",
    "⊃": "supset", "⊆": "subseteq", "⊇": "supseteq", "∩": "cap", "∪": "cup",
    # Math operators and symbols
    "×": "x", "·": "*", "−": "-", "–": "-", "—": "-",
    "′": "'", "″": "\"", "≤": "<=", "≥": ">=", "≠": "!=",
    "≈": "~=", "±": "+-", "∞": "inf", "°": "deg",
    # Subscripts and superscripts
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
    "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
    "₊": "+", "₋": "-", "₌": "=", "₍": "(", "₎": ")",
    "ₐ": "a", "ₑ": "e", "ₒ": "o", "ₓ": "x", "ₕ": "h",
    "ₖ": "k", "ₗ": "l", "ₘ": "m", "ₙ": "n", "ₚ": "p",
    "ₛ": "s", "ₜ": "t",
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "⁺": "+", "⁻": "-", "⁼": "=", "⁽": "(", "⁾": ")",
    "ⁿ": "n", "ⁱ": "i",
    # Common fractions
    "½": "1/2", "⅓": "1/3", "¼": "1/4", "⅔": "2/3", "¾": "3/4",
    "⅕": "1/5", "⅖": "2/5", "⅗": "3/5", "⅘": "4/5",
    "⅙": "1/6", "⅚": "5/6", "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8",
    # Ligatures (common in PDFs)
    "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
    "œ": "oe", "Œ": "OE", "æ": "ae", "Æ": "AE",
    "ĳ": "ij", "Ĳ": "IJ", "ﬆ": "st", "ﬅ": "ft",
    # Invisible/control characters (map to empty string)
    "\u00AD": "",  # Soft hyphen
    "\u200B": "",  # Zero-width space
    "\u200C": "",  # Zero-width non-joiner
    "\u200D": "",  # Zero-width joiner
    "\uFEFF": "",  # BOM / zero-width no-break space
    "\u2060": "",  # Word joiner
    "\u00A0": " ",  # Non-breaking space → regular space
    "\u2007": " ",  # Figure space
    "\u2008": " ",  # Punctuation space
    "\u2009": " ",  # Thin space
    "\u200A": " ",  # Hair space
    "\u202F": " ",  # Narrow no-break space
    "\u205F": " ",  # Medium mathematical space
    # Quotation marks normalization
    """: "\"", """: "\"", "'": "'", "'": "'",
    "«": "\"", "»": "\"", "‹": "'", "›": "'",
    # Bullet and list markers
    "•": "*", "◦": "o", "‣": ">", "⁃": "-",
}


@dataclass
class TextMatch:
    """Result of a text search in a PDF page."""
    page_index: int
    page_height: float
    page_width: float
    rects: List[List[float]]  # [[x0, y0, x1, y1], ...]
    method: str  # "search_for", "word_match", "pymupdf4llm"


@dataclass
class PDFInfo:
    """Information about a PDF file for annotation purposes."""
    total_pages: int
    page_dimensions: List[Tuple[float, float]]  # [(width, height), ...] for each page
    has_cover: bool  # True if first page appears to be a cover (different size)
    page_labels: List[str]  # PDF page labels if available (e.g., ["i", "ii", "1", "2"])
    page_previews: List[str] = field(default_factory=list)  # First ~200 chars of each page
    
    def get_logical_page(self, display_page: int, cover_offset: int = 0) -> int:
        """
        Convert user-friendly 1-based page number to 0-based index.
        
        Args:
            display_page: The page number as shown in a PDF reader (1-based).
            cover_offset: Number of cover/front-matter pages to skip.
        
        Returns:
            0-based page index for use with PyMuPDF.
        """
        return display_page - 1 + cover_offset
    
    def find_text(self, query: str, threshold: float = 0.6) -> List[dict]:
        """
        Search for text in page previews.
        
        Args:
            query: Text to search for.
            threshold: Minimum similarity ratio (0.0-1.0).
        
        Returns:
            List of {page: int, confidence: float, preview: str} for matching pages.
        """
        results = []
        query_lower = query.lower()
        query_alpha = CoordinateExtractor.extract_alpha_only(query).lower()
        
        for i, preview in enumerate(self.page_previews):
            preview_lower = preview.lower()
            preview_alpha = CoordinateExtractor.extract_alpha_only(preview).lower()
            
            # Direct substring match
            if query_lower in preview_lower:
                results.append({"page": i, "confidence": 1.0, "preview": preview[:100]})
                continue
            
            # Alpha-only fuzzy match
            ratio = difflib.SequenceMatcher(None, query_alpha, preview_alpha).ratio()
            if ratio >= threshold:
                results.append({"page": i, "confidence": ratio, "preview": preview[:100]})
        
        # Sort by confidence descending
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results


@dataclass
class CoordinateExtractor:
    """
    Extracts text coordinates from PDF files using PyMuPDF.
    
    Supports three extraction strategies:
    1. Primary: page.search_for() - fast exact-string match
    2. Fallback A: word-level matching with NFKC normalization (handles ligatures)
    3. Fallback B: pymupdf4llm for dual-column layouts with reading order
    """
    
    flip_y: bool = True  # Convert to standard PDF coordinate space (bottom-left origin)
    
    @staticmethod
    def normalize(text: str) -> str:
        """NFKC normalization: decomposes ligatures (ﬂ→fl, ﬁ→fi, etc.)."""
        return unicodedata.normalize("NFKC", text)
    
    @staticmethod
    def normalize_math(text: str) -> str:
        """
        Extended normalization for math-heavy text.
        
        Applies NFKC normalization plus explicit math symbol mapping
        to handle Greek letters, subscripts, and math operators.
        """
        # First apply NFKC
        result = unicodedata.normalize("NFKC", text)
        # Then apply math symbol mapping
        for symbol, replacement in MATH_NORMALIZE_MAP.items():
            result = result.replace(symbol, replacement)
        return result
    
    @staticmethod
    def strip_special_chars(text: str, keep_spaces: bool = True) -> str:
        """
        Strip special characters for ultra-fuzzy matching.
        
        Removes all non-alphanumeric characters except optionally spaces.
        Also removes Unicode control characters (Cc, Cf) and various
        spacing categories (Zs) that cause matching issues in PDFs.
        
        Args:
            text: Input text to clean.
            keep_spaces: If True, preserve spaces; if False, remove all whitespace.
        
        Returns:
            Cleaned text with only alphanumeric characters (and spaces if keep_spaces).
        """
        # First apply math normalization to convert symbols to ASCII equivalents
        result = CoordinateExtractor.normalize_math(text)
        
        # Remove Unicode control characters (Cc), format chars (Cf), and line/para separators
        cleaned_chars = []
        for char in result:
            category = unicodedata.category(char)
            # Skip control chars, format chars, line separators, paragraph separators
            if category in ("Cc", "Cf", "Zl", "Zp"):
                continue
            # Convert various space categories to regular space
            if category == "Zs":
                if keep_spaces:
                    cleaned_chars.append(" ")
                continue
            cleaned_chars.append(char)
        
        result = "".join(cleaned_chars)
        
        # Remove non-alphanumeric (keep spaces if requested)
        if keep_spaces:
            result = re.sub(r"[^\w\s]", "", result, flags=re.UNICODE)
            # Collapse multiple spaces
            result = re.sub(r"\s+", " ", result).strip()
        else:
            result = re.sub(r"[^\w]", "", result, flags=re.UNICODE)
        
        return result
    
    @staticmethod
    def extract_alpha_only(text: str) -> str:
        """
        Extract only alphabetic characters for aggressive fuzzy matching.
        
        This is the most aggressive text normalization - used when math symbols
        are extracted as OCR garbage (e.g., 'd∂' becomes 'd鈭') and even
        strip_special_chars fails.
        
        Process:
        1. Extract sequences of letters only (a-zA-Z)
        2. Filter out short words (< 2 characters) to reduce noise
        3. Join with spaces
        
        Args:
            text: Input text potentially containing corrupted math symbols.
        
        Returns:
            Space-separated letter sequences (2+ chars each).
        
        Example:
            >>> extract_alpha_only("where d∂ is")
            'where is'  # 'd' filtered as too short
            >>> extract_alpha_only("the gradient ∇f(x)")
            'the gradient'  # 'f' and 'x' filtered
        """
        # Extract only sequences of letters
        letter_sequences = re.findall(r'[a-zA-Z]+', text)
        # Filter out short sequences (< 2 chars) as they're often noise
        meaningful_words = [w for w in letter_sequences if len(w) >= 2]
        return " ".join(meaningful_words)
    
    @staticmethod
    def _tokens_match(pdf_word: str, target_token: str) -> bool:
        """Check if a PDF word matches a target token (with normalization)."""
        norm = CoordinateExtractor.normalize(pdf_word).lower()
        norm = norm.strip(".,;:!?")
        # Handle prefixes like "Abstract—Agile" → take suffix after last dash
        for dash in ("—", "–", "-"):
            if dash in norm:
                norm = norm.split(dash)[-1]
        return norm == target_token.strip(".,;:!?—–-")
    
    @staticmethod
    def _group_wrapped_search_results(hits: List[pymupdf.Rect]) -> List[List[pymupdf.Rect]]:
        """
        Groups consecutive search hits that belong to one wrapped multi-line match.

        This is adapted from the zotero-paper-coach project to improve multi-line
        text matching. PyMuPDF's search_for returns one rect per line fragment
        for a wrapped match. This function merges nearby vertical fragments into
        a single logical group.
        """
        if not hits:
            return []

        groups: List[List[pymupdf.Rect]] = [[hits[0]]]
        prev_rect = hits[0]
        for hit in hits[1:]:
            rect = hit
            
            # Check if the current hit is on the next line and close vertically
            prev_h = max(prev_rect.height, 1)
            curr_h = max(rect.height, 1)
            
            # Not on the same horizontal line
            same_line = abs(rect.y0 - prev_rect.y0) <= max(prev_h, curr_h) * 0.25
            
            # Vertical gap is small and positive (current rect is below previous)
            vertical_gap = rect.y0 - prev_rect.y1
            
            # Heuristic for a wrapped line
            wrapped_next_line = (not same_line) and (0 <= vertical_gap <= max(prev_h, curr_h) * 1.5)

            if wrapped_next_line:
                groups[-1].append(rect)
            else:
                groups.append([rect])
            prev_rect = rect
        return groups

    def _search_primary(
        self, page: pymupdf.Page, target_text: str
    ) -> Optional[List[List[float]]]:
        """
        Primary search using page.search_for() with multi-line grouping.
        
        Uses optimized flags:
        - TEXT_DEHYPHENATE: finds hyphenated words across lines
        - TEXT_PRESERVE_WHITESPACE: maintains spacing
        - TEXT_MEDIABOX_CLIP: ignores text outside page bounds
        - NOT using TEXT_PRESERVE_LIGATURES: expands fi/fl/ff ligatures
        """
        # Flags without TEXT_PRESERVE_LIGATURES to expand ligatures automatically
        flags = (
            pymupdf.TEXT_DEHYPHENATE
            | pymupdf.TEXT_PRESERVE_WHITESPACE
            | pymupdf.TEXT_MEDIABOX_CLIP
        )
        
        # Try with original text first
        bboxes = page.search_for(target_text, quads=False, flags=flags)
        
        # If not found, try with NFKC normalized text
        if not bboxes:
            normalized = self.normalize(target_text)
            if normalized != target_text:
                bboxes = page.search_for(normalized, quads=False, flags=flags)
        
        if not bboxes:
            return None
            
        # Group the results to handle multi-line matches
        grouped_hits = self._group_wrapped_search_results(bboxes)
        
        if not grouped_hits:
            return None
            
        # Return the first logical group of rectangles. This assumes we only want
        # the first occurrence of the target text on the page.
        first_group = grouped_hits[0]
        return [[bbox.x0, bbox.y0, bbox.x1, bbox.y1] for bbox in first_group]
    
    def _search_word_match(
        self, page: pymupdf.Page, target_text: str
    ) -> Optional[List[List[float]]]:
        """Fallback A: word-level sliding window with NFKC normalization."""
        words = page.get_text("words", sort=True)
        target_tokens = self.normalize(target_text).lower().split()
        n_target = len(target_tokens)
        
        word_strings = [w[4] for w in words]
        match_start = None
        
        for idx in range(len(word_strings) - n_target + 1):
            window = word_strings[idx : idx + n_target]
            if all(self._tokens_match(a, b) for a, b in zip(window, target_tokens)):
                match_start = idx
                break
        
        if match_start is None:
            return None
        
        matched_words = words[match_start : match_start + n_target]
        return self._group_words_to_rects(matched_words)
    
    def _search_merged_word(
        self, page: pymupdf.Page, target_text: str
    ) -> Optional[List[List[float]]]:
        """
        Fallback: find target text within merged word blobs.
        
        Some PDFs have text rendered without spaces, resulting in
        single "words" like "TheactionproducedbyRLpolicyis".
        This method finds those and returns their bounding boxes.
        """
        words = page.get_text("words", sort=True)
        if not words:
            return None
        
        # Normalize target without spaces
        target_no_space = self.normalize_math(target_text).lower().replace(" ", "")
        
        for word in words:
            word_text = word[4]
            word_normalized = self.normalize_math(word_text).lower()
            
            # Check if the target (without spaces) is contained in this word
            if target_no_space in word_normalized:
                x0, y0, x1, y1 = word[0], word[1], word[2], word[3]
                return [[x0, y0, x1, y1]]
        
        return None
    
    def _search_substring(
        self, page: pymupdf.Page, target_text: str
    ) -> Optional[List[List[float]]]:
        """
        Fallback: substring search in full page text.
        
        Extracts full page text, normalizes both page and target,
        then finds matching words by position.
        """
        # Get full page text with positions
        words = page.get_text("words", sort=True)
        if not words:
            return None
        
        # Build normalized full text from words
        word_strings = [w[4] for w in words]
        full_text = " ".join(word_strings)
        
        # Normalize both
        norm_full = self.normalize_math(full_text).lower()
        norm_target = self.normalize_math(target_text).lower()
        
        # Search for target in full text
        match = re.search(re.escape(norm_target), norm_full)
        if not match:
            return None
        
        # Find which words are in the match range
        # Build character-to-word mapping
        char_pos = 0
        word_ranges = []  # [(start_char, end_char, word_index), ...]
        for idx, word in enumerate(word_strings):
            norm_word = self.normalize_math(word).lower()
            start = char_pos
            end = char_pos + len(norm_word)
            word_ranges.append((start, end, idx))
            char_pos = end + 1  # +1 for space
        
        # Find words that overlap with match
        match_start, match_end = match.start(), match.end()
        matched_indices = []
        for start, end, idx in word_ranges:
            # Check if word overlaps with match
            if start < match_end and end > match_start:
                matched_indices.append(idx)
        
        if not matched_indices:
            return None
        
        matched_words = [words[i] for i in matched_indices]
        return self._group_words_to_rects(matched_words)
    
    def _search_fuzzy(
        self, page: pymupdf.Page, target_text: str, threshold: float = 0.85
    ) -> Tuple[Optional[List[List[float]]], Optional[str]]:
        """
        Final fallback: fuzzy matching using difflib.SequenceMatcher.
        
        Uses sliding window approach to find best match with similarity >= threshold.
        Returns (rects, matched_text) tuple.
        """
        words = page.get_text("words", sort=True)
        if not words:
            return None, None
        
        word_strings = [w[4] for w in words]
        target_tokens = self.normalize_math(target_text).lower().split()
        n_target = len(target_tokens)
        
        if n_target == 0:
            return None, None
        
        best_match_start = None
        best_ratio = 0.0
        best_matched_text = None
        
        # Sliding window with variable size (±2 words from target length)
        for window_size in range(max(1, n_target - 2), n_target + 3):
            for idx in range(len(word_strings) - window_size + 1):
                window = word_strings[idx : idx + window_size]
                window_text = " ".join(
                    self.normalize_math(w).lower() for w in window
                )
                target_normalized = " ".join(target_tokens)
                
                ratio = difflib.SequenceMatcher(
                    None, window_text, target_normalized
                ).ratio()
                
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match_start = idx
                    best_matched_text = " ".join(window)
        
        if best_ratio < threshold or best_match_start is None:
            return None, None
        
        # Determine actual window size used
        for window_size in range(max(1, n_target - 2), n_target + 3):
            if best_match_start + window_size <= len(words):
                window = word_strings[best_match_start : best_match_start + window_size]
                window_text = " ".join(
                    self.normalize_math(w).lower() for w in window
                )
                target_normalized = " ".join(target_tokens)
                ratio = difflib.SequenceMatcher(
                    None, window_text, target_normalized
                ).ratio()
                if abs(ratio - best_ratio) < 0.001:  # Found the matching window
                    matched_words = words[best_match_start : best_match_start + window_size]
                    return self._group_words_to_rects(matched_words), best_matched_text
        
        return None, None
    
    def _search_ultra_fuzzy(
        self, page: pymupdf.Page, target_text: str, threshold: float = 0.70
    ) -> Tuple[Optional[List[List[float]]], Optional[str]]:
        """
        Ultra-fuzzy fallback: strips all special characters before matching.
        
        This is the last resort for texts with heavy special characters,
        math symbols, or OCR artifacts. Uses lower threshold (70%) and
        compares only alphanumeric content.
        
        Returns (rects, matched_text) tuple.
        """
        words = page.get_text("words", sort=True)
        if not words:
            return None, None
        
        word_strings = [w[4] for w in words]
        
        # Strip special chars from target
        target_stripped = self.strip_special_chars(target_text, keep_spaces=True).lower()
        target_tokens = target_stripped.split()
        n_target = len(target_tokens)
        
        if n_target == 0:
            return None, None
        
        # Strip special chars from each word
        words_stripped = [
            self.strip_special_chars(w, keep_spaces=False).lower() 
            for w in word_strings
        ]
        
        best_match_start = None
        best_ratio = 0.0
        best_matched_text = None
        best_window_size = 0
        
        # Wider window range for ultra-fuzzy (±3 words)
        for window_size in range(max(1, n_target - 3), n_target + 4):
            for idx in range(len(words_stripped) - window_size + 1):
                window = words_stripped[idx : idx + window_size]
                window_text = " ".join(window)
                target_normalized = " ".join(target_tokens)
                
                ratio = difflib.SequenceMatcher(
                    None, window_text, target_normalized
                ).ratio()
                
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match_start = idx
                    best_matched_text = " ".join(word_strings[idx : idx + window_size])
                    best_window_size = window_size
        
        if best_ratio < threshold or best_match_start is None:
            return None, None
        
        matched_words = words[best_match_start : best_match_start + best_window_size]
        return self._group_words_to_rects(matched_words), best_matched_text
    
    def _search_pymupdf4llm(
        self, pdf_path: Path, page_index: int, target_text: str
    ) -> Optional[List[List[float]]]:
        """Fallback B: pymupdf4llm for dual-column reading order."""
        chunks = pymupdf4llm.to_markdown(
            str(pdf_path),
            pages=[page_index],
            page_chunks=True,
            extract_words=True,
        )
        llm_words = chunks[0].get("words", []) if chunks else []
        
        if not llm_words:
            return None
        
        target_tokens = self.normalize(target_text).lower().split()
        n_target = len(target_tokens)
        llm_strings = [w[4] for w in llm_words]
        
        match_start = None
        for idx in range(len(llm_strings) - n_target + 1):
            window = llm_strings[idx : idx + n_target]
            if all(self._tokens_match(a, b) for a, b in zip(window, target_tokens)):
                match_start = idx
                break
        
        if match_start is None:
            return None
        
        matched_words = llm_words[match_start : match_start + n_target]
        return self._group_words_to_rects(matched_words)
    
    @staticmethod
    def _group_words_to_rects(words: List[Tuple]) -> List[List[float]]:
        """Group consecutive words on the same line into merged rectangles."""
        line_groups: dict[tuple, list] = {}
        for w in words:
            x0, y0, x1, y1, text, bno, lno, wno = w
            key = (bno, lno)
            line_groups.setdefault(key, []).append((x0, y0, x1, y1))
        
        rects = []
        for key in sorted(line_groups.keys()):
            line_words = line_groups[key]
            lx0 = min(r[0] for r in line_words)
            ly0 = min(r[1] for r in line_words)
            lx1 = max(r[2] for r in line_words)
            ly1 = max(r[3] for r in line_words)
            rects.append([lx0, ly0, lx1, ly1])
        return rects
    
    def _transform_rect(
        self, rect: List[float], page_height: float
    ) -> List[float]:
        """Transform coordinates from PyMuPDF (top-left) to PDF (bottom-left) space."""
        x0, y0, x1, y1 = rect
        if self.flip_y:
            new_y0 = page_height - y1
            new_y1 = page_height - y0
            return [x0, new_y0, x1, new_y1]
        return [x0, y0, x1, y1]
    
    def extract(
        self,
        pdf_path: str | Path,
        target_text: str,
        page_index: int = 0,
    ) -> TextMatch:
        """
        Extract bounding boxes for target text in a PDF.
        
        Args:
            pdf_path: Path to the PDF file.
            target_text: Text to search for.
            page_index: 0-based page number.
        
        Returns:
            TextMatch with transformed coordinates.
        
        Raises:
            ValueError: If text is not found via any method.
        """
        pdf_path = Path(pdf_path)
        doc = pymupdf.open(str(pdf_path))
        
        try:
            page = doc[page_index]
            page_height = page.rect.height
            page_width = page.rect.width
            
            # Try primary search
            raw_rects = self._search_primary(page, target_text)
            method = "search_for"
            
            # Fallback A: word matching
            if not raw_rects:
                raw_rects = self._search_word_match(page, target_text)
                method = "word_match"
            
            # Fallback B: merged word search (handles PDFs without spaces)
            if not raw_rects:
                raw_rects = self._search_merged_word(page, target_text)
                method = "merged_word"
            
            # Fallback C: substring search (normalized)
            if not raw_rects:
                raw_rects = self._search_substring(page, target_text)
                method = "substring"
            
            # Fallback D: pymupdf4llm (close doc first to avoid bake() issues)
            if not raw_rects:
                doc.close()
                doc = None
                raw_rects = self._search_pymupdf4llm(pdf_path, page_index, target_text)
                method = "pymupdf4llm"
                # Need to reopen for fuzzy fallback if this fails
                if not raw_rects:
                    doc = pymupdf.open(str(pdf_path))
                    page = doc[page_index]
            
            # Fallback E: fuzzy matching (85% threshold)
            fuzzy_matched_text = None
            if not raw_rects:
                raw_rects, fuzzy_matched_text = self._search_fuzzy(page, target_text)
                method = "fuzzy"
                if raw_rects and fuzzy_matched_text:
                    warnings.warn(
                        f"Fuzzy match used (may not be exact): "
                        f"matched '{fuzzy_matched_text}' for target '{target_text}'"
                    )
            
            # Fallback F: ultra-fuzzy matching (70% threshold, strips special chars)
            if not raw_rects:
                raw_rects, fuzzy_matched_text = self._search_ultra_fuzzy(page, target_text)
                method = "ultra_fuzzy"
                if raw_rects and fuzzy_matched_text:
                    warnings.warn(
                        f"Ultra-fuzzy match used (verify carefully): "
                        f"matched '{fuzzy_matched_text}' for target '{target_text}'"
                    )
            
            if not raw_rects:
                raise ValueError(
                    f"Target text not found on page {page_index}: {target_text!r}\n"
                    "Tips: Shorten the text, check the page index, or verify exact wording."
                )
            
            # Transform coordinates
            final_rects = [self._transform_rect(r, page_height) for r in raw_rects]
            
            return TextMatch(
                page_index=page_index,
                page_height=page_height,
                page_width=page_width,
                rects=final_rects,
                method=method,
            )
        finally:
            if doc:
                doc.close()


def get_pdf_info(pdf_path: str | Path) -> PDFInfo:
    """
    Get information about a PDF file.
    
    Useful for understanding page structure before creating annotations.
    
    Args:
        pdf_path: Path to the PDF file.
    
    Returns:
        PDFInfo with page count, dimensions, and detection of cover pages.
    
    Example:
        >>> info = get_pdf_info("paper.pdf")
        >>> print(f"Total pages: {info.total_pages}")
        >>> print(f"Has cover: {info.has_cover}")
        >>> # Convert display page 5 to 0-based index (with 1 cover page)
        >>> page_idx = info.get_logical_page(5, cover_offset=1)
        >>> # Search for text across all pages
        >>> matches = info.find_text("gradient descent")
    """
    pdf_path = Path(pdf_path)
    doc = pymupdf.open(str(pdf_path))
    
    try:
        total_pages = len(doc)
        page_dimensions = []
        page_labels = []
        page_previews = []
        
        for i in range(total_pages):
            page = doc[i]
            page_dimensions.append((page.rect.width, page.rect.height))
            
            # Try to get PDF page label (if defined in PDF)
            try:
                label = doc.get_page_labels()[i] if doc.get_page_labels() else str(i + 1)
            except (IndexError, AttributeError):
                label = str(i + 1)
            page_labels.append(label)
            
            # Extract first ~200 characters of page text for preview
            try:
                text = page.get_text("text", sort=True)[:500]  # Get more, trim later
                # Clean up whitespace
                text = " ".join(text.split())[:200]
                page_previews.append(text)
            except Exception:
                page_previews.append("")
        
        # Detect cover page: first page has significantly different dimensions
        has_cover = False
        if total_pages > 1:
            first_w, first_h = page_dimensions[0]
            second_w, second_h = page_dimensions[1]
            # Check if first page differs by >5% in either dimension
            w_diff = abs(first_w - second_w) / max(second_w, 1) > 0.05
            h_diff = abs(first_h - second_h) / max(second_h, 1) > 0.05
            has_cover = w_diff or h_diff
        
        return PDFInfo(
            total_pages=total_pages,
            page_dimensions=page_dimensions,
            has_cover=has_cover,
            page_labels=page_labels,
            page_previews=page_previews,
        )
    finally:
        doc.close()


def search_text_in_pdf(pdf_path: str | Path, query: str, max_results: int = 5) -> List[dict]:
    """
    Search for text across all pages of a PDF.
    
    Useful for pre-flight verification: find where text appears before
    attempting to create an annotation with a specific page index.
    
    Args:
        pdf_path: Path to the PDF file.
        query: Text to search for.
        max_results: Maximum number of results to return.
    
    Returns:
        List of {page: int, context: str, confidence: float, method: str}
        sorted by confidence descending.
    
    Example:
        >>> results = search_text_in_pdf("paper.pdf", "gradient descent")
        >>> for r in results:
        ...     print(f"Page {r['page']}: {r['context'][:50]}... ({r['confidence']:.0%})")
    """
    pdf_path = Path(pdf_path)
    doc = pymupdf.open(str(pdf_path))
    results = []
    
    # Prepare query variations
    query_normalized = CoordinateExtractor.normalize(query)
    query_alpha = CoordinateExtractor.extract_alpha_only(query).lower()
    
    try:
        for i in range(len(doc)):
            page = doc[i]
            text = page.get_text("text", sort=True)
            text_lower = text.lower()
            
            # Method 1: Exact search with PyMuPDF
            flags = pymupdf.TEXT_DEHYPHENATE | pymupdf.TEXT_PRESERVE_WHITESPACE
            bboxes = page.search_for(query, quads=False, flags=flags)
            if bboxes:
                # Found exact match
                # Extract context around first match
                idx = text_lower.find(query.lower())
                if idx == -1:
                    idx = text_lower.find(query_normalized.lower())
                if idx >= 0:
                    start = max(0, idx - 30)
                    end = min(len(text), idx + len(query) + 30)
                    context = text[start:end].strip()
                else:
                    context = text[:100].strip()
                
                results.append({
                    "page": i,
                    "context": context,
                    "confidence": 1.0,
                    "method": "exact",
                })
                continue
            
            # Method 2: Alpha-only fuzzy match
            text_alpha = CoordinateExtractor.extract_alpha_only(text).lower()
            ratio = difflib.SequenceMatcher(None, query_alpha, text_alpha[:len(query_alpha)*3]).ratio()
            if ratio >= 0.6:
                # Find approximate location
                context = text[:100].strip()
                results.append({
                    "page": i,
                    "context": context,
                    "confidence": ratio,
                    "method": "alpha_fuzzy",
                })
        
        # Sort by confidence descending
        results.sort(key=lambda x: (x["confidence"], -x["page"]), reverse=True)
        return results[:max_results]
    finally:
        doc.close()
