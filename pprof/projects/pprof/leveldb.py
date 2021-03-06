from pprof.projects.pprof.group import PprofGroup
from os import path
from plumbum import local


class LevelDB(PprofGroup):
    NAME = 'leveldb'
    DOMAIN = 'database'

    src_uri = "https://github.com/google/leveldb"

    def download(self):
        from pprof.utils.downloader import Git

        with local.cwd(self.builddir):
            Git(self.src_uri, "leveldb.src")

    def configure(self):
        pass

    def build(self):
        from plumbum.cmd import make
        from pprof.utils.compiler import lt_clang, lt_clang_cxx
        from pprof.utils.run import run

        leveldb_dir = path.join(self.builddir, "leveldb.src")

        with local.cwd(self.builddir):
            clang = lt_clang(self.cflags, self.ldflags,
                             self.compiler_extension)
            clang_cxx = lt_clang_cxx(self.cflags, self.ldflags,
                                     self.compiler_extension)

        with local.cwd(leveldb_dir):
            with local.env(CXX=str(clang_cxx), CC=str(clang)):
                run(make["clean", "out-static/db_bench"])

    def run_tests(self, experiment):
        """
        Execute LevelDB's runtime configuration.

        Args:
            experiment: The experiment's run function.
        """
        from pprof.project import wrap
        from pprof.utils.run import run

        leveldb_dir = path.join(self.builddir, "leveldb.src")
        exp = wrap(path.join(leveldb_dir, "out-static", "db_bench"), experiment)
        run(exp)
