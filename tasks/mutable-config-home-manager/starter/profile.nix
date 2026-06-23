{ profileDir ? ".thunderbird/default" }:
{
  programs.thunderbird.enable = true;

  home.file.".thunderbird/profiles.ini".text = ''
    [Profile0]
    Path=${profileDir}
  '';

  home.file.".thunderbird/default/prefs.js".text = ''
    user_pref("app.update.enabled", false);
  '';

  home.file.".thunderbird".recursive = true;
}
