# Copyright (c) 2016-2017, 2019, 2021 Arm Limited
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

# System components used by the bigLITTLE.py configuration script

import m5
from m5.objects import *
m5.util.addToPath('../../')
from common.Caches import *
from common import ObjectList
import math

have_kvm = "ArmV8KvmCPU" in ObjectList.cpu_list.get_names()
have_fastmodel = "FastModelCortexA76" in ObjectList.cpu_list.get_names()

class L1I(L1_ICache):
    tag_latency = 2
    data_latency = 2
    response_latency = 0
    mshrs = 16
    tgts_per_mshr = 20
    size = '32kB'
    assoc = 8
    write_buffers = 16


class L1D(L1_DCache):
    tag_latency = 2
    data_latency = 2
    response_latency = 0
    mshrs = 16
    tgts_per_mshr = 20
    size = '64kB'
    assoc = 8
    write_buffers = 16


class WalkCache(PageTableWalkerCache):
    tag_latency = 2
    data_latency = 2
    response_latency = 0
    mshrs = 16
    tgts_per_mshr = 20
    size = '32kB'
    assoc = 8
    write_buffers = 16


class L2(L2Cache):
    tag_latency = 10
    data_latency = 10
    response_latency = 0
    mshrs = 32
    tgts_per_mshr = 20
    size = '1MB'
    assoc = 16
    write_buffers = 32
    writeback_clean = True


class L3(Cache):
    size = '2MB'
    assoc = 16
    tag_latency = 20
    data_latency = 20
    response_latency = 0
    mshrs = 64
    tgts_per_mshr = 20
    write_buffers = 64
    clusivity='mostly_excl'


class MemBus(SystemXBar):
    badaddr_responder = BadAddr(warn_access="warn")
    default = Self.badaddr_responder.pio


