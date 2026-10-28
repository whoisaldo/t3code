#!/bin/bash
# Runs in the Aqua session: real frontmost app + native CG list, then the UNMODIFIED production lookup scripts.
W=/tmp/trifecta-desktop-work; out=$1
{ echo "## probe"; /usr/bin/osascript -l JavaScript $W/probe.js
  for v in before after; do echo "## $v"; /usr/bin/osascript -l JavaScript $W/lookup-$v.js; echo; done; echo "## END"; } > $out.tmp 2>&1
mv $out.tmp $out
