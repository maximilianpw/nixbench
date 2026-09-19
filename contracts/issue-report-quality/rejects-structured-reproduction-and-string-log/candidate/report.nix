{
  title = "SDDM configuration uses a removed services.xserver option path";
  failureClass = "evaluation";

  system = {
    system = "x86_64-linux";
    nixosRelease = "25.05";
    nixpkgsRevision = "8f3b2d1";
  };

  reproduction = {
    command = "nixos-rebuild test --flake .#workstation";
  };

  expectedStatus = "evaluation-succeeds";
  actualStatus = "evaluation-fails";

  expected = ''
    The workstation configuration should evaluate when it enables SDDM through
    the current option path, services.displayManager.sddm.enable.
  '';

  actual = ''
    Evaluation stops because the configuration refers to
    services.xserver.displayManager.sddm.enable, which does not exist.
  '';

  logs = ''
    error: The option services.xserver.displayManager.sddm.enable does not exist
  '';

  analysis = {
    observed = [
      "The configuration refers to services.xserver.displayManager.sddm.enable."
      "Evaluation reports that services.xserver.displayManager.sddm.enable does not exist."
    ];
    likelyFix = "Replace services.xserver.displayManager.sddm.enable with services.displayManager.sddm.enable.";
    unverified = [
      "Whether other configuration files still refer to the stale services.xserver display-manager path."
      "Whether the configuration evaluates after this option-path change."
    ];
  };

  confidence = "observed";
}
