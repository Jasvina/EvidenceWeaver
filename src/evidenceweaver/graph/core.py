from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Iterable


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "did",
    "does",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "to",
    "what",
    "why",
    "with",
}

NEGATION_TOKENS = {
    "cannot",
    "failed",
    "fails",
    "failing",
    "lack",
    "lacks",
    "lacking",
    "missing",
    "never",
    "no",
    "none",
    "not",
    "without",
}


def _expect_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def _expect_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return value


def _expect_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _expect_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    return tuple(_expect_string(item, f"{field_name}[]") for item in _expect_list(value, field_name))


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _tokenize(text: str) -> tuple[str, ...]:
    return tuple(token for token in _normalize(text).split() if token and token not in STOPWORDS)


def _jaccard(lhs: set[str], rhs: set[str]) -> float:
    if not lhs or not rhs:
        return 0.0
    union = lhs | rhs
    if not union:
        return 0.0
    return len(lhs & rhs) / len(union)


def _content_tokens(text: str) -> set[str]:
    return {token for token in _tokenize(text) if token not in NEGATION_TOKENS}


def _has_negation(text: str) -> bool:
    return bool(set(_tokenize(text)) & NEGATION_TOKENS)


def _contradiction_overlap(lhs_text: str, rhs_text: str) -> float:
    return _jaccard(_content_tokens(lhs_text), _content_tokens(rhs_text))


@dataclass(frozen=True, slots=True)
class SourceNode:
    source_id: str
    title: str
    url: str
    source_type: str = "snapshot"
    opened: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceNode":
        return cls(
            source_id=_expect_string(data.get("source_id"), "evidence_graph.source_nodes[].source_id"),
            title=_expect_string(data.get("title"), "evidence_graph.source_nodes[].title"),
            url=_expect_string(data.get("url"), "evidence_graph.source_nodes[].url"),
            source_type=str(data.get("source_type", "snapshot")),
            opened=_expect_bool(data.get("opened", False), "evidence_graph.source_nodes[].opened"),
        )


@dataclass(frozen=True, slots=True)
class ClaimNode:
    claim_id: str
    text: str
    citations: tuple[str, ...] = ()
    focus_tokens: tuple[str, ...] = ()
    status: str = "supported"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClaimNode":
        return cls(
            claim_id=_expect_string(data.get("claim_id"), "evidence_graph.claim_nodes[].claim_id"),
            text=_expect_string(data.get("text"), "evidence_graph.claim_nodes[].text"),
            citations=_string_tuple(data.get("citations", []), "evidence_graph.claim_nodes[].citations"),
            focus_tokens=_string_tuple(data.get("focus_tokens", []), "evidence_graph.claim_nodes[].focus_tokens"),
            status=str(data.get("status", "supported")),
        )


@dataclass(frozen=True, slots=True)
class GraphEdge:
    edge_id: str
    kind: str
    from_id: str
    to_id: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphEdge":
        return cls(
            edge_id=_expect_string(data.get("edge_id"), "evidence_graph.edges[].edge_id"),
            kind=_expect_string(data.get("kind"), "evidence_graph.edges[].kind"),
            from_id=_expect_string(data.get("from_id"), "evidence_graph.edges[].from_id"),
            to_id=_expect_string(data.get("to_id"), "evidence_graph.edges[].to_id"),
        )


@dataclass(frozen=True, slots=True)
class OpenQuestion:
    question_id: str
    text: str
    focus_tokens: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OpenQuestion":
        return cls(
            question_id=_expect_string(data.get("question_id"), "evidence_graph.open_questions[].question_id"),
            text=_expect_string(data.get("text"), "evidence_graph.open_questions[].text"),
            focus_tokens=_string_tuple(data.get("focus_tokens", []), "evidence_graph.open_questions[].focus_tokens"),
        )


