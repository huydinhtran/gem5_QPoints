/*
 * Copyright (c) 2007 The Hewlett-Packard Development Company
 * Copyright (c) 2013 Advanced Micro Devices, Inc.
 * All rights reserved.
 *
 * The license below extends only to copyright in the software and shall
 * not be construed as granting a license to any other intellectual
 * property including but not limited to intellectual property relating
 * to a hardware implementation of the functionality of the software
 * licensed hereunder.  You may use the software subject to the license
 * terms below provided that you ensure that this notice is replicated
 * unmodified and in its entirety in all distributions of the software,
 * modified or unmodified, in source code or in binary form.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include "arch/x86/insts/static_inst.hh"

#include "arch/x86/regs/segment.hh"
#include "cpu/reg_class.hh"

namespace gem5
{

namespace X86ISA
{

void
X86StaticInst::printMnemonic(std::ostream &os, const char *mnemonic)
{
    ccprintf(os, "  %s   ", mnemonic);
}

void
X86StaticInst::printMnemonic(std::ostream &os, const char *instMnemonic,
        const char *mnemonic)
{
    ccprintf(os, "  %s : %s   ", instMnemonic, mnemonic);
}

void X86StaticInst::printSegment(std::ostream &os, int segment)
{
    switch (segment)
    {
      case SEGMENT_REG_ES:
        ccprintf(os, "ES");
        break;
      case SEGMENT_REG_CS:
        ccprintf(os, "CS");
        break;
      case SEGMENT_REG_SS:
        ccprintf(os, "SS");
        break;
      case SEGMENT_REG_DS:
        ccprintf(os, "DS");
        break;
      case SEGMENT_REG_FS:
        ccprintf(os, "FS");
        break;
      case SEGMENT_REG_GS:
        ccprintf(os, "GS");
        break;
      case SEGMENT_REG_HS:
        ccprintf(os, "HS");
        break;
      case SEGMENT_REG_TSL:
        ccprintf(os, "TSL");
        break;
      case SEGMENT_REG_TSG:
        ccprintf(os, "TSG");
        break;
      case SEGMENT_REG_LS:
        ccprintf(os, "LS");
        break;
      case SEGMENT_REG_MS:
        ccprintf(os, "MS");
        break;
      case SYS_SEGMENT_REG_TR:
        ccprintf(os, "TR");
        break;
      case SYS_SEGMENT_REG_IDTR:
        ccprintf(os, "IDTR");
        break;
      default:
        panic("Unrecognized segment %d\n", segment);
    }
}

void
X86StaticInst::divideStep(uint64_t dividend, uint64_t divisor,
        uint64_t &quotient, uint64_t &remainder)
{
    // Check for divide by zero.
    assert(divisor != 0);
    // If the divisor is bigger than the dividend, don't do anything.
    if (divisor <= dividend) {
        // Shift the divisor so it's msb lines up with the dividend.
        int dividendMsb = findMsbSet(dividend);
        int divisorMsb = findMsbSet(divisor);
        int shift = dividendMsb - divisorMsb;
        divisor <<= shift;
        // Compute what we'll add to the quotient if the divisor isn't
        // now larger than the dividend.
        uint64_t quotientBit = 1;
        quotientBit <<= shift;
        // If we need to step back a bit (no pun intended) because the
        // divisor got too to large, do that here. This is the "or two"
        // part of one or two bit division.
        if (divisor > dividend) {
            quotientBit >>= 1;
            divisor >>= 1;
        }
        // Decrement the remainder and increment the quotient.
        quotient += quotientBit;
        remainder -= divisor;
    }
}

void
X86StaticInst::printReg(std::ostream &os, RegId reg, int size)
{
    assert(size == 1 || size == 2 || size == 4 || size == 8 || size == 0);
    static const char * abcdFormats[9] =
        {"", "%s",  "%sx",  "", "e%sx", "", "", "", "r%sx"};
    static const char * piFormats[9] =
        {"", "%s",  "%s",   "", "e%s",  "", "", "", "r%s"};
    static const char * longFormats[9] =
        {"", "r%sb", "r%sw", "", "r%sd", "", "", "", "r%s"};
    static const char * microFormats[9] =
        {"", "t%db", "t%dw", "", "t%dd", "", "", "", "t%d"};

    RegIndex reg_idx = reg.index();

    switch (reg.classValue()) {
      case IntRegClass:
        {
            const char * suffix = "";
            bool fold = reg_idx & IntFoldBit;
            reg_idx &= ~IntFoldBit;

            if (fold)
                suffix = "h";
            else if (reg_idx < 8 && size == 1)
                suffix = "l";

            switch (reg_idx) {
              case INTREG_RAX:
                ccprintf(os, abcdFormats[size], "a");
                break;
              case INTREG_RBX:
                ccprintf(os, abcdFormats[size], "b");
                break;
              case INTREG_RCX:
                ccprintf(os, abcdFormats[size], "c");
                break;
              case INTREG_RDX:
                ccprintf(os, abcdFormats[size], "d");
                break;
              case INTREG_RSP:
                ccprintf(os, piFormats[size], "sp");
                break;
              case INTREG_RBP:
                ccprintf(os, piFormats[size], "bp");
                break;
              case INTREG_RSI:
                ccprintf(os, piFormats[size], "si");
                break;
              case INTREG_RDI:
                ccprintf(os, piFormats[size], "di");
                break;
              case INTREG_R8W:
                ccprintf(os, longFormats[size], "8");
                break;
              case INTREG_R9W:
                ccprintf(os, longFormats[size], "9");
                break;
              case INTREG_R10W:
                ccprintf(os, longFormats[size], "10");
                break;
              case INTREG_R11W:
                ccprintf(os, longFormats[size], "11");
                break;
              case INTREG_R12W:
                ccprintf(os, longFormats[size], "12");
                break;
              case INTREG_R13W:
                ccprintf(os, longFormats[size], "13");
                break;
              case INTREG_R14W:
                ccprintf(os, longFormats[size], "14");
                break;
              case INTREG_R15W:
                ccprintf(os, longFormats[size], "15");
                break;
              default:
                ccprintf(os, microFormats[size], reg_idx - INTREG_MICRO_BEGIN);
            }
            ccprintf(os, suffix);
        }
        break;
      case FloatRegClass:
        if (reg_idx < NumMMXRegs) {
            ccprintf(os, "%%mmx%d", reg_idx);
            return;
        }
        reg_idx -= NumMMXRegs;
        if (reg_idx < NumXMMRegs * 2) {
            ccprintf(os, "%%xmm%d_%s", reg_idx / 2,
                    (reg_idx % 2) ? "high": "low");
            return;
        }
        reg_idx -= NumXMMRegs * 2;
        if (reg_idx < NumMicroFpRegs) {
            ccprintf(os, "%%ufp%d", reg_idx);
            return;
        }
        reg_idx -= NumMicroFpRegs;
        ccprintf(os, "%%st(%d)", reg_idx);
        break;
      case CCRegClass:
        ccprintf(os, "%%cc%d", reg_idx);
        break;
      case MiscRegClass:
        switch (reg_idx) {
          default:
            ccprintf(os, "%%ctrl%d", reg_idx);
        }
        break;
      default:
        panic("Unrecognized register class.");
    }
}

void
X86StaticInst::printMem(std::ostream &os, uint8_t segment,
        uint8_t scale, RegIndex index, RegIndex base,
        uint64_t disp, uint8_t addressSize, bool rip)
{
    bool someAddr = false;
    printSegment(os, segment);
    os << ":[";
    if (rip) {
        os << "rip";
        someAddr = true;
    } else {
        if (scale != 0 && index != NUM_INTREGS) {
            if (scale != 1)
                ccprintf(os, "%d*", scale);
            printReg(os, RegId(IntRegClass, index), addressSize);
            someAddr = true;
        }
        if (base != NUM_INTREGS) {
            if (someAddr)
                os << " + ";
            printReg(os, RegId(IntRegClass, base), addressSize);
            someAddr = true;
        }
    }
    if (disp != 0) {
        if (someAddr)
            os << " + ";
        ccprintf(os, "%#x", disp);
        someAddr = true;
    }
    if (!someAddr)
        os << "0";
    os << "]";
}

std::string
X86StaticInst::generateDisassembly(
        Addr pc, const loader::SymbolTable *symtab) const
{
    std::stringstream ss;

    printMnemonic(ss, mnemonic);

    return ss.str();
}

} // namespace X86ISA
} // namespace gem5
