{
  title = "NixOS 25.05 rejects the old SDDM option";
  failureClass = "evaluation";
  system = { system = "x86_64-linux"; nixosRelease = "25.05"; nixpkgsRevision = "8f3b2d1"; };
  reproduction = [
    "git checkout 8f3b2d1"
    "nixos-rebuild test --flake .#workstation"
  ];
  expectedStatus = "evaluation-succeeds";
  actualStatus = "evaluation-fails";
  expected = "services.displayManager.sddm.enable should allow evaluation to complete.";
  actual = "Evaluation stops because services.xserver.displayManager.sddm.enable is unavailable.";
  logs = [
    "evaluating the workstation configuration"
    "error: The option services.xserver.displayManager.sddm.enable does not exist"
  ];
  analysis = {
    observed = [
      "The evaluator reports services.xserver.displayManager.sddm.enable."
      "The replacement appears to be services.displayManager.sddm.enable."
    ];
    likelyFix = "Move the setting to services.displayManager.sddm.enable.";
    unverified = [
      "Whether another imported module also uses the old path is not verified."
      "A full switch was not attempted."
    ];
  };
  confidence = "observed";
}