@dataclass(frozen=True, slots=True)
class EvidenceGraph:
    graph_id: str
    prompt_focus: tuple[str, ...]
    source_nodes: tuple[SourceNode, ...]
    claim_nodes: tuple[ClaimNode, ...]
    edges: tuple[GraphEdge, ...]
    open_questions: tuple[OpenQuestion, ...] = ()

    @property
    def opened_source_ids(self) -> tuple[str, ...]:
        return tuple(node.source_id for node in self.source_nodes if node.opened)

    @property
    def supported_claim_ids(self) -> tuple[str, ...]:
        claim_ids: list[str] = []
        for claim in self.claim_nodes:
            if claim.citations:
                claim_ids.append(claim.claim_id)
        return tuple(claim_ids)

    @property
    def unsupported_claim_ids(self) -> tuple[str, ...]:
        return tuple(claim.claim_id for claim in self.claim_nodes if not claim.citations)

    @property
    def contradicted_claim_ids(self) -> tuple[str, ...]:
        claim_ids: list[str] = []
        seen_ids: set[str] = set()
        claim_node_ids = {claim.claim_id for claim in self.claim_nodes}
        for edge in self.edges:
            if edge.kind != "contradicts":
                continue
            for claim_id in (edge.from_id, edge.to_id):
                if claim_id in claim_node_ids and claim_id not in seen_ids:
                    seen_ids.add(claim_id)
                    claim_ids.append(claim_id)
        return tuple(claim_ids)

    @property
    def covered_focus_tokens(self) -> tuple[str, ...]:
        tokens: list[str] = []
        for claim in self.claim_nodes:
            for token in claim.focus_tokens:
                if token not in tokens:
                    tokens.append(token)
        return tuple(tokens)

    @property
    def prompt_focus_coverage_ratio(self) -> float:
        if not self.prompt_focus:
            return 1.0
        return len(self.covered_focus_tokens) / len(self.prompt_focus)

    @property
    def opened_source_count(self) -> int:
        return len(self.opened_source_ids)

    @property
    def edge_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for edge in self.edges:
            counts[edge.kind] = counts.get(edge.kind, 0) + 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceGraph":
        return cls(
            graph_id=_expect_string(data.get("graph_id"), "evidence_graph.graph_id"),
            prompt_focus=_string_tuple(data.get("prompt_focus", []), "evidence_graph.prompt_focus"),
            source_nodes=tuple(
                SourceNode.from_dict(_expect_mapping(item, "evidence_graph.source_nodes[]"))
                for item in _expect_list(data.get("source_nodes", []), "evidence_graph.source_nodes")
            ),
            claim_nodes=tuple(
                ClaimNode.from_dict(_expect_mapping(item, "evidence_graph.claim_nodes[]"))
                for item in _expect_list(data.get("claim_nodes", []), "evidence_graph.claim_nodes")
            ),
            edges=tuple(
                GraphEdge.from_dict(_expect_mapping(item, "evidence_graph.edges[]"))
                for item in _expect_list(data.get("edges", []), "evidence_graph.edges")
            ),
            open_questions=tuple(
                OpenQuestion.from_dict(_expect_mapping(item, "evidence_graph.open_questions[]"))
                for item in _expect_list(data.get("open_questions", []), "evidence_graph.open_questions")
            ),
        )


