from dcdata.contribution.sources.crp import CYCLES, FILE_TYPES
from dcdata.utils.dryrub import CountEmitter
from saucebrush.filters import Filter, FieldAdder, FieldCopier, FieldMerger, FieldModifier, FieldRemover, FieldRenamer
from saucebrush.emitters import Emitter, CSVEmitter, DebugEmitter
from saucebrush.sources import CSVSource
from saucebrush.utils import Files
import datetime
import logging
import os
import saucebrush

from denormalize import *

#####

class RecipientFilter(Filter):
    def __init__(self, candidates):
        super(RecipientFilter, self).__init__()
        self._candidates = candidates
    def process_record(self, record):
        cid = record['cid'].upper()
        candidate = self._candidates.get('%s:%s' % (record['cycle'], cid), None)
        if candidate:
            record['recipient_name'] = candidate['first_last_p']
            record['recipient_party'] = candidate['party']
            record['recipient_type'] = 'politician'
            record['seat_status'] = candidate['crp_ico']
            seat = candidate['dist_id_run_for'].upper()
            if len(seat) == 4:
                if seat == 'PRES':
                    record['seat'] = 'federal:president'
                else:
                    if seat[2] == 'S':
                        record['seat'] = 'federal:senate'
                    else:
                        record['seat'] = 'federal:house'
                        record['district'] = "%s-%s" % (seat[:2], seat[2:])
        return record

class ContributorFilter(Filter):
    def __init__(self, committees):
        super(ContributorFilter, self).__init__()
        self._committees = committees
    def process_record(self, record):
        pac_id = record['pac_id'].upper()
        committee = self._committees.get('%s:%s' % (record['cycle'], pac_id), None)
        if committee:
            record['recipient_name'] = committee['pac_short']
            record['recipient_party'] = committee['party']
            record['recipient_type'] = 'committee'
        return record

def main():

    from optparse import OptionParser

    usage = "usage: %prog [options]"

    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--cycles", dest="cycles",
                      help="cycles to load ex: 90,92,08", metavar="CYCLES")
    parser.add_option("-d", "--dataroot", dest="dataroot",
                      help="path to data directory", metavar="PATH")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="noisy output")

    (options, args) = parser.parse_args()

    if not options.dataroot:
        parser.error("path to dataroot is required")

    cycles = []
    if options.cycles:
        for cycle in options.cycles.split(','):
            if len(cycle) == 4:
                cycle = cycle[2:4]
            if cycle in CYCLES:
                cycles.append(cycle)
    else:
        cycles = CYCLES

    dataroot = os.path.abspath(options.dataroot)
    tmppath = os.path.join(dataroot, 'denormalized')
    if not os.path.exists(tmppath):
        os.makedirs(tmppath)

    print "Loading catcodes..."
    catcodes = load_catcodes(dataroot)

    print "Loading candidates..."
    candidates = load_candidates(dataroot)

    print "Loading committees..."
    committees = load_committees(dataroot)
    
    emitter = CSVEmitter(open(os.path.join(tmppath, 'denorm_pac2cand.csv'), 'w'), fieldnames=FIELDNAMES)

    files = Files(*[os.path.join(dataroot, 'raw', 'crp', 'pacs%s.csv' % cycle) for cycle in cycles])
    
    spec = dict(((fn, None) for fn in FIELDNAMES))
    
    def candidate_urn(s):
        return 'urn:crp:candidate:%s' % s.strip().upper() if s else None
    
    def committee_urn(s):
        return 'urn:crp:committee:%s' % s.strip().upper() if s else None
    
    def org_urn(s):
        return 'urn:crp:organization:%s' % s.strip() if s else None
    
    saucebrush.run_recipe(
        
        # load source
        CSVSource(files, fieldnames=FILE_TYPES['pacs']),
        
        # transaction filters
        FieldAdder('transaction_namespace', 'urn:fec:transaction'),
        FieldMerger({'transaction_id': ('cycle','fec_rec_no')}, lambda cycle, fecid: '%s:%s' % (cycle, fecid), keep_fields=True),
        FieldMerger({'transaction_type': ('type',)}, lambda t: t.strip().lower()),
        
        # date stamp
        FieldModifier('datestamp', parse_date_iso),
        
        # contributor and recipient fields
        ContributorFilter(committees),
        FieldMerger({'contributor_urn': ('pac_id',)}, committee_urn),
        FieldAdder('contributor_type', 'committee'),
        
        RecipientFilter(candidates),
        FieldMerger({'recipient_urn': ('cid',)}, candidate_urn),
        FieldAdder('recipient_type', 'politician'),
        
        # catcode
        CatCodeFilter('contributor', catcodes),
        
        # add static fields
        FieldAdder('is_amendment', False),
        FieldAdder('election_type', 'G'),
        
        # filter through spec
        SpecFilter(spec),
        
        #DebugEmitter(),
        CountEmitter(every=100),
        emitter,
        
    )


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    main()