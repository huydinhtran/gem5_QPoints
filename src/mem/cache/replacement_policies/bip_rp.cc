/**
 * Copyright (c) 2018-2020 Inria
 * All rights reserved.
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

#include "mem/cache/replacement_policies/bip_rp.hh"

#include <memory>

#include "base/random.hh"
#include "params/BIPRP.hh"
#include "sim/cur_tick.hh"

namespace gem5
{

GEM5_DEPRECATED_NAMESPACE(ReplacementPolicy, replacement_policy);
namespace replacement_policy
{

BIP::BIP(const Params &p)
  : LRU(p), btp(p.btp)
{
}

void
BIP::reset(const std::shared_ptr<ReplacementData>& replacement_data) const
{
    std::shared_ptr<LRUReplData> casted_replacement_data =
        std::static_pointer_cast<LRUReplData>(replacement_data);

    // Entries are inserted as MRU if lower than btp, LRU otherwise
    if (random_mt.random<unsigned>(1, 100) <= btp) {
        casted_replacement_data->lastTouchTick = curTick();
    } else {
        // Make their timestamps as old as possible, so that they become LRU
        casted_replacement_data->lastTouchTick = 1;
    }
}

void
BIP::reset_inst_line(const std::shared_ptr<ReplacementData>& replacement_data, bool is_inst) const
{
    std::shared_ptr<LRUReplData> casted_replacement_data =
        std::static_pointer_cast<LRUReplData>(replacement_data);

    DPRINTFN("BIP INST_ONLY is inst %d\n",is_inst);

    if(!is_inst){
        casted_replacement_data->lastTouchTick = curTick();
        return; 
    }

    // Entries are inserted as MRU if lower than btp, LRU otherwise
    if (random_mt.random<unsigned>(1, 100) <= btp) {
        casted_replacement_data->lastTouchTick = curTick();
    } else {
        // Make their timestamps as old as possible, so that they become LRU
        casted_replacement_data->lastTouchTick = 1;
    }
}

} // namespace replacement_policy
} // namespace gem5
