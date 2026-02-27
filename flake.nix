{
  description = "Timeflip Tracker";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    pytimefliplib = {
      url = "github:pierre-24/pytimefliplib";
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
        in
        {
          unit-tests = {
            type = "app";
            program = "${unitTestsScript}/bin/unit-tests";
          };
        }
      );

      defaultPackage = forAllSystems (system: self.packages.${system}.default);
    };
}
