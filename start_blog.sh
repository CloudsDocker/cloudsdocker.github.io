#!/usr/bin/env bash
# ==============================================================================
# Jekyll Blog Local Runner (Linux / WSL / Docker)
# ==============================================================================
set -e

CONTAINER_NAME="jekyll-server"
IMAGE_NAME="jekyll/jekyll:latest"
GEM_VOLUME="jekyll-gems"
PORT="4000"
LIVERELOAD_PORT="35729"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_banner() {
    echo "=================================================="
    echo "  CloudsDocker / Jekyll Blog Local Runner"
    echo "=================================================="
}

check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        echo "[ERROR] Docker is not installed or not in PATH."
        echo "Please install Docker or Docker Desktop to run this blog locally."
        exit 1
    fi

    if ! docker ps >/dev/null 2>&1; then
        echo "[ERROR] Docker daemon is not running or accessible without sudo."
        echo "Please ensure Docker is running."
        exit 1
    fi
}

is_running() {
    [ "$(docker ps -q -f name=^/${CONTAINER_NAME}$)" ]
}

stop_server() {
    if is_running; then
        echo "[INFO] Stopping container '${CONTAINER_NAME}'..."
        docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
        docker rm "${CONTAINER_NAME}" >/dev/null 2>&1 || true
        echo "[INFO] Jekyll server stopped."
    else
        echo "[INFO] Jekyll server is not running."
    fi
}

start_background() {
    check_docker
    if is_running; then
        echo "[INFO] Jekyll server is already running at http://localhost:${PORT}"
        return 0
    fi

    echo "[INFO] Starting Jekyll server in background..."
    docker run --rm -d \
        --name "${CONTAINER_NAME}" \
        -p "${PORT}:${PORT}" \
        -p "${LIVERELOAD_PORT}:${LIVERELOAD_PORT}" \
        -v "${REPO_DIR}":/srv/jekyll \
        -v "${GEM_VOLUME}":/usr/local/bundle \
        -w /srv/jekyll \
        "${IMAGE_NAME}" \
        bundle exec jekyll serve --livereload --host 0.0.0.0 --port "${PORT}" --force_polling

    echo "[INFO] Container '${CONTAINER_NAME}' launched."
    echo "[INFO] Web URL: http://localhost:${PORT}"
    echo "[INFO] Run '$0 logs' to view output or '$0 stop' to stop."
}

start_foreground() {
    check_docker
    if is_running; then
        echo "[INFO] Jekyll server is already running in background."
        echo "[INFO] Web URL: http://localhost:${PORT}"
        echo "[INFO] Tailing logs (Press Ctrl+C to exit tailing, or run '$0 stop' to shut down)..."
        docker logs -f "${CONTAINER_NAME}"
        return 0
    fi

    trap 'echo ""; echo "[INFO] Stopping Jekyll server..."; docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true; exit 0' INT TERM

    echo "[INFO] Starting Jekyll server (Press Ctrl+C to stop)..."
    echo "[INFO] Access URL: http://localhost:${PORT}"
    echo ""

    docker run --rm \
        --name "${CONTAINER_NAME}" \
        -p "${PORT}:${PORT}" \
        -p "${LIVERELOAD_PORT}:${LIVERELOAD_PORT}" \
        -v "${REPO_DIR}":/srv/jekyll \
        -v "${GEM_VOLUME}":/usr/local/bundle \
        -w /srv/jekyll \
        "${IMAGE_NAME}" \
        bundle exec jekyll serve --livereload --host 0.0.0.0 --port "${PORT}" --force_polling
}

build_site() {
    check_docker
    echo "[INFO] Building static site to _site/..."
    docker run --rm \
        -v "${REPO_DIR}":/srv/jekyll \
        -v "${GEM_VOLUME}":/usr/local/bundle \
        -w /srv/jekyll \
        "${IMAGE_NAME}" \
        bundle exec jekyll build
    echo "[INFO] Build completed successfully."
}

status() {
    if is_running; then
        echo "[INFO] Jekyll server is RUNNING (http://localhost:${PORT})"
        docker ps -f name="^/${CONTAINER_NAME}$"
    else
        echo "[INFO] Jekyll server is STOPPED"
    fi
}

show_logs() {
    if is_running; then
        docker logs -f --tail 50 "${CONTAINER_NAME}"
    else
        echo "[WARN] Jekyll server is not running."
    fi
}

print_banner

case "${1:-start}" in
    start)
        start_foreground
        ;;
    bg|background)
        start_background
        ;;
    stop)
        stop_server
        ;;
    status)
        status
        ;;
    logs)
        show_logs
        ;;
    build)
        build_site
        ;;
    *)
        echo "Usage: $0 [start|background|stop|status|logs|build]"
        echo "  start       - Start Jekyll server interactively (default)"
        echo "  background  - Start Jekyll server as background daemon"
        echo "  stop        - Stop running Jekyll server"
        echo "  status      - Check server status"
        echo "  logs        - View and stream live server logs"
        echo "  build       - Run 'jekyll build' once without serving"
        exit 1
        ;;
esac
