"""Layer-0 framework vocabulary.

``contracts`` holds the dependency-free types every other layer speaks in: the
error taxonomy, the shared value types (``Score``, ``Timing``), and the
environment-expansion helper. It imports nothing from the rest of ``cage`` —
every other package may import *down* into it, never the reverse. That one rule
is what keeps the layer order legible.
"""

from __future__ import annotations

from cage.contracts.coerce import (
    int_or_zero,
    optional_float,
    optional_int,
    positive_float_or_none,
    positive_int_or_none,
)
from cage.contracts.env import expand_env_refs
from cage.contracts.exceptions import (
    CageError,
    CageInterrupt,
    ContainerError,
    ProxyError,
    TrialError,
    TrialTimeout,
)
from cage.contracts.execution import (
    Timing,
    classify_max_rounds,
    max_rounds_config_label,
    normalize_max_rounds_config,
    resolve_max_rounds,
    resolve_wrapup,
    round_budget_is_unbounded,
    run_lacks_termination_condition,
    sample_max_rounds,
)
from cage.contracts.jsonio import (
    append_jsonl_record,
    count_jsonl_lines,
    dump_jsonl_record,
    iter_jsonl_entries,
    iter_jsonl_lines,
    load_json_file,
    read_jsonl_entries,
    write_json_file,
)
from cage.contracts.runtime_state import (
    CHECK_SUPPORTED_KEY,
    RUNTIME_STATE_KEY,
    RuntimeState,
)
from cage.contracts.sample_keys import (
    SAMPLE_MAX_ROUNDS_KEY,
    SAMPLE_NETWORK_NAME_KEY,
    SAMPLE_NETWORK_SUBNET_KEY,
    SAMPLE_PASS_INDEX_KEY,
    SAMPLE_RUNTIME_ARGS_KEY,
    SAMPLE_TARGET_INFO_KEY,
    SAMPLE_VARIANT_KEY,
    SAMPLE_WRAPUP_BEFORE_KEY,
    SAMPLE_WRAPUP_MESSAGE_KEY,
    sample_pass_index,
)
from cage.contracts.scoring import Score, extract_numeric_score_value
from cage.contracts.trial_status import (
    COMPLETED_TRIAL_STATUSES,
    COMPLETED_TRIAL_STATUSES_ON_READ,
    LEGACY_SCORING_TRIAL_STATUSES,
    TERMINAL_TRIAL_STATUSES,
    TERMINAL_TRIAL_STATUSES_ON_READ,
    FAILED_TRIAL_STATUSES,
    INTERRUPTED_TRIAL_STATUSES,
    TrialCounts,
    classify_trial_status,
    count_trials,
)

__all__ = [
    "CHECK_SUPPORTED_KEY",
    "COMPLETED_TRIAL_STATUSES",
    "COMPLETED_TRIAL_STATUSES_ON_READ",
    "LEGACY_SCORING_TRIAL_STATUSES",
    "TERMINAL_TRIAL_STATUSES",
    "TERMINAL_TRIAL_STATUSES_ON_READ",
    "FAILED_TRIAL_STATUSES",
    "INTERRUPTED_TRIAL_STATUSES",
    "CageError",
    "CageInterrupt",
    "ContainerError",
    "ProxyError",
    "RUNTIME_STATE_KEY",
    "RuntimeState",
    "SAMPLE_MAX_ROUNDS_KEY",
    "SAMPLE_NETWORK_NAME_KEY",
    "SAMPLE_NETWORK_SUBNET_KEY",
    "SAMPLE_PASS_INDEX_KEY",
    "SAMPLE_RUNTIME_ARGS_KEY",
    "SAMPLE_TARGET_INFO_KEY",
    "SAMPLE_VARIANT_KEY",
    "SAMPLE_WRAPUP_BEFORE_KEY",
    "SAMPLE_WRAPUP_MESSAGE_KEY",
    "Score",
    "Timing",
    "TrialCounts",
    "TrialError",
    "TrialTimeout",
    "classify_trial_status",
    "append_jsonl_record",
    "count_jsonl_lines",
    "count_trials",
    "dump_jsonl_record",
    "expand_env_refs",
    "iter_jsonl_entries",
    "iter_jsonl_lines",
    "load_json_file",
    "read_jsonl_entries",
    "write_json_file",
    "classify_max_rounds",
    "max_rounds_config_label",
    "normalize_max_rounds_config",
    "round_budget_is_unbounded",
    "run_lacks_termination_condition",
    "extract_numeric_score_value",
    "int_or_zero",
    "optional_float",
    "optional_int",
    "positive_float_or_none",
    "positive_int_or_none",
    "resolve_max_rounds",
    "resolve_wrapup",
    "sample_max_rounds",
    "sample_pass_index",
]
