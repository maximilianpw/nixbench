{
  title = "SDDM option path fails to evaluate on NixOS 25.05";
  failureClass = "evaluation";

  system = {
    system = "x86_64-linux";
    nixosRelease = "25.05";
    nixpkgsRevision = "8f3b2d1";
  };

  reproduction = [
    "nixos-rebuild test --flake .#workstation"
  ];

  expectedStatus = "evaluation-succeeds";
  actualStatus = "evaluation-fails";
  expected = "The rebuild command should complete and activate the requested login manager option.";
  actual = "The rebuild command stops at services.xserver.displayManager.sddm.enable because that option is absent.";

  logs = [
    "error: The option services.xserver.displayManager.sddm.enable does not exist"
  ];

  analysis = {
    observed = [
      "The failure is an option evaluation error."
      "The stale option path is services.xserver.displayManager.sddm.enable."
    ];
    likelyFix = "Use services.displayManager.sddm.enable.";
    unverified = [];
  };

  confidence = "observed";
}
