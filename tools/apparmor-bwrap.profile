# AppArmor profile permitting bubblewrap to create user namespaces.
#
# **Why this file exists.**  Ubuntu 24.04 ships
# `kernel.apparmor_restrict_unprivileged_userns = 1`, which stops any
# unconfined binary from creating a user namespace.  Every unprivileged
# sandbox on this machine needs one — `bwrap` fails with
#
#     bwrap: setting up uid map: Permission denied
#
# and `systemd-run --user` silently declines to apply `ProtectHome`,
# `PrivateNetwork` and the rest, which is worse: the unit starts, the
# command runs, and nothing is fenced.  That failure mode is why
# `tools/sandbox.sh --check` exists and why it must pass before the
# sandbox is trusted for anything.
#
# This profile grants `userns` to one binary and nothing else.  It is
# narrower than the two alternatives:
#
#   * `sysctl -w kernel.apparmor_restrict_unprivileged_userns=0`
#     — lifts the restriction for every binary on the system.
#   * `chmod u+s /usr/bin/bwrap`
#     — makes bubblewrap setuid root.  It is written to be safe this way
#       and drops privileges immediately, but it is a larger surface than
#       one AppArmor rule.
#
# **Install** (needs root, so run it yourself):
#
#     sudo install -m 644 tools/apparmor-bwrap.profile /etc/apparmor.d/bwrap
#     sudo apparmor_parser -r /etc/apparmor.d/bwrap
#     tools/sandbox.sh --check
#
# **Uninstall:**
#
#     sudo rm /etc/apparmor.d/bwrap && sudo systemctl reload apparmor

abi <abi/4.0>,

include <tunables/global>

profile bwrap /usr/bin/bwrap flags=(unconfined) {
  userns,

  include if exists <local/bwrap>
}
