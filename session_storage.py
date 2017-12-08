class SessionStorage(object):
    pre_code_sessions = {}
    sessions = {}

    @staticmethod
    def set_pre_code_session(session, code, user_id):
        SessionStorage.pre_code_sessions[session] = {'Code': str(code), 'UserId': user_id}

    @staticmethod
    def get_valid_code(session):
        res = SessionStorage.pre_code_sessions.get(session, None)
        return res

    @staticmethod
    def set_session(session, user_id):
        SessionStorage.sessions[session] = user_id
        if session in SessionStorage.pre_code_sessions.keys():
            SessionStorage.pre_code_sessions.pop(session)
