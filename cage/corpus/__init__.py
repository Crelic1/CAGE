"""Turn recorded agent trajectories into training corpora.

``proxy.jsonl`` is the immutable record of every model call a trial made. This
package converts that record into training rows — one complete conversation per
row, in ms-swift ``messages + loss`` shape — without inventing anything the
model did not actually see.

Layering: this package knows about *harnesses* (compaction, subagents, director
injection, reasoning dialects) because those are framework facts true of every
benchmark. It knows nothing about any benchmark. Domain admission gates —
"this variant leaks the answer", "this task is in the eval set" — arrive through
:meth:`cage.benchmarks.Benchmark.admit_for_training`, and reach the CLI as
opaque codes the framework matches but never interprets.
"""

from cage.corpus.records import (
    Segment,
    TrainingAdmission,
    TrialCorpusView,
)

__all__ = [
    "Segment",
    "TrainingAdmission",
    "TrialCorpusView",
]
