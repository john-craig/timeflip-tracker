{
  description = "Timeflip Tracker";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    pytimefliplib = {
      url = "git+https://gitea.chiliahedron.wtf/john-craig/pytimefliplib.git";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, pytimefliplib }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          python = pkgs.python3;
          pyPkgs = python.pkgs;

          pytimefliplibPkg = pyPkgs.buildPythonPackage {
            pname = "pytimefliplib";
            version = pytimefliplib.shortRev or "unstable";
            src = pytimefliplib;
            pyproject = true;
            build-system = [ pyPkgs.setuptools ];
            dependencies = [
              pyPkgs.bleak
            ];
          };
        in
        {
          default = pyPkgs.buildPythonApplication {
            pname = "timeflip_tracker";
            version = "0.0.0";
            src = self;
            pyproject = true;

            build-system = [ pyPkgs.setuptools ];

            nativeBuildInputs = [
              pkgs.pkg-config
              pkgs.mariadb-connector-c
            ];

            dependencies = [
              pyPkgs.aiooui
              pyPkgs.autopep8
              pyPkgs.bleak
              pyPkgs."bluetooth-adapters"
              pyPkgs.certifi
              pyPkgs."charset-normalizer"
              pyPkgs.colour
              pyPkgs."dbus-fast"
              pyPkgs."dbus-next"
              pyPkgs.flake8
              pyPkgs.idna
              pyPkgs.mariadb
              pyPkgs.mccabe
              pyPkgs.packaging
              pyPkgs."prometheus-client"
              pyPkgs.pycodestyle
              pyPkgs.pyflakes
              pyPkgs."python-dotenv"
              pytimefliplibPkg
              pyPkgs.requests
              pyPkgs."ruamel-yaml"
              pyPkgs."ruamel-yaml-clib"
              pyPkgs.toml
              pyPkgs."typing-extensions"
              pyPkgs.urllib3
              pyPkgs."usb-devices"
            ];

            MARIADB_CONFIG = "${pkgs.mariadb-connector-c}/bin/mariadb_config";

            pythonImportsCheck = [ "timeflip_tracker" ];
          };
        }
      );

      apps = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          unitTestsScript = pkgs.writeShellApplication {
            name = "unit-tests";
            runtimeInputs = [
              pkgs.python3Packages.pytest
            ];
            text = ''
              export PYTHONPATH="${self}/timeflip_tracker/src"
              exec pytest -q -p no:cacheprovider "${self}/timeflip_tracker/tests"
            '';
          };
          timeflipLocalDeviceScript = pkgs.writeShellApplication {
            name = "timeflip-local-device";
            runtimeInputs = [
              pkgs.bluez
              self.packages.${system}.default
            ];
            text = ''
              config_path="''${CONFIG_PATH:-$PWD/config.yaml}"

              if [ ! -f "$config_path" ]; then
                echo "Missing local config: $config_path" >&2
                echo "Create it from config.example.yaml and set the TimeFlip MAC address." >&2
                exit 1
              fi

              bluetoothctl show >/dev/null
              export CONFIG_PATH="$config_path"
              export LOG_LEVEL="''${LOG_LEVEL:-INFO}"
              exec timeflip-tracker "$@"
            '';
          };
        in
        {
          unit-tests = {
            type = "app";
            program = "${unitTestsScript}/bin/unit-tests";
          };

          timeflip-local-device = {
            type = "app";
            program = "${timeflipLocalDeviceScript}/bin/timeflip-local-device";
          };
        }
      );

      defaultPackage = forAllSystems (system: self.packages.${system}.default);
    };
}
