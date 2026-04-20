from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


class ValidationError(ValueError):
    """Raised when a benchmark or run artifact does not match the expected shape."""


def _expect_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{field_name} must be an object")
    return value


def _expect_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{field_name} must be a list")
    return value


def _expect_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} must be a non-empty string")
    return value


def _expect_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError(f"{field_name} must be an integer")
    return value


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    return tuple(_expect_string(item, f"{field_name}[]") for item in _expect_list(value, field_name))


@dataclass(frozen=True, slots=True)
class Budget:
    max_steps: int
    max_document_reads: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Budget":
        max_steps = _expect_int(data.get("max_steps"), "budget.max_steps")
        raw_reads = data.get("max_document_reads")
        if raw_reads is None:
            max_document_reads = None
        else:
            max_document_reads = _expect_int(raw_reads, "budget.max_document_reads")
        return cls(max_steps=max_steps, max_document_reads=max_document_reads)


@dataclass(frozen=True, slots=True)
class Document:
    doc_id: str
    title: str
    url: str
    content: str
    source_type: str = "snapshot"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Document":
        return cls(
            doc_id=_expect_string(data.get("doc_id"), "documents[].doc_id"),
            title=_expect_string(data.get("title"), "documents[].title"),
            url=_expect_string(data.get("url"), "documents[].url"),
            content=_expect_string(data.get("content"), "documents[].content"),
            source_type=str(data.get("source_type", "snapshot")),
        )


@dataclass(frozen=True, slots=True)
class RequiredClaim:
    claim_id: str
    text: str
    supported_by: tuple[str, ...]
    keywords: tuple[str, ...]
    depends_on: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequiredClaim":
        return cls(
            claim_id=_expect_string(data.get("claim_id"), "required_claims[].claim_id"),
            text=_expect_string(data.get("text"), "required_claims[].text"),
            supported_by=_string_tuple(data.get("supported_by", []), "required_claims[].supported_by"),
            keywords=_string_tuple(data.get("keywords", []), "required_claims[].keywords"),
            depends_on=_string_tuple(data.get("depends_on", []), "required_claims[].depends_on"),
        )


@dataclass(frozen=True, slots=True)
class TaskBundle:
    schema_version: str
    task_id: str
    prompt: str
    reference_answer: str
    documents: tuple[Document, ...]
    required_claims: tuple[RequiredClaim, ...]
    budget: Budget | None = None

    @property
    def document_ids(self) -> set[str]:
        return {document.doc_id for document in self.documents}

    @property
    def scorable_document_ids(self) -> set[str]:
        supported_ids: set[str] = set()
        for claim in self.required_claims:
            supported_ids.update(claim.supported_by)
        return supported_ids or self.document_ids

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskBundle":
        documents = tuple(Document.from_dict(_expect_mapping(item, "documents[]")) for item in _expect_list(data.get("documents"), "documents"))
        required_claims = tuple(
            RequiredClaim.from_dict(_expect_mapping(item, "required_claims[]"))
            for item in _expect_list(data.get("required_claims"), "required_claims")
        )
        raw_budget = data.get("budget")
        budget = None if raw_budget is None else Budget.from_dict(_expect_mapping(raw_budget, "budget"))
        bundle = cls(
            schema_version=_expect_string(data.get("schema_version"), "schema_version"),
            task_id=_expect_string(data.get("task_id"), "task_id"),
            prompt=_expect_string(data.get("prompt"), "prompt"),
            reference_answer=_expect_string(data.get("reference_answer"), "reference_answer"),
            documents=documents,
            required_claims=required_claims,
            budget=budget,
        )
        bundle.validate_references()
        return bundle

    def validate_references(self) -> None:
        document_ids = self.document_ids
        claim_ids = {claim.claim_id for claim in self.required_claims}
        if len(document_ids) != len(self.documents):
            raise ValidationError("documents contain duplicate doc_id values")
        if len(claim_ids) != len(self.required_claims):
            raise ValidationError("required_claims contain duplicate claim_id values")
        for claim in self.required_claims:
            if not claim.supported_by:
                raise ValidationError(f"required claim {claim.claim_id} must reference at least one supporting document")
            missing_docs = set(claim.supported_by) - document_ids
            if missing_docs:
                raise ValidationError(f"required claim {claim.claim_id} references missing documents: {sorted(missing_docs)}")
            missing_deps = set(claim.depends_on) - claim_ids
            if missing_deps:
                raise ValidationError(f"required claim {claim.claim_id} depends on missing claims: {sorted(missing_deps)}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GeneratedClaim:
    claim_id: str
    text: str
    citations: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any], index: int) -> "GeneratedClaim":
        return cls(
            claim_id=_expect_string(data.get("claim_id", f"generated-claim-{index}"), f"claims[{index}].claim_id"),
            text=_expect_string(data.get("text"), f"claims[{index}].text"),
            citations=_string_tuple(data.get("citations", []), f"claims[{index}].citations"),
        )