class CpuCluster(SubSystem):
    def __init__(self, system,  num_cpus, cpu_clock, cpu_voltage,
                 cpu_type, l1i_type, l1d_type, wcache_type, l2_type,
                 l1i_rp, l2_rp, preserve_ways, args):
        super(CpuCluster, self).__init__()
        self._cpu_type = cpu_type
        self._l1i_type = l1i_type
        self._l1d_type = l1d_type
        self._wcache_type = wcache_type
        self._l2_type = l2_type
        self._l1i_rp = l1i_rp
        self._preserve_ways = preserve_ways
        self._args = args
        self._l2_rp = l2_rp

        assert num_cpus > 0

        self.voltage_domain = VoltageDomain(voltage=cpu_voltage)
        self.clk_domain = SrcClockDomain(clock=cpu_clock,
                                         voltage_domain=self.voltage_domain)

        self.cpus = [ self._cpu_type(cpu_id=system.numCpus() + idx,
                                     clk_domain=self.clk_domain)
                      for idx in range(num_cpus) ]

        for cpu in self.cpus:
            cpu.createThreads()
            cpu.createInterruptController()
            cpu.socket_id = system.numCpuClusters()

            print(cpu_type)
            if cpu_type == O3CPU:
                if args.fdip:
                    cpu.enableFDIP = args.fdip

                if args.perfectICache:
                    cpu.enablePerfectICache = args.perfectICache

                if args.starveAtleast:
                    cpu.starveAtleast = args.starveAtleast

                if args.randomStarve:
                    cpu.randomStarve = args.randomStarve

                if args.starveRandomness:
                    cpu.starveRandomness = args.starveRandomness

                if args.pureRandom:
                    cpu.pureRandom = args.pureRandom

                if args.dump_tms:
                    cpu.dumpTms = args.dump_tms

                if args.dump_btbconf:
                    cpu.dumpBTBConf = args.dump_btbconf

                if args.btbConfThreshold:
                    cpu.btbConfThreshold = args.btbConfThreshold

                if args.btbConfMinInst:
                    cpu.btbConfMinInst = args.btbConfMinInst

                if args.histRandom:
                    cpu.histRandom = args.histRandom

                if args.fetchQSize:
                    cpu.fetchQueueSize = args.fetchQSize

                if args.ftqSize >=0:
                    cpu.ftqSize = args.ftqSize

                if args.ftqInst >0:
                    cpu.ftqInst = args.ftqInst

                if args.oracleEMISSARY:
                    cpu.oracleEMISSARY = args.oracleEMISSARY

                if args.oracleStarvationsFileName:
                    cpu.oracleStarvationsFileName = args.oracleStarvationsFileName

                if args.oracleStarvationCountThreshold:
                    cpu.oracleStarvationCountThreshold = args.oracleStarvationCountThreshold


                if self._l1i_rp == "LRUEmissary" or self._l2_rp =="LRUEmissary":
                    cpu.enableStarvationEMISSARY = True
                cpu.enableStarvationEMISSARY = True


                if args.totalSimInsts:
                    cpu.totalSimInsts = args.totalSimInsts
                    if args.warmup_insts:
                        cpu.totalSimInsts += args.warmup_insts

                # 0: ORACLE
                # 1: LRU
                # 2: RANDOM
                # 3: NONE
                if args.opt:
                    cpu.cache_repl = 0

                if args.numSets:
                    cpu.numSets = args.numSets

            if args.maxinsts:
                cpu.max_insts_any_thread = args.maxinsts
                if args.warmup_insts:
                    cpu.max_insts_any_thread += args.warmup_insts


            if args.bp_type:
                bpClass = ObjectList.bp_list.get(args.bp_type)
                cpu.branchPred = bpClass()
                if args.btb_entries:
                    cpu.branchPred.BTBEntries = args.btb_entries
                    #cpu.branchPred.BTBEntries = 64*1024*1024
                    cpu.branchPred.BTBTagSize = 64 - (math.log(cpu.branchPred.BTBEntries,2) + 2)
                #indirectBPClass = ObjectList.indirect_bp_list.get('SimpleIndirectPredictor')
                indirectBPClass = ObjectList.indirect_bp_list.get('ITTAGE')
                cpu.branchPred.indirectBranchPred = indirectBPClass()

            #if args.indirect_bp_type:
            #    indirectBPClass = ObjectList.indirect_bp_list.get(args.indirect_bp_type)
            #    indirectBPClass = ObjectList.indirect_bp_list.get('SimpleIndirectPredictor')
            #    cpu.branchPred.indirectBranchPred = indirectBPClass()

        system.addCpuCluster(self, num_cpus)

    def requireCaches(self):
        return self._cpu_type.require_caches()

    def memoryMode(self):
        return self._cpu_type.memory_mode()

    def addL1(self):
        for cpu in self.cpus:
            l1i = None if self._l1i_type is None else self._l1i_type()
            l1d = None if self._l1d_type is None else self._l1d_type()
            iwc = None if self._wcache_type is None else self._wcache_type()
            dwc = None if self._wcache_type is None else self._wcache_type()

            if self._args.l1i_size:
                l1i.size=self._args.l1i_size

            if self._l1i_rp:
                if self._l1i_rp == "LRUEmissary":
                    l1i.replacement_policy = LRUEmissaryRP()
                    l1i.lru_ways = 2
                    if self._args.hist_freq_cycles:
                        l1i.replacement_policy.flush_freq_in_cycles = self._args.hist_freq_cycles
                    if self._preserve_ways:
                        l1i.preserve_ways = self._preserve_ways
                        l1i.lru_ways = 8 - int(self._preserve_ways)
                    else:
                        l1i.preserve_ways = 6
                elif self._l1i_rp == "OPT":
                    l1i.replacement_policy = OPTRP()
                    l1i.assoc = 256
                    l1i.size = '1024kB'
                elif self._l1i_rp == "LIP":
                    l1i.replacement_policy = LIPRP()
                elif self._l1i_rp == "BIP":
                    l1i.replacement_policy = BIPRP()
                    #if self.btp:
                    l1i.replacement_policy.btp = 3 # self.btp
                elif self._l1i_rp == "SBIP":
                    l1i.replacement_policy = SBIPRP()
                elif self._l1i_rp == "MLP":
                    l1i.replacement_policy = MLPLINRP()
                else:
                    l1i.replacement_policy = LRURP()
            else:
                l1i.replacement_policy = LRURP()

            if self._args.opt:
                l1i.assoc = 256
                l1i.size = '1024kB'


            print("adding L1 Caches")
            cpu.addPrivateSplitL1Caches(l1i, l1d, iwc, dwc)

    def addL2(self, clk_domain):
        if self._l2_type is None:
            return
        self.toL2Bus = L2XBar(width=64, clk_domain=clk_domain)
        self.l2 = self._l2_type()

        if self._l2_rp == "LRUEmissary":
            self.l2.replacement_policy = LRUEmissaryRP()
            self.l2.lru_ways = 2
            if self._preserve_ways:
                self.l2.preserve_ways = self._preserve_ways
                self.l2.lru_ways = self.l2.assoc - int(self._preserve_ways)
            else:
                self.l2.preserve_ways = 6
                self.l2.lru_ways = self.l2.assoc - int(self._preserve_ways)

            if self._args.hist_freq_cycles:
                self.l2.replacement_policy.flush_freq_in_cycles = self._args.hist_freq_cycles

        elif self._l2_rp == "LIP":
            self.l2.replacement_policy = LIPRP()
        elif self._l2_rp == "MLP":
            self.l2.replacement_policy = MLPLINRP()
        elif self._l2_rp == "SBIP":
            self.l2.replacement_policy = SBIPRP()
        elif self._l2_rp == "BIP":
            self.l2.replacement_policy = BIPRP()
            self.l2.replacement_policy.btp = 3 # self.btp

        if self._args.l2_size:
            self.l2.size = self._args.l2_size

        if self._l1i_rp == "OPT" or self._args.opt:
            self.l2.size = '2MB'
            self.l2.assoc = 32

        #NLPClass = ObjectList.hwp_list.get('TaggedPrefetcher')
        #self.l2.prefetcher = NLPClass()

        for cpu in self.cpus:
            cpu.connectAllPorts(self.toL2Bus)
        self.toL2Bus.mem_side_ports = self.l2.cpu_side
        print("after addL2")

    def addPMUs(self, ints, events=[]):
        """
        Instantiates 1 ArmPMU per PE. The method is accepting a list of
        interrupt numbers (ints) used by the PMU and a list of events to
        register in it.

        :param ints: List of interrupt numbers. The code will iterate over
            the cpu list in order and will assign to every cpu in the cluster
            a PMU with the matching interrupt.
        :type ints: List[int]
        :param events: Additional events to be measured by the PMUs
        :type events: List[Union[ProbeEvent, SoftwareIncrement]]
        """
        assert len(ints) == len(self.cpus)
        for cpu, pint in zip(self.cpus, ints):
            int_cls = ArmPPI if pint < 32 else ArmSPI
            for isa in cpu.isa:
                isa.pmu = ArmPMU(interrupt=int_cls(num=pint))
                isa.pmu.addArchEvents(cpu=cpu,
                                      itb=cpu.mmu.itb, dtb=cpu.mmu.dtb,
                                      icache=getattr(cpu, 'icache', None),
                                      dcache=getattr(cpu, 'dcache', None),
                                      l2cache=getattr(self, 'l2', None))
                for ev in events:
                    isa.pmu.addEvent(ev)

    def connectMemSide(self, bus):
        try:
            self.l2.mem_side = bus.cpu_side_ports
        except AttributeError:
            for cpu in self.cpus:
                cpu.connectAllPorts(bus)


