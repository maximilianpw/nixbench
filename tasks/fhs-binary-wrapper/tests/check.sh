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
  appimageTools.wrapType2 = attrs: attrs // { __appimage = "wrapType2"; };
  buildFHSUserEnv = attrs: attrs // { __fhs = true; };
  fetchurl = attrs: attrs // { __fetcher = "url"; };
  makePackage = name: { __package = name; };
  pkgs = {
    alsa-lib = makePackage "alsa-lib";
    glib = makePackage "glib";
    gtk3 = makePackage "gtk3";
  };
  result = import ${workdir}/wrapper.nix {
    inherit appimageTools buildFHSUserEnv fetchurl pkgs;
  };
  collectStrings = value:
    if builtins.isString value then [ value ]
    else if builtins.isList value then
      builtins.concatLists (map collectStrings value)
    else if builtins.isAttrs value then
      builtins.concatLists (map collectStrings (builtins.attrValues value))
    else [];
  containsLdConfig = value:
    builtins.isAttrs value
    && builtins.any
      (name:
        builtins.match ".*ld[.]so[.]conf.*" name != null
        || containsLdConfig value.\${name})
      (builtins.attrNames value);
  moduleArgs = {
    config = {};
    lib = {
      mkDefault = value: value;
      mkForce = value: value;
      mkIf = condition: value: if condition then value else {};
    };
    inherit pkgs;
  };
  inspectModule = value:
    if builtins.isFunction value then
      builtins.tryEval (
        let evaluated = value moduleArgs;
        in builtins.deepSeq evaluated evaluated
      )
    else { success = true; inherit value; };
  moduleAttempts = map inspectModule [
    (result.boot or {})
    (result.module or {})
    (result.nixosModule or {})
  ];
  mutationSurfaces = [
    (result.activation or {})
    (result.environment.extraInit or "")
    (result.environment.sessionVariables or {})
    (result.system.activationScripts or {})
    (result.system.timers or {})
    (result.system.tmpfiles or {})
    (result.systemd.timers or {})
    (result.systemd.tmpfiles or {})
  ] ++ map (attempt: attempt.value) moduleAttempts;
  mutationStrings = collectStrings mutationSurfaces;
  tmpfilesText = builtins.concatStringsSep "\n" (collectStrings [
    (result.system.tmpfiles or {})
    (result.systemd.tmpfiles or {})
  ]);
  isForbiddenMutation = text:
    builtins.match "(.|\n)*(mkdir|install[[:space:]]+-d|ln[[:space:]]+(-s|--symbolic))(.|\n)*" text != null
    && builtins.match "(.|\n)*/(usr|lib|bin)(/|[^A-Za-z0-9_-])(.|\n)*" text != null;
  hasForbiddenMutation = builtins.any isForbiddenMutation mutationStrings;
  hasForbiddenTmpfilesPath =
    builtins.match "(.|\n)*/(usr|lib|bin)(/|[^A-Za-z0-9_-])(.|\n)*" tmpfilesText != null;
  fhsPackages = result.fhsEnv.targetPkgs pkgs;
  requiredFhsPackages = [ pkgs.alsa-lib pkgs.glib pkgs.gtk3 ];
in {
  schema_version = 2;
  criteria = {
    "appimage-package" = passes (
      result.appimage.__appimage == "wrapType2"
      && result.appimage.pname == "vendor-tool" && result.appimage.version == "2.0.0"
    );
    "pinned-source" = passes (
      result.appimage.src.__fetcher == "url"
      && builtins.isString result.appimage.src.url
      && builtins.match "https?://.+" result.appimage.src.url != null
      && builtins.isString result.appimage.src.hash
      && builtins.match "sha256-[A-Za-z0-9+/]{43}=" result.appimage.src.hash != null
    );
    "fhs-runtime" = passes (
      result.fhsEnv.__fhs == true && result.fhsEnv.name == "vendor-tool-fhs"
      && builtins.all (package: builtins.elem package fhsPackages) requiredFhsPackages
      && result.fhsEnv.runScript == "vendor-tool"
    );
    "no-host-mutation" = passes (
      !containsLdConfig (result.environment.etc or {})
      && builtins.all (attempt: attempt.success) moduleAttempts
      && !hasForbiddenMutation && !hasForbiddenTmpfilesPath
      && !(result.appimage ? activation) && !(result.fhsEnv ? activation)
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"appimage-package":false,"pinned-source":false,"fhs-runtime":false,"no-host-mutation":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
