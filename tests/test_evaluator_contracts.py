from __future__ import annotations

import shutil
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from nixbench.runner import TaskRunResult, run_task
from nixbench.task import load_task


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class CandidateCase:
    name: str
    task_id: str
    filename: str
    replacements: tuple[tuple[str, str], ...]


INVALID_CANDIDATES = (
    CandidateCase(
        name="fetcher-empty-sri-payload",
        task_id="fetcher-source-pin",
        filename="source.nix",
        replacements=((
            'hash = "sha256-BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=";',
            'hash = "sha256-";',
        ),),
    ),
    CandidateCase(
        name="development-shell-only-comments-about-nix-config",
        task_id="devshell-tooling-contract",
        filename="shell.nix",
        replacements=((
            '    export NIX_CONFIG="experimental-features = nix-command flakes"',
            '    # export NIX_CONFIG="experimental-features = nix-command flakes"',
        ),),
    ),
    CandidateCase(
        name="development-shell-assigns-an-empty-nix-config",
        task_id="devshell-tooling-contract",
        filename="shell.nix",
        replacements=((
            '    export NIX_CONFIG="experimental-features = nix-command flakes"',
            '    # nix-command flakes\n    export NIX_CONFIG=""',
        ),),
    ),
    CandidateCase(
        name="flake-app-missing-package-metadata",
        task_id="flake-per-system-outputs",
        filename="flake.nix",
        replacements=((
            "        meta.package = packages.${system}.default.pname;\n",
            "",
        ),),
    ),
    CandidateCase(
        name="fhs-wrapper-creates-a-global-host-directory",
        task_id="fhs-binary-wrapper",
        filename="wrapper.nix",
        replacements=((
            "  fhsEnv = buildFHSUserEnv {",
            "  activation = \"mkdir -p /usr/lib\";\n\n  fhsEnv = buildFHSUserEnv {",
        ),),
    ),
    CandidateCase(
        name="fhs-wrapper-creates-a-global-tmpfiles-entry",
        task_id="fhs-binary-wrapper",
        filename="wrapper.nix",
        replacements=((
            '    runScript = "vendor-tool";\n  };\n}',
            '    runScript = "vendor-tool";\n  };\n\n'
            '  systemd.tmpfiles.rules = [ "d /usr/lib 0755 root root -" ];\n}',
        ),),
    ),
    CandidateCase(
        name="fhs-wrapper-fetches-an-unpinned-empty-source",
        task_id="fhs-binary-wrapper",
        filename="wrapper.nix",
        replacements=((
            "    src = fetchurl {\n"
            '      url = "https://example.invalid/vendor-tool-2.0.0.AppImage";\n'
            '      hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";\n'
            "    };",
            "    src = fetchurl {};",
        ),),
    ),
    CandidateCase(
        name="home-manager-hard-coded-directory",
        task_id="home-manager-xdg-files",
        filename="home.nix",
        replacements=((
            'documents = "${homeDirectory}/Documents";',
            'documents = "/home/alice/Documents";',
        ),),
    ),
    CandidateCase(
        name="home-manager-placeholder-is-not-text",
        task_id="home-manager-xdg-files",
        filename="home.nix",
        replacements=((
            'home.file."GitHub_Repos/.keep".text = "";',
            'home.file."GitHub_Repos/.keep".text = null;',
        ),),
    ),
    CandidateCase(
        name="home-manager-forwards-only-known-inputs",
        task_id="home-manager-extra-special-args",
        filename="flake.nix",
        replacements=((
            "home-manager.extraSpecialArgs = { inherit inputs; };",
            "home-manager.extraSpecialArgs.inputs = { inherit (inputs) nixvim agenix; };",
        ),),
    ),
    CandidateCase(
        name="issue-report-missing-expected-behavior",
        task_id="issue-report-quality",
        filename="report.nix",
        replacements=((
            '  expected = "The configuration evaluates using the current SDDM option path.";\n',
            "",
        ),),
    ),
    CandidateCase(
        name="issue-report-contradicts-the-observed-outcome",
        task_id="issue-report-quality",
        filename="report.nix",
        replacements=(
            (
                'expected = "The configuration evaluates using the current SDDM option path.";',
                'expected = "The configuration should keep failing.";',
            ),
            (
                'actual = "Evaluation fails because services.xserver.displayManager.sddm.enable does not exist.";',
                'actual = "The command succeeds with no errors.";',
            ),
        ),
    ),
    CandidateCase(
        name="issue-report-claims-a-confirmed-root-cause",
        task_id="issue-report-quality",
        filename="report.nix",
        replacements=((
            "  analysis = {",
            '  analysis = {\n    confirmedRootCause = "The stale option definitely caused the failure.";',
        ),),
    ),
    CandidateCase(
        name="attrset-normalizer-removes-argument-defaults",
        task_id="lang-attrsets-normalize",
        filename="lib.nix",
        replacements=(
            (
                '  allSystems ? ["x86_64-linux" "aarch64-linux" "aarch64-darwin"],',
                "  allSystems,",
            ),
            ('  defaultSystem ? "x86_64-linux",', "  defaultSystem,"),
        ),
    ),
    CandidateCase(
        name="attrset-normalizer-hard-codes-the-default-system-universe",
        task_id="lang-attrsets-normalize",
        filename="lib.nix",
        replacements=((
            "    allSystems);",
            '    [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ]);',
        ),),
    ),
    CandidateCase(
        name="service-hard-codes-enabled-condition",
        task_id="module-service-options",
        filename="module.nix",
        replacements=(("config = lib.mkIf cfg.enable", "config = lib.mkIf true"),),
    ),
    CandidateCase(
        name="service-declares-wrong-port-type",
        task_id="module-service-options",
        filename="module.nix",
        replacements=(("type = lib.types.port;", "type = lib.types.str;"),),
    ),
    CandidateCase(
        name="service-uses-an-unavailable-lib-helper",
        task_id="module-service-options",
        filename="module.nix",
        replacements=(("builtins.concatStringsSep", "lib.concatStringsSep"),),
    ),
    CandidateCase(
        name="network-diagnosis-never-returns-unknown",
        task_id="debug-network-false-lead",
        filename="diagnosis.nix",
        replacements=((
            '    rootCause = "unknown";',
            '    rootCause = "dns-resolution";',
        ),),
    ),
    CandidateCase(
        name="network-diagnosis-blames-audio-in-its-evidence",
        task_id="debug-network-false-lead",
        filename="diagnosis.nix",
        replacements=(
            ('"gateway arp failed"', '"audio and HDMI are the cause"'),
            ('"gateway arp is reachable"', '"audio appears healthy"'),
        ),
    ),
    CandidateCase(
        name="nushell-hook-only-mentions-the-contract",
        task_id="nushell-command-not-found",
        filename="module.nix",
        replacements=(
            (
                "      def __nix_command_not_found [command: string] {",
                "      # hooks.command_not_found /nix/store/nix-index/bin/command-not-found",
            ),
            (
                "      $env.config = ($env.config | upsert hooks.command_not_found {|hooks|",
                "      # hooks.command_not_found",
            ),
        ),
    ),
    CandidateCase(
        name="nushell-registers-an-empty-hook-list",
        task_id="nushell-command-not-found",
        filename="module.nix",
        replacements=((
            "      $env.config = ($env.config | upsert hooks.command_not_found {|hooks|",
            "      $env.config.hooks.command_not_found = []",
        ),),
    ),
    CandidateCase(
        name="mutable-profile-hides-prefs-behind-a-target",
        task_id="mutable-config-home-manager",
        filename="profile.nix",
        replacements=((
            "  mutableState = [\n    profileDir\n  ];",
            '  mutableState = [\n    profileDir\n  ];\n\n  home.file.sneaky.target = profileDir + "/prefs.js";',
        ),),
    ),
    CandidateCase(
        name="overlay-appends-wrong-patch",
        task_id="overlay-override-package",
        filename="overlay.nix",
        replacements=(("muslPatch = ./fix-musl.patch;", "muslPatch = ./overlay.nix;"),),
    ),
    CandidateCase(
        name="overlay-debug-package-bypasses-final",
        task_id="overlay-override-package",
        filename="overlay.nix",
        replacements=(
            ("in {", "in rec {"),
            ("tinygrep-debug = final.tinygrep.overrideAttrs", "tinygrep-debug = tinygrep.overrideAttrs"),
        ),
    ),
    CandidateCase(
        name="overlay-exports-an-unrelated-attribute",
        task_id="overlay-module-boundary",
        filename="overlay.nix",
        replacements=((
            '    installFlags = [ "DESTDIR=$(out)" ];\n  };\n}',
            '    installFlags = [ "DESTDIR=$(out)" ];\n  };\n  unrelated = true;\n}',
        ),),
    ),
    CandidateCase(
        name="overlay-uses-prev-for-runtime-inputs",
        task_id="overlay-module-boundary",
        filename="overlay.nix",
        replacements=((
            "buildInputs = [ final.iproute final.curl ];",
            "buildInputs = [ prev.iproute prev.curl ];",
        ),),
    ),
    CandidateCase(
        name="package-list-hard-codes-lookalike-values",
        task_id="package-name-lookup-contract",
        filename="packages.nix",
        replacements=tuple(
            (f"pkgs.{name}", f'"{name}"')
            for name in (
                "git",
                "ripgrep",
                "fd",
                "bat",
                "eza",
                "nixfmt-rfc-style",
                "nil",
                "statix",
                "deadnix",
            )
        ),
    ),
    CandidateCase(
        name="python-package-uses-wrong-license",
        task_id="package-python-application",
        filename="default.nix",
        replacements=(("license = lib.licenses.asl20;", "license = lib.licenses.mit;"),),
    ),
    CandidateCase(
        name="cuda-package-hard-codes-a-dependency-name",
        task_id="python-cuda-uv2nix-patch",
        filename="python-cuda.nix",
        replacements=(("python.pkgs.hatchling", '"hatchling"'),),
    ),
    CandidateCase(
        name="cuda-package-comments-out-the-patchelf-search-path",
        task_id="python-cuda-uv2nix-patch",
        filename="python-cuda.nix",
        replacements=((
            "    addAutoPatchelfSearchPath ${python.pkgs.torch}/${python.sitePackages}/torch/lib",
            "    # addAutoPatchelfSearchPath ${python.pkgs.torch}/${python.sitePackages}/torch/lib",
        ),),
    ),
    CandidateCase(
        name="cuda-package-exports-an-impure-library-path-in-a-phase",
        task_id="python-cuda-uv2nix-patch",
        filename="python-cuda.nix",
        replacements=((
            "  preFixup = ''",
            '  preBuild = "export LD_LIBRARY_PATH=/tmp/host-libs";\n\n  preFixup = \'\'',
        ),),
    ),
    CandidateCase(
        name="cuda-package-hard-codes-the-torch-library-path",
        task_id="python-cuda-uv2nix-patch",
        filename="python-cuda.nix",
        replacements=((
            "${python.pkgs.torch}/${python.sitePackages}/torch/lib",
            "/nix/store/torch/lib/python3.12/site-packages/torch/lib",
        ),),
    ),
    CandidateCase(
        name="stdenv-package-comments-out-the-install",
        task_id="package-stdenv-cli",
        filename="package.nix",
        replacements=((
            "    install -Dm755 tinygrep $out/bin/tinygrep",
            "    # install -Dm755 tinygrep $out/bin/tinygrep",
        ),),
    ),
    CandidateCase(
        name="stdenv-package-hides-the-install-in-an-inline-comment",
        task_id="package-stdenv-cli",
        filename="package.nix",
        replacements=((
            "    install -Dm755 tinygrep $out/bin/tinygrep",
            "    true # install -Dm755 tinygrep $out/bin/tinygrep",
        ),),
    ),
    CandidateCase(
        name="stdenv-package-uses-null-hash",
        task_id="package-stdenv-cli",
        filename="package.nix",
        replacements=((
            'hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";',
            "hash = null;",
        ),),
    ),
    CandidateCase(
        name="pure-wrapper-uses-forbidden-get-exe-helper",
        task_id="purity-wrapper-derivation",
        filename="derivation.nix",
        replacements=(("${bash}/bin/bash", "${lib.getExe bash}"),),
    ),
    CandidateCase(
        name="pure-wrapper-hard-codes-a-bash-store-path",
        task_id="purity-wrapper-derivation",
        filename="derivation.nix",
        replacements=(("${bash}/bin/bash", "/nix/store/bash/bin/bash"),),
    ),
    CandidateCase(
        name="cuda-package-runs-pip-in-a-different-phase",
        task_id="python-cuda-uv2nix-patch",
        filename="python-cuda.nix",
        replacements=((
            "    addAutoPatchelfSearchPath ${python.pkgs.torch}/${python.sitePackages}/torch/lib\n",
            "    addAutoPatchelfSearchPath ${python.pkgs.torch}/${python.sitePackages}/torch/lib\n    pip install .\n",
        ),),
    ),
    CandidateCase(
        name="systemd-command-does-not-append-output",
        task_id="string-escaping-systemd",
        filename="service.nix",
        replacements=((" >> ", " "),),
    ),
    CandidateCase(
        name="systemd-command-appends-separately-from-the-message",
        task_id="string-escaping-systemd",
        filename="service.nix",
        replacements=((" >> ", " > /dev/null; : >> "),),
    ),
    CandidateCase(
        name="portal-configuration-hard-codes-enabled-condition",
        task_id="xdg-portal-merge",
        filename="portal.nix",
        replacements=(("lib.mkIf cfg.enable", "lib.mkIf true"),),
    ),
    CandidateCase(
        name="rust-model-fetch-has-an-empty-hash",
        task_id="rust-no-network-build",
        filename="package.nix",
        replacements=((
            'hash = "sha256-CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC=";',
            'hash = "";',
        ),),
    ),
    CandidateCase(
        name="rust-build-phase-downloads-an-asset",
        task_id="rust-no-network-build",
        filename="package.nix",
        replacements=((
            "      --replace-fail 'download_model()' 'use_pinned_model()'",
            "      --replace-fail 'download_model()' 'use_pinned_model()'\n"
            "    curl https://models.example.invalid/vision-indexer/model-v1.onnx",
        ),),
    ),
    CandidateCase(
        name="rust-build-environment-only-names-required-concepts",
        task_id="rust-no-network-build",
        filename="package.nix",
        replacements=(
            (
                '    ORT_DYLIB_PATH = "${onnxruntime}/lib/libonnxruntime.so";',
                '    ORT_NOTE = "onnxruntime";',
            ),
            (
                '    VISION_INDEXER_MODEL = "${model}";',
                '    MODEL_NOTE = "vision-indexer-model";',
            ),
        ),
    ),
    CandidateCase(
        name="rust-build-environment-contains-an-unused-http-url",
        task_id="rust-no-network-build",
        filename="package.nix",
        replacements=((
            "  env = {",
            '  env = {\n    UNUSED_URL = "http://evil.invalid/model";',
        ),),
    ),
)


