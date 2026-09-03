"""
chunker.py — a generalizable text chunker for RAG / retrieval pipelines. It is a work in progress and is completely generate by Claude, based around a conversation between Claude and the project maintainer. If you plan to modify the function, please read the following design principles first to understand how this was created and how it works.

Design principles (distilled from working through this problem):

  1. Respect topic boundaries before length limits. If the source has
     structural headings (Markdown ATX headers), split on those FIRST,
     so a chunk never silently welds two unrelated sections together.
     Only fall back to paragraph/sentence-level splitting within a
     section that's too long to be one chunk.

  2. If there are no headings, degrade gracefully. Most real-world text
     (scraped pages, plain-text exports, transcripts) has no heading
     markup at all. The function detects this and falls back to pure
     paragraph -> sentence -> whitespace -> hard-cut splitting across
     the whole document, exactly as if there were no sectioning step.

  3. Never guess at what "looks like" a heading. Early heuristics (e.g.
     "a short line is probably a heading") produce false positives on
     ordinary short paragraphs. This only trusts unambiguous Markdown
     heading syntax by default, and lets you supply your own regex for
     other formats (e.g. already-tagged HTML/docx headings) — see
     `heading_pattern`.

  4. Length is pluggable, not just character count. LLM and embedding
     limits are token-based, not character-based, and the token/char
     ratio isn't fixed. `length_fn` lets you pass a tokenizer (e.g.
     tiktoken) so max_chunk_length/min_overlap/max_overlap are measured
     in whatever unit actually matters for your downstream model.
     Defaults to character count so it works with zero configuration.

  5. A chunk must always add new content. Every chunk's end position is
     required to be strictly after the previous chunk's end — this is
     the fix for a real bug where an overlap-window boundary could
     coincide with a section's own natural boundary, producing a
     "chunk" that was just a re-serving of the previous chunk's tail
     with zero new information.

  6. No cross-section overlap. Overlap exists to preserve continuity of
     thought between adjacent chunks of the SAME topic. Overlapping
     across a heading boundary would just re-inject unrelated content,
     so overlap is only ever computed within a section.

This intentionally does NOT do LLM-generated context injection
(Contextual Retrieval) or long-context-embedding pooling (Late
Chunking) — those are embedding/generation-time techniques layered on
top of chunking, not chunking itself.
"""

import re
import bisect
from typing import Callable, Dict, List, Optional, Set, Tuple


# --------------------------------------------------------------------------
# Structural boundary detection (headings, paragraphs, sentences)
# --------------------------------------------------------------------------

# Markdown ATX headings only ("#" .. "######") — unambiguous syntax, no
# guessing. Pass your own `heading_pattern` for other formats.
_DEFAULT_HEADING_RE = re.compile(r'^(#{1,6})[ \t]+(\S.*?)\s*#*\s*$', re.MULTILINE)

_PARAGRAPH_BREAK_RE = re.compile(r'\n[ \t]*\n[ \t]*')
# Includes typographic ("smart") quotes alongside straight ones -- real-world
# text (Word, Docs, CMS exports) overwhelmingly uses curly quotes, and a
# sentence ending like `...them?" Or "...` was previously invisible to this
# regex because ? was followed by a curly ", not a straight one.
_SENTENCE_BREAK_RE = re.compile(r'[.!?]+(?=[\'"\)\]\u2018\u2019\u201c\u201d]*(?:\s|$))')


def _char_len(text: str) -> int:
    """Default length function: character count."""
    return len(text)


def _find_break_points(text: str) -> Tuple[List[int], List[int]]:
    """
    One pass over the text to find candidate 'end of paragraph' and 'end
    of sentence' positions. A position `p` means text[:p] is a clean,
    complete unit -- a good place to end a chunk, or (after skipping
    trailing whitespace) to start the next one.
    """
    paragraph_breaks = [m.start() for m in _PARAGRAPH_BREAK_RE.finditer(text)]
    sentence_breaks = [m.end() for m in _SENTENCE_BREAK_RE.finditer(text)]
    return paragraph_breaks, sentence_breaks


