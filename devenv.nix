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
      zstd
      glib
      zlib
      libGL
      libxkbcommon
      fontconfig
      libglvnd
      dbus
      freetype
      wayland
      stdenv.cc.cc.lib
      xorg.libX11
      xorg.libxcb
      xorg.xcbutil
      xorg.xcbutilcursor
      xorg.xcbutilimage
      xorg.xcbutilkeysyms
      xorg.xcbutilrenderutil
      xorg.xcbutilwm
    ]
  );

  packages = with pkgs; [
    zstd
    glib
    zlib
    libGL
    libxkbcommon
    fontconfig
    libglvnd
    dbus
    freetype
    wayland
    stdenv.cc.cc.lib
    xorg.libX11
    xorg.libxcb
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

  env = {
    # ARTIST_RESOLVER_HOST = "myendpoint.com";
    # ARTIST_RESOLVER_PORT = "80";
  };

  enterShell = ''
    export QT_PLUGIN_PATH="$DEVENV_ROOT/.devenv/state/venv/lib/python3.14/site-packages/PyQt6/Qt6/plugins"
    unset QML2_IMPORT_PATH
    git --version
    python --version
    uv --version
  '';

}
