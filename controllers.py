from flask_restful import Resource
from flask import request
# from flask_api import status
import json
import random
import uuid
from datetime import datetime
from datetime import timedelta
from dateutil import parser as date_parser

from constants import *
from db_helper import Session
from mail_helper import MailHelper
from session_storage import SessionStorage


class Authorization(Resource):
    def post(self):
        data = request.data
        try:
            data = json.loads(data)
            email = data['Email']
            password = data['Password']
        except (ValueError, KeyError):
            return {'Message': 'Bad request data!', 'Status': 2}

        session = Session()
        query = session.execute("SELECT Id, Email, FirstName, LastName FROM Account WHERE email = '{0}' AND password = '{1}' AND AccountRole in ('Admin', 'Agent')".format(email, password))

        user = query.fetchone()
        if not user:
            return {'Message': 'Invalid login or password!', 'Status': 1}

        response = self._make_one_response(query.keys(), user)
        session = self._generate_session()
        code = self._generate_code()
        response['Session'] = session
        user_id = response['Id']

        SessionStorage.set_pre_code_session(session, code, user_id)
        MailHelper().send_code(response['Email'], code)

        return {'Results': response, 'Message': 'OK', 'Status': 0}

    def _make_one_response(self, keys, values):
        res = {}
        for i, k in enumerate(keys):
            res[k] = values[i]
        return res

    def _generate_code(self):
        return random.randint(100000, 999999)

    def _generate_session(self):
        return uuid.uuid4().hex

class CheckAuthCode(Resource):
    def post(self):
        data = request.data
        try:
            data = json.loads(data)
            session = data['Session']
            code = data['Code']
        except (ValueError, KeyError):
            return {'Message': 'Bad request data!', 'Status': 2}

        valid = SessionStorage.get_valid_code(session)
        if valid is not None and str(valid['Code']) == str(code):
            user_id = valid['UserId']
            SessionStorage.set_session(session, user_id)
            sql_session = Session()
            query = sql_session.execute("SELECT FirstName, LastName, Balance, Currency FROM Account WHERE id = {0}".format(user_id))

            user = query.fetchone()
            if not user:
                return {'Message': 'User doesn exist!', 'Status': -1}

            response = self._make_one_response(query.keys(), user)
            response['Balance'] = float(response['Balance'])

            return {'Results': response, 'Message': 'OK', 'Status': 0}
        else:
            return {'Message': 'Wrong code!', 'Status': 3}

    def _make_one_response(self, keys, values):
        res = {}
        for i, k in enumerate(keys):
            res[k] = values[i]
        return res


class SportsWithRelations(Resource):
    def get(self):
        if not SessionStorage.check_access(request.headers.get(SESSION_HEADER)):
            return PERMISSIONS_DENIED

        sql_session = Session()
        sports = self._get_sports(sql_session)
        sports = self._update_sports_with_bet_types(sql_session, sports)

        return sports

    def _get_sports(self, sql_session):
        sql_query = sql_session.execute("exec webAPI_Admin_GetAllSportWithRelations")
        keys = sql_query.keys()
        data = [self._raw_sql_row_to_dict_with_keys(keys, row) for row in sql_query.fetchall()]

        sports = []
        inserted_sports = {}

        for row in data:
            if not inserted_sports.has_key(row['SportId']):
                sports.append({
                    'SportId': row['SportId'],
                    'SportName': row['SportName'],
                    'Countries': [],
                    'Teams': [],
                    })
                inserted_sports[row['SportId']] = True

        for sport in sports:
            inserted_countries = {}
            inserted_teams = {}
            for row in data:
                if sport['SportId'] == row['SportId'] and not inserted_countries.has_key(row['CountryCode']):
                    sport['Countries'].append({
                        'CountryCode': row['CountryCode'],
                        'CountryName': row['CountryName'],
                        'Leagues': [],
                        })
                    inserted_countries[row['CountryCode']] = True
                if sport['SportId'] == row['SportId'] and not inserted_teams.has_key(row['TeamId']) and row['TeamId'] != None:
                    sport['Teams'].append({
                        'TeamId': row['TeamId'],
                        'TeamName': row['TeamName'],
                        })
                    inserted_teams[row['TeamId']] = True

            for country in sport['Countries']:
                inserted_leagues = {}
                for row in data:
                    if sport['SportId'] == row['SportId'] and country['CountryCode'] == row['CountryCode'] and not inserted_leagues.has_key(row['LeagueId']):
                        country['Leagues'].append({
                            'LeagueId': row['LeagueId'],
                            'LeagueName': row['LeagueName'],
                            })
                        inserted_leagues[row['LeagueId']] = True

        return sports

    def _update_sports_with_bet_types(self, sql_session, sports):
        sql_query = sql_session.execute("exec webAPI_Admin_GetAllSportWithBetTypes")
        keys = sql_query.keys()
        data = [self._raw_sql_row_to_dict_with_keys(keys, row) for row in sql_query.fetchall()]

        for sport in sports:
            sport['BetTypes'] = []
            inserted_bet_types = {}

            for row in data:
                if sport['SportId'] == row['SportId'] and not inserted_bet_types.has_key(row['BetTypeId']):
                    sport['BetTypes'].append({
                        'BetTypeId': row['BetTypeId'],
                        'BetTypeName': row['BetTypeName'],
                        'Odds': [],
                        })
                    inserted_bet_types[row['BetTypeId']] = True

            for bet_type in sport['BetTypes']:
                inserted_odds = {}

                for row in data:
                    if sport['SportId'] == row['SportId'] and bet_type['BetTypeId'] == row['BetTypeId'] and not inserted_odds.has_key(row['OddId']):
                        bet_type['Odds'].append({
                            'OddId': row['OddId'],
                            'OddTitle': row['OddTitle'],
                            'IsOddPoint': row['IsOddPoint'],
                            })
                        inserted_odds[row['OddId']] = True

        return sports

    def _raw_sql_row_to_dict_with_keys(self, keys, row):
        res = {}
        for i in xrange(len(keys)):
            res[keys[i]] = row[i]
        return res



