from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from evidenceweaver.eval.offline import evaluate_run
from evidenceweaver.graph import EvidenceGraphBuilder
from evidenceweaver.models import Action, Document, GeneratedClaim, RunArtifact, TaskBundle, load_task_bundle


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "do",
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

SIGNAL_FRAGMENTS = (
    "because",
    "failure",
    "collapse",
    "stabil",
    "mitig",
    "proposes",
    "introduces",
    "diagnos",
    "filter",
    "compare",
    "decoupling",
    "asynchronous",
    "framework",
    "citation",
    "ground",
    "factuality",
    "comprehensiveness",
    "tool calls",
    "hundred",
    "multi turn",
    "long horizon",
)


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _tokenize(text: str) -> tuple[str, ...]:
    return tuple(token for token in _normalize(text).split() if token and token not in STOPWORDS)


def _sentence_split(text: str) -> list[str]:
    candidates = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    return candidates or [text.strip()]


def _overlap_score(query_tokens: set[str], text: str) -> float:
    text_tokens = set(_tokenize(text))
    if not query_tokens or not text_tokens:
        return 0.0
    shared = len(query_tokens & text_tokens)
    coverage = shared / max(1, len(query_tokens))
    density = shared / max(1, len(text_tokens))
    return (0.7 * coverage) + (0.3 * density)


def _dedupe_key(text: str) -> str:
    return _normalize(text)


def _signal_bonus(text: str) -> float:
    normalized = _normalize(text)
    return sum(0.3 for fragment in SIGNAL_FRAGMENTS if fragment in normalized)


@dataclass(frozen=True, slots=True)
class SearchHit:
    document: Document
    score: float


class SnapshotEnvironment:
    """A tiny snapshot environment that supports search and open actions."""

    def __init__(self, task: TaskBundle) -> None:
        self.task = task
        self.steps = 0
        self.document_reads = 0

    def _consume_step(self) -> None:
        self.steps += 1

    def search(self, query: str, limit: int = 5) -> list[SearchHit]:
        self._consume_step()
        query_tokens = set(_tokenize(query))
        hits = [
            SearchHit(
                document=document,
                score=_overlap_score(query_tokens, f"{document.title}. {document.content}"),
            )
            for document in self.task.documents
        ]
        ranked_hits = sorted(hits, key=lambda hit: (-hit.score, hit.document.doc_id))
        return ranked_hits[:limit]

    def open(self, doc_id: str) -> Document:
        self._consume_step()
        self.document_reads += 1
        for document in self.task.documents:
            if document.doc_id == doc_id:
                return document
        raise KeyError(f"unknown document id: {doc_id}")