class AtomicCluster(CpuCluster):
    def __init__(self, system, num_cpus, cpu_clock, cpu_voltage="1.0V"):
        cpu_config = [ ObjectList.cpu_list.get("AtomicSimpleCPU"), None,
                       None, None, None ]
        super(AtomicCluster, self).__init__(system, num_cpus, cpu_clock,
                                            cpu_voltage, *cpu_config)
    def addL1(self):
        pass

class KvmCluster(CpuCluster):
    def __init__(self, system, num_cpus, cpu_clock, cpu_voltage="1.0V"):
        cpu_config = [ ObjectList.cpu_list.get("ArmV8KvmCPU"), None, None,
            None, None ]
        super(KvmCluster, self).__init__(system, num_cpus, cpu_clock,
                                         cpu_voltage, *cpu_config)
    def addL1(self):
        pass

class FastmodelCluster(SubSystem):
    def __init__(self, system,  num_cpus, cpu_clock, cpu_voltage="1.0V"):
        super(FastmodelCluster, self).__init__()

        # Setup GIC
        gic = system.realview.gic
        gic.sc_gic.cpu_affinities = ','.join(
            [ '0.0.%d.0' % i for i in range(num_cpus) ])

        # Parse the base address of redistributor.
        redist_base = gic.get_redist_bases()[0]
        redist_frame_size = 0x40000 if gic.sc_gic.has_gicv4_1 else 0x20000
        gic.sc_gic.reg_base_per_redistributor = ','.join([
            '0.0.%d.0=%#x' % (i, redist_base + redist_frame_size * i)
            for i in range(num_cpus)
        ])

        gic_a2t = AmbaToTlmBridge64(amba=gic.amba_m)
        gic_t2g = TlmToGem5Bridge64(tlm=gic_a2t.tlm,
                                    gem5=system.iobus.cpu_side_ports)
        gic_g2t = Gem5ToTlmBridge64(gem5=system.membus.mem_side_ports)
        gic_g2t.addr_ranges = gic.get_addr_ranges()
        gic_t2a = AmbaFromTlmBridge64(tlm=gic_g2t.tlm)
        gic.amba_s = gic_t2a.amba

        system.gic_hub = SubSystem()
        system.gic_hub.gic_a2t = gic_a2t
        system.gic_hub.gic_t2g = gic_t2g
        system.gic_hub.gic_g2t = gic_g2t
        system.gic_hub.gic_t2a = gic_t2a

        self.voltage_domain = VoltageDomain(voltage=cpu_voltage)
        self.clk_domain = SrcClockDomain(clock=cpu_clock,
                                         voltage_domain=self.voltage_domain)

        # Setup CPU
        assert num_cpus <= 4
        CpuClasses = [FastModelCortexA76x1, FastModelCortexA76x2,
                      FastModelCortexA76x3, FastModelCortexA76x4]
        CpuClass = CpuClasses[num_cpus - 1]

        cpu = CpuClass(GICDISABLE=False)
        for core in cpu.cores:
            core.semihosting_enable = False
            core.RVBARADDR = 0x10
            core.redistributor = gic.redistributor
            core.createThreads()
            core.createInterruptController()
        self.cpus = [ cpu ]

        a2t = AmbaToTlmBridge64(amba=cpu.amba)
        t2g = TlmToGem5Bridge64(tlm=a2t.tlm, gem5=system.membus.cpu_side_ports)
        system.gic_hub.a2t = a2t
        system.gic_hub.t2g = t2g

        system.addCpuCluster(self, num_cpus)

    def requireCaches(self):
        return False

    def memoryMode(self):
        return 'atomic_noncaching'

    def addL1(self):
        pass

    def addL2(self, clk_domain):
        pass

    def connectMemSide(self, bus):
        pass

