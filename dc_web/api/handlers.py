from django.db.models import Q
from piston.handler import BaseHandler
from matchbox.models import Entity, Normalization
from dcdata.contribution.models import Contribution
from dc_web.search.contributions import CONTRIBUTION_SCHEMA
from matchbox.queries import search_entities_by_name

RESERVED_PARAMS = ('key','limit')

#
# contribution filter
#

class ContributionFilterHandler(BaseHandler):
    allowed_methods = ('GET',)
    exclude = ('id','import_reference')
    model = Contribution
    
    def read(self, request):
        params = request.GET.copy()
        limit = int(request.GET.get('limit', 10))
        for param in RESERVED_PARAMS:
            if param in params:
                del params[param]
        q = CONTRIBUTION_SCHEMA.extract_query(params)
        return Contribution.objects.filter(*q)[:limit]

#
# entity handlers
#

class EntityHandler(BaseHandler):
    allowed_methods = ('GET',)
    model = Entity
    
    def read(self, request, entity_id):
        return Entity.objects.get(pk=entity_id)

class EntityFilterHandler(BaseHandler):
    allowed_methods = ('GET',)
    fields = ('id','name','type','timestamp','reviewer',('attributes',('namespace','value')),('aliases',('alias',)))
    model = Entity

    def read(self, request):
        qs = Entity.objects.all().select_related()
        if 'name' in request.GET:
            print search_entities_by_name(request.GET['name'])
        if 'type' in request.GET:
            qs = qs.filter(type=request.GET['type'])
        return qs[:100]