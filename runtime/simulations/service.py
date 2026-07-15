"""Evidence-aware service layer for BRIXTA simulation packs."""

from __future__ import annotations

import json
from typing import Any

from brixta_sdk.simulation import (
    SimulationPreflightRequest,
    SimulationRunRequest,
)
from runtime.knowledge import KnowledgeBaseError, describe_knowledge_base, search_knowledge_base
from runtime.simulations.case_cards import get_case_card, validate_case_parameters
from runtime.simulations.registry import simulation_registry
from runtime.simulations.repository import SimulationRunRepository


class SimulationError(RuntimeError):
    pass


def _collect_evidence(
    *,
    tenant_id: str,
    knowledge_base_ids: list[str],
    query: str,
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for knowledge_base_id in knowledge_base_ids:
        try:
            manifest = describe_knowledge_base(knowledge_base_id)
        except KnowledgeBaseError as exc:
            raise SimulationError(str(exc)) from exc
        if manifest["tenant_id"] != tenant_id:
            raise SimulationError("A selected knowledge base belongs to another tenant.")
        try:
            matches = search_knowledge_base(
                knowledge_base_id,
                query,
                limit=3,
                tenant_id=tenant_id,
            )
        except KnowledgeBaseError as exc:
            raise SimulationError(str(exc)) from exc
        for match in matches:
            evidence.append(
                {
                    "knowledge_base_id": knowledge_base_id,
                    "knowledge_base_name": manifest["name"],
                    "result_id": match["id"],
                    "title": match["title"],
                    "score": match["score"],
                    "snippet": match["text"][:1_000],
                    "url": match["url"],
                }
            )
    return evidence


def build_preflight(payload: SimulationPreflightRequest) -> dict[str, Any]:
    card = get_case_card(payload.case_card_id)
    parameters = validate_case_parameters(payload.case_card_id, payload.parameters)
    query = payload.evidence_query or (
        "engineering material properties boundary conditions solver assumptions "
        f"{card['analysis_type']}"
    )
    evidence = _collect_evidence(
        tenant_id=payload.tenant_id,
        knowledge_base_ids=payload.knowledge_base_ids,
        query=query,
    )
    compiler = simulation_registry.load("compiler", card["solver"])
    compiled = compiler.compile(payload.case_card_id, parameters.model_dump())
    warnings = list(card["limitations"])
    if card["solver"] == "openfoam" and compiled.analytical_reference["reynolds_number"] >= 2_300:
        warnings.insert(
            0,
            "Estimated Reynolds number is outside this starter card's nominal laminar range.",
        )
    if not evidence:
        warnings.append("No knowledge evidence is attached; all engineering values are user supplied.")
    spec = {
        "schema_version": "1.0",
        "case_card_id": payload.case_card_id,
        "solver": card["solver"],
        "parameters": parameters.model_dump(),
        "knowledge_base_ids": payload.knowledge_base_ids,
    }
    return {
        "valid": True,
        "case_card": card,
        "normalized_parameters": parameters.model_dump(),
        "analytical_reference": compiled.analytical_reference,
        "evidence": evidence,
        "warnings": warnings,
        "compiled_files": sorted(compiled.files),
        "simulation_spec": spec,
        "visualization": json.loads(compiled.files["visualization.json"]),
    }


def create_simulation_run(payload: SimulationRunRequest) -> dict[str, Any]:
    preflight = build_preflight(
        SimulationPreflightRequest(
            tenant_id=payload.tenant_id,
            case_card_id=payload.case_card_id,
            parameters=payload.parameters,
            knowledge_base_ids=payload.knowledge_base_ids,
            evidence_query=payload.evidence_query,
        )
    )
    spec = {
        "schema_version": "1.0",
        "case_card_id": payload.case_card_id,
        "solver": preflight["case_card"]["solver"],
        "execution_mode": payload.execution_mode,
        "parameters": preflight["normalized_parameters"],
        "knowledge_base_ids": payload.knowledge_base_ids,
        "evidence_query": payload.evidence_query,
        "validation_warnings": preflight["warnings"],
    }
    return SimulationRunRepository.create(
        tenant_id=payload.tenant_id,
        case_card_id=payload.case_card_id,
        solver=preflight["case_card"]["solver"],
        execution_mode=payload.execution_mode,
        spec=spec,
        evidence=preflight["evidence"],
        label=payload.label,
    )