def _find_sections(
    text: str,
    use_headings: bool,
    heading_pattern: Optional[re.Pattern],
    heading_levels: Optional[Set[int]],
) -> List[Tuple[int, int, Optional[str], Optional[int]]]:
    """
    Split text into (start, end, title, level) sections at heading
    boundaries. If headings are disabled, none are found, or none match
    the requested levels, returns a single section spanning the whole
    text with title=None -- i.e. this degrades to "no sectioning" and
    the caller falls through to plain paragraph/sentence chunking.
    """
    if not use_headings:
        return [(0, len(text), None, None)]

    pattern = heading_pattern or _DEFAULT_HEADING_RE
    matches = list(pattern.finditer(text))

    headings = []
    for m in matches:
        if pattern is _DEFAULT_HEADING_RE:
            level = len(m.group(1))
            title = m.group(2).strip()
        else:
            # Custom pattern: whole match is the heading line; level unknown.
            level = None
            title = m.group(0).strip()
        if heading_levels is not None and level is not None and level not in heading_levels:
            continue
        headings.append((m.start(), title, level))

    if not headings:
        return [(0, len(text), None, None)]

    sections = []
    if headings[0][0] > 0:
        # Preamble text before the first heading (e.g. an intro paragraph).
        sections.append((0, headings[0][0], None, None))

    for i, (start, title, level) in enumerate(headings):
        end = headings[i + 1][0] if i + 1 < len(headings) else len(text)
        sections.append((start, end, title, level))

    return sections


def _merge_tiny_sections(
    text: str,
    sections: List[Tuple[int, int, Optional[str], Optional[int]]],
    min_section_length: int,
    length_fn: Callable[[str], int],
) -> List[Tuple[int, int, Optional[str]]]:
    """
    Greedily fold sections shorter than `min_section_length` into their
    neighbor, so a one-line heading with a single sentence under it
    doesn't become its own near-empty chunk. Titles of merged sections
    are joined with ' / ' so no information is silently dropped.
    """
    if min_section_length <= 0 or len(sections) <= 1:
        return [(s, e, t) for s, e, t, _ in sections]

    merged: List[Tuple[int, int, Optional[str]]] = []
    buf_start, buf_end, buf_titles = None, None, []

    for i, (start, end, title, _level) in enumerate(sections):
        if buf_start is None:
            buf_start, buf_end = start, end
            buf_titles = [title] if title else []
        else:
            buf_end = end
            if title:
                buf_titles.append(title)

        is_last = i == len(sections) - 1
        buf_len = length_fn(text[buf_start:buf_end])
        if buf_len >= min_section_length or is_last:
            merged.append((buf_start, buf_end, " / ".join(buf_titles) or None))
            buf_start = None

    # If the trailing merged section is still tiny, fold it into the one
    # before it rather than let it stand alone (it has nothing left to
    # merge forward into).
    if len(merged) > 1:
        last_start, last_end, last_title = merged[-1]
        if length_fn(text[last_start:last_end]) < min_section_length:
            prev_start, prev_end, prev_title = merged[-2]
            combined_title = " / ".join(t for t in (prev_title, last_title) if t) or None
            merged[-2:] = [(prev_start, last_end, combined_title)]

    return merged


# --------------------------------------------------------------------------
# Length-function-agnostic position search (binary search when length_fn
# isn't plain character count, so this generalizes to tokenizers without
# rescanning the whole text one character at a time)
# --------------------------------------------------------------------------

def _advance_by_length(
    text: str, start: int, hard_max: int, limit: int, length_fn: Callable[[str], int]
) -> int:
    """Largest `end` in [start, hard_max] such that length_fn(text[start:end]) <= limit."""
    if length_fn is _char_len:
        return min(start + limit, hard_max)
    lo, hi, best = start, hard_max, start
    while lo <= hi:
        mid = (lo + hi) // 2
        if length_fn(text[start:mid]) <= limit:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def _retreat_by_length(
    text: str, end: int, hard_min: int, limit: int, length_fn: Callable[[str], int]
) -> int:
    """Smallest `start` in [hard_min, end] such that length_fn(text[start:end]) <= limit."""
    if length_fn is _char_len:
        return max(end - limit, hard_min)
    lo, hi, best = hard_min, end, end
    while lo <= hi:
        mid = (lo + hi) // 2
        if length_fn(text[mid:end]) <= limit:
            best = mid
            hi = mid - 1
        else:
            lo = mid + 1
    return best


