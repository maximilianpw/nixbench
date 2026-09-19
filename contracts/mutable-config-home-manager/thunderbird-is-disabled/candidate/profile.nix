{ profileDir ? ".thunderbird/default" }:
{
  programs.thunderbird.enable = false;

  home.sessionVariables.THUNDERBIRD_PROFILE_DIR = profileDir;

  xdg.configFile."thunderbird/policies.json".text = builtins.toJSON {
    policies.DisableAppUpdate = true;
  };

  mutableState = [
    profileDir
  ];
}
