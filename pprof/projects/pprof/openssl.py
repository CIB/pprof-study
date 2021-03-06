from pprof.projects.pprof.group import PprofGroup
from os import path
from plumbum import local


class LibreSSL(PprofGroup):
    """ OpenSSL """

    NAME = 'libressl'
    DOMAIN = 'encryption'

    src_dir = "libressl-2.1.6"
    src_file = src_dir + ".tar.gz"
    src_uri = "http://ftp.openbsd.org/pub/OpenBSD/LibreSSL/" + src_file

    def download(self):
        from pprof.utils.downloader import Wget
        from plumbum.cmd import tar

        openssl_dir = path.join(self.builddir, self.src_file)
        with local.cwd(self.builddir):
            Wget(self.src_uri, self.src_file)
            tar("xfz", openssl_dir)

    def configure(self):
        from pprof.utils.compiler import lt_clang
        from pprof.utils.run import run
        openssl_dir = path.join(self.builddir, self.src_dir)

        configure = local[path.join(openssl_dir, "configure")]
        with local.cwd(self.builddir):
            clang = lt_clang(self.cflags, self.ldflags)

        with local.cwd(openssl_dir):
            with local.env(CC=str(clang)):
                run(configure["--disable-asm"])

    def build(self):
        from plumbum.cmd import make
        from pprof.utils.run import run

        openssl_dir = path.join(self.builddir, self.src_dir)
        with local.cwd(openssl_dir):
            run(make["check"])

    def run_tests(self, experiment):
        from plumbum.cmd import find, make
        from pprof.project import wrap
        from pprof.utils.run import run

        with local.cwd(path.join(self.src_dir, "tests", ".libs")):
            files = find(".", "-type", "f", "-executable")
            for wrap_f in files.split("\n"):
                if len(wrap_f) > 0:
                    wrap(wrap_f, experiment)
        with local.cwd(self.src_dir):
            run(make["V=1", "check"])
