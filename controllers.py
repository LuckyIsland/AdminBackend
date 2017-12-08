from flask_restful import Resource
from flask import request
# from flask_api import status
import json
import random
import uuid

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
        pass
        # try:
        #     data = request.data
        # except:
        #     return {'Message': 'Bad request data!', 'Status': 2}
        # return {}

        # try:
        #     data['SportId']
        #     data['LeagueId']
        #     data['EventDate']
        #     data['HomeId']
        #     data['GuestId']
        #     data['Description']
        #     data['CountryCode']
        #     data['BetType']

        #     event_code = self._generate_event_code()
        #     event_type = 0
        #     event_name = 'HomeTeam - GuestTeam'
        #     period = 1
        #     timer = 0
        #     status = 0
        #     created_date = now()
        #     betting_line_template_id = 1
        #     league_status = league(status)
        #     end_date = calculate start + delta
        #     team_winner_id = None
        #     is_approved = 0
        # except KeyError:
        #     return {'Message': 'Bad request data!', 'Status': 2}

    def _generate_event_code():
        return str(random.randint(1000, 9999))




class SportByTree(Resource):
    def get(self):
        session = Session()
        session.connection()
        query = session.execute("exec webAPI_Client_GetSportsTree")
        headers = query.keys()
        sports_tree = query.fetchall()

        result = {'headers': list(headers), 'data': []}
        for sport in sports_tree:
            result['data'] += list(sport)

        return result, status.HTTP_200_OK