class BaseSimpleSystem(ArmSystem):
    cache_line_size = 64

    def __init__(self, mem_size, platform, m1, **kwargs):
        super(BaseSimpleSystem, self).__init__(**kwargs)

        print("M1 enabled {}".format(m1))
        self.voltage_domain = VoltageDomain(voltage="1.0V")
        self.clk_domain = SrcClockDomain(
            clock="1GHz",
            voltage_domain=Parent.voltage_domain)

        if platform is None:
            #self.realview = VExpress_GEM5_V1()
            if m1:
                self.realview = QEMU_VirtM1()
            else:
                self.realview = QEMU_Virt()
        else:
            self.realview = platform

        if hasattr(self.realview.gic, 'cpu_addr'):
            self.gic_cpu_addr = self.realview.gic.cpu_addr

        self.terminal = Terminal()
        self.vncserver = VncServer()

        self.iobus = IOXBar()
        # Device DMA -> MEM
        self.mem_ranges = self.getMemRanges(int(Addr(mem_size)))

        self._clusters = []
        self._num_cpus = 0

    def getMemRanges(self, mem_size):
        """
        Define system memory ranges. This depends on the physical
        memory map provided by the realview platform and by the memory
        size provided by the user (mem_size argument).
        The method is iterating over all platform ranges until they cover
        the entire user's memory requirements.
        """
        mem_ranges = []
        print(self.realview._mem_regions)
        for mem_range in self.realview._mem_regions:
            size_in_range = min(mem_size, mem_range.size())

            mem_ranges.append(
                AddrRange(start=mem_range.start, size=size_in_range))

            mem_size -= size_in_range
            if mem_size == 0:
                return mem_ranges

        raise ValueError("memory size too big for platform capabilities")

    def numCpuClusters(self):
        return len(self._clusters)

    def addCpuCluster(self, cpu_cluster, num_cpus):
        assert cpu_cluster not in self._clusters
        assert num_cpus > 0
        self._clusters.append(cpu_cluster)
        self._num_cpus += num_cpus

    def numCpus(self):
        return self._num_cpus

    def addCaches(self, need_caches, last_cache_level):
        if not need_caches:
            # connect each cluster to the memory hierarchy
            for cluster in self._clusters:
                cluster.connectMemSide(self.membus)
            return

        cluster_mem_bus = self.membus
        assert last_cache_level >= 1 and last_cache_level <= 3
        for cluster in self._clusters:
            cluster.addL1()
        if last_cache_level > 1:
            for cluster in self._clusters:
                cluster.addL2(cluster.clk_domain)
        if last_cache_level > 2:
            max_clock_cluster = max(self._clusters,
                                    key=lambda c: c.clk_domain.clock[0])
            self.l3 = L3(clk_domain=max_clock_cluster.clk_domain)
            self.toL3Bus = L2XBar(width=64)
            self.toL3Bus.mem_side_ports = self.l3.cpu_side
            self.l3.mem_side = self.membus.cpu_side_ports
            cluster_mem_bus = self.toL3Bus

        # connect each cluster to the memory hierarchy
        for cluster in self._clusters:
            cluster.connectMemSide(cluster_mem_bus)

