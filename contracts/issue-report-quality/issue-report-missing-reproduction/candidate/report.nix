{
  title = "SDDM option path fails to evaluate on NixOS 25.05";
  failureClass = "evaluation";
  system = { system = "x86_64-linux"; nixosRelease = "25.05"; nixpkgsRevision = "8f3b2d1"; };
  reproduction = [];
  expectedStatus = "evaluation-succeeds";
  actualStatus = "evaluation-fails";
  expected = "Using services.displayManager.sddm.enable should evaluate successfully.";
  actual = "Evaluation fails at services.xserver.displayManager.sddm.enable.";
  logs = [ "error: The option services.xserver.displayManager.sddm.enable does not exist" ];
  analysis = {
    observed = [ "The stale path is services.xserver.displayManager.sddm.enable." ];
    likelyFix = "Use services.displayManager.sddm.enable.";
    unverified = [];
  };
  confidence = "observed";
}