class Event(Resource):
    def post(self):
        if not SessionStorage.check_access(request.headers.get(SESSION_HEADER)):
            return PERMISSIONS_DENIED

        data = request.data
        try:
            data = json.loads(data)
            sport_id = data['SportId']
            league_id = data['LeagueId']
            event_date = data['EventDate']
            home_id = data['HomeId']
            guest_id = data['GuestId']
            description = data.get('Description', '')
            country_code = data['CountryCode']
            bet_type_id = data['BetType']['BetTypeId']
            odds = data['BetType']['Odds']
        except:
            return {'Message': 'Bad request data!', 'Status': 2}

        session = Session()
        try:
            event_code = self._generate_event_code()
            event_name = self._get_event_name(home_id, guest_id)
            created_date = str(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
            league_status = self._get_league_status(league_id)
            end_date = self._get_end_date(event_date, sport_id)
            # event_type = 0
            # period = 1
            # timer = 0
            # status = 0
            # betting_line_template_id = 1
            # team_winner_id = None
            # is_approved = 0

            session.execute("insert into event(sportid, leagueid, eventdate, homeid, guestid, description, countrycode, bettypeid, eventcode, eventname, createddate, leaguestatus, enddate) values({sport_id}, {league_id}, '{event_date}', {home_id}, {guest_id}, '{description}', '{country_code}', {bet_type_id}, '{event_code}', '{event_name}', '{created_date}', {league_status}, '{end_date}')".format(
                sport_id=sport_id,
                league_id=league_id,
                event_date=event_date,
                home_id=home_id,
                guest_id=guest_id,
                description=description,
                country_code=country_code,
                bet_type_id=bet_type_id,
                event_code=event_code,
                event_name=event_name,
                created_date=created_date,
                league_status=league_status,
                end_date=end_date
            ))
            event_id = session.execute("select top(1) id from event with(nolock) order by id desc").fetchone()[0]

            for odd in odds:
                factor = odd.get('OddFactor', None)
                type_id = odd.get('OddId', None)
                limit = odd.get('OddLimit', None)
                if limit is None or type_id is None or factor is None:
                    print 'Something is None (limit, factor, type_id)'
                    return {'Message': 'Bad request data!', 'Status': 2}
                session.execute("insert into eventodds(eventid, bettypeid, oddtypeid, oddfactor, limit) values({event_id}, {bet_type_id}, {type_id}, {factor}, {limit})".format(
                    event_id=event_id,
                    bet_type_id=bet_type_id,
                    type_id=type_id,
                    factor=factor,
                    limit=limit
                ))

            session.commit()
            return {'Message': 'Success!', 'Status': 0}
        except Exception as e:
            session.rollback()
            print e
            return {'Message': 'Bad request data!', 'Status': 2}
        finally:
            session.close()


    def _generate_event_code(self):
        return str(random.randint(1000, 9999))

    def _get_end_date(self, start_date, sport_id):
        session = Session()
        dur = session.execute("select top(1) matchduration from sport with(nolock) where id = {sport_id}".format(sport_id=sport_id)).fetchone()[0]
        dur = timedelta(minutes=int(dur))
        start_date = date_parser.parse(start_date)
        end_date = str(start_date + dur)
        session.close()
        return end_date

    def _get_league_status(self, league_id):
        session = Session()
        status = session.execute("select top(1) status from league with(nolock) where id = {league_id}".format(league_id=league_id)).fetchone()[0]
        return int(status)

    def _get_event_name(self, home_id, guest_id):
        session = Session()
        home = session.execute("select top(1) name from team with(nolock) where id = {home_id}".format(home_id=home_id)).fetchone()[0]
        guest = session.execute("select top(1) name from team with(nolock) where id = {guest_id}".format(guest_id=guest_id)).fetchone()[0]
        return "{home} - {guest}".format(home=home, guest=guest)


class AgentTree(Resource):
    def get(self):
        if not SessionStorage.check_access(request.headers.get(SESSION_HEADER)):
            return PERMISSIONS_DENIED

        session = Session()
        agents = session.execute("select id, firstname, lastname, parrentid from account where accountrole = 'Agent'").fetchall()

        auth_user_role = SessionStorage.get_account_role(request.headers.get(SESSION_HEADER))
        resp = []
        if auth_user_role == AGENT:
            resp = self._generate_agents_tree(agents, SessionStorage.get_user_id(request.headers.get(SESSION_HEADER)))
        elif auth_user_role == ADMIN:
            resp = self._generate_agents_tree(agents)

        return {'Message': 'OK!', 'Status': 0, 'Results': resp}

    def _generate_agents_tree(self, agents, start_agent=None):
        old_count = 0
        count = 0

        res = []
        cur = {}
        for agent in agents:
            if (agent[3] is None and start_agent is None) or (start_agent is not None and agent[0] == start_agent):
                tmp = {
                    "Name": agent[1] + ' ' + agent[2],
                    "Id": int(agent[0]),
                    "Agents" : []
                    }
                cur[agent[0]] = tmp['Agents']
                res.append(tmp)
                count += 1

        while count != old_count:
            old_count = count
            new_cur = {}
            for agent in agents:
                tmp = cur.get(agent[3], None)
                if tmp is not None:
                    t = {
                    "Name": agent[1] + ' ' + agent[2],
                    "Id": int(agent[0]),
                    "Agents" : []
                    }
                    new_cur[agent[0]] = t['Agents']
                    tmp.append(t)
                    count += 1
            cur = new_cur

        return res

class UsersByAgent(Resource):
    def post(self):
        if not SessionStorage.check_access(request.headers.get(SESSION_HEADER)):
            return PERMISSIONS_DENIED

        data = request.data
        try:
            data = json.loads(data)
            agent_id = data['AgentId']
        except:
            return {'Message': 'Bad request data!', 'Status': 2}
        session = Session()
        query = session.execute("select FirstName, LastName, Email, PostCode, Balance, LimitGroupId, CountryCode, City, TimeZone, Currency from account with(nolock) where parrentid = {agent_id} and accountrole = 'User'".format(agent_id=agent_id))
        users = query.fetchall()
        resp = self._make_resp(query.keys(), users)
        return {'Message': 'OK!', 'Status': 0, 'Results': resp}

    def _make_resp(self, keys, rows):
        res = []
        for values in rows:
            d = {}
            for i, k in enumerate(keys):
                d[k] = values[i]
                if type(d[k]).__name__ == 'Decimal':
                    d[k] = float(d[k])
            res.append(d)
        return res


class DetailUser(Resource):
    def post(self):
        if not SessionStorage.check_access(request.headers.get(SESSION_HEADER)):
            return PERMISSIONS_DENIED

        data = request.data
        try:
            data = json.loads(data)
            user_id = data['UserId']
        except:
            return {'Message': 'Bad request data!', 'Status': 2}

        session = Session()
        query = session.execute("select top(1) FirstName, LastName, Email, PostCode, Balance, LimitGroupId, CountryCode, City, TimeZone, Currency, AccountRole from account with(nolock) where id = {user_id}".format(user_id=user_id))
        user = query.fetchone()
        resp = self._make_one_response(query.keys(), user)
        return {'Message': 'OK!', 'Status': 0, 'Results': resp}

    def _make_one_response(self, keys, values):
        res = {}
        for i, k in enumerate(keys):
            res[k] = values[i]
            if type(res[k]).__name__ == 'Decimal':
                res[k] = float(res[k])
        return res