VALID_ALTERNATIVES = (
    CandidateCase(
        name="diagnostic-evidence-uses-different-wording",
        task_id="debug-network-false-lead",
        filename="diagnosis.nix",
        replacements=(
            ('"gateway arp failed"', '"ARP resolution for the gateway failed"'),
            ('"gateway arp is reachable"', '"ARP confirms that the gateway is reachable"'),
        ),
    ),
    CandidateCase(
        name="development-tools-use-a-different-order",
        task_id="devshell-tooling-contract",
        filename="shell.nix",
        replacements=(
            (
                "      nixfmt-rfc-style\n      statix\n      deadnix\n      nil",
                "      nil\n      deadnix\n      statix\n      nixfmt-rfc-style",
            ),
            ("nix-command flakes", "flakes nix-command"),
        ),
    ),
    CandidateCase(
        name="fhs-packages-use-a-different-order",
        task_id="fhs-binary-wrapper",
        filename="wrapper.nix",
        replacements=((
            "      pkgs.alsa-lib\n      pkgs.glib\n      pkgs.gtk3",
            "      pkgs.gtk3\n      pkgs.alsa-lib\n      pkgs.glib",
        ),),
    ),
    CandidateCase(
        name="system-packages-use-a-different-order",
        task_id="flake-input-package-selection",
        filename="packages.nix",
        replacements=((
            "    pkgs.mangohud\n    inputs.legacylauncher.packages.${pkgs.system}.legacylauncher\n    pkgs.libreoffice-fresh",
            "    pkgs.libreoffice-fresh\n    pkgs.mangohud\n    inputs.legacylauncher.packages.${pkgs.system}.legacylauncher",
        ),),
    ),
    CandidateCase(
        name="fhs-wrapper-keeps-descriptive-metadata",
        task_id="fhs-binary-wrapper",
        filename="wrapper.nix",
        replacements=((
            "    };\n  };",
            '    };\n    meta.description = "Wraps software that expects /bin paths";\n  };',
        ),),
    ),
    CandidateCase(
        name="issue-report-rewords-the-likely-fix",
        task_id="issue-report-quality",
        filename="report.nix",
        replacements=((
            'likelyFix = "Use services.displayManager.sddm.enable.";',
            'likelyFix = "The current option appears to be services.displayManager.sddm.enable.";',
        ),),
    ),
    CandidateCase(
        name="issue-report-records-an-unverified-question",
        task_id="issue-report-quality",
        filename="report.nix",
        replacements=((
            "    unverified = [];",
            '    unverified = [ "Whether another module introduced the stale path remains unverified." ];',
        ),),
    ),
    CandidateCase(
        name="issue-report-rewords-expected-and-actual-behavior",
        task_id="issue-report-quality",
        filename="report.nix",
        replacements=(
            (
                'expected = "The configuration evaluates using the current SDDM option path.";',
                'expected = "Using services.displayManager.sddm.enable should evaluate successfully.";',
            ),
            (
                'actual = "Evaluation fails because services.xserver.displayManager.sddm.enable does not exist.";',
                'actual = "The stale services.xserver.displayManager.sddm.enable option triggers an evaluation error.";',
            ),
        ),
    ),
    CandidateCase(
        name="nushell-hook-uses-a-different-function-name",
        task_id="nushell-command-not-found",
        filename="module.nix",
        replacements=(
            ("__nix_command_not_found", "handle_missing_command"),
            ("__nix_command_not_found", "handle_missing_command"),
        ),
    ),
    CandidateCase(
        name="service-does-not-add-an-undocumented-wanted-by-target",
        task_id="module-service-options",
        filename="module.nix",
        replacements=((
            '      wantedBy = ["multi-user.target"];\n',
            "",
        ),),
    ),
    CandidateCase(
        name="stale-option-migration-keeps-an-unrelated-xserver-option",
        task_id="module-stale-option-migration",
        filename="module.nix",
        replacements=((
            "    services.displayManager.sddm.enable = true;",
            "    services.displayManager.sddm.enable = true;\n    services.xserver.enable = true;",
        ),),
    ),
    CandidateCase(
        name="mutable-profile-keeps-unrelated-managed-files-and-policies",
        task_id="mutable-config-home-manager",
        filename="profile.nix",
        replacements=(
            (
                "    policies.DisableAppUpdate = true;",
                "    policies = {\n      DisableAppUpdate = true;\n      OfferToSaveLogins = false;\n    };",
            ),
            (
                "  mutableState = [\n    profileDir\n  ];",
                '  mutableState = [\n    profileDir\n  ];\n\n  home.file."notes.txt".text = "managed note";',
            ),
        ),
    ),
    CandidateCase(
        name="wsl-module-keeps-an-unrelated-import",
        task_id="home-manager-wsl-module-import",
        filename="configuration.nix",
        replacements=((
            "    homeManagerModule\n",
            "    homeManagerModule\n    { extra = true; }\n",
        ),),
    ),
    CandidateCase(
        name="wsl-module-has-an-inline-explanatory-comment",
        task_id="home-manager-wsl-module-import",
        filename="configuration.nix",
        replacements=((
            "    homeManagerModule\n",
            "    homeManagerModule # do not use <home-manager/nixos>\n",
        ),),
    ),
    CandidateCase(
        name="python-dependencies-use-a-different-order",
        task_id="package-python-application",
        filename="default.nix",
        replacements=((
            "with python3Packages; [click rich]",
            "with python3Packages; [rich click]",
        ),),
    ),
    CandidateCase(
        name="stdenv-package-uses-a-one-line-install-phase",
        task_id="package-stdenv-cli",
        filename="package.nix",
        replacements=((
            "  installPhase = ''\n"
            "    runHook preInstall\n"
            "    install -Dm755 tinygrep $out/bin/tinygrep\n"
            "    installShellCompletion --cmd tinygrep --bash completions/tinygrep.bash\n"
            "    runHook postInstall\n"
            "  '';",
            '  installPhase = "install -Dm755 tinygrep $out/bin/tinygrep";',
        ),),
    ),
    CandidateCase(
        name="stdenv-package-copies-the-binary",
        task_id="package-stdenv-cli",
        filename="package.nix",
        replacements=((
            "    install -Dm755 tinygrep $out/bin/tinygrep",
            "    mkdir -p $out/bin\n    cp tinygrep $out/bin/tinygrep",
        ),),
    ),
    CandidateCase(
        name="python-package-keeps-an-additional-runtime-helper",
        task_id="package-python-application",
        filename="default.nix",
        replacements=((
            "with python3Packages; [click rich]",
            'with python3Packages; [click rich { package = "runtime-helper"; marker = 149; }]',
        ),),
    ),
    CandidateCase(
        name="rust-package-relies-on-the-pinned-model-environment",
        task_id="rust-no-network-build",
        filename="package.nix",
        replacements=((
            "  postPatch = ''\n"
            "    substituteInPlace crates/model/build.rs \\\n"
            "      --replace-fail 'download_model()' 'use_pinned_model()'\n"
            "  '';\n\n",
            "",
        ),),
    ),
    CandidateCase(
        name="rust-package-comments-that-network-is-forbidden",
        task_id="rust-no-network-build",
        filename="package.nix",
        replacements=((
            "  postPatch = ''",
            "  preBuild = ''\n    # Never curl https://example.invalid during the build\n  '';\n\n  postPatch = ''",
        ),),
    ),
    CandidateCase(
        name="portal-fallbacks-include-an-additional-desktop",
        task_id="xdg-portal-merge",
        filename="portal.nix",
        replacements=((
            '      "hyprland"\n      "gtk"\n    ];\n  };\n}',
            '      "hyprland"\n      "gtk"\n      "cosmic"\n    ];\n  };\n}',
        ),),
    ),
    CandidateCase(
        name="pure-wrapper-keeps-an-additional-native-tool",
        task_id="purity-wrapper-derivation",
        filename="derivation.nix",
        replacements=((
            "nativeBuildInputs = [makeWrapper];",
            "nativeBuildInputs = [makeWrapper coreutils];",
        ),),
    ),
    CandidateCase(
        name="pure-wrapper-keeps-an-inline-explanatory-comment",
        task_id="purity-wrapper-derivation",
        filename="derivation.nix",
        replacements=((
            "nativeBuildInputs = [makeWrapper];",
            "nativeBuildInputs = [makeWrapper]; # avoid lib.getExe here",
        ),),
    ),
    CandidateCase(
        name="systemd-command-appends-with-tee",
        task_id="string-escaping-systemd",
        filename="service.nix",
        replacements=((" >> ", " | tee -a "),),
    ),
    CandidateCase(
        name="systemd-module-keeps-an-inline-explanatory-comment",
        task_id="string-escaping-systemd",
        filename="service.nix",
        replacements=((
            'StateDirectory = "quote-runner";',
            'StateDirectory = "quote-runner"; # never use /bin/sh here',
        ),),
    ),
)


