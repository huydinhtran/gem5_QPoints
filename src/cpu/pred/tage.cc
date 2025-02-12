/*
 * Copyright (c) 2014 The University of Wisconsin
 *
 * Copyright (c) 2006 INRIA (Institut National de Recherche en
 * Informatique et en Automatique  / French National Research Institute
 * for Computer Science and Applied Mathematics)
 *
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

/* @file
 * Implementation of a TAGE branch predictor
 */

#include "cpu/pred/tage.hh"

#include "base/intmath.hh"
#include "base/logging.hh"
#include "base/random.hh"
#include "base/trace.hh"
#include "debug/Fetch.hh"
#include "debug/Tage.hh"

namespace gem5
{

namespace branch_prediction
{

TAGE::TAGE(const TAGEParams &params) : BPredUnit(params), tage(params.tage), prevBi(NULL)
{
}

// PREDICTOR UPDATE
void
TAGE::update(ThreadID tid, Addr branch_pc, bool taken, void* bp_history,
              bool squashed, const StaticInstPtr & inst, Addr corrTarget)
{
    DPRINTF(Tage, "Bgodala TAGE update is called\n");
    assert(bp_history);

    TageBranchInfo *bi = static_cast<TageBranchInfo*>(bp_history);
    TAGEBase::BranchInfo *tage_bi = bi->tageBranchInfo;

    if (squashed) {
        // This restores the global history, then update it
        // and recomputes the folded histories.
        tage->squash(tid, taken, tage_bi, corrTarget);
        return;
    }

    int nrand = random_mt.random<int>() & 3;
    // Bgodala removing randomness for sanity check
    //int nrand = 1;
    if (bi->tageBranchInfo->condBranch) {
        tage_bi->isUpdated = true;
        DPRINTF(Tage, "Updating tables for branch:%lx; taken?:%d\n",
                branch_pc, taken);
        tage->updateStats(taken, bi->tageBranchInfo);
        tage->condBranchUpdate(tid, branch_pc, taken, tage_bi, nrand,
                               corrTarget, bi->tageBranchInfo->tagePred);
    }

    // optional non speculative update of the histories
    tage->updateHistories(tid, branch_pc, taken, tage_bi, false, inst,
                          corrTarget);
    if(prevBi){
      delete prevBi;
    }
    prevBi = bi;
}

void
TAGE::squash(ThreadID tid, void *bp_history)
{
    TageBranchInfo *bi = static_cast<TageBranchInfo*>(bp_history);
    DPRINTF(Tage, "Deleting branch info: %lx\n", bi->tageBranchInfo->branchPC);
    TAGEBase::BranchInfo *tage_bi = bi->tageBranchInfo;
    tage->squash(tid, tage_bi);
    delete bi;
}

bool
TAGE::predict(ThreadID tid, Addr branch_pc, bool cond_branch, void* &b)
{
    TageBranchInfo *bi = new TageBranchInfo(*tage);//nHistoryTables+1);
    b = (void*)(bi);
    bool pred_taken =  tage->tagePredict(tid, branch_pc, cond_branch, bi->tageBranchInfo);
    DPRINTF(Tage, "Bgodala PREDICT FUNCTION TAGE CHECK Lookup branch: %lx; predict:%d\n", branch_pc, pred_taken);
    DPRINTF(Tage, "predict: tid:%d bp_history:%lx\n",tid, b);
    return pred_taken;
}

bool
TAGE::lookup(ThreadID tid, Addr branch_pc, void* &bp_history)
{
    bool retval=false;
    retval = predict(tid, branch_pc, true, bp_history);

    TageBranchInfo *bi = static_cast<TageBranchInfo*>(bp_history);

    DPRINTF(Tage, "Lookup branch: %lx; predict:%d\n", branch_pc, retval);

    tage->updateHistories(tid, branch_pc, retval, bi->tageBranchInfo, true);
    TAGEBase::BranchInfo *tage_bi = bi->tageBranchInfo;

    DPRINTF(Tage, "At look up branch info: %lx; PathHistory:%x, "
            "pointer:%d\n", tage_bi->branchPC, tage_bi->pathHist, tage_bi->ptGhist);

    return retval;
}

void
TAGE::btbUpdate(ThreadID tid, Addr branch_pc, void* &bp_history)
{
    TageBranchInfo *bi = static_cast<TageBranchInfo*>(bp_history);
    tage->btbUpdate(tid, branch_pc, bi->tageBranchInfo);
}

void
TAGE::uncondBranch(ThreadID tid, Addr br_pc, void* &bp_history)
{
    DPRINTF(Tage, "UnConditionalBranch: %lx\n", br_pc);
    predict(tid, br_pc, false, bp_history);
    TageBranchInfo *bi = static_cast<TageBranchInfo*>(bp_history);
    tage->updateHistories(tid, br_pc, true, bi->tageBranchInfo, true);
}

} // namespace branch_prediction
} // namespace gem5
