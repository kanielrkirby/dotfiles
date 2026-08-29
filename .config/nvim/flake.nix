{
  description = "Neovim 2026 setup";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            neovim
            git
            lazygit
            fzf
            bat
            nodejs_24
            luarocks
            python3
            fd
            ripgrep
            tree-sitter
            gcc
            pkg-config
            curl
            unzip
            lazydocker
          ];
        };
      });
}
