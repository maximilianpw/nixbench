{
  confidence = "observed";
  logs = [ "error: The option services.xserver.displayManager.sddm.enable does not exist" ];
  expectedStatus = "evaluation-succeeds";
  actualStatus = "evaluation-fails";
  actual = "The stale services.xserver.displayManager.sddm.enable path causes evaluation to fail.";
  expected = "The configuration should evaluate with services.displayManager.sddm.enable.";
  reproduction = [ "nixos-rebuild test --flake .#workstation" ];
  system = { nixpkgsRevision = "8f3b2d1"; nixosRelease = "25.05"; system = "x86_64-linux"; };
  failureClass = "evaluation";
  title = "Stale SDDM setting blocks evaluation";
  analysis = {
    observed = [ "services.xserver.displayManager.sddm.enable is stale; services.displayManager.sddm.enable is current." ];
    likelyFix = "Replace the former path with the latter path.";
    unverified = [];
  };
}
