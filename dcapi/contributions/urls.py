from django.conf.urls.defaults import *
from piston.resource import Resource
from dcapi.contributions.handlers import ContributionFilterHandler
from locksmith.auth.authentication import PistonKeyAuthentication

ad = { 'authentication': PistonKeyAuthentication() }
contributionfilter_handler = Resource(ContributionFilterHandler, **ad)

urlpatterns = patterns('',
    url(r'^.(?P<emitter_format>csv|json)$', contributionfilter_handler, name='api_contributions_filter'),
)