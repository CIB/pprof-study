from pprof.projects.pprof.group import PprofGroup
from os import path
from plumbum import local


class Linpack(PprofGroup):
    """ Linpack (C-Version) """

    NAME = 'linpack'
    DOMAIN = 'scientific'

    src_uri = "http://www.netlib.org/benchmark/linpackc.new"

    def download(self):
        from pprof.utils.downloader import Wget
        from plumbum.cmd import patch, cp

        lp_patch = path.join(self.sourcedir, "linpack.patch")
        with local.cwd(self.builddir):
            Wget(self.src_uri, "linpackc.new")
            cp("-a", "linpackc.new", "linpack.c")

            (patch["-p0"] < lp_patch)()

    def configure(self):
        pass

    def build(self):
        from pprof.utils.compiler import lt_clang
        from pprof.utils.run import run

        cflags = self.cflags
        ldflags = self.ldflags + ["-lm"]

        with local.cwd(self.builddir):
            clang = lt_clang(cflags, ldflags, self.compiler_extension)
            run(clang["-o", self.run_f, "linpack.c"])
