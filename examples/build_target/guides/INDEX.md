# Build-target guide index

These files contain optional mechanics, not facts about the current challenge.
The supplied deployment and the artifacts it actually starts remain the source
of truth.

Do not read every guide up front. First inspect the real Dockerfile, Compose
file, entrypoint, boot command, and solver. Then search this index and open the
guide mapped to each triggered layer before inspecting inside or editing it.
Consumption is itself a trigger: for example, a `.cpio` passed to QEMU selects
the archive guide even if the initial plan is to keep that file unchanged,
because listing, extraction, or startup-time repacking touches its semantics.
Multiple real triggers may require multiple small guides; unrelated guides
remain unread:

```sh
rg -n -i 'qemu|initramfs|cpio|squashfs|relay|stdio|chroot|sidecar|browser' \
  /opt/cage/build-target-guides/INDEX.md
```

| Observed trigger | Read |
| --- | --- |
| The executed command references `.cpio`, initramfs, a disk image, squashfs, or another packed filesystem | `artifacts/archive-images.md` |
| A TCP listener proxies bytes to a child process, VM serial console, pipe, PTY, or subprocess | `transport/interactive-relays.md` |
| The executed deployment starts `qemu-system-*`, a kernel, initrd/initramfs, or a guest disk | `runtime/qemu.md` |
| The flag or exploit crosses a VM, chroot, sidecar, browser, worker, or subprocess boundary | `validation/runtime-boundaries.md` |

A formal route or category name is not a trigger. For example, do not read the
QEMU guide merely because a task is Pwn. A missing or inapplicable guide is not
a blocker: continue from the actual files and record the evidence.
