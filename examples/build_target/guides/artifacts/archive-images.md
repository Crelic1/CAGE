# Packed filesystem and boot-image mechanics

Use this guide only when the deployment actually consumes a packed artifact.

## Establish the artifact that matters

1. Trace the executed Dockerfile, entrypoint, and boot command to the exact
   archive or disk image used at runtime.
2. Hash that artifact before editing it. A similarly named extracted directory
   or loose sibling file is secondary evidence unless the executed build
   regenerates the archive from it.
3. Identify its real format with `file` and format-aware listing tools. Filename
   suffixes are hints, not proof; initramfs images are often compressed cpio
   archives with more than one compression choice.
4. Inspect the guest init, service binary, users, permissions, flag path, and
   any already-present exploit/helper inside the artifact before reconstructing
   them elsewhere.

Prefer an unpack-edit-repack workflow in a fresh working directory. Preserve
path type, symlink target, executable bit, owner/group, and device metadata
needed during boot. Do not silently turn a symlink or special file into a
regular file. If a format-specific tool is missing, installing or downloading
one is ordinary; verify that it supports the observed format before using it.
If the agent user cannot preserve owners or special nodes, perform the
format-aware transformation during the image build as root, then reopen the
result; do not commit an archive reconstructed from degraded metadata.
Treat every tree extracted as the unprivileged agent as inspection-only, even
when most paths look correct or `cpio` produced many blocks. Never feed that
tree back into the archive writer. Create a separate root-owned transformation
inside the Docker build or root startup path from the original archive.
Keep the extracted tree outside any broad recursive `chown`/`chmod` used for
host-side service files. A convenient `chmod -R` can silently change every
guest executable, directory, set-ID bit, and flag access rule even when the
archive tool itself is correct.

## Verify the write, not the command

An archive tool exiting zero proves only that it completed. Reopen the exact
artifact consumed by the boot command and verify:

- the intended internal path exists exactly once;
- its type, mode, owner/group, and symlink target are correct;
- its size and SHA256 match the file meant to be embedded;
- the deployment still points at this artifact, not the pre-edit copy.

When the archive contains the flag placeholder, also verify that the placeholder
does not match the challenge flag format. At container start, the validator's
fresh value must be inserted before the consumer boots or enters its nested
boundary. Never bake a value observed during one validation attempt into the
committed archive.

Keep the original archive and one reversible transformation until boot is
proven. If a change regresses a previously working boot, compare hashes and
revert that transformation before testing another hypothesis.
