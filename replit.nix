{pkgs}: {
  deps = [
    pkgs.rustc
    pkgs.pkg-config
    pkgs.openssl
    pkgs.libxcrypt
    pkgs.libiconv
    pkgs.cargo
    pkgs.lsof
    pkgs.haskellPackages.postgresql-migration
    pkgs.postgresql
    pkgs.glibcLocales
    pkgs.freetype
    pkgs.unzipNLS
  ];
}
