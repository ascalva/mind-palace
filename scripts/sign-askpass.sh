#!/bin/sh
# sign-askpass.sh — SSH_ASKPASS helper for silent git commit signing (finding-0122).
#
# git SSH signing (`gpg.format=ssh`) invokes `ssh-keygen -Y sign`, which needs the signing key's
# passphrase. With SSH_ASKPASS pointing here + SSH_ASKPASS_REQUIRE=force, ssh-keygen reads the
# passphrase from this script instead of prompting a TTY — so the ouroboros-work orchestrator's
# commits sign SILENTLY and stay Verified as the human (dn-plane-principals §3.2).
#
# The passphrase is read from the ENVIRONMENT (PALACE_SIGN_PASS), which orchestrator-launch.sh
# populates from ascalva's login keychain at launch. It is NEVER stored in this file or the repo
# (non-negotiable #10). If unset, this prints nothing and signing falls back to a TTY prompt — a
# visible failure, never a silent wrong-sign.
printf '%s' "${PALACE_SIGN_PASS:-}"
