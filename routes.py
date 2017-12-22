from constants import *
from controllers import Authorization
from controllers import CheckAuthCode
from controllers import Event
from controllers import SportsWithRelations
from controllers import AgentTree
from controllers import UsersByAgent
from controllers import DetailUser

def route(api):
    api.add_resource(Authorization, API_PREFIX + '/login')
    api.add_resource(CheckAuthCode, API_PREFIX + '/checkcode')
    api.add_resource(Event, API_PREFIX + '/event')
    api.add_resource(SportsWithRelations, API_PREFIX + '/sportswithrelations')
    api.add_resource(AgentTree, API_PREFIX + '/agentstree')
    api.add_resource(UsersByAgent, API_PREFIX + '/usersbyagent')
    api.add_resource(DetailUser, API_PREFIX + '/detailuser')
