#!/usr/bin/env bash
# deploy_build.sh BUILD_HARNESS_DIR VIEWER_DIR: the live harness and page become these (rsync, no deletes), the server is restarted. Stops if a
# session is running. The backup of what was live before the audit's deploy is live_before_deploy_audit (undo_deploy_audit.sh).
set -e
B="$1"; V="$2"
if pgrep -f "^[^ ]*python[^ ]* [^ ]*harness/loop.py --session" >/dev/null; then echo "a session is running: not deployed"; exit 1; fi
rsync -a --exclude __pycache__ --exclude loop.log "$B"/ "$HOME/project/harness/"
rsync -a --exclude __pycache__ "$V"/ "$HOME/project/viewer/"
diff -rq --exclude=__pycache__ --exclude=loop.log "$HOME/project/harness" "$B"
diff -rq --exclude=__pycache__ "$HOME/project/viewer" "$V"
echo "copied: the live harness and page are the build"
tmux kill-session -t control 2>/dev/null || true; sleep 1
tmux new-session -d -s control -c "$HOME/project" "/home/chunguck.kim/miniforge3/bin/python3 harness/control.py --network on"
sleep 4
curl -s -o /dev/null -w "page on 8600: %{http_code}\n" "http://127.0.0.1:8600/viewer/index.html?session=s053"
echo "deployed $(date +%H:%M)"
