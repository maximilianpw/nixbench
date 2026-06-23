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

  expected = "The configuration evaluates using the current SDDM option path.";
  actual = "Evaluation fails because services.xserver.displayManager.sddm.enable does not exist.";

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
