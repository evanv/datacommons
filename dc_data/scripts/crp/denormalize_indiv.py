from dcdata.utils.dryrub import CountEmitter, FieldCountValidator
from saucebrush.filters import FieldAdder, FieldMerger, FieldModifier, FieldRenamer
from saucebrush.emitters import CSVEmitter
from saucebrush.sources import CSVSource
from saucebrush.utils import Files
import logging
import os
import saucebrush

from denormalize import *

### Filters

class RecipCodeFilter(Filter):
    def __init__(self):
        super(RecipCodeFilter, self).__init__()
    def process_record(self, record):
        if record['recip_id'].startswith('N'):
            if record['recip_code']:
                recip_code = record['recip_code'].strip().upper()
                record['recipient_party'] = recip_code[0]
                record['seat_result'] = recip_code[1] if recip_code[1] in ('W','L') else None
        return record

# this list was built by searching for the most frequent organization names in the unfiltered
# contribution data. I went through all organization names with at least 200 entries and entered
# all of the names that weren't organziations. -epg
disallowed_orgnames = set(['retired', 'homemaker', 'attorney', '[24i contribution]', 'self-employed', 
                          'physician', 'self', 'information requested', 'self employed', '[24t contribution]', 
                          'consultant', 'investor', '[candidate contribution]', 'n/a', 'farmer', 'real estate', 
                          'none', 'writer', 'dentist', 'info requested', 'business owner', 'accountant', 
                          'artist', 'rancher', 'student', 'realtor', 'investments', 'real estate developer', 
                          'unemployed', 'requested', 'owner', 'developer', 'businessman', 'contractor', 
                          'president', 'engineer', 'n', 'psychologist', 'real estate broker', 'executive', 
                          'private investor', 'architect', 'sales', 'real estate investor', 'selfemployed', 
                          'philanthropist', 'not employed', 'author', 'builder', 'insurance agent', 'volunteer', 
                          'construction', 'insurance', 'entrepreneur', 'lobbyist', 'ceo', 'n.a', 'actor', 
                          'photographer', 'musician', 'interior designer', 'restaurant owner', 'teacher', 
                          'designer', 'surgeon', 'social worker', 'veterinarian', 'psychiatrist', 'chiropractor', 
                          'auto dealer', 'small business owner', 'optometrist', 'producer', 'business', 
                          '.information requested', 'financial advisor', 'pharmacist', 'psychotherapist', 
                          'manager', 'management consultant', 'general contractor', 'finance', 'orthodontist', 
                          'actress', 'n.a.', 'restauranteur', 'property management', 'home builder', 'oil & gas', 
                          'real estate investments', 'geologist', 'professor', 'farming', 'real estate agent', 
                          'na', 'financial planner', 'community volunteer', 'property manager', 'political consultant', 
                          'public relations', 'business consultant', 'publisher', 'insurance broker', 'educator', 
                          'nurse', 'orthopedic surgeon', 'editor', 'marketing', 'dairy farmer', 'investment advisor', 
                          'freelance writer', 'investment banker', 'trader', 'computer consultant', 'banker', 
                          'oral surgeon', 'business executive', 'unknown', 'civic volunteer', 'filmmaker', 'economist'])

class OrganizationFilter(Filter):
    def process_record(self, record):
        orgname = record.get('org_name', '').strip()
        if not orgname or orgname.lower() in disallowed_orgnames:
            orgname = record.get('emp_ef', '').strip()
            if (not orgname or orgname.lower() in disallowed_orgnames) and '/' in record.get('fec_occ_emp',''):
                (emp, occ) = record.get('fec_occ_emp','').split('/', 1)
                orgname = emp.strip()
        record['organization_name'] = orgname if orgname and orgname.lower() not in disallowed_orgnames else None
        return record

class CommitteeFilter(Filter):
    def __init__(self, committees):
        super(CommitteeFilter, self).__init__()
        self._committees = committees
    def process_record(self, record):
        cmte_id = record['cmte_id'].upper()
        committee = self._committees.get('%s:%s' % (record['cycle'], cmte_id), None)
        if committee:
            record['committee_name'] = committee['pac_short']
            record['committee_party'] = committee['party']
        return record
        

