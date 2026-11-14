{
  description = "SPAICOM site: development environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let pkgs = nixpkgs.legacyPackages.${system};
      in {
        # `nix develop` (or direnv with `use flake`) gives you every tool the repo needs.
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            hugo   # static site generator (the theme needs the "extended" edition, which nixpkgs ships)
            go     # Hugo modules (the theme) are fetched with Go
            uv     # runs the Python scripts, dependencies are declared inside each script
            just   # task runner, see the justfile
            git
            gh     # GitHub CLI, used to open pull requests
          ];
          shellHook = ''
            echo "SPAICOM site dev shell: hugo $(hugo version | cut -d' ' -f2 | cut -d- -f1), run 'just' to list tasks"
          '';
        };
      });
}
