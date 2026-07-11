# -*- coding: utf-8 -*-
"""
Undiscord Core 단위 테스트
requests API를 Mocking하여 UndiscordCore 클래스의 검색, 필터링 및 오프셋 관리 로직을 검증합니다.
"""

import unittest
from unittest.mock import patch, MagicMock
import queue
import time
import sys

# undiscord_gui 파일로부터 UndiscordCore 및 to_snowflake 가져오기
from undiscord_gui import UndiscordCore, to_snowflake

class TestUndiscordCore(unittest.TestCase):
    def setUp(self):
        # 기본 옵션 설정
        self.options = {
            'authToken': 'fake_token',
            'authorId': '12345',
            'guildId': '67890',
            'channelId': '111213',
            'minId': None,
            'maxId': None,
            'content': None,
            'hasLink': False,
            'hasFile': False,
            'includeNsfw': True,
            'includePinned': False,
            'searchDelay': 1,
            'deleteDelay': 1,
            'minDeleteDelay': 0,
            'maxDeleteDelay': 0,
            'useRandomDelay': False,
            'maxAttempt': 1,
            'askForConfirmation': False
        }
        self.log_queue = queue.Queue()
        self.progress_calls = []
        self.stop_calls = []
        
        def progress_cb(state, stats):
            self.progress_calls.append((state.copy(), stats.copy()))
            
        def stop_cb(state, stats):
            self.stop_calls.append((state.copy(), stats.copy()))
            
        self.core = UndiscordCore(self.options, self.log_queue, progress_cb, stop_cb)

    def test_to_snowflake(self):
        # 1. 날짜 문자열 변환 검증
        sf = to_snowflake("2026-01-01 00:00:00")
        self.assertIsNotNone(sf)
        self.assertTrue(sf.isdigit(), "Snowflake는 숫자 형태여야 합니다.")
        
        # 2. 일반 Snowflake ID 입력 시 통과 검증
        self.assertEqual(to_snowflake("1234567890"), "1234567890")
        
        # 3. None 또는 빈 값 입력 시 None 반환 검증
        self.assertIsNone(to_snowflake(""))
        self.assertIsNone(to_snowflake(None))

    @patch('requests.Session.get')
    def test_search_success(self, mock_get):
        # API 성공 응답 모의화
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            'total_results': 100,
            'messages': [
                [
                    {'id': '101', 'hit': True, 'type': 0, 'content': '안녕하세요', 'author': {'username': 'testuser'}, 'channel_id': '111213'}
                ]
            ]
        }
        mock_get.return_value = mock_response
        
        res = self.core.search()
        self.assertEqual(res['total_results'], 100)
        self.assertEqual(self.core.state['_searchResponse']['total_results'], 100)

    @patch('requests.Session.get')
    def test_search_rate_limited(self, mock_get):
        # 429 에러 후 200 성공 순차 모의화
        mock_resp_429 = MagicMock()
        mock_resp_429.status_code = 429
        mock_resp_429.ok = False
        mock_resp_429.json.return_value = {'retry_after': 0.01}
        
        mock_resp_200 = MagicMock()
        mock_resp_200.status_code = 200
        mock_resp_200.ok = True
        mock_resp_200.json.return_value = {'total_results': 5, 'messages': []}
        
        # side_effect를 통해 차례대로 다른 응답을 주도록 설정
        mock_get.side_effect = [mock_resp_429, mock_resp_200]
        
        res = self.core.search()
        self.assertEqual(res['total_results'], 5)
        self.assertEqual(self.core.stats['throttledCount'], 1, "Rate Limit 제한 횟수가 누적되어야 합니다.")

    def test_filter_response_types_and_pins(self):
        # 필터링 및 핀 고정 메시지 처리 테스트
        self.core.state['_searchResponse'] = {
            'total_results': 10,
            'messages': [
                # 1) 삭제 가능한 일반 메시지 (type=0, hit=True)
                [
                    {'id': '101', 'hit': True, 'type': 0, 'content': '정상 삭제 대상', 'author': {'username': 'user1'}, 'channel_id': '111213'},
                    {'id': '999', 'hit': False, 'type': 0, 'content': '대화 주변 컨텍스트'}
                ],
                # 2) 핀 고정된 메시지 (pinned=True, includePinned=False)
                [
                    {'id': '102', 'hit': True, 'type': 0, 'content': '핀 고정 메시지', 'pinned': True, 'author': {'username': 'user1'}, 'channel_id': '111213'}
                ],
                # 3) 삭제 불가능한 시스템 메시지 (type=3, hit=True)
                [
                    {'id': '103', 'hit': True, 'type': 3, 'content': '그룹 참여 알림', 'author': {'username': 'system'}, 'channel_id': '111213'}
                ]
            ]
        }
        
        # includePinned = False 상태로 실행
        self.core.filter_response()
        
        # 101번만 삭제 대상에 들어가야 함
        self.assertEqual(len(self.core.state['_messagesToDelete']), 1)
        self.assertEqual(self.core.state['_messagesToDelete'][0]['id'], '101')
        # 102(핀 고정으로 스킵), 103(타입 유효성 미달로 스킵)
        self.assertEqual(len(self.core.state['_skippedMessages']), 2)

    # test_filter_response_with_regex 제거됨 (정규식 필터링 기능 제거에 따른 검증 불필요)
    @patch('undiscord_gui.UndiscordCore.delete_message')
    def test_consecutive_delete_failures(self, mock_delete_msg):
        # 5회 연속 실패 시 작업이 조기에 멈추는지 검증
        mock_delete_msg.return_value = 'FAILED'
        
        # 6개의 삭제 메시지 세팅
        self.core.state['_messagesToDelete'] = [
            {'id': f'900{i}', 'timestamp': '2026-06-30T00:00:00', 'author': {'username': 'test'}, 'content': 'test', 'channel_id': '111'}
            for i in range(6)
        ]
        self.core.state['grandTotal'] = 6
        self.core.state['running'] = True
        
        self.core.delete_messages_from_list()
        
        # 5회 연속 실패 시 6번째는 실행하지 않고, running 상태가 False가 되어야 함.
        self.assertEqual(mock_delete_msg.call_count, 5, "5회 실패 시 루프가 즉각 중단되어야 합니다.")
        self.assertFalse(self.core.state['running'])

    @patch('undiscord_gui.UndiscordCore.search')
    @patch('undiscord_gui.UndiscordCore.filter_response')
    def test_empty_response_retry_limit(self, mock_filter, mock_search):
        # search와 filter_response가 호출될 때 빈 삭제 목록을 반환하도록 모의화
        def side_effect_search():
            self.core.state['_searchResponse'] = {'messages': []}
            return {'messages': []}

        def side_effect_filter():
            self.core.state['_messagesToDelete'] = []
            self.core.state['_skippedMessages'] = []

        mock_search.side_effect = side_effect_search
        mock_filter.side_effect = side_effect_filter
        
        # 빠른 테스트 실행을 위해 검색 딜레이를 0으로 설정
        self.core.options['searchDelay'] = 0
        
        # run() 실행
        self.core.run(is_job=False)
        
        # 최초 1회 실행 + 재시도 10회 = 총 11회 호출되어야 함
        self.assertEqual(mock_search.call_count, 11, "최초 1회 및 10회 재시도로 총 11회 호출되어야 합니다.")
        self.assertFalse(self.core.state['running'], "10회 재시도 초과 후 루프가 중단되어야 합니다.")

    @patch('undiscord_gui.UndiscordCore.search')
    @patch('undiscord_gui.UndiscordCore.filter_response')
    def test_empty_response_retry_bypass(self, mock_filter, mock_search):
        # 1. 초기 상태 설정
        self.core.state['last_min_id'] = '123456789'
        self.core.options['searchDelay'] = 0

        # search와 filter_response가 호출될 때 빈 삭제 목록을 반환하도록 모의화
        def side_effect_search():
            self.core.state['_searchResponse'] = {'messages': []}
            return {'messages': []}

        def side_effect_filter():
            self.core.state['_messagesToDelete'] = []
            self.core.state['_skippedMessages'] = []

        mock_search.side_effect = side_effect_search
        mock_filter.side_effect = side_effect_filter

        # 2. run() 실행
        self.core.run(is_job=False)

        # 3. 우회 검증
        # 최초 호출 + 2회 재시도 = 3회째에 bypass 동작하여 maxId = '123456788' 갱신 후 count=0 리셋
        # 그 후 다시 10회 재시도 후 루프 종료 조건 검사 직전까지 가므로 총 14회 호출되어야 함.
        self.assertEqual(mock_search.call_count, 14)
        self.assertEqual(self.core.options['maxId'], '123456788')
        self.assertEqual(self.core.state['offset'], 0)
        self.assertIsNone(self.core.state['last_min_id'])
        self.assertFalse(self.core.state['running'])

    @patch('builtins.open', new_callable=MagicMock)
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('undiscord_gui.UndiscordCore.delete_message')
    def test_backup_deleted_messages(self, mock_delete_msg, mock_makedirs, mock_exists, mock_open_file):
        # 1. backupDeleted = True 검증
        self.core.options['backupDeleted'] = True
        mock_delete_msg.return_value = 'OK'
        mock_exists.return_value = False
        
        # 삭제 대상 1개 세팅
        message = {'id': '99999', 'timestamp': '2026-07-11T16:44:05', 'author': {'username': 'backup_test', 'discriminator': '1234', 'id': '8888'}, 'content': '백업용 테스트 메시지', 'channel_id': '7777'}
        self.core.state['_messagesToDelete'] = [message]
        self.core.state['grandTotal'] = 1
        self.core.state['running'] = True
        
        self.core.delete_messages_from_list()
        
        # open 함수가 호출되었는지 검증
        mock_open_file.assert_called_once()
        # 파일명 포맷 검증 (guildId=67890, channel_id=7777)
        called_args = mock_open_file.call_args[0]
        self.assertTrue('backup_67890_7777.txt' in called_args[0].replace('/', '\\'))
        
        # 2. backupDeleted = False 일 때 호출 안 됨 검증
        mock_open_file.reset_mock()
        self.core.options['backupDeleted'] = False
        self.core.state['_messagesToDelete'] = [message]
        self.core.state['running'] = True
        
        self.core.delete_messages_from_list()
        mock_open_file.assert_not_called()

    @patch('builtins.open', new_callable=MagicMock)
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('undiscord_gui.UndiscordCore.delete_message')
    def test_mask_chat_log_and_backup_intact(self, mock_delete_msg, mock_makedirs, mock_exists, mock_open_file):
        mock_delete_msg.return_value = 'OK'
        mock_exists.return_value = True
        
        # 1. maskChatLog = True 일 때 로그 마스킹 검증 및 백업본 원본 유지 검증
        self.core.options['maskChatLog'] = True
        self.core.options['backupDeleted'] = True
        
        message = {'id': '99999', 'timestamp': '2026-07-11T16:44:05', 'author': {'username': 'mask_test', 'discriminator': '1234', 'id': '8888'}, 'content': '마스킹 대상 원래 내용', 'channel_id': '7777'}
        self.core.state['_messagesToDelete'] = [message]
        self.core.state['grandTotal'] = 1
        self.core.state['running'] = True
        
        # 로그 큐를 가로채기 위해 log 함수 임시 모의화
        logged_messages = []
        def mock_log(log_type, text):
            logged_messages.append(text)
        self.core.log = mock_log
        
        self.core.delete_messages_from_list()
        
        # 로그에 '●●● (마스킹됨)'이 포함되어 있는지 검증
        mask_logged = any('●●● (마스킹됨)' in log_text for log_text in logged_messages)
        self.assertTrue(mask_logged, "마스킹 옵션이 활성화되면 로그에 마스킹된 내용이 출력되어야 합니다.")
        
        # 백업 파일 쓰기(write) 시 원본 내용이 그대로 전달되었는지 검증
        mock_open_file.assert_called_once()
        handle = mock_open_file.return_value.__enter__.return_value
        written_content = "".join([call_args[0][0] for call_args in handle.write.call_args_list])
        self.assertIn('마스킹 대상 원래 내용', written_content, "마스킹 옵션이 활성화되더라도 백업 파일에는 원본 내용이 저장되어야 합니다.")
        self.assertNotIn('●●● (마스킹됨)', written_content, "백업 파일에는 마스킹 내용이 들어가면 안 됩니다.")
        
        # 2. maskChatLog = False 일 때 로그에 원본 노출 검증
        self.core.options['maskChatLog'] = False
        self.core.state['_messagesToDelete'] = [message]
        self.core.state['running'] = True
        logged_messages.clear()
        
        self.core.delete_messages_from_list()
        
        normal_logged = any('마스킹 대상 원래 내용' in log_text for log_text in logged_messages)
        self.assertTrue(normal_logged, "마스킹 옵션이 비활성화되면 로그에 원래 메시지 내용이 노출되어야 합니다.")

if __name__ == '__main__':
    unittest.main()