class BaselineAgent:
    """A simple deterministic search-read-write baseline for snapshot tasks."""

    def __init__(self, max_docs: int | None = None, max_claims: int | None = None) -> None:
        self.max_docs = max_docs
        self.max_claims = max_claims

    def _select_documents(self, task: TaskBundle, hits: list[SearchHit]) -> list[Document]:
        budget_reads = task.budget.max_document_reads if task.budget and task.budget.max_document_reads else len(task.documents)
        max_docs = min(self.max_docs or 3, budget_reads, len(hits))
        return [hit.document for hit in hits[:max_docs]]

    def _select_claims(self, task: TaskBundle, documents: Iterable[Document], graph: EvidenceGraphBuilder) -> list[GeneratedClaim]:
        prompt_tokens = set(_tokenize(task.prompt))
        document_list = list(documents)
        sentence_pool: list[tuple[set[str], float, str, str]] = []
        for document in document_list:
            for sentence in _sentence_split(document.content):
                sentence_tokens = set(_tokenize(sentence))
                score = _overlap_score(prompt_tokens, sentence) + _signal_bonus(sentence) + (0.1 if len(sentence) <= 260 else 0.0)
                sentence_pool.append((sentence_tokens, score, sentence.strip(), document.doc_id))

        max_steps = task.budget.max_steps if task.budget else 8
        open_count = len(document_list)
        max_claim_budget = max(1, max_steps - open_count - 2)
        max_claims = min(self.max_claims or max_claim_budget, max_claim_budget)

        claims: list[GeneratedClaim] = []
        seen: set[str] = set()
        remaining_tokens = set(graph.uncovered_focus_tokens) or set(prompt_tokens)
        while sentence_pool and len(claims) < max_claims:
            best_index = None
            best_score = None
            for index, (sentence_tokens, base_score, sentence, doc_id) in enumerate(sentence_pool):
                novelty = len(sentence_tokens & remaining_tokens)
                score = (1.5 * novelty) + base_score
                if best_score is None or score > best_score:
                    best_score = score
                    best_index = index
            assert best_index is not None
            sentence_tokens, _, sentence, doc_id = sentence_pool.pop(best_index)
            key = _dedupe_key(sentence)
            if not sentence or key in seen:
                continue
            seen.add(key)
            remaining_tokens -= sentence_tokens
            claims.append(
                GeneratedClaim(
                    claim_id=f"claim-{len(claims) + 1}",
                    text=sentence if sentence.endswith((".", "!", "?")) else f"{sentence}.",
                    citations=(doc_id,),
                )
            )
            graph.add_claim(claims[-1].claim_id, claims[-1].text, claims[-1].citations)
            remaining_tokens = set(graph.uncovered_focus_tokens) or set(prompt_tokens)
        return claims

    def run(self, task: TaskBundle, run_id: str | None = None) -> RunArtifact:
        environment = SnapshotEnvironment(task)
        graph = EvidenceGraphBuilder(graph_id=f"graph-{task.task_id}", prompt=task.prompt, documents=task.documents)
        actions: list[Action] = []

        search_query = task.prompt
        hits = environment.search(search_query, limit=5)
        actions.append(Action(kind="search", argument=search_query))

        documents = self._select_documents(task, hits)
        for document in documents:
            environment.open(document.doc_id)
            graph.mark_source_opened(document.doc_id)
            actions.append(Action(kind="open", argument=document.title, document_ids=(document.doc_id,)))

        claims = self._select_claims(task, documents, graph)
        for claim in claims:
            actions.append(Action(kind="write_claim", argument=claim.text, document_ids=claim.citations))

        final_citations = tuple(dict.fromkeys(doc_id for claim in claims for doc_id in claim.citations))
        answer = " ".join(claim.text for claim in claims) if claims else "No grounded answer could be composed from the available snapshot."
        uncovered = graph.uncovered_focus_tokens
        if uncovered:
            graph.add_open_question(
                text=f"Need stronger support for prompt focus terms: {', '.join(uncovered[:6])}",
                focus_tokens=uncovered[:6],
            )
        actions.append(Action(kind="finish", argument="return cited answer", document_ids=final_citations))

        run = RunArtifact(
            schema_version="run-artifact.v0",
            run_id=run_id or f"baseline-{task.task_id}",
            task_id=task.task_id,
            answer=answer,
            claims=tuple(claims),
            actions=tuple(actions),
            final_citations=final_citations,
            evidence_graph=graph.build(),
        )
        report = evaluate_run(task, run)
        return run.with_reward_bundle(report.to_reward_bundle())


def run_task(task_path: str | Path, run_id: str | None = None, max_docs: int | None = None, max_claims: int | None = None) -> RunArtifact:
    task = load_task_bundle(task_path)
    agent = BaselineAgent(max_docs=max_docs, max_claims=max_claims)
    return agent.run(task, run_id=run_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the EvidenceWeaver deterministic baseline agent on a task bundle")
    parser.add_argument("task", help="Path to a task bundle JSON file")
    parser.add_argument("-o", "--output", help="Optional path to write the run artifact JSON")
    parser.add_argument("--run-id", help="Optional run identifier override")
    parser.add_argument("--max-docs", type=int, default=None, help="Maximum number of documents to read")
    parser.add_argument("--max-claims", type=int, default=None, help="Maximum number of claims to emit")
    args = parser.parse_args()

    run = run_task(args.task, run_id=args.run_id, max_docs=args.max_docs, max_claims=args.max_claims)
    payload = json.dumps(run.to_dict(), indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
