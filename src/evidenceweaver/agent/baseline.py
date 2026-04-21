from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from evidenceweaver.eval.offline import evaluate_run
from evidenceweaver.graph import EvidenceGraphBuilder
from evidenceweaver.models import Action, Document, GeneratedClaim, RunArtifact, RunDiagnostics, TaskBundle, load_task_bundle
from evidenceweaver.reward.compose import compose_reward_bundle, reward_notes


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
    "test time scaling",
    "tool augmented",
    "lsp",
    "repository state",
    "executable tests",
    "verifiable",
    "issue resolution",
    "real repositories",
    "environment feedback",
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


@dataclass(frozen=True, slots=True)
class BaselineAgentConfig:
    max_docs: int = 3
    max_claims: int = 4
    search_limit: int = 5
    initial_doc_cap: int = 3
    followup_doc_limit: int = 1
    novelty_weight: float = 1.5
    signal_bonus_weight: float = 1.0
    sentence_length_bonus: float = 0.1
    followup_min_total_budget: int = 9


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

    def __init__(
        self,
        max_docs: int | None = None,
        max_claims: int | None = None,
        config: BaselineAgentConfig | None = None,
    ) -> None:
        base = config or BaselineAgentConfig()
        resolved_max_docs = max_docs if max_docs is not None else base.max_docs
        resolved_max_claims = max_claims if max_claims is not None else base.max_claims
        self.config = BaselineAgentConfig(
            max_docs=resolved_max_docs,
            max_claims=resolved_max_claims,
            search_limit=base.search_limit,
            initial_doc_cap=base.initial_doc_cap,
            followup_doc_limit=base.followup_doc_limit,
            novelty_weight=base.novelty_weight,
            signal_bonus_weight=base.signal_bonus_weight,
            sentence_length_bonus=base.sentence_length_bonus,
            followup_min_total_budget=base.followup_min_total_budget,
        )

    def _select_documents(self, task: TaskBundle, hits: list[SearchHit], opened_doc_ids: set[str], limit: int) -> list[Document]:
        budget_reads = task.budget.max_document_reads if task.budget and task.budget.max_document_reads else len(task.documents)
        max_docs = min(limit, budget_reads, len(hits))
        selected: list[Document] = []
        for hit in hits:
            if hit.document.doc_id in opened_doc_ids:
                continue
            selected.append(hit.document)
            if len(selected) >= max_docs:
                break
        return selected

    def _select_claims(
        self,
        task: TaskBundle,
        documents: Iterable[Document],
        graph: EvidenceGraphBuilder,
        seen_claim_texts: set[str],
        start_index: int,
        max_claims: int,
    ) -> list[GeneratedClaim]:
        prompt_tokens = set(_tokenize(task.prompt))
        document_list = list(documents)
        sentence_pool: list[tuple[set[str], float, str, str]] = []
        for document in document_list:
            sentences = _sentence_split(document.content)
            for index, sentence in enumerate(sentences):
                sentence_tokens = set(_tokenize(sentence))
                score = (
                    _overlap_score(prompt_tokens, sentence)
                    + (self.config.signal_bonus_weight * _signal_bonus(sentence))
                    + (self.config.sentence_length_bonus if len(sentence) <= 260 else 0.0)
                )
                sentence_pool.append((sentence_tokens, score, sentence.strip(), document.doc_id))
                if index + 1 < len(sentences):
                    combined = f"{sentence.strip()} {sentences[index + 1].strip()}"
                    combined_tokens = set(_tokenize(combined))
                    combined_score = (
                        _overlap_score(prompt_tokens, combined)
                        + (self.config.signal_bonus_weight * _signal_bonus(combined))
                        + (self.config.sentence_length_bonus if len(combined) <= 320 else 0.0)
                    )
                    sentence_pool.append((combined_tokens, combined_score, combined.strip(), document.doc_id))

        claims: list[GeneratedClaim] = []
        remaining_tokens = set(graph.uncovered_focus_tokens) or set(prompt_tokens)
        while sentence_pool and len(claims) < max_claims:
            best_index = None
            best_score = None
            for index, (sentence_tokens, base_score, sentence, doc_id) in enumerate(sentence_pool):
                novelty = len(sentence_tokens & remaining_tokens)
                score = (self.config.novelty_weight * novelty) + base_score
                if best_score is None or score > best_score:
                    best_score = score
                    best_index = index
            assert best_index is not None
            sentence_tokens, _, sentence, doc_id = sentence_pool.pop(best_index)
            key = _dedupe_key(sentence)
            if not sentence or key in seen_claim_texts:
                continue
            seen_claim_texts.add(key)
            remaining_tokens -= sentence_tokens
            claims.append(
                GeneratedClaim(
                    claim_id=f"claim-{start_index + len(claims)}",
                    text=sentence if sentence.endswith((".", "!", "?")) else f"{sentence}.",
                    citations=(doc_id,),
                )
            )
            graph.add_claim(claims[-1].claim_id, claims[-1].text, claims[-1].citations)
            remaining_tokens = set(graph.uncovered_focus_tokens) or set(prompt_tokens)
        return claims

    def _remaining_read_budget(self, task: TaskBundle, opened_doc_ids: set[str]) -> int:
        max_reads = task.budget.max_document_reads if task.budget and task.budget.max_document_reads else len(task.documents)
        return max(0, max_reads - len(opened_doc_ids))

    def _remaining_action_budget(self, task: TaskBundle, actions: list[Action]) -> int:
        max_steps = task.budget.max_steps if task.budget else 8
        return max(0, max_steps - len(actions))

    def _build_follow_up_query(self, graph: EvidenceGraphBuilder) -> str | None:
        uncovered = graph.uncovered_focus_tokens
        if not uncovered:
            return None
        return "evidence for " + " ".join(uncovered[:6])

    def run(self, task: TaskBundle, run_id: str | None = None) -> RunArtifact:
        environment = SnapshotEnvironment(task)
        graph = EvidenceGraphBuilder(graph_id=f"graph-{task.task_id}", prompt=task.prompt, documents=task.documents)
        actions: list[Action] = []
        opened_doc_ids: set[str] = set()
        seen_claim_texts: set[str] = set()
        claims: list[GeneratedClaim] = []
        search_queries: list[str] = []
        iteration_count = 0

        while self._remaining_action_budget(task, actions) > 1:
            if iteration_count == 0:
                search_query = task.prompt
            else:
                search_query = self._build_follow_up_query(graph)
                if not search_query:
                    break

            iteration_count += 1
            hits = environment.search(search_query, limit=self.config.search_limit)
            search_queries.append(search_query)
            actions.append(Action(kind="search", argument=search_query))

            remaining_reads = self._remaining_read_budget(task, opened_doc_ids)
            if remaining_reads <= 0:
                break
            remaining_action_budget = self._remaining_action_budget(task, actions)
            if remaining_action_budget <= 1:
                break
            if iteration_count == 1:
                total_budget = task.budget.max_steps if task.budget else 8
                allow_follow_up = total_budget >= self.config.followup_min_total_budget and remaining_reads > 0 and len(task.documents) > 2
                initial_doc_cap = self.config.initial_doc_cap if allow_follow_up else self.config.max_docs
                target_doc_limit = min(initial_doc_cap, remaining_reads, max(1, remaining_action_budget - 1))
            else:
                target_doc_limit = min(self.config.followup_doc_limit, remaining_reads, max(1, remaining_action_budget - 1))
            documents = self._select_documents(task, hits, opened_doc_ids, limit=target_doc_limit)
            if not documents:
                break

            for document in documents:
                if self._remaining_action_budget(task, actions) <= 1:
                    break
                environment.open(document.doc_id)
                opened_doc_ids.add(document.doc_id)
                graph.mark_source_opened(document.doc_id)
                actions.append(Action(kind="open", argument=document.title, document_ids=(document.doc_id,)))

            documents = [document for document in documents if document.doc_id in opened_doc_ids]
            if not documents:
                break

            remaining_unopened_docs = self._remaining_read_budget(task, opened_doc_ids)
            reserve_actions = 1  # reserve finish
            total_budget = task.budget.max_steps if task.budget else 8
            if iteration_count == 1 and remaining_unopened_docs > 0 and total_budget >= self.config.followup_min_total_budget:
                reserve_actions += 4  # reserve search + open + one follow-up claim path
            remaining_claim_budget = max(0, self._remaining_action_budget(task, actions) - reserve_actions)
            if remaining_claim_budget <= 0:
                break
            new_claims = self._select_claims(
                task,
                documents,
                graph,
                seen_claim_texts=seen_claim_texts,
                start_index=len(claims) + 1,
                max_claims=remaining_claim_budget,
            )
            for claim in new_claims:
                claims.append(claim)
                actions.append(Action(kind="write_claim", argument=claim.text, document_ids=claim.citations))

            graph.refresh_open_questions()
            if not new_claims and iteration_count > 1:
                break
            if not graph.uncovered_focus_tokens:
                break

        final_citations = tuple(dict.fromkeys(doc_id for claim in claims for doc_id in claim.citations))
        answer = " ".join(claim.text for claim in claims) if claims else "No grounded answer could be composed from the available snapshot."
        graph.refresh_open_questions()
        actions.append(Action(kind="finish", argument="return cited answer", document_ids=final_citations))

        evidence_graph = graph.build()
        diagnostics = RunDiagnostics(
            search_queries=tuple(search_queries),
            iteration_count=iteration_count,
            opened_source_ids=evidence_graph.opened_source_ids,
            opened_source_count=evidence_graph.opened_source_count,
            claim_count=len(claims),
            covered_prompt_focus_ratio=round(evidence_graph.prompt_focus_coverage_ratio, 4),
            uncovered_focus_tokens=evidence_graph.open_questions[0].focus_tokens if evidence_graph.open_questions else (),
            notes=tuple(
                note
                for note in [
                    "follow-up search executed" if iteration_count > 1 else "",
                    "remaining prompt focus tokens unresolved" if evidence_graph.open_questions else "",
                ]
                if note
            ),
        )

        run = RunArtifact(
            schema_version="run-artifact.v0",
            run_id=run_id or f"baseline-{task.task_id}",
            task_id=task.task_id,
            answer=answer,
            claims=tuple(claims),
            actions=tuple(actions),
            final_citations=final_citations,
            evidence_graph=evidence_graph,
            diagnostics=diagnostics,
        )
        report = evaluate_run(task, run)
        enriched_diagnostics = RunDiagnostics(
            search_queries=diagnostics.search_queries,
            iteration_count=diagnostics.iteration_count,
            opened_source_ids=diagnostics.opened_source_ids,
            opened_source_count=diagnostics.opened_source_count,
            claim_count=diagnostics.claim_count,
            covered_prompt_focus_ratio=diagnostics.covered_prompt_focus_ratio,
            uncovered_focus_tokens=diagnostics.uncovered_focus_tokens,
            notes=tuple(dict.fromkeys((*diagnostics.notes, *reward_notes(report)))),
        )
        return run.with_diagnostics(enriched_diagnostics).with_reward_bundle(compose_reward_bundle(report))


def run_task(
    task_path: str | Path,
    run_id: str | None = None,
    max_docs: int | None = None,
    max_claims: int | None = None,
    config: BaselineAgentConfig | None = None,
) -> RunArtifact:
    task = load_task_bundle(task_path)
    agent = BaselineAgent(max_docs=max_docs, max_claims=max_claims, config=config)
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
