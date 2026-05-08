{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:

{
  env.GREET = "Artist Resolver Frontend";

  packages = [ pkgs.git ];
  cachix.pull = [ "nix-linter" ];

  languages.python = {
    enable = true;
    venv.enable = false;
    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  enterShell = ''
    git --version
    python --version
    uv --version
  '';

}
