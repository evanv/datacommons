from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.utils import simplejson
from django.db.models import Model
from piston.emitters import Emitter
from dcapi.middleware import RETURN_ENTITIES_KEY
from dcapi.models import Invocation
from dcapi.validate_jsonp import is_valid_jsonp_callback_value
from dcentity.models import entityref_cache
from dcdata.contribution.models import NIMSP_TRANSACTION_NAMESPACE, CRP_TRANSACTION_NAMESPACE
from time import time
import csv
import datetime

class AmnesiacFile(object):
    def __init__(self):
        self.content = ""
    def write(self, chunk):
        self.content += chunk
    def read(self, size=None):
        value = self.content
        self.content = ""
        return value

class StatsLogger(object):
    def __init__(self):
        self.stats = { 'total': 0 }
    def log(self, record):
        self.stats['total'] += 1

class StreamingLoggingEmitter(Emitter):
            
    def stream(self, request, stats):
        raise NotImplementedError('please implement this method')
    
    def stream_render(self, request):
        
        stats = self.handler.statslogger() if hasattr(self.handler, 'statslogger') else StatsLogger()
        
        if self.handler.fields:
            fields = self.handler.fields
        else:
            fields = self.data.model._meta.get_all_field_names()
            if self.handler.exclude:
                for field in self.handler.exclude:
                    fields.remove(field)
        
        if request.session.get(RETURN_ENTITIES_KEY, False):
            entity_fields = entityref_cache.get(self.handler.model, [])
            final_fields = fields + entity_fields
        else:
            final_fields = fields
        
        start_time = time()
        
        for chunk in self.stream(request, final_fields, stats):
            yield chunk
            
        end_time = time()
            
        Invocation.objects.create(
            caller_key=request.apikey.key,
            method=self.handler.__class__.__name__,
            query_string=request.META['QUERY_STRING'],
            total_records=stats.stats['total'],
            crp_records=stats.stats.get(CRP_TRANSACTION_NAMESPACE, 0),
            nimsp_records=stats.stats.get(NIMSP_TRANSACTION_NAMESPACE, 0),
            execution_time=(end_time - start_time) * 1000,
        )
        
            
class StreamingLoggingJSONEmitter(StreamingLoggingEmitter):
    
    def stream(self, request, fields, stats):
        
        cb = request.GET.get('callback', None)
        cb = cb if cb and is_valid_jsonp_callback_value(cb) else None
        
        qs = self.data
        if isinstance(qs, (Model, dict)):
            seria = simplejson.dumps(self.construct(), cls=DateTimeAwareJSONEncoder, ensure_ascii=False)
            yield seria

        else:
            yield '%s([' % cb if cb else '['

            for record in qs:
                self.data = record
                seria = simplejson.dumps(self.construct(), cls=DateTimeAwareJSONEncoder, ensure_ascii=False)
                if stats.stats['total'] == 0:
                    yield seria
                else:
                    yield ',%s' % seria
                stats.log(record)
            
            self.data = qs
        
            yield ']);' if cb else ']';

class StreamingLoggingCSVEmitter(StreamingLoggingEmitter):
    
    def stream(self, request, fields, stats):
        f = AmnesiacFile()
        writer = csv.DictWriter(f, fieldnames=fields)
        yield ",".join(fields) + "\n"
        for record in self.data.values(*fields):
            stats.log(record)
            writer.writerow(record)
            yield f.read()
            
            