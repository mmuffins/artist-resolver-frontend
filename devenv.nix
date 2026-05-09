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
    ]
  );

  packages = with pkgs; [
    python3Packages.pyqt6
    qt6.qtbase
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

    # Because Qt6 applications on Nix need to find their plugins and schemas.
    QT_PLUGIN_PATH = "${pkgs.qt6.qtbase}/${pkgs.qt6.qtbase.qtPluginPrefix}";
    QML2_IMPORT_PATH = "${pkgs.qt6.qtbase}/${pkgs.qt6.qtbase.qtQmlPrefix}";
  };

  enterShell = ''
    git --version
    python --version
    uv --version
  '';

}
