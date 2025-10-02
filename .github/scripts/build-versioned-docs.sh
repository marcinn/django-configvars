#!/usr/bin/env bash
set -euo pipefail

REPO_SLUG="${REPO_SLUG:-marcinn/django-configvars}"
SITE_DIR="${SITE_DIR:-site}"
PAGES_URL="${PAGES_URL:-https://marcinn.github.io/django-configvars/}"

TMP_ROOT="$(mktemp -d)"
BUILT_COUNT=0
LATEST_TAG=""
LATEST_TAG_PATH=""

cleanup() {
  if [[ -d "$TMP_ROOT" ]]; then
    git worktree prune >/dev/null 2>&1 || true
    rm -rf "$TMP_ROOT"
  fi
}

trap cleanup EXIT

build_ref() {
  local ref="$1"
  local out_dir="$2"
  local label="$3"
  local worktree_dir="$TMP_ROOT/$out_dir"

  echo "==> Building docs for $label ($ref)"
  git worktree add --force --detach "$worktree_dir" "$ref" >/dev/null

  if [[ ! -f "$worktree_dir/docs/conf.py" ]]; then
    echo "    Skipping $label (no docs/ in this ref)"
    git worktree remove --force "$worktree_dir" >/dev/null
    return 0
  fi

  DOCS_VERSION="$label" \
  DOCS_RELEASE="$label" \
  DOCS_BASE_URL="${PAGES_URL}${out_dir}/" \
  python -m sphinx -b html "$worktree_dir/docs" "$SITE_DIR/$out_dir"

  git worktree remove --force "$worktree_dir" >/dev/null
  BUILT_COUNT=$((BUILT_COUNT + 1))

  if [[ "$out_dir" != "dev" && -z "$LATEST_TAG" ]]; then
    LATEST_TAG="$label"
    LATEST_TAG_PATH="$out_dir"
  fi
}

render_root_index() {
  local index_file="$SITE_DIR/index.html"
  local versions_file="$SITE_DIR/versions.txt"

  {
    echo "<!doctype html>"
    echo "<html lang=\"en\">"
    echo "<head>"
    echo "  <meta charset=\"utf-8\">"
    echo "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
    echo "  <title>django-configvars documentation</title>"
    echo "  <style>"
    echo "    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:880px;margin:3rem auto;padding:0 1rem;color:#222;line-height:1.5;background:#fafafa}"
    echo "    h1{margin-bottom:.25rem}"
    echo "    .muted{color:#555}"
    echo "    ul{padding-left:1.25rem}"
    echo "    li{margin:.35rem 0}"
    echo "    code{background:#eee;padding:.1rem .3rem;border-radius:4px}"
    echo "    .box{background:#fff;border:1px solid #ddd;border-radius:10px;padding:1rem 1.25rem}"
    echo "  </style>"
    echo "</head>"
    echo "<body>"
    echo "  <div class=\"box\">"
    echo "    <h1>django-configvars documentation</h1>"
    echo "    <p class=\"muted\">Versioned docs published from git tags, plus a moving <code>dev</code> version from the development branch.</p>"
    if [[ -n "$LATEST_TAG_PATH" ]]; then
      echo "    <p><a href=\"./${LATEST_TAG_PATH}/\"><strong>Open latest release docs (${LATEST_TAG})</strong></a></p>"
    fi
    echo "    <h2>Available versions</h2>"
    echo "    <ul>"
    if [[ -d "$SITE_DIR/dev" ]]; then
      echo "      <li><a href=\"./dev/\">dev</a> (development branch)</li>"
    fi
    while IFS= read -r version_dir; do
      [[ -z "$version_dir" ]] && continue
      [[ "$version_dir" == "dev" ]] && continue
      echo "      <li><a href=\"./${version_dir}/\">${version_dir}</a></li>"
    done < "$versions_file"
    echo "    </ul>"
    echo "    <p class=\"muted\">Repository: <a href=\"https://github.com/${REPO_SLUG}\">${REPO_SLUG}</a></p>"
    echo "  </div>"
    echo "</body>"
    echo "</html>"
  } >"$index_file"
}

main() {
  rm -rf "$SITE_DIR"
  mkdir -p "$SITE_DIR"
  : >"$SITE_DIR/versions.txt"
  touch "$SITE_DIR/.nojekyll"

  git fetch --force --tags origin >/dev/null 2>&1 || true
  git fetch --force origin +refs/heads/devel:refs/remotes/origin/devel >/dev/null 2>&1 || true

  while IFS= read -r tag; do
    [[ -z "$tag" ]] && continue
    build_ref "refs/tags/$tag" "$tag" "$tag"
    if [[ -d "$SITE_DIR/$tag" ]]; then
      echo "$tag" >>"$SITE_DIR/versions.txt"
    fi
  done < <(git for-each-ref --sort=-version:refname --format='%(refname:strip=2)' refs/tags)

  if git show-ref --verify --quiet refs/remotes/origin/devel; then
    build_ref "refs/remotes/origin/devel" "dev" "dev"
    if [[ -d "$SITE_DIR/dev" ]]; then
      echo "dev" >>"$SITE_DIR/versions.txt"
    fi
  else
    echo "==> Branch 'devel' not found; skipping dev docs"
  fi

  if [[ "$BUILT_COUNT" -eq 0 ]]; then
    echo "No documentation versions were built."
    exit 1
  fi

  render_root_index
  rm -f "$SITE_DIR/versions.txt"
}

main "$@"
