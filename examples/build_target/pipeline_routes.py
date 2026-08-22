"""Static-material pipeline routing for build_target (env-gen ⊕ exp-gen).

This module is the single source of truth for *which* generation pipeline a
challenge runs, derived from the upstream A/W/P/B material profile produced by
the issue-5 static-data layer (`static_material_pipeline_route`). It is the
Layer-2 realization of the fusion ``build_mode``: the ``build → adapt/generate
EXP → validate`` main chain.

Material bits (authored upstream; build_target only CONSUMES, never recomputes):

    A = attachment            W = writeup
    P = public exploit/solver B = build material (Dockerfile / compose / deploy)

Two orthogonal decisions per challenge:

    build_source   how the runtime environment is produced
    exploit_source how the exploit that proves faithful reproduction is obtained

Each of the 9 routes fixes one (build_source, exploit_source) pair and a
material-context policy (which material roles are surfaced to each sub-task).
No models are called here; this is pure, deterministic routing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# --- Strategy vocabularies -------------------------------------------------

class BuildSource:
    """How the environment is produced."""

    USE_BUILD_MATERIAL = "use_build_material"   # B present: use Dockerfile/compose directly
    INFER_FROM_EXPLOIT = "infer_from_exploit"   # no B, P present: reverse-engineer runtime from the exploit
    INFER_FROM_WRITEUP = "infer_from_writeup"   # no B, W present: infer runtime from the writeup
    NONE = "none"                               # no build anchor -> not producible yet


class ExploitSource:
    """How the proving exploit is obtained."""

    ADAPT_EXISTING = "adapt_existing"                     # P present: adapt the confirmed solver to the rebuilt target
    GENERATE_FROM_WRITEUP = "generate_from_writeup"       # no P, W present: synthesize the exploit guided by the writeup
    GENERATE_FROM_ATTACHMENT = "generate_from_attachment" # no P/W: derive the exploit from binary/attachment analysis
    NONE = "none"                                         # no solve anchor -> not producible yet


# Material roles surfaced to a sub-task. These are the A/W/P/B roles; the
# materialization step maps them onto the concrete files under each role.
ROLE_ATTACHMENT = "attachments"
ROLE_WRITEUP = "writeups"
ROLE_EXPLOIT = "exploit"
ROLE_BUILD = "deployment"
ROLE_SOURCE = "source"


@dataclass(frozen=True)
class RoutePipeline:
    """The full pipeline contract for one static-material route."""

    route: str
    profile: str
    build_source: str
    exploit_source: str
    # Does each half actually run for this route?
    env_generation: bool
    exp_generation: bool
    # Production gating: A / NO_A route to material enrichment, not generation.
    producible: bool
    priority: int                         # lower = earlier; the 2099 main chain is 0/1
    summary: str
    # Context policy: which material roles each sub-task's agent may see.
    env_context_roles: tuple[str, ...]
    exp_context_roles: tuple[str, ...]
    # Prompt template basenames (resolved under prompts/pipelines/{env,exp}/routes/).
    env_prompt: str
    exp_prompt: str

    @property
    def build_mode(self) -> str:
        """Coarse fusion mode for the seam contract (see BUILD_EXP_SEAM_CONTRACT)."""
        if not self.producible:
            return "skip"
        if self.build_source == BuildSource.USE_BUILD_MATERIAL:
            # Has a trusted build anchor; exploit still validates R5/X.
            return "downstream_exp" if self.exp_generation else "rehost_only"
        # Runtime is inferred -> env and exp co-evolve in one joint episode.
        return "joint_reproduction"

    @property
    def exploit_required(self) -> bool:
        return self.exp_generation

    @property
    def episode_plan(self) -> str:
        """One-shot vs staged, the machine form of the build⊕exp overlap.

        ``joint``  — a confirmed solver already exists (``adapt_existing``), so
        the environment is *proven faithful by running that solver*: build and
        exploit close in ONE trial. These are the "one-shot" routes.
        ``staged`` — no solver (``generate_*``): build and freeze the env, THEN
        synthesize the exploit against it. Same R5 gate, harder exploit source.
        ``none``   — not producible.
        """
        if not self.producible:
            return "none"
        if self.exploit_source == ExploitSource.ADAPT_EXISTING:
            return "joint"
        return "staged"

    def to_contract(self) -> dict[str, Any]:
        """Additive contract keys consumed by the scorer (per seam contract §3)."""
        return {
            "pipeline_route": self.route,
            "material_profile": self.profile,
            "build_mode": self.build_mode,
            "episode_plan": self.episode_plan,
            "build_source": self.build_source,
            "exploit_source": self.exploit_source,
            "exploit_required": self.exploit_required,
            "producible": self.producible,
        }


# --- The 9 routes ----------------------------------------------------------
# One entry per upstream `pipeline_route`. Ordered by production priority: the
# fusion-ready main chain (B+P both present) first.

ROUTE_PIPELINES: dict[str, RoutePipeline] = {
    "fast_track_full": RoutePipeline(
        route="fast_track_full", profile="AWPB",
        build_source=BuildSource.USE_BUILD_MATERIAL,
        exploit_source=ExploitSource.ADAPT_EXISTING,
        env_generation=True, exp_generation=True, producible=True, priority=0,
        summary="B+P+W: build from B, adapt confirmed exploit, writeup aids diagnosis.",
        # A is not redundant with B/P: it commonly carries the served binary and
        # exact libc/loader pair.  Joint prompts must surface every formal profile
        # bit, even though prepare_trial copies all declared files either way.
        env_context_roles=(ROLE_ATTACHMENT, ROLE_BUILD, ROLE_SOURCE, ROLE_WRITEUP),
        exp_context_roles=(ROLE_ATTACHMENT, ROLE_EXPLOIT, ROLE_WRITEUP),
        env_prompt="fast_track_full.j2", exp_prompt="fast_track_full.j2",
    ),
    "fast_track_no_writeup": RoutePipeline(
        route="fast_track_no_writeup", profile="APB",
        build_source=BuildSource.USE_BUILD_MATERIAL,
        exploit_source=ExploitSource.ADAPT_EXISTING,
        env_generation=True, exp_generation=True, producible=True, priority=1,
        summary="B+P: build from B, adapt confirmed exploit directly (no writeup aid).",
        env_context_roles=(ROLE_ATTACHMENT, ROLE_BUILD, ROLE_SOURCE),
        exp_context_roles=(ROLE_ATTACHMENT, ROLE_EXPLOIT),
        env_prompt="fast_track_no_writeup.j2", exp_prompt="fast_track_no_writeup.j2",
    ),
    "build_then_solve": RoutePipeline(
        route="build_then_solve", profile="AB",
        build_source=BuildSource.USE_BUILD_MATERIAL,
        exploit_source=ExploitSource.GENERATE_FROM_ATTACHMENT,
        env_generation=True, exp_generation=True, producible=True, priority=2,
        summary="B, no P/W: build from B, then generate the exploit from binary/attachment analysis.",
        env_context_roles=(ROLE_BUILD, ROLE_SOURCE),
        exp_context_roles=(ROLE_ATTACHMENT, ROLE_SOURCE),
        env_prompt="build_then_solve.j2", exp_prompt="build_then_solve.j2",
    ),
    "build_then_generate": RoutePipeline(
        route="build_then_generate", profile="AWB",
        build_source=BuildSource.USE_BUILD_MATERIAL,
        exploit_source=ExploitSource.GENERATE_FROM_WRITEUP,
        env_generation=True, exp_generation=True, producible=True, priority=3,
        summary="B+W, no P: build from B, then synthesize the exploit guided by the writeup.",
        env_context_roles=(ROLE_BUILD, ROLE_SOURCE, ROLE_WRITEUP),
        exp_context_roles=(ROLE_WRITEUP, ROLE_SOURCE),
        env_prompt="build_then_generate.j2", exp_prompt="build_then_generate.j2",
    ),
    "infer_env_from_exp": RoutePipeline(
        route="infer_env_from_exp", profile="AP",
        build_source=BuildSource.INFER_FROM_EXPLOIT,
        exploit_source=ExploitSource.ADAPT_EXISTING,
        env_generation=True, exp_generation=True, producible=True, priority=4,
        summary="P, no B: reverse-engineer the runtime (libc/loader/ABI/protections) FROM the exploit, then adapt it. The env and exploit co-evolve.",
        env_context_roles=(ROLE_EXPLOIT, ROLE_SOURCE, ROLE_ATTACHMENT),
        exp_context_roles=(ROLE_EXPLOIT, ROLE_ATTACHMENT),
        env_prompt="infer_env_from_exp.j2", exp_prompt="infer_env_from_exp.j2",
    ),
    "infer_env_then_adapt": RoutePipeline(
        route="infer_env_then_adapt", profile="AWP",
        build_source=BuildSource.INFER_FROM_WRITEUP,
        exploit_source=ExploitSource.ADAPT_EXISTING,
        env_generation=True, exp_generation=True, producible=True, priority=5,
        summary="W+P, no B: infer the runtime from writeup+exploit, then adapt the confirmed exploit.",
        env_context_roles=(ROLE_WRITEUP, ROLE_EXPLOIT, ROLE_SOURCE, ROLE_ATTACHMENT),
        exp_context_roles=(ROLE_EXPLOIT, ROLE_WRITEUP),
        env_prompt="infer_env_then_adapt.j2", exp_prompt="infer_env_then_adapt.j2",
    ),
    "infer_both_from_writeup": RoutePipeline(
        route="infer_both_from_writeup", profile="AW",
        build_source=BuildSource.INFER_FROM_WRITEUP,
        exploit_source=ExploitSource.GENERATE_FROM_WRITEUP,
        env_generation=True, exp_generation=True, producible=True, priority=6,
        summary="W only: infer the runtime from the writeup AND synthesize the exploit from the writeup. Weakest anchors.",
        env_context_roles=(ROLE_WRITEUP, ROLE_SOURCE, ROLE_ATTACHMENT),
        exp_context_roles=(ROLE_WRITEUP, ROLE_SOURCE),
        env_prompt="infer_both_from_writeup.j2", exp_prompt="infer_both_from_writeup.j2",
    ),
    "enrich_materials": RoutePipeline(
        route="enrich_materials", profile="A",
        build_source=BuildSource.NONE, exploit_source=ExploitSource.NONE,
        env_generation=False, exp_generation=False, producible=False, priority=8,
        summary="A only: no build or solve anchor. Route to material enrichment (search W/P/B); not production-eligible.",
        env_context_roles=(ROLE_ATTACHMENT,),
        exp_context_roles=(),
        env_prompt="enrich_materials.j2", exp_prompt="enrich_materials.j2",
    ),
    "candidate_inventory_only": RoutePipeline(
        route="candidate_inventory_only", profile="NO_A",
        build_source=BuildSource.NONE, exploit_source=ExploitSource.NONE,
        env_generation=False, exp_generation=False, producible=False, priority=9,
        summary="No confirmed attachment: candidate inventory only. Not production-eligible.",
        env_context_roles=(), exp_context_roles=(),
        env_prompt="candidate_inventory_only.j2", exp_prompt="candidate_inventory_only.j2",
    ),
}


PROFILE_TO_ROUTE: dict[str, str] = {
    "AWPB": "fast_track_full",
    "APB": "fast_track_no_writeup",
    "AB": "build_then_solve",
    "AWB": "build_then_generate",
    "AP": "infer_env_from_exp",
    "AWP": "infer_env_then_adapt",
    "AW": "infer_both_from_writeup",
    "A": "enrich_materials",
    "NO_A": "candidate_inventory_only",
}


def route_for_profile(profile: str) -> str:
    """Map an A/W/P/B profile to its pipeline route."""
    key = str(profile or "").strip().upper()
    if key not in PROFILE_TO_ROUTE:
        raise ValueError(f"unknown material profile {profile!r}; expected one of {sorted(PROFILE_TO_ROUTE)}")
    return PROFILE_TO_ROUTE[key]


def resolve_route(sample: dict[str, Any]) -> RoutePipeline:
    """Resolve the pipeline for a build_target sample.

    Precedence: an explicit ``pipeline_route`` wins; else derive from
    ``material_profile``; else fall back to the legacy material-role inference
    so pre-profile datasets still route. The static profile is authored
    upstream and is authoritative — build_target never recomputes it.
    """
    explicit = str(sample.get("pipeline_route") or "").strip()
    if explicit:
        if explicit not in ROUTE_PIPELINES:
            raise ValueError(f"unknown pipeline_route {explicit!r}; expected one of {sorted(ROUTE_PIPELINES)}")
        return ROUTE_PIPELINES[explicit]

    profile = str(sample.get("material_profile") or "").strip().upper()
    if profile:
        return ROUTE_PIPELINES[route_for_profile(profile)]

    return ROUTE_PIPELINES[route_for_profile(_infer_profile_from_materials(sample))]


def _infer_profile_from_materials(sample: dict[str, Any]) -> str:
    """Legacy fallback: derive an A/W/P/B profile from role presence.

    Only used when neither pipeline_route nor material_profile is present.
    A challenge with no confirmed attachment is NO_A.
    """
    materials = sample.get("materials") or {}
    material_states = sample.get("material_states") or {}

    def _present(role: str) -> bool:
        return bool(materials.get(role))

    has_a = _present("attachments") or _present("source")
    has_w = _present("writeups")
    # Exploit material lives under an explicit `exploit` role when materialized,
    # else falls back to the upstream material_states.exp count.
    has_p = _present("exploit") or bool((material_states.get("exp") or {}).get("count"))
    has_b = _present("deployment")

    if not has_a:
        return "NO_A"
    return "A" + ("W" if has_w else "") + ("P" if has_p else "") + ("B" if has_b else "")


if __name__ == "__main__":  # pragma: no cover - developer convenience
    import json
    import sys

    if len(sys.argv) > 1:
        rp = ROUTE_PIPELINES.get(sys.argv[1]) or ROUTE_PIPELINES[route_for_profile(sys.argv[1])]
        print(json.dumps({**rp.to_contract(), "summary": rp.summary,
                          "env_context_roles": rp.env_context_roles,
                          "exp_context_roles": rp.exp_context_roles}, indent=2, ensure_ascii=False))
    else:
        for rp in sorted(ROUTE_PIPELINES.values(), key=lambda r: r.priority):
            print(f"{rp.priority} {rp.route:24s} {rp.profile:5s} "
                  f"build={rp.build_source:20s} exp={rp.exploit_source:24s} mode={rp.build_mode}")