@dataclass(frozen=True, slots=True)
class Action:
    kind: str
    argument: str = ""
    document_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any], index: int) -> "Action":
        return cls(
            kind=_expect_string(data.get("kind"), f"actions[{index}].kind"),
            argument=str(data.get("argument", "")),
            document_ids=_string_tuple(data.get("document_ids", []), f"actions[{index}].document_ids"),
        )


@dataclass(frozen=True, slots=True)
class RewardBundle:
    answer_score: float = 0.0
    citation_score: float = 0.0
    chain_score: float = 0.0
    diversity_score: float = 0.0
    efficiency_score: float = 0.0
    total_score: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RewardBundle":
        return cls(**{key: float(data.get(key, 0.0)) for key in cls.__dataclass_fields__})


@dataclass(frozen=True, slots=True)
class RunArtifact:
    schema_version: str
    run_id: str
    task_id: str
    answer: str
    claims: tuple[GeneratedClaim, ...] = ()
    actions: tuple[Action, ...] = ()
    final_citations: tuple[str, ...] = ()
    reward_bundle: RewardBundle | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunArtifact":
        claims = tuple(
            GeneratedClaim.from_dict(_expect_mapping(item, f"claims[{index}]"), index)
            for index, item in enumerate(_expect_list(data.get("claims", []), "claims"))
        )
        actions = tuple(
            Action.from_dict(_expect_mapping(item, f"actions[{index}]"), index)
            for index, item in enumerate(_expect_list(data.get("actions", []), "actions"))
        )
        raw_reward = data.get("reward_bundle")
        reward_bundle = None if raw_reward is None else RewardBundle.from_dict(_expect_mapping(raw_reward, "reward_bundle"))
        return cls(
            schema_version=_expect_string(data.get("schema_version"), "schema_version"),
            run_id=_expect_string(data.get("run_id"), "run_id"),
            task_id=_expect_string(data.get("task_id"), "task_id"),
            answer=_expect_string(data.get("answer"), "answer"),
            claims=claims,
            actions=actions,
            final_citations=_string_tuple(data.get("final_citations", []), "final_citations"),
            reward_bundle=reward_bundle,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ClaimMatch:
    claim_id: str
    covered: bool
    coverage: float
    supported: bool
    matched_text: str
    citations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvalReport:
    task_id: str
    run_id: str
    metrics: dict[str, float]
    claim_results: tuple[ClaimMatch, ...]
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "metrics": self.metrics,
            "claim_results": [asdict(result) for result in self.claim_results],
            "notes": list(self.notes),
        }


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_task_bundle(path: str | Path) -> TaskBundle:
    return TaskBundle.from_dict(_expect_mapping(load_json(path), str(path)))


def load_run_artifact(path: str | Path) -> RunArtifact:
    return RunArtifact.from_dict(_expect_mapping(load_json(path), str(path)))