class EvidenceGraphBuilder:
    """Mutable builder used by the baseline agent while it explores a task."""

    def __init__(self, graph_id: str, prompt: str, documents: Iterable[Any]) -> None:
        prompt_focus = tuple(dict.fromkeys(_tokenize(prompt)))
        self.graph_id = graph_id
        self.prompt_focus = prompt_focus
        self._covered_focus_tokens: set[str] = set()
        self._source_nodes: dict[str, SourceNode] = {}
        self._claim_nodes: list[ClaimNode] = []
        self._edges: list[GraphEdge] = []
        self._open_questions: list[OpenQuestion] = []
        for document in documents:
            source_id = getattr(document, "doc_id")
            self._source_nodes[source_id] = SourceNode(
                source_id=source_id,
                title=getattr(document, "title"),
                url=getattr(document, "url"),
                source_type=str(getattr(document, "source_type", "snapshot")),
                opened=False,
            )

    @property
    def uncovered_focus_tokens(self) -> tuple[str, ...]:
        return tuple(token for token in self.prompt_focus if token not in self._covered_focus_tokens)

    def mark_source_opened(self, source_id: str) -> None:
        node = self._source_nodes[source_id]
        self._source_nodes[source_id] = SourceNode(
            source_id=node.source_id,
            title=node.title,
            url=node.url,
            source_type=node.source_type,
            opened=True,
        )

    def add_claim(self, claim_id: str, text: str, citations: Iterable[str] = ()) -> ClaimNode:
        citation_tuple = tuple(dict.fromkeys(citations))
        focus_tokens = tuple(token for token in self.prompt_focus if token in set(_tokenize(text)))
        status = "supported" if citation_tuple else "unsupported"
        claim_node = ClaimNode(
            claim_id=claim_id,
            text=text,
            citations=citation_tuple,
            focus_tokens=focus_tokens,
            status=status,
        )
        self._claim_nodes.append(claim_node)
        self._covered_focus_tokens.update(focus_tokens)
        for citation in citation_tuple:
            self._edges.append(
                GraphEdge(
                    edge_id=f"edge-{len(self._edges) + 1}",
                    kind="supports",
                    from_id=citation,
                    to_id=claim_id,
                )
            )
        self._refresh_relationship_edges()
        return claim_node

    def add_open_question(self, text: str, focus_tokens: Iterable[str]) -> OpenQuestion:
        question = OpenQuestion(
            question_id=f"question-{len(self._open_questions) + 1}",
            text=text,
            focus_tokens=tuple(dict.fromkeys(focus_tokens)),
        )
        self._open_questions.append(question)
        return question

    def refresh_open_questions(self, max_tokens: int = 6) -> None:
        uncovered = self.uncovered_focus_tokens
        self._open_questions = []
        if uncovered:
            self.add_open_question(
                text=f"Need stronger support for prompt focus terms: {', '.join(uncovered[:max_tokens])}",
                focus_tokens=uncovered[:max_tokens],
            )

    def _refresh_relationship_edges(self) -> None:
        support_edges = [edge for edge in self._edges if edge.kind == "supports"]
        relationship_edges: list[GraphEdge] = []
        for index, current in enumerate(self._claim_nodes):
            current_tokens = set(_tokenize(current.text))
            current_citations = set(current.citations)
            for previous in self._claim_nodes[:index]:
                previous_tokens = set(_tokenize(previous.text))
                previous_citations = set(previous.citations)
                token_overlap = _jaccard(current_tokens, previous_tokens)
                contradiction_overlap = _contradiction_overlap(current.text, previous.text)
                focus_overlap = set(current.focus_tokens) & set(previous.focus_tokens)
                citation_overlap = current_citations & previous_citations
                kind = None
                if (
                    _has_negation(current.text) != _has_negation(previous.text)
                    and contradiction_overlap >= 0.6
                    and (focus_overlap or token_overlap >= 0.45)
                ):
                    kind = "contradicts"
                elif citation_overlap and token_overlap >= 0.65:
                    kind = "duplicates"
                elif (citation_overlap and focus_overlap) or token_overlap >= 0.35:
                    kind = "derived_from"
                if kind is not None:
                    relationship_edges.append(
                        GraphEdge(
                            edge_id=f"edge-{len(support_edges) + len(relationship_edges) + 1}",
                            kind=kind,
                            from_id=current.claim_id,
                            to_id=previous.claim_id,
                        )
                    )
        self._edges = support_edges + relationship_edges

    def build(self) -> EvidenceGraph:
        ordered_sources = tuple(self._source_nodes[source_id] for source_id in sorted(self._source_nodes))
        return EvidenceGraph(
            graph_id=self.graph_id,
            prompt_focus=self.prompt_focus,
            source_nodes=ordered_sources,
            claim_nodes=tuple(self._claim_nodes),
            edges=tuple(self._edges),
            open_questions=tuple(self._open_questions),
        )
