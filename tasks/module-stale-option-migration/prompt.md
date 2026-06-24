# Migrate Stale NixOS Options

Edit `module.nix`.

The starter uses older NixOS option paths. Rewrite it to use the current option names for a Plasma desktop module:

- Enable SDDM with `services.displayManager.sddm.enable`.
- Enable Plasma 6 with `services.desktopManager.plasma6.enable`.
- Enable graphics with `hardware.graphics.enable`.
- Enable KDE Connect with `programs.kdeconnect.enable`.
- Do not keep the old `services.xserver.displayManager`, `services.xserver.desktopManager.plasma5`, or `hardware.opengl` paths.

## Source Context

This task is modeled after community complaints that LLM answers for NixOS often lag current releases and suggest deprecated or removed options.

- Reddit: https://www.reddit.com/r/NixOS/comments/1k0s6co/nixos_llms_is_really_exciting/
- Reddit: https://www.reddit.com/r/NixOS/comments/1dkgkso/best_language_model_for_nix_language_questions/
