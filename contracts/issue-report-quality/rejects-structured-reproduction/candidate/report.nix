{
  title = "SDDM display manager option path is stale";
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

  expected = "The configuration should evaluate using the current SDDM option path.";
  actual = "Evaluation fails because the configuration refers to an option path that does not exist.";

  logs = [
    "error: The option services.xserver.displayManager.sddm.enable does not exist"
  ];

  analysis = {
    observed = [
      "The configuration uses the stale option path services.xserver.displayManager.sddm.enable."
    ];
    likelyFix = "Replace services.xserver.displayManager.sddm.enable with services.displayManager.sddm.enable.";
    unverified = [
      "The current option path has not been checked against the referenced nixpkgs revision."
    ];
  };

  confidence = "observed";
}
