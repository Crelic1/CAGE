# Flag and exploit flow across runtime boundaries

Use this guide when the service crosses a VM, chroot, sidecar, browser, worker,
subprocess, or another filesystem/process boundary.

Draw the concrete flow before editing:

```text
validator injection
  -> container file or environment
  -> startup transfer/repack step
  -> nested runtime's authentic flag location
  -> vulnerable component
  -> exploit output
```

For every arrow, name the executed file/command that performs the transfer and
the observation that proves it happened. A path existing in the outer
container does not make it exist in a VM, chroot, sidecar, browser profile, or
child with a different environment. Likewise, setting a Compose environment
variable does not update an already-packed guest image.

Keep the authentic final location and access rules. Transfer the validator's
fresh value at instance startup, before the nested consumer starts, without
placing it in a public command line, banner, readiness response, image layer,
world-readable log, or player-visible environment. The normal player path must
not read the value before exploiting the intended vulnerability.

Do not create a local substitute target or use a locally packed canary as proof
of this flow. During static preparation, inspect the exact startup transfer,
packed artifact paths, types, modes, and identities. `cage-check` is the only
authority that the flow works at runtime. During validation, do not print or
copy the private value for debugging; the committed exploit must retrieve it
through the intended challenge behavior. If the validator reports a boundary
failure, repair that exact startup transfer and let the next `cage-check`
rebuild the target.

For per-instance guests or workers, confirm the transfer happens on every clean
start rather than only at image build time. A passing run with a stale baked
value is not evidence that fresh injection works.
