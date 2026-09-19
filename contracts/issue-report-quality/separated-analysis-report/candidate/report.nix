{
  title = "Workstation evaluation reports a removed display-manager setting";
  failureClass = "evaluation";
  system = {
    system = "x86_64-linux";
    nixosRelease = "25.05";
    nixpkgsRevision = "8f3b2d1";
  };
  reproduction = [ "nixos-rebuild test --flake .#workstation" ];
  expectedStatus = "evaluation-succeeds";
  actualStatus = "evaluation-fails";
  expected = "Evaluation succeeds after selecting services.displayManager.sddm.enable.";
  actual = "Evaluation fails while reading services.xserver.displayManager.sddm.enable.";
  logs = [ "error: The option services.xserver.displayManager.sddm.enable does not exist" ];
  analysis = {
    observed = [
      "Reported option: services.xserver.displayManager.sddm.enable"
      "Result: option evaluation stopped"
      "Candidate replacement: services.displayManager.sddm.enable"
    ];
    likelyFix = "Test the current path services.displayManager.sddm.enable.";
    unverified = [ "The proposed replacement has not yet been switched on this host." ];
  };
  confidence = "observed";
}
