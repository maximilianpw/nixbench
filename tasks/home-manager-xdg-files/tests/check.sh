#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
command -v nix >/dev/null 2>&1 || exit 2
command -v python3 >/dev/null 2>&1 || exit 2

cat > "$tmpdir/test.nix" <<EOF
let
  passes = value:
    let attempt = builtins.tryEval (builtins.deepSeq value value);
    in attempt.success && attempt.value == true;
  aliceHome = import ${workdir}/home.nix {
    homeDirectory = "/home/alice";
    configText = "theme = \"dark\"\n";
  };
  bobHome = import ${workdir}/home.nix {
    homeDirectory = "/srv/users/bob";
    configText = "theme = \"light\"\nfont = \"mono\"\n";
  };
  homeChecks = homeDirectory: configText: home:
    let
      fileEntries =
        builtins.attrValues (home.home.file or {})
        ++ builtins.attrValues (home.xdg.configFile or {})
        ++ builtins.attrValues (home.xdg.dataFile or {});
      activeFileText = entry:
        if !builtins.isAttrs entry then ""
        else builtins.concatStringsSep "\n" [
          (entry.onChange or "")
          (if entry.executable or false then entry.text or "" else "")
        ];
      usesImperativeFileHook = entry:
        let
          text = activeFileText entry;
          usesMkdir = builtins.match "(.|\n)*mkdir(.|\n)*" text != null;
          usesSymlink =
            builtins.match "(.|\n)*ln[[:space:]]+(-s|--symbolic)([[:space:]]|$)(.|\n)*" text != null;
        in usesMkdir || usesSymlink;
    in {
      userDirectories =
        home.xdg.userDirs.enable == true
        && home.xdg.userDirs.createDirectories == true
        && home.xdg.userDirs.documents == "\${homeDirectory}/Documents"
        && home.xdg.userDirs.download == "\${homeDirectory}/Downloads";
      configText = home.xdg.configFile."nixbench/app.toml".text == configText;
      placeholder =
        home.home.file ? "GitHub_Repos/.keep"
        && home.home.file."GitHub_Repos/.keep" ? text
        && builtins.isString home.home.file."GitHub_Repos/.keep".text;
      noImperativeHooks =
        !(home.home ? activation)
        && builtins.all (entry: !usesImperativeFileHook entry) fileEntries;
    };
  sourcePaths = home:
    let
      fileEntries =
        builtins.attrValues (home.home.file or {})
        ++ builtins.attrValues (home.xdg.configFile or {})
        ++ builtins.attrValues (home.xdg.dataFile or {});
    in map
      (entry: builtins.toString entry.source)
      (builtins.filter
        (entry:
          builtins.isAttrs entry
          && (entry.executable or false)
          && entry ? source
          && builtins.isPath entry.source)
        fileEntries);
  alice = homeChecks "/home/alice" "theme = \"dark\"\n" aliceHome;
  bob = homeChecks "/srv/users/bob" "theme = \"light\"\nfont = \"mono\"\n" bobHome;
in {
  criteria = {
    "user-directories" = passes (alice.userDirectories && bob.userDirectories);
    "config-text" = passes (alice.configText && bob.configText);
    "placeholder-file" = passes (alice.placeholder && bob.placeholder);
    "no-imperative-hooks" = passes (alice.noImperativeHooks && bob.noImperativeHooks);
  };
  sources = sourcePaths aliceHome ++ sourcePaths bobHome;
}
EOF

evaluation_ok=true
if ! nix eval --json --file "$tmpdir/test.nix" >"$tmpdir/active-files.json"; then
  evaluation_ok=false
fi

python3 - "$workdir" "$tmpdir/active-files.json" "$NIXBENCH_SCORE_FILE" "$evaluation_ok" <<'PY'
import json
import os
import re
import sys
from pathlib import Path


workdir = Path(sys.argv[1]).resolve()
criteria = {
    "user-directories": False,
    "config-text": False,
    "placeholder-file": False,
    "no-imperative-hooks": False,
}
source_paths = []
if sys.argv[4] == "true":
    with open(sys.argv[2], encoding="utf-8") as handle:
        evaluation = json.load(handle)
    criteria.update(evaluation["criteria"])
    source_paths = evaluation["sources"]

imperative = re.compile(r"\bmkdir\b|\bln\s+(?:-s|--symbolic)(?:\s|$)")
for source_path in source_paths:
    source = Path(source_path)
    try:
        resolved = source.resolve(strict=True)
        resolved.relative_to(workdir)
    except (OSError, ValueError):
        continue
    if source.is_symlink() or not resolved.is_file():
        continue
    if imperative.search(resolved.read_text(encoding="utf-8", errors="replace")):
        criteria["no-imperative-hooks"] = False

payload = {"schema_version": 2, "criteria": criteria, "notes": []}
temporary = sys.argv[3] + ".tmp"
with open(temporary, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, separators=(",", ":"))
os.replace(temporary, sys.argv[3])
PY
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