@unittest.skipIf(shutil.which("nix") is None, "nix is required for evaluator contract tests")
class EvaluatorContractTests(unittest.TestCase):
    def test_invalid_candidates_are_rejected(self) -> None:
        for case in INVALID_CANDIDATES:
            with self.subTest(case=case.name):
                result, log = self._run_case(case)
                self.assertFalse(result.passed, f"{case.name} unexpectedly passed:\n{log}")
                self.assertTrue(result.score_valid, log)
                self.assertFalse(result.check.timed_out, log)
                self.assertEqual(result.check.returncode, 1, log)

    def test_valid_alternatives_are_accepted(self) -> None:
        for case in VALID_ALTERNATIVES:
            with self.subTest(case=case.name):
                result, log = self._run_case(case)
                self.assertTrue(result.passed, f"{case.name} unexpectedly failed:\n{log}")

    def _run_case(self, case: CandidateCase) -> tuple[TaskRunResult, str]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = REPO_ROOT / "tasks" / case.task_id
            task_root = root / case.task_id
            shutil.copytree(source, task_root)
            shutil.copytree(task_root / "reference", task_root / "starter", dirs_exist_ok=True)

            candidate_path = task_root / "starter" / case.filename
            text = candidate_path.read_text()
            for old, new in case.replacements:
                self.assertIn(old, text, f"stale mutation in {case.name}: {old!r}")
                text = text.replace(old, new, 1)
            candidate_path.write_text(text)

            task = load_task(task_root)
            result = run_task(
                task,
                results_dir=root / "results",
                run_id=case.name,
                solution_mode="starter",
            )

            log = Path(result.check.log_path).read_text()
            return result, log


if __name__ == "__main__":
    unittest.main()
