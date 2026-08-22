# Interactive relay mechanics

Use this guide when the network service relays bytes to a process, pipe, PTY,
VM console, or another socket.

## Required behavior

An exploit-facing relay must:

- forward partial child output immediately, including prompts without a newline;
- forward partial client writes without waiting for EOF or a fixed-size buffer;
- keep both directions live concurrently;
- drain or deliberately merge stderr so a full pipe cannot deadlock the child;
- preserve the intended one-process-per-connection or shared-process lifecycle;
- propagate EOF and termination without killing the child merely because it is
  temporarily quiet.

Buffered `read(N)` calls may wait for all `N` bytes or EOF. A prompt shorter than
`N` can therefore exist in the child while the client sees nothing. Use
readiness-driven I/O (`selectors`, `select`, `poll`, or equivalent), `os.read`
or a non-buffering primitive, and a complete-write loop or `sendall`. Disable
language-level stdout buffering where the original service requires immediate
prompts.

Do not infer a child crash from empty client output. Separately observe child
state, stderr, and the relay's pending buffers. A timeout, EOF, and a still-live
silent child are three different facts.

## Diagnose the real relay on the retained target

Do not replace the challenge with a harmless child or launch a local relay as
runtime proof. Let `cage-check` build and start the authentic target. If it
returns R3/R4 plus timeout, EOF, or missing prompt, keep that target and connect
the committed solver or its smallest unchanged prefix directly to the returned
address. Use flushed, non-secret stage markers and the returned service/child
stderr to distinguish relay buffering from challenge logic.

When the evidence points to relay behavior, make one implementation change
that preserves the authentic child command and protocol. A solver-only change
can be exercised against the retained target; a relay or target change requires
the next `cage-check` to rebuild it. Reap child processes and close only the
corresponding connection; do not leave zombies or turn a per-connection service
into a single global session.
