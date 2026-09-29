import pytest

from globParams import state

#ТЕСТЫ РЕГИСТРАЦИИ
class TestRegistration:
    #РЕГИСТРАЦИЯ С АДЕКВАТНЫМИ ВВОДНЫМИ
    def test_start_registration_correct_id(self):
        test_role = 'TestRole'
        state.start_registration(test_role)
        assert state.registration_open is True
        assert state.registration_role == test_role

    '''
    #ЕСЛИ id ДОЛЖЕН БЫТЬ ТОЛЬКО СТРОКОЙ:
    @pytest.mark.parametrize('role', [None, 0, [], {}])
    def test_start_registration_invalid_id_type(self, role):
        with pytest.raises((TypeError, ValueError)):
            state.start_registration(role)
    '''
    #ЕСЛИ ДОПУСТИМ ЛЮБОЙ ТИП id:
    @pytest.mark.parametrize('role', [None, '', ' ', 0, 'a', 'ИТМО', 'итмо'])
    def test_start_registration_any_id_type(self, role):
        state.start_registration(role)
        assert state.registration_open is True
        assert state.registration_role == role


    #ЗАКРЫТИЕ РЕГИСТРАЦИИ
    def test_stop_registration(self):
        state.start_registration('TestRole')
        state.stop_registration()
        assert state.registration_open is False
        assert state.registration_role is None

    #ЗАКРЫТИЕ РЕГИСТРАЦИИ КОТОРАЯ НЕ БЫЛА ОТКРЫТА
    def test_stop_closed_registration(self):
        state.stop_registration()
        assert state.registration_open is False
        assert state.registration_role is None

    #ЗАКРЫТИЕ РЕГИСТРАЦИИ ДВАЖДЫ
    def test_stop_registration_twice(self):
        state.start_registration('TestRole')
        state.stop_registration()
        state.stop_registration()
        assert state.registration_open is False
        assert state.registration_role is None


#ТЕСТЫ ДЛЯ СЕССИЙ
class TestSession:
    #ПРОВЕРКА РАБОТЫ start_answer С РАЗНЫМИ ВВОДНЫМИ
    @pytest.mark.parametrize('test_user_id, test_query_id', [(10, 1), ('a', 'b'), (0, 10**15), (10**15, 0)])
    def test_start_answer(self, test_user_id, test_query_id):
        state.start_answer(test_user_id, test_query_id)
        assert state.user_sessions[test_user_id] == {'mode': 'answering', 'id_query': test_query_id}

    #ДВОЙНОЙ ВЫЗОВ start_answer 
    def test_start_answer_twice(self):
        test_user_id  = 10
        test_query_id = 1
        state.start_answer(test_user_id, test_query_id)
        state.start_answer(test_user_id, test_query_id)
        assert state.user_sessions[test_user_id] == {'mode': 'answering', 'id_query': test_query_id}

    #ПРОВЕРКА РАБОТЫ start_asking С РАЗНЫМИ ВВОДНЫМИ
    @pytest.mark.parametrize('test_user_id, test_ask_id, test_department', [(10, 1, 'department'), ('a', 'b', 0), (0, 1000, 'a' * 1000), (1000, 0, '')])
    def test_start_asking(self, test_user_id, test_ask_id, test_department):
        state.start_asking(test_user_id, test_ask_id, test_department)
        assert state.user_sessions[test_user_id] == {'mode': 'asking', 'id_ask': test_ask_id, 'depart': test_department} 
    
    #ДВОЙНОЙ ВЫЗОВ start_asking
    def test_start_asking_twice(self):
        test_user_id = 10
        test_ask_id = 1
        test_department = 'department'
        state.start_asking(test_user_id, test_ask_id, test_department)
        state.start_asking(test_user_id, test_ask_id, test_department)
        assert state.user_sessions[test_user_id] == {'mode': 'asking', 'id_ask': test_ask_id, 'depart': test_department}    

        #get_session ДО СОЗДАНИЯ СЕССИИ
    def test_get_session_returns_none(self):
        assert state.get_session(999) is None

        #get_session С УЖЕ СОЗДАННОЙ СЕССИЕЙ
    def test_get_session_returns_existing(self):
        state.start_answer(10, 1)
        result = state.get_session(10)
        assert result == {'mode': 'answering', 'id_query': 1}
    
    def test_clear_session_removes_user(self):
        state.start_answer(10, 1)
        assert 10 in state.user_sessions
        
        state.clear_session(10)
        assert 10 not in state.user_sessions

    #ДВОЙНОЙ ВЫЗОВ clear_session 
    def test_clear_session_twice(self):
        state.start_answer(10, 1)
        state.clear_session(10)
        state.clear_session(10)
        assert state.user_sessions == {}