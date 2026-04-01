#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
ENV_FILE="${KIMODO_WEB_ENV_FILE:-$SCRIPT_DIR/kimodo_web.env}"

load_env() {
    if [[ ! -f "$ENV_FILE" ]]; then
        echo "Missing env file: $ENV_FILE" >&2
        exit 1
    fi

    # shellcheck disable=SC1090
    source "$ENV_FILE"

    SESSION_NAME="${KIMODO_SESSION_NAME:-kimodo_web}"
    WORKDIR="${KIMODO_WORKDIR:-/root/Project/Kimodo}"
    CONDA_SH_PATH="${CONDA_SH:-/root/miniforge3/etc/profile.d/conda.sh}"
    CONDA_ENV_NAME="${KIMODO_CONDA_ENV:-kimodo}"
    MODEL_NAME="${KIMODO_MODEL:-Kimodo-G1-RP-v1}"
    TEXT_ENCODER_DEVICE_NAME="${TEXT_ENCODER_DEVICE:-auto}"
}

activate_env() {
    # shellcheck disable=SC1090
    source "$CONDA_SH_PATH"
    conda activate "$CONDA_ENV_NAME"
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    cd "$WORKDIR"
}

run_textencoder() {
    load_env
    activate_env
    exec kimodo_textencoder --device "$TEXT_ENCODER_DEVICE_NAME"
}

run_demo() {
    load_env
    activate_env
    until ss -ltn | rg -q ':9550\b'; do
        sleep 1
    done
    exec kimodo_demo --model "$MODEL_NAME"
}

start_session() {
    load_env
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        echo "tmux session '$SESSION_NAME' already exists."
        status_session
        return 0
    fi

    tmux new-session -d -s "$SESSION_NAME" -n textencoder "$SCRIPT_PATH" _run_textencoder
    tmux new-window -t "$SESSION_NAME" -n demo "$SCRIPT_PATH" _run_demo
    tmux set-option -t "$SESSION_NAME" remain-on-exit on
    tmux set-option -t "$SESSION_NAME" mouse on

    echo "Started tmux session '$SESSION_NAME'."
    status_session
}

stop_session() {
    load_env
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        tmux kill-session -t "$SESSION_NAME"
        echo "Stopped tmux session '$SESSION_NAME'."
    else
        echo "tmux session '$SESSION_NAME' is not running."
    fi
}

restart_session() {
    stop_session
    start_session
}

attach_session() {
    load_env
    exec tmux attach-session -t "$SESSION_NAME"
}

status_session() {
    load_env
    if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        echo "tmux session '$SESSION_NAME' is not running."
        return 1
    fi

    echo "tmux session: $SESSION_NAME"
    tmux list-windows -t "$SESSION_NAME"
    echo
    echo "listening ports:"
    ss -ltnp | rg ':(7860|9550)\b' || true
}

usage() {
    cat <<EOF
Usage: $(basename "$SCRIPT_PATH") <start|stop|restart|status|attach>

Commands:
  start    Start detached tmux windows for kimodo_textencoder and kimodo_demo
  stop     Stop the tmux session and both services
  restart  Stop then start the tmux session
  status   Show tmux windows and listening ports
  attach   Attach to the tmux session for live logs
EOF
}

main() {
    local cmd="${1:-}"
    case "$cmd" in
        start)
            start_session
            ;;
        stop)
            stop_session
            ;;
        restart)
            restart_session
            ;;
        status)
            status_session
            ;;
        attach)
            attach_session
            ;;
        _run_textencoder)
            run_textencoder
            ;;
        _run_demo)
            run_demo
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

main "${1:-}"
