#!/usr/bin/env python
# encoding: utf-8

from ..experiment import Experiment, RuntimeExperiment, try_catch_log
from pprof.experiment import step, substep
from ..settings import config
from pprof import likwid
from pprof.utils.db import create_run, get_db_connection

from plumbum import local, FG
from plumbum.cmd import cp, awk, echo, tee, time, sed, rm
from os import path

polli = None
likwid_perfctr = None
pprof_calibrate = None
pprof_analyze = None
opt = None

import pdb


class PapiScopCoverage(RuntimeExperiment):

    """ The polyjit experiment """

    def setup_commands(self):
        super(PolyJIT, self).setup_commands()
        global polli, likwid_perfctr, pprof_calibrate, pprof_analyze, opt
        bin_path = path.join(config["llvmdir"], "bin")
        likwid_path = path.join(config["likwiddir"], "bin")

        likwid_perfctr = local[path.join(likwid_path, "likwid-perfctr")]
        polli = local[path.join(bin_path, "polli")]
        pprof_calibrate = local[path.join(bin_path, "pprof-calibrate")]
        pprof_analyze = local[path.join(bin_path, "pprof-analyze")]
        opt = local[path.join(bin_path, "opt")]

    def run_project(self, p):
        from plumbum.cmd import time

        llvm_libs = path.join(config["llvmdir"], "lib")

        with step("No recompilation, PAPI"):
            p.download()
            p.ldflags = ["-L" + llvm_libs, "-lpjit", "-lpprof", "-lpapi"]
            p.cflags = ["-O3",
                        "-Xclang", "-load",
                        "-Xclang", "LLVMPolyJIT.so",
                        "-mllvm", "-polli",
                        "-mllvm", "-jitable",
                        "-mllvm", "-instrument",
                        "-mllvm", "-no-recompilation",
                        "-mllvm", "-polly-detect-keep-going"]
            with substep("reconf & rebuild"):
                p.configure()
                p.build()
            with substep("run"):
                def runner(run_f):
                    return time["-f", "%U,%S,%e", "-a", "-o", p.time_f, run_f]
                p.run(runner)

        with step("Evaluation"):
            # Print header here.
            (echo["---------------------------------------------------------------"]
                >> p.result_f)()
            (echo[">>> ========= " + p.name + " Program"]
                >> p.result_f)()
            (echo["---------------------------------------------------------------"]
                >> p.result_f)()

            with substep("pprof analyze"):
                with local.env(PPROF_USE_DATABASE=1,
                               PPROF_DB_RUN_GROUP=p.run_uuid,
                               PPROF_USE_FILE=0,
                               PPROF_USE_CSV=0):
                    (pprof_analyze | tee["-a", p.result_f])()

            with substep("pprof calibrate"):
                papi_calibration = self.get_papi_calibration(
                    p, pprof_calibrate)
                # FIXME: This needs to go into the database.
                if papi_calibration:
                    (awk[("{s+=$1} END {"
                          " time = (s*" + papi_calibration + "/1000000000);"
                          " print \"Time spent in libPAPI (s) - \" time }"
                          ),
                         p.calls_f] |
                     tee["-a", p.result_f])()
                    (echo["Real time per PAPI call (ns) - ", papi_calibration] |
                        tee["-a", p.result_f])()

            (awk["-F", ",", ("{ usr+=$1; sys+=$2; wall+=$3 }"
                             " END {"
                             " print \"User time - \" usr;"
                             " print \"System time - \" sys;"
                             " print \"Wall clock - \" wall;}"), p.time_f] |
             tee["-a", p.result_f])()
