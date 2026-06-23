# Separate Mutable App State From Home Manager Defaults

Edit `profile.nix`.

The starter tries to manage Thunderbird's writable profile files as read-only Home Manager files. Rewrite it so Home Manager manages stable defaults and leaves mutable profile state writable.

Requirements:

- Keep the file as a function accepting `profileDir`.
- Set `programs.thunderbird.enable = true`.
- Set `home.sessionVariables.THUNDERBIRD_PROFILE_DIR = profileDir`.
- Write managed defaults to `xdg.configFile."thunderbird/policies.json".text`.
- The policies JSON must include `"DisableAppUpdate": true`.
- Record `mutableState = [ profileDir ]` so callers know that profile directory is intentionally not Home Manager-owned.
- Do not manage `.thunderbird/profiles.ini`, `prefs.js`, or profile directories through `home.file`.
- Do not set `recursive = true` for `.thunderbird`.

## Source Context

This task is modeled after NixOS Discourse discussions where LLM advice suggested using Home Manager to bootstrap mutable GUI application state, but read-only linked files broke applications that need to write their own profile data.

- NixOS Discourse: https://discourse.nixos.org/t/purpose-of-authentications-option-home-manager/76999
- NixOS Discourse: https://discourse.nixos.org/t/strategies-for-declarative-approaches-to-programs-with-mutable-configuration-files/66276
