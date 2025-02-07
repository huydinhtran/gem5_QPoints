# Copyright (c) 2016-2017, 2020 ARM Limited
# All rights reserved.
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""This script is the full system example script from the ARM
Research Starter Kit on System Modeling. More information can be found
at: http://www.arm.com/ResearchEnablement/SystemModeling
"""

import os
import m5
from m5.util import addToPath
from m5.objects import *
from m5.options import *
import argparse

m5.util.addToPath('../..')

from common import Options
from common import Simulation
from common import SysPaths
from common import ObjectList
from common import CacheConfig
from common import MemConfig
from common.cores.arm import HPI

import devices


######################################
from common import Simulation
import sys
import trace
######################################

default_kernel = 'vmlinux.arm64'
default_disk = 'linaro-minimal-aarch64.img'
default_root_device = '/dev/vda'


# Pre-defined CPU configurations. Each tuple must be ordered as : (cpu_class,
# l1_icache_class, l1_dcache_class, walk_cache_class, l2_Cache_class). Any of
# the cache class may be 'None' if the particular cache is not present.
cpu_types = {

    # "atomic" : (AtomicSimpleCPU, None, None, None, None),
    "atomic" : (AtomicSimpleCPU,
                devices.L1I, devices.L1D,
               devices.WalkCache,
               devices.L2),
    "minor"  : (MinorCPU,
               devices.L1I, devices.L1D,
               devices.WalkCache,
               devices.L2),
    "hpi"    : (HPI.HPI,
               HPI.HPI_ICache, HPI.HPI_DCache,
               HPI.HPI_WalkCache,
               HPI.HPI_L2),
    "ooo"    : (O3CPU,
               devices.L1I, devices.L1D,
               devices.WalkCache,
               devices.L2),
}

def create_cow_image(name):
    """Helper function to create a Copy-on-Write disk image"""
    image = CowDiskImage()
    image.child.image_file = SysPaths.disk(name)

    return image


def create(args):
    ''' Create and configure the system object. '''

    if args.script and not os.path.isfile(args.script):
        print("Error: Bootscript %s does not exist" % args.script)
        sys.exit(1)

    want_caches = False
    if args.cpu_type == "O3CPU":
        (CPUClass, test_mem_mode, FutureClass) = Simulation.setCPUClass(args)
        print(test_mem_mode)
        cpu_class = CPUClass
        mem_mode = test_mem_mode
        args.cpu = "ooo"
        want_caches = True
    else:
        cpu_class = cpu_types[args.cpu][0]
        mem_mode = cpu_class.memory_mode()
        want_caches = True if mem_mode == "timing" else False

    # Only simulate caches when using a timing CPU (e.g., the HPI model)
    #want_caches = True

    system = devices.SimpleSystem(caches=want_caches,
                                  mem_size = args.mem_size,
                                  mem_mode=mem_mode,
                                  workload=ArmFsLinux(
                                      object_file=
                                      SysPaths.binary(args.kernel)),
                                  readfile=args.script,
                                  m1=args.m1)

    #CacheConfig.config_cache(args, system)
    MemConfig.config_mem(args, system)

    system.realview.vio[0].vio=VirtIOBlock(image=create_cow_image(args.disk_image))

    # Wire up the system's memory system
    system.connect()

    # Add CPU clusters to the system
    system.cpu_cluster = [
        devices.CpuCluster(system,
                           args.num_cores,
                           args.cpu_freq, "1.0V",
                           *cpu_types[args.cpu],
                           l1i_rp=args.l1i_rp,
                           l2_rp=args.l2_rp,
                           preserve_ways=args.preserve_ways,
                           args=args),
    ]
    # Create a cache hierarchy for the cluster. We are assuming that
    # clusters have core-private L1 caches and an L2 that's shared
    # within the cluster.
    print("WANT_CACHES = ",want_caches)
    want_caches = True
    system.addCaches(want_caches, last_cache_level=3)

    # Setup gem5's minimal Linux boot loader.
    system.realview.setupBootLoader(system, SysPaths.binary, args.bootloader)
    #system.realview.setupBootLoader(system, SysPaths.binary)

    if args.dtb:
        system.workload.dtb_filename = args.dtb
    else:
        # No DTB specified: autogenerate DTB
        system.workload.dtb_filename = \
            os.path.join(m5.options.outdir, 'system.dtb')
        system.generateDtb(system.workload.dtb_filename)

    # Linux boot command flags
    kernel_cmd = [
        # Tell Linux to use the simulated serial port as a console
        "console=ttyAMA0",
        # Hard-code timi
        "lpj=19988480",
        # Disable address space randomisation to get a consistent
        # memory layout.
        "norandmaps",
        # Tell Linux where to find the root disk image.
        "root=%s" % args.root_device,
        # Mount the root disk read-write by default.
        "rw",
        # Tell Linux about the amount of physical memory present.
        "mem=%s" % args.mem_size,
    ]
    system.workload.command_line = " ".join(kernel_cmd)

    return system

def parse_stats(args):
    stats_file = os.path.join(m5.options.outdir,'stats.txt')
    stats_file_handle = open(stats_file,'r')
    found = False

    warmup_instcount = 5000000
    if args.warmup_insts:
        warmup_instcount = args.warmup_insts
    for line in stats_file_handle:
        if "simInsts" in line:
            toks = line.split()
            inst_count = int(toks[1])
            #print(toks)
            #print(inst_count)
            if(inst_count >= warmup_instcount):
                found = True
                break
    stats_file_handle.close()
    return found

def run(args):
    cptdir = m5.options.outdir
    if args.checkpoint:
        print("Checkpoint directory: %s" % cptdir)

    if args.warmup_insts:
        while True:
            event = m5.simulate(250000000)
            m5.stats.dump()
            if(parse_stats(args)):
                break

        # Reset stats and prepare to get final stats
        m5.stats.reset()
        m5.stats.outputList.clear()
        m5.stats.addStatVisitor("stats_final.txt")

    while True:
        event = m5.simulate()
        exit_msg = event.getCause()
        if exit_msg == "checkpoint":
            print("Dropping checkpoint at tick %d" % m5.curTick())
            cpt_dir = os.path.join(m5.options.outdir, "cpt.%d" % m5.curTick())
            m5.checkpoint(os.path.join(cpt_dir))
            print("Checkpoint done.")
        else:
            print(exit_msg, " @ ", m5.curTick())
            break

    m5.stats.dump()
    sys.exit(event.getCode())


def main():
    parser = argparse.ArgumentParser(epilog=__doc__)

    parser.add_argument("--dtb", type=str, default=None,
                        help="DTB file to load")
    parser.add_argument("--kernel", type=str, default=default_kernel,
                        help="Linux kernel")
    parser.add_argument("--disk-image", type=str,
                        default=default_disk,
                        help="Disk to instantiate")
    parser.add_argument("--bootloader", type=str,
                        default="boot.arm64",
                        help="bootloader")
    parser.add_argument("--root-device", type=str,
                        default=default_root_device,
                        help="OS device name for root partition (default: {})"
                             .format(default_root_device))
    parser.add_argument("--script", type=str, default="",
                        help = "Linux bootscript")
    parser.add_argument("--cpu", type=str, choices=list(cpu_types.keys()),
                        default="atomic",
                        help="CPU model to use")
    parser.add_argument("--cpu-freq", type=str, default="2GHz")
    parser.add_argument("--m1", default=False, action="store_true")
    parser.add_argument("--opt", default=False, action="store_true")
    parser.add_argument("--numSets", type=int, default=64,
                        help="Number of L1i sets")
    parser.add_argument("--num-cores", type=int, default=1,
                        help="Number of CPU cores")
    parser.add_argument("--checkpoint", action="store_true")
    parser.add_argument("--restore", type=str, default=None)


    Options.addCommonOptions(parser)
    args = parser.parse_args()
    print(args)
    root = Root(full_system=True)
    root.system = create(args)

    
    ###################################
    timing_cpus   = [TimingSimpleCPU(switched_out=True, cpu_id=(i))
                     for i in range(args.num_cpus)]
    o3_cpus = [DerivO3CPU(switched_out=True, cpu_id=(i))
                     for i in range(args.num_cpus)]

    for i in range(args.num_cpus):
        timing_cpus[i].system =  root.system
        o3_cpus[i].system =  root.system
        timing_cpus[i].workload = root.system.cpu_cluster[0].cpus[i].workload
        o3_cpus[i].workload = root.system.cpu_cluster[0].cpus[i].workload
        timing_cpus[i].clk_domain = root.system.cpu_cluster[0].cpus[i].clk_domain
        o3_cpus[i].clk_domain = root.system.cpu_cluster[0].cpus[i].clk_domain
        timing_cpus[i].isa = root.system.cpu_cluster[0].cpus[i].isa
        o3_cpus[i].isa = root.system.cpu_cluster[0].cpus[i].isa


        # simulation period
        if args.maxinsts:
            timing_cpus[i].max_insts_any_thread =  args.maxinsts
            o3_cpus[i].max_insts_any_thread = args.maxinsts

        # attach the checker cpu if selected
        if args.checker:
            timing_cpus[i].addCheckerCpu()
            o3_cpus[i].addCheckerCpu()



    root.system.timing_cpus = timing_cpus
    root.system.o3_cpus = o3_cpus
    atomic_to_timing = [
        (root.system.cpu_cluster[0].cpus[i], timing_cpus[i]) for i in range(args.num_cpus)
    ]
    timing_to_o3 = [
        (timing_cpus[i], o3_cpus[i]) for i in range(args.num_cpus)
    ]
    o3_to_atomic = [
        (o3_cpus[i], root.system.cpu_cluster[0].cpus[i]) for i in range(args.num_cpus)
    ]

    if args.restore is not None:
        m5.instantiate(args.restore)
    else:
        m5.instantiate()


    # # while(m5.curTick() < max_tick):
    # print("Running with ATOMIC CPU")
    # event = m5.simulate(10000000000)

    # m5.switchCpus(root.system, atomic_to_timing)
    # print("Running with TIMING CPU")
    # event = m5.simulate(10000000000)

    # m5.switchCpus(root.system, timing_to_o3)
    # print("Running with O3 CPU")
    # event = m5.simulate(10000000000)

    # m5.switchCpus(root.system, o3_to_atomic)
    # # print("Running with ATOMIC CPU")
    # # event = m5.simulate(100000000000)

    # exit_msg = event.getCause()
    # print(exit_msg, " @ ", m5.curTick())
    # m5.stats.dump()
    # sys.exit(event.getCode())
    ###################################
    # run(args)
    try:
        event = m5.simulate()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        exit_msg = event.getCause()
        print(exit_msg, " @ ", m5.curTick())
        m5.stats.dump()
        sys.exit(event.getCode())


if __name__ == "__m5_main__":
    main()
