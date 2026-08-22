# Overlay that swaps in a fixed proxy sidecar without rebuilding the world.
#
# A full `cage agent build` would also pull whatever Claude Code CLI is current,
# which changes agent behaviour and confounds any before/after comparison. The
# cache fix touches exactly one file, so derive from the image the fleet is
# already running and replace only that file. Everything else stays
# byte-identical to the parent.
#
#   docker build -f docker/claude_code/cachefix.Dockerfile \
#     -t pursu1ng/cage-images:claude-code-cachefix .
#
# Build context is the repo root, same as docker/claude_code/Dockerfile.
FROM pursu1ng/cage-images:claude-code-latest

COPY cage/proxy/sidecar.py /opt/cage-proxy/container_proxy.py