class SimpleSystem(BaseSimpleSystem):
    """
    Meant to be used with the classic memory model
    """
    def __init__(self, caches, mem_size, platform=None, **kwargs):
        super(SimpleSystem, self).__init__(mem_size, platform, **kwargs)

        self.membus = MemBus()
        # CPUs->PIO
        self.iobridge = Bridge(delay='50ns')

        self._caches = caches
        if self._caches:
            self.iocache = IOCache(addr_ranges=self.mem_ranges)
        else:
            self.dmabridge = Bridge(delay='50ns',
                                    ranges=self.mem_ranges)

    def connect(self):
        self.iobridge.mem_side_port = self.iobus.cpu_side_ports
        self.iobridge.cpu_side_port = self.membus.mem_side_ports

        if self._caches:
            self.iocache.mem_side = self.membus.cpu_side_ports
            self.iocache.cpu_side = self.iobus.mem_side_ports
        else:
            self.dmabridge.mem_side_port = self.membus.cpu_side_ports
            self.dmabridge.cpu_side_port = self.iobus.mem_side_ports

        if hasattr(self.realview.gic, 'cpu_addr'):
            self.gic_cpu_addr = self.realview.gic.cpu_addr
        self.realview.attachOnChipIO(self.membus, self.iobridge)
        self.realview.attachIO(self.iobus)
        self.system_port = self.membus.cpu_side_ports

    def attach_pci(self, dev):
        self.realview.attachPciDevice(dev, self.iobus)

class ArmRubySystem(BaseSimpleSystem):
    """
    Meant to be used with ruby
    """
    def __init__(self, mem_size, platform=None, **kwargs):
        super(ArmRubySystem, self).__init__(mem_size, platform, **kwargs)
        self._dma_ports = []
        self._mem_ports = []

    def connect(self):
        self.realview.attachOnChipIO(self.iobus,
            dma_ports=self._dma_ports, mem_ports=self._mem_ports)

        self.realview.attachIO(self.iobus, dma_ports=self._dma_ports)

        for cluster in self._clusters:
            for i, cpu in enumerate(cluster.cpus):
                self.ruby._cpu_ports[i].connectCpuPorts(cpu)

    def attach_pci(self, dev):
        self.realview.attachPciDevice(dev, self.iobus,
            dma_ports=self._dma_ports)
