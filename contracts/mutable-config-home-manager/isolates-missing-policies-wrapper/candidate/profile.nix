{ profileDir ? ".thunderbird/default" }:
{
  programs.thunderbird.enable = true;

  home.sessionVariables.THUNDERBIRD_PROFILE_DIR = profileDir;

  xdg.configFile."thunderbird/policies.json".text = ''
    {
      "DisableAppUpdate": true
    }
  '';

  mutableState = [ profileDir ];
}
