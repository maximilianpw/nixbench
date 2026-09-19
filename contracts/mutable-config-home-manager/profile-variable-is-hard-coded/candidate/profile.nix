{ profileDir ? ".thunderbird/default" }:
{
  programs.thunderbird.enable = true;

  home.sessionVariables.THUNDERBIRD_PROFILE_DIR = ".thunderbird/default";

  xdg.configFile."thunderbird/policies.json".text = builtins.toJSON {
    policies.DisableAppUpdate = true;
  };

  mutableState = [
    profileDir
  ];
}