def _best_break_point(candidates: List[int], low: int, high: int) -> Optional[int]:
    """Largest candidate in [low, high] (pushes the chunk as close to the limit as possible)."""
    if not candidates or low > high:
        return None
    idx = bisect.bisect_right(candidates, high)
    if idx == 0:
        return None
    candidate = candidates[idx - 1]
    return candidate if candidate >= low else None


def _pick_chunk_end(
    paragraph_breaks: List[int], sentence_breaks: List[int],
    search_low: int, target_end: int, substantial_low: int,
) -> Tuple[Optional[int], Optional[str]]:
    """
    Try paragraph breaks, then sentence breaks. Within each tier, prefer a
    break that yields a *substantial* chunk (>= substantial_low), and only
    settle for a smaller one if that's genuinely the only option -- this
    is what stops "## Background" (a heading immediately followed by a
    blank line) from becoming its own near-empty chunk when a perfectly
    good sentence break exists a bit further in.
    """
    tiers = ((paragraph_breaks, "paragraph"), (sentence_breaks, "sentence"))

    # Pass 1: try BOTH tiers at the substantial threshold first, so a tiny
    # paragraph break doesn't win over a properly-sized sentence break.
    preferred_low = max(search_low, substantial_low)
    if preferred_low <= target_end:
        for candidates, label in tiers:
            c = _best_break_point(candidates, preferred_low, target_end)
            if c is not None:
                return c, label

    # Pass 2: nothing substantial anywhere -- accept whatever's available.
    for candidates, label in tiers:
        c = _best_break_point(candidates, search_low, target_end)
        if c is not None:
            return c, label
    return None, None


def _closest_break_point(candidates: List[int], low: int, high: int, target: float) -> Optional[int]:
    """Candidate in [low, high] closest to `target`."""
    if not candidates or low > high:
        return None
    lo_idx = bisect.bisect_left(candidates, low)
    hi_idx = bisect.bisect_right(candidates, high)
    window = candidates[lo_idx:hi_idx]
    if not window:
        return None
    return min(window, key=lambda c: abs(c - target))


def _skip_leading_whitespace(text: str, pos: int, hard_max: int) -> int:
    while pos < hard_max and text[pos] in ' \t\n\r':
        pos += 1
    return pos


def _closest_whitespace(text: str, low: int, high: int, target: float) -> Optional[int]:
    """
    Nearest whitespace character position in [low, high] to `target`. This
    is the safety net for choosing where the next chunk starts: if no
    paragraph or sentence break falls inside the overlap window, landing on
    *any* whitespace is still far better than a raw arithmetic position,
    which can slice through the middle of a word.
    """
    low = max(low, 0)
    high = min(high, len(text) - 1)
    if low > high:
        return None
    best, best_dist = None, None
    for i in range(low, high + 1):
        if text[i].isspace():
            d = abs(i - target)
            if best_dist is None or d < best_dist:
                best, best_dist = i, d
    return best


# --------------------------------------------------------------------------
# Section-scoped chunking (paragraph -> sentence -> whitespace -> hard cut)
# --------------------------------------------------------------------------