class RecipientFilter(Filter):
    def __init__(self, candidates, committees):
        super(RecipientFilter, self).__init__()
        self._candidates = candidates
        self._committees = committees
    def process_record(self, record):
        recip_id = record['recip_id'].upper()
        if recip_id.startswith('N'):
            recipient = self._candidates.get('%s:%s' % (record['cycle'], recip_id), None)
            self.load_candidate(recipient, record)
        else:
            recipient = self._committees.get('%s:%s' % (record['cycle'], recip_id), None)
            self.load_committee(recipient, record)
        return record
    def load_candidate(self, candidate, record):
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
    def load_committee(self, committee, record):
        if committee:
            record['recipient_name'] = committee['pac_short']
            record['recipient_party'] = committee['party']
            record['recipient_type'] = 'committee'
            cmte_id = record['cmte_id'].upper()
            recip_id = committee['recip_id'].upper()
            if cmte_id == record['recip_id'].upper() and cmte_id != recip_id:
                print "!!!!  loading committee recipient"
                candidate = self._candidates.get('%s:%s' % (record['cycle'], recip_id), None)
                self.load_candidate(candidate, record)

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
    tmppath = os.path.join(dataroot, 'tmp')
    if not os.path.exists(tmppath):
        os.makedirs(tmppath)

    print "Loading catcodes..."
    catcodes = load_catcodes(dataroot)
    
    print "Loading candidates..."
    candidates = load_candidates(dataroot)
    
    print "Loading committees..."
    committees = load_committees(dataroot)
    
    emitter = CSVEmitter(open(os.path.join(tmppath, 'denorm_indivs.csv'), 'w'), fieldnames=FIELDNAMES)

    files = Files(*[os.path.join(dataroot, 'raw', 'crp', 'indivs%s.csv' % cycle) for cycle in cycles])
    
    spec = dict(((fn, None) for fn in FIELDNAMES))
    
    # urn methods
    
    def recipient_urn(s):
        if s.startswith('N'):
            return candidate_urn(s)
        elif s.startswith('C'):
            return committee_urn(s)
        return None
    
    def candidate_urn(s):    
        return 'urn:crp:candidate:%s' % s.strip().upper() if s else None        
    
    def contributor_urn(s):
        return 'urn:crp:individual:%s' % s.strip().upper() if s else None
    
    def committee_urn(s):
        return 'urn:crp:committee:%s' % s.strip().upper() if s else None
    
    def org_urn(s):
        return 'urn:crp:organization:%s' % s.strip() if s else None
    
    #
    # main recipe
    #
    
    recipe = saucebrush.run_recipe(
        
        # load source
        CSVSource(files, fieldnames=FILE_TYPES['indivs']),
        
        FieldCountValidator(len(FILE_TYPES['indivs'])),
        
        # transaction filters
        FieldAdder('transaction_namespace', 'urn:fec:transaction'),
        FieldMerger({'transaction_id': ('cycle','fec_trans_id')}, lambda cycle, fecid: '%s:%s' % (cycle, fecid), keep_fields=True),
        FieldMerger({'transaction_type': ('type',)}, lambda t: t.strip().lower(), keep_fields=True),
        
        # filing reference ID
        FieldRenamer({'filing_id': 'microfilm'}),
        
        # date stamp
        FieldModifier('datestamp', parse_date_iso),
        
        # rename contributor, organization, and parent_organization fields
        FieldRenamer({'contributor_name': 'contrib',
                      'parent_organization_name': 'ult_org',}),
                      
        RecipientFilter(candidates, committees),
        CommitteeFilter(committees),
        OrganizationFilter(),
        
        # create URNs
        FieldMerger({'contributor_urn': ('contrib_id',)}, contributor_urn, keep_fields=True),
        FieldMerger({'recipient_urn': ('recip_id',)}, recipient_urn, keep_fields=True),
        FieldMerger({'committee_urn': ('cmte_id',)}, committee_urn, keep_fields=True),
        
        # recip code filter
        RecipCodeFilter(),  # recipient party
                            # seat result
        
        # address and gender fields
        FieldRenamer({'contributor_address': 'street',
                      'contributor_city': 'city',
                      'contributor_state': 'state',
                      'conitrbutor_zipcode': 'zipcode',
                      'contributor_gender': 'gender'}),
        FieldModifier('contributor_state', lambda s: s.upper() if s else None),
        FieldModifier('contributor_gender', lambda s: s.upper() if s else None),
        
        # employer/occupation filter
        FECOccupationFilter(),
        
        # catcode
        CatCodeFilter('contributor', catcodes),
        
        # add static fields
        FieldAdder('contributor_type', 'individual'),
        FieldAdder('is_amendment', False),
        FieldAdder('election_type', 'G'),
        
        # filter through spec
        SpecFilter(spec),
        
        #DebugEmitter(),
        CountEmitter(every=1000),
        emitter,
        
    )
    
    print recipe.rejected

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    main()
    
