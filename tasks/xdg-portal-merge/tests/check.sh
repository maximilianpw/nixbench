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
  lib.mkIf = condition: content: {
    __mkIf = condition;
    inherit content;
  };
  lib.mkAfter = content: { __merge = "after"; value = content; };
  lib.mkForce = content: { __merge = "force"; value = content; };
  lib.mkDefault = content: content;
  pkgs = {
    xdg-desktop-portal-hyprland = "/nix/store/xdg-desktop-portal-hyprland";
  };
  evaluate = enabled: import ${workdir}/portal.nix {
    config = {
      wayland.windowManager.hyprland.enable = enabled;
      xdg.portal.extraPortals = throw "do not read an option while defining it";
      xdg.portal.configPackages = throw "do not read an option while defining it";
    };
    inherit lib pkgs;
  };
  portal = (evaluate true).xdg.portal;
  disabledPortal = (evaluate false).xdg.portal;
  existingPortals = [
    "/nix/store/existing-cosmic-portal"
    "/nix/store/existing-gtk-portal"
  ];
  existingConfigPackages = [
    "/nix/store/existing-cosmic-session"
  ];
  existingDefaults = [ "gtk" ];
  isMerge = kind: value:
    builtins.isAttrs value && (value.__merge or null) == kind;
  unwrap = value:
    if builtins.isAttrs value && value ? __merge then value.value else value;
  mergeList = existing: definition:
    if definition == null then existing
    else if isMerge "force" definition then unwrap definition
    else existing ++ unwrap definition;
  extraPortals = portal.content.extraPortals or [];
  configPackages = portal.content.configPackages or null;
  commonDefaultDefinition = portal.content.config.common.default or [];
  hyprlandDefaultDefinition = portal.content.config.hyprland.default or [];
  commonDefaults = unwrap commonDefaultDefinition;
  hyprlandDefaults = unwrap hyprlandDefaultDefinition;
  mergedPortals = mergeList existingPortals extraPortals;
  mergedConfigPackages = mergeList existingConfigPackages configPackages;
  mergedDefaults =
    mergeList (mergeList existingDefaults commonDefaultDefinition)
      hyprlandDefaultDefinition;
in {
  schema_version = 2;
  criteria = {
    "conditional-enable" = passes (
      portal.__mkIf == true && disabledPortal.__mkIf == false && portal.content.enable == true
    );
    "portal-package-merge" = passes (
      builtins.elem pkgs.xdg-desktop-portal-hyprland mergedPortals
      && builtins.elem "/nix/store/existing-cosmic-portal" mergedPortals
      && builtins.elem "/nix/store/existing-gtk-portal" mergedPortals
    );
    "config-package-preservation" = passes (
      builtins.elem "/nix/store/existing-cosmic-session" mergedConfigPackages
    );
    "fallback-merge" = passes (
      builtins.elem "hyprland" mergedDefaults
      && builtins.any (fallback: fallback != "hyprland") mergedDefaults
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"conditional-enable":false,"portal-package-merge":false,"config-package-preservation":false,"fallback-merge":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
