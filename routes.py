from constants import *
from controllers import Authorization
from controllers import SportByTree
from controllers import CheckAuthCode
from controllers import Event
from controllers import SportsWithRelations

def route(api):
    api.add_resource(Authorization, API_PREFIX + '/login')
    api.add_resource(SportByTree, API_PREFIX + '/sports')
    api.add_resource(CheckAuthCode, API_PREFIX + '/checkcode')
    api.add_resource(Event, API_PREFIX + '/event')
    api.add_resource(SportsWithRelations, API_PREFIX + '/sportswithrelations')
