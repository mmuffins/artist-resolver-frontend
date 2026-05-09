{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:

{
  env.GREET = "Artist Resolver Frontend";
  env.LD_LIBRARY_PATH = lib.makeLibraryPath (
    with pkgs;
    [
      libGL
      libglvnd
      glib
      dbus
      fontconfig
      freetype
      libxkbcommon
      wayland
      stdenv.cc.cc.lib
      zlib
      zstd
      xorg.libX11
      xorg.libXcursor
      xorg.libXi
      xorg.libXext
      xorg.libXfixes
      xorg.libXrandr
      xorg.libXrender
      xorg.libxcb
      xorg.libxkbfile
      xorg.libSM
      xorg.libICE
      xorg.xcbutil
      xorg.xcbutilcursor
      xorg.xcbutilimage
      xorg.xcbutilkeysyms
      xorg.xcbutilrenderutil
      xorg.xcbutilwm
    ]
  );

  packages = with pkgs; [
    git
    libGL
    libglvnd
    glib
    dbus
    fontconfig
    freetype
    libxkbcommon
    wayland
    stdenv.cc.cc.lib
    zlib
    zstd
    xorg.libX11
    xorg.libXcursor
    xorg.libXi
    xorg.libXext
    xorg.libXfixes
    xorg.libXrandr
    xorg.libXrender
    xorg.libxcb
    xorg.libxkbfile
    xorg.libSM
    xorg.libICE
    xorg.xcbutil
    xorg.xcbutilcursor
    xorg.xcbutilimage
    xorg.xcbutilkeysyms
    xorg.xcbutilrenderutil
    xorg.xcbutilwm
  ];
  cachix.pull = [ "nix-linter" ];

  languages.python = {
    enable = true;
    version = "3.14";
    venv.enable = true;
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
