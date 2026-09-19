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
  mkShell = attrs: attrs // { __shell = true; };
  makeTool = name: { __tool = name; };
  alejandraTool = makeTool "alejandra";
  baseArgs = {
    inherit mkShell;
    nixfmt-rfc-style = makeTool "nixfmt-rfc-style";
    statix = makeTool "statix";
    deadnix = makeTool "deadnix";
    nil = makeTool "nil";
  };
  withoutAlejandra = import ${workdir}/shell.nix baseArgs;
  withAlejandra = import ${workdir}/shell.nix (baseArgs // { alejandra = alejandraTool; });
  requiredTools = [
    baseArgs.nixfmt-rfc-style
    baseArgs.statix
    baseArgs.deadnix
    baseArgs.nil
  ];
in {
  criteria = {
    "shell-construction" = passes (
      withoutAlejandra.__shell == true && withAlejandra.__shell == true
      && withoutAlejandra.name == "nixbench-dev" && withAlejandra.name == "nixbench-dev"
    );
    "required-tools" = passes (
      builtins.all (tool: builtins.elem tool withoutAlejandra.packages) requiredTools
      && !(builtins.elem null withoutAlejandra.packages)
      && builtins.all (tool: builtins.elem tool withAlejandra.packages) requiredTools
      && builtins.elem alejandraTool withAlejandra.packages
    );
    "formatter-contract" = passes (
      withoutAlejandra.NIXBENCH_FORMATTER == "nixfmt-rfc-style"
      && withAlejandra.NIXBENCH_FORMATTER == "nixfmt-rfc-style"
    );
  };
  shellHooks = {
    withoutAlejandra = withoutAlejandra.shellHook or "";
    withAlejandra = withAlejandra.shellHook or "";
  };
}
EOF

evaluation_ok=true
if ! nix eval --json --file "$tmpdir/test.nix" >"$tmpdir/evaluation.json"; then
  evaluation_ok=false
fi

python3 - "$tmpdir/evaluation.json" "$NIXBENCH_SCORE_FILE" "$evaluation_ok" <<'PY'
import json
import os
import re
import shlex
import sys


def enables_required_features(shell_hook: str) -> bool:
    lexer = shlex.shlex(shell_hook, posix=True, punctuation_chars=";\n&|")
    lexer.whitespace_split = True
    lexer.whitespace = " \t\r"
    lexer.commenters = "#"
    commands = []
    command = []
    for token in lexer:
        if token and all(character in ";\n&|" for character in token):
            if command:
                commands.append(command)
                command = []
        else:
            command.append(token)
    if command:
        commands.append(command)

    assignment = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*", re.DOTALL)
    for command in commands:
        if command[0] == "export":
            assignments = [token for token in command[1:] if assignment.fullmatch(token)]
        elif all(assignment.fullmatch(token) for token in command):
            assignments = command
        else:
            assignments = []
        for token in assignments:
            name, _, value = token.partition("=")
            if name != "NIX_CONFIG":
                continue
            features = set()
            for match in re.finditer(
                r"(?:^|\n)\s*(?:extra-)?experimental-features\s*=\s*([^\n]*)",
                value,
            ):
                features.update(match.group(1).split())
            if {"nix-command", "flakes"} <= features:
                return True
    return False


criteria = {
    "shell-construction": False,
    "required-tools": False,
    "formatter-contract": False,
    "experimental-features": False,
}
if sys.argv[3] == "true":
    with open(sys.argv[1], encoding="utf-8") as handle:
        evaluation = json.load(handle)
    criteria.update(evaluation["criteria"])
    criteria["experimental-features"] = all(
        enables_required_features(value) for value in evaluation["shellHooks"].values()
    )
payload = {"schema_version": 2, "criteria": criteria, "notes": []}
temporary = sys.argv[2] + ".tmp"
with open(temporary, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, separators=(",", ":"))
os.replace(temporary, sys.argv[2])
PY
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
