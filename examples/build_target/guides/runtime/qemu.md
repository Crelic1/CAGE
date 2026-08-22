# QEMU and guest-runtime reconstruction

Use this guide only when an executed deployment path starts QEMU.

## Freeze the real boot tuple

Record the exact QEMU executable/version, guest architecture, machine and CPU
options, kernel, initrd/initramfs or disk, kernel command line, devices, and I/O
topology from the executed command. Inspect the actual guest init and service
inside the referenced boot artifact. Loose source or extracted files are
secondary unless the build demonstrably regenerates that artifact.

Preserve the guest boundary and the vulnerability-bearing kernel/userland. Do
not replace a VM challenge with a host process merely because the host process
is easier to expose. If historical acceleration such as KVM is unavailable and
is not part of the vulnerability, use architecture-correct software emulation
such as TCG, record the compatibility change, and keep all guest-visible
semantics fixed.

First distinguish a full-system VM (`qemu-system-*`) from user-mode emulation
(`qemu-*-static`, binfmt, or a foreign-architecture chroot). For user-mode
emulation, guest `execve`, `system`, and shell launches cross another runtime
boundary: trace which kernel/binfmt/interpreter path actually handles the child
instead of assuming that a working parent process proves child execution.

Do not fabricate `/proc/self/exe` or point it at the emulator unless that exact
semantic is supported by evidence and tested. A guest child can otherwise
re-enter the emulator recursively. Before exploit validation, run one harmless
guest child command through the same path, verify that it creates only the
expected bounded child process(es), produces its output, and terminates. Treat
unbounded process growth, repeated emulator re-entry, or a child that never
terminates as a target lifecycle failure; repair that boundary before retrying
the exploit.

Follow `artifacts/archive-images.md` when modifying a boot artifact and
`validation/runtime-boundaries.md` when moving the injected flag into the
guest.

## Preserve the interaction path

Determine whether the original player path is guest networking, a serial
console, a virtio channel, or a wrapper around QEMU stdio. Reproduce that path:

- for serial/stdin interaction, preserve raw bidirectional bytes and immediate
  partial prompts; use `transport/interactive-relays.md`;
- for guest networking, distinguish the guest listen address, QEMU forwarding,
  and the container's declared internal port;
- keep boot logs separate from, or faithfully multiplexed with, the challenge
  protocol as the original wrapper does.

Preserve guest login/authentication and P's delivery path. If the supplied
driver logs in with known credentials, replacing that flow with autologin is a
semantic change, not a transport repair. If P uploads a payload, keep the
payload player-side and adapt the upload mechanism. Never preinstall that
payload in the guest unless the historical executed B/P chain already made the
exact payload player-reachable there. Saving transfer time or fitting a scorer
timeout is not compatibility evidence; preinstallation otherwise changes the
solve surface.

A running QEMU PID proves only that the emulator process exists. Prove in order:
QEMU started with the intended artifacts, the guest reached init, the guest
service reached its authentic prompt/input point, the relay exposed that point,
and the exploit completed against it. Empty output does not prove a kernel
crash; inspect QEMU stderr, serial output, process state, and relay state
separately.

When an exact historical QEMU/browser/kernel build matters, public downloads
are allowed. Verify challenge identity, architecture, version/build metadata,
and preferably hashes against supplied or independently corroborated evidence.
Do not silently substitute the distribution's current package.