def _chunk_section(
    text: str,
    section_start: int,
    section_end: int,
    paragraph_breaks: List[int],
    sentence_breaks: List[int],
    max_chunk_length: int,
    min_overlap: int,
    max_overlap: int,
    length_fn: Callable[[str], int],
) -> List[Dict]:
    """
    Chunk a single section's text range, never reading past section_end
    and never overlapping past section_start. Guarantees every chunk's
    end is strictly after the previous chunk's end (no zero-content
    duplicate chunks -- see module docstring, point 5).
    """
    chunks: List[Dict] = []
    pos = section_start
    prev_end = section_start  # first chunk just needs to end after the section's own start

    while pos < section_end:
        search_low = max(pos + 1, prev_end + 1)
        remaining_len = length_fn(text[pos:section_end])

        if remaining_len <= max_chunk_length:
            chunk_end = section_end
            boundary_type = "end_of_section"
        else:
            target_end = _advance_by_length(text, pos, section_end, max_chunk_length, length_fn)
            substantial_low = _advance_by_length(
                text, pos, section_end, max(1, max_chunk_length // 5), length_fn
            )

            chunk_end, boundary_type = _pick_chunk_end(
                paragraph_breaks, sentence_breaks, search_low, target_end, substantial_low
            )

            if chunk_end is None:
                lookback_limit = max(search_low - 1, target_end - 100)
                ws_pos = None
                for i in range(min(target_end, section_end - 1), lookback_limit, -1):
                    if i >= search_low and text[i].isspace():
                        ws_pos = i
                        break
                if ws_pos is not None:
                    chunk_end = ws_pos
                    boundary_type = "whitespace"

            if chunk_end is None:
                chunk_end = max(target_end, search_low)
                boundary_type = "hard_cut"

        chunk_str = text[pos:chunk_end]
        chunks.append({
            "text": chunk_str,
            "start_char": pos,
            "end_char": chunk_end,
            "char_count": len(chunk_str),
            "length": length_fn(chunk_str),
            "boundary_type": boundary_type,
            "overlap_prev_text": "",
            "overlap_prev_chars": 0,
            "overlap_next_chars": 0,
        })

        prev_end = chunk_end
        if chunk_end >= section_end:
            break

        # Decide where the next chunk starts, i.e. how much overlap -- never
        # reaching before this chunk's own start (pos) or past section_end.
        earliest_start = _retreat_by_length(text, chunk_end, pos, max_overlap, length_fn)
        latest_start = _retreat_by_length(text, chunk_end, pos, min_overlap, length_fn)
        target_overlap_pos = (earliest_start + latest_start) / 2

        next_start = _closest_break_point(paragraph_breaks, earliest_start, latest_start, target_overlap_pos)
        if next_start is None:
            next_start = _closest_break_point(sentence_breaks, earliest_start, latest_start, target_overlap_pos)
        if next_start is None:
            next_start = _closest_whitespace(text, earliest_start, latest_start, target_overlap_pos)
        if next_start is None:
            next_start = int(round(target_overlap_pos))
            next_start = max(earliest_start, min(latest_start, next_start))

        next_start = _skip_leading_whitespace(text, next_start, section_end)
        if next_start <= pos:
            next_start = chunk_end  # guarantee forward progress

        chunks[-1]["overlap_next_chars"] = max(0, chunk_end - next_start)
        pos = next_start

    # Record each chunk's overlap with the previous one (within this section only).
    for i in range(1, len(chunks)):
        prev, cur = chunks[i - 1], chunks[i]
        if prev["end_char"] > cur["start_char"]:
            cur["overlap_prev_text"] = text[cur["start_char"]:prev["end_char"]]
            cur["overlap_prev_chars"] = len(cur["overlap_prev_text"])

    return chunks


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def chunk_text(
    text: str,
    source: Optional[str] = None,
    max_chunk_length: int = 1000,
    min_overlap: int = 100,
    max_overlap: int = 200,
    length_fn: Optional[Callable[[str], int]] = None,
    use_headings: bool = False,
    heading_pattern: Optional[re.Pattern] = None,
    heading_levels: Optional[Set[int]] = None,
    min_section_length: Optional[int] = None,
) -> List[Dict]:
    """
    Split `text` into overlapping, topic-respecting chunks.

    Two-level strategy:
      Level 1 (sectioning): split on Markdown headings, if present. Tiny
        sections get merged into a neighbor. A section that fits under
        max_chunk_length becomes exactly one chunk, however short --
        it's never padded out with unrelated neighboring content.
      Level 2 (sub-chunking): a section too long for one chunk is split
        at paragraph, then sentence, then whitespace boundaries, falling
        back to a hard cut only as a last resort. Overlap between
        consecutive chunks stays between min_overlap and max_overlap,
        and never crosses a section boundary.

    Parameters
    ----------
    text : str
        The source text.
    source : str, optional
        A name/path/URL identifying where `text` came from (e.g. a
        filename or document ID). When given, each chunk's `id` field
        becomes "{source}_{index}" -- a stable, source-qualified
        identifier, so chunks from different documents can share the
        same vector store or DB table without colliding on plain
        integer indices. Also stored as its own `source` field on every
        chunk for filtering/metadata purposes. If omitted, `id` falls
        back to the bare index.
    max_chunk_length, min_overlap, max_overlap : int
        Measured in whatever unit `length_fn` returns (characters by
        default). max_overlap must be < max_chunk_length.
    length_fn : Callable[[str], int], optional
        How to measure length. Defaults to character count. Pass a
        tokenizer-backed function (e.g. `lambda t: len(enc.encode(t))`
        using tiktoken) to make the limits token-based instead.
    use_headings : bool
        If False, skip sectioning entirely and chunk the whole document
        as plain paragraph/sentence text (old behavior).
    heading_pattern : re.Pattern, optional
        Overrides the default Markdown ATX-heading detector (`^#{1,6} `).
        Use this for other formats (e.g. a regex matching pre-tagged
        headings extracted from HTML/docx).
    heading_levels : set[int], optional
        Restrict sectioning to specific Markdown heading levels (e.g.
        {1, 2} to ignore h3-h6). Only meaningful with the default
        pattern, which reports levels; a custom pattern reports no level
        and is unaffected by this filter. None = all levels count.
    min_section_length : int, optional
        Sections shorter than this get merged into a neighboring
        section. Defaults to max_chunk_length // 5 (~20%). Set to 0 to
        disable merging.

    Returns
    -------
    List[dict], one per chunk:
        id                     : "{source}_{index}" if source is given,
                                  else str(index) -- a unique, stable
                                  identifier suitable for use as a
                                  vector-store or DB primary key
        source                 : the `source` argument, unchanged (None
                                  if not given)
        index, total_chunks   : position in the overall sequence
        text                  : the chunk's text
        start_char, end_char  : [start, end) offsets into the original text
        char_count            : character length (always available)
        length                : length_fn(text) -- matches your limits' unit
        section_index          : which section this chunk belongs to (0-based)
        section_title          : heading text for that section, or None
        chunk_index_in_section : position within its own section (0-based)
        boundary_type          : "end_of_section" | "paragraph" | "sentence"
                                  | "whitespace" | "hard_cut"
        overlap_prev_text/chars: text and length shared with the previous
                                  chunk (0/"" for a section's first chunk --
                                  overlap never crosses section boundaries)
        overlap_next_chars     : trailing chars of this chunk repeated at
                                  the start of the next one (0 for a
                                  section's last chunk)
        source_text_length     : len(original text)
    """
    if not text:
        return []
    if max_chunk_length <= 0:
        raise ValueError("max_chunk_length must be positive")
    if min_overlap < 0 or max_overlap < 0:
        raise ValueError("overlap values must be non-negative")
    if min_overlap > max_overlap:
        raise ValueError("min_overlap cannot exceed max_overlap")
    if max_overlap >= max_chunk_length:
        raise ValueError("max_overlap must be smaller than max_chunk_length")

    length_fn = length_fn or _char_len
    if min_section_length is None:
        min_section_length = max_chunk_length // 5

    paragraph_breaks, sentence_breaks = _find_break_points(text)

    raw_sections = _find_sections(text, use_headings, heading_pattern, heading_levels)
    sections = _merge_tiny_sections(text, raw_sections, min_section_length, length_fn)

    all_chunks: List[Dict] = []
    for section_index, (sec_start, sec_end, sec_title) in enumerate(sections):
        section_chunks = _chunk_section(
            text, sec_start, sec_end, paragraph_breaks, sentence_breaks,
            max_chunk_length, min_overlap, max_overlap, length_fn,
        )
        for chunk_index_in_section, c in enumerate(section_chunks):
            c["section_index"] = section_index
            c["section_title"] = sec_title
            c["chunk_index_in_section"] = chunk_index_in_section
            all_chunks.append(c)

    total_chunks = len(all_chunks)
    for i, c in enumerate(all_chunks):
        c["id"] = f"{source}_{i}" if source is not None else str(i)
        c["source"] = source
        c["index"] = i
        c["total_chunks"] = total_chunks
        c["source_text_length"] = len(text)
        # Reorder for a friendlier dict repr (purely cosmetic).
        ordered = {}
        for key in ("id", "source", "index", "total_chunks", "text", "start_char", "end_char",
                    "char_count", "length", "section_index", "section_title",
                    "chunk_index_in_section", "boundary_type",
                    "overlap_prev_text", "overlap_prev_chars", "overlap_next_chars",
                    "source_text_length"):
            ordered[key] = c[key]
        all_chunks[i] = ordered

    return all_chunks