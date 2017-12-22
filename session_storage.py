from db_helper import Session
from constants import *

class SessionStorage(object):
    pre_code_sessions = {}
    sessions = {}

    @staticmethod
    def set_pre_code_session(session, code, user_id):
        SessionStorage.pre_code_sessions[session] = {'Code': str(code), 'UserId': user_id, 'Count': 0}

    @staticmethod
    def get_valid_code(session):
        res = SessionStorage.pre_code_sessions.get(session, None)
        if res:
            res['Count'] += 1
        if res and res['Count'] > 3:
            res = None
            if session in SessionStorage.pre_code_sessions.keys():
                SessionStorage.pre_code_sessions.pop(session)
        # print res
        return res

    @staticmethod
    def set_session(session, user_id):
        SessionStorage.sessions[session] = user_id
        if session in SessionStorage.pre_code_sessions.keys():
            SessionStorage.pre_code_sessions.pop(session)

    @staticmethod
    def get_account_role(session):
        user_id = SessionStorage.sessions.get(session, -1)
        db = Session()
        role = UNDEFINED
        try:
            role = db.execute("select top(1) AccountRole from account with(nolock) where id = {user_id}".format(user_id=user_id)).fetchone()[0]
        except:
            role = UNDEFINED
        db.close()
        return role

    @staticmethod
    def get_user_id(session):
        return SessionStorage.sessions.get(session, -1)

    @staticmethod
    def check_access(session):
        # print SessionStorage.sessions
        role = SessionStorage.get_account_role(session)
        if role == ADMIN or role == AGENT:
            return True
        else:
            return False
