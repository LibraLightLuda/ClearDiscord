# -*- coding: utf-8 -*-
"""
Undiscord Core 엔진 모듈
디스코드 API와의 인터페이스 및 실제 메시지 검색/삭제 파이프라인 처리를 수행합니다.
모든 로그 및 API 연동 결과 안내 메시지가 다국어(i18n) 설정에 맞추어 출력되도록 설계되었습니다.
"""

import re
import time
import random
import requests
from datetime import datetime
from undiscord_utils import ms_to_hms, to_snowflake, validate_discord_url
from undiscord_i18n import MESSAGES

class UndiscordCore:
    """
    Discord API를 사용하여 특정 채널 내 지정된 조건의 메시지를 자동으로 일괄 검색 및 삭제하는 핵심 엔진입니다.
    """
    def __init__(self, options, log_queue, progress_callback, stop_callback):
        self.options = options
        self.log_queue = log_queue
        self.progress_callback = progress_callback
        self.stop_callback = stop_callback
        
        # 주입된 언어 정보 추출 (기본값 ko)
        self.lang = self.options.get('language', 'ko')

        self.state = {
            'running': False,
            'delCount': 0,
            'failCount': 0,
            'grandTotal': 0,
            'offset': 0,
            'iterations': 0,
            '_searchResponse': None,
            '_messagesToDelete': [],
            '_skippedMessages': []
        }

        self.stats = {
            'startTime': None,
            'endTime': None,
            'throttledCount': 0,
            'throttledTotalTime': 0,
            'lastPing': 0,
            'avgPing': 0,
            'etr': 0
        }

        self.session = requests.Session()
        self.session.trust_env = False
        # 만인간 공격(MitM) 프록시 탈취 방지를 위해 로컬 프록시 우회 설정 강제 주입
        self.session.proxies = {'http': None, 'https': None}
        self.session.headers.update({
            'Authorization': self.options.get('authToken', ''),
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self._before_ts = 0

    def log(self, log_type, message):
        """이벤트 및 경고 내용을 GUI 스레드로 안전하게 전달하기 위해 큐(Queue)에 적재합니다."""
        self.log_queue.put((log_type, message))

    def reset_state(self):
        """엔진 재작동 또는 배치 작업 처리를 위해 내부 상태를 완전 초기화합니다."""
        self.state = {
            'running': False,
            'delCount': 0,
            'failCount': 0,
            'grandTotal': 0,
            'offset': 0,
            'iterations': 0,
            '_searchResponse': None,
            '_messagesToDelete': [],
            '_skippedMessages': []
        }
        self.options['askForConfirmation'] = True

    def before_request(self):
        """네트워크 요청 직전 타임스탬프를 캡처하여 지연(Ping)을 산출할 준비를 합니다."""
        self._before_ts = time.time()

    def after_request(self):
        """네트워크 요청 직후 지연 시간을 밀리초 단위로 수집하고, 이동평균 핑(Average Ping)을 갱신합니다."""
        last_ping = int((time.time() - self._before_ts) * 1000)
        self.stats['lastPing'] = last_ping
        if self.stats['avgPing'] > 0:
            self.stats['avgPing'] = int((self.stats['avgPing'] * 0.9) + (last_ping * 0.1))
        else:
            self.stats['avgPing'] = last_ping

    def print_stats(self):
        """현재 엔진의 구동 지연 세팅 및 평균 핑, 차단 횟수 통계를 GUI 로그로 출력합니다."""
        min_d = self.options.get('minDeleteDelay', 1500)
        max_d = self.options.get('maxDeleteDelay', 3000)
        
        self.log('verb', MESSAGES[self.lang]['log_engine_stats_delay'].format(
            min_d=min_d, 
            max_d=max_d, 
            search=self.options['searchDelay']
        ))
        self.log('verb', MESSAGES[self.lang]['log_engine_stats_ping'].format(
            ping=self.stats['lastPing'], 
            avg_ping=self.stats['avgPing']
        ))
        self.log('verb', MESSAGES[self.lang]['log_engine_stats_throttled'].format(
            count=self.stats['throttledCount'], 
            time=ms_to_hms(self.stats['throttledTotalTime'])
        ))

    def get_delete_delay(self):
        """설정된 범위(minDeleteDelay ~ maxDeleteDelay) 내에서 무작위 대기 시간(초)을 결정해 반환합니다."""
        min_d = self.options.get('minDeleteDelay', 1500) / 1000.0
        max_d = self.options.get('maxDeleteDelay', 3000) / 1000.0
        if min_d > max_d:
            min_d, max_d = max_d, min_d
        val = random.uniform(min_d, max_d)
        
        self.log('debug', MESSAGES[self.lang]['log_engine_delay'].format(val=val))
        return val

    def calc_etr(self):
        """
        남은 메시지 수량과 평균 삭제 지연 시간, 검색 호출 횟수를 연산하여
        최종 완료까지 걸릴 예상 소요 시간(ETR)을 계산합니다.
        """
        remaining_searches = max(0, round(self.state['grandTotal'] / 25.0))
        search_wait = (self.options['searchDelay'] * remaining_searches)

        avg_delete_delay = (self.options.get('minDeleteDelay', 1500) + self.options.get('maxDeleteDelay', 3000)) / 2.0
        remaining_messages = max(0, self.state['grandTotal'] - self.state['delCount'])
        delete_wait = (avg_delete_delay + self.stats['avgPing']) * remaining_messages
        self.stats['etr'] = int(max(0, search_wait + delete_wait))

    def search(self):
        """
        디스코드 검색 API를 호출하여 삭제 대상 메시지들을 25건 단위 오프셋 기반으로 쿼리해 옵니다.
        Rate Limit(HTTP 429) 또는 인덱싱 중(HTTP 202) 발생 시 안전 지연 후 자동 재시도합니다.
        """
        guild_id = self.options['guildId']
        channel_id = self.options['channelId']

        if guild_id == '@me':
            url = f"https://discord.com/api/v9/channels/{channel_id}/messages/search"
        else:
            url = f"https://discord.com/api/v9/guilds/{guild_id}/messages/search"

        # 위조 도메인 방지용 화이트리스트 검사
        validate_discord_url(url)

        params = {}
        if self.options.get('authorId'):
            params['author_id'] = self.options['authorId']
        if guild_id != '@me' and channel_id:
            params['channel_id'] = channel_id
        if self.options.get('minId'):
            params['min_id'] = to_snowflake(self.options['minId'])
        if self.options.get('maxId'):
            params['max_id'] = to_snowflake(self.options['maxId'])

        params['sort_by'] = 'timestamp'
        params['sort_order'] = 'desc'
        params['offset'] = self.state['offset']

        if self.options.get('hasLink'):
            params['has'] = 'link'
        if self.options.get('hasFile'):
            params['has'] = 'file'
        if self.options.get('content'):
            params['content'] = self.options['content']
        if self.options.get('includeNsfw'):
            params['include_nsfw'] = 'true'

        self.before_request()
        try:
            # verify=True 설정으로 HTTPS SSL 인증서 유효성 체크 강제 적용
            resp = self.session.get(url, params=params, verify=True)
            self.after_request()
        except Exception as e:
            self.state['running'] = False
            self.log('error', MESSAGES[self.lang]['log_engine_search_http_err'].format(e=e))
            raise e

        # HTTP 202: 디스코드 서버가 메시지를 인덱싱 중인 경우
        if resp.status_code == 202:
            try:
                retry_after = resp.json().get('retry_after', 2.0)
            except Exception:
                retry_after = 2.0
            w = int(retry_after * 1000)
            self.stats['throttledCount'] += 1
            self.stats['throttledTotalTime'] += w
            
            self.log('warn', MESSAGES[self.lang]['log_engine_indexing'].format(retry_after=retry_after))
            time.sleep(retry_after)
            return self.search()

        # HTTP 429: 요청 속도 초과 제한이 발생한 경우
        if resp.status_code == 429:
            try:
                retry_after = resp.json().get('retry_after', 2.0)
            except Exception:
                retry_after = 2.0
            w = int(retry_after * 1000)
            self.stats['throttledCount'] += 1
            self.stats['throttledTotalTime'] += w
            self.options['searchDelay'] += w
            
            self.log('warn', MESSAGES[self.lang]['log_engine_rate_limit_search'].format(wait_time=retry_after * 2))
            time.sleep(retry_after * 2)
            return self.search()

        if not resp.ok:
            self.state['running'] = False
            try:
                err_body = resp.json()
            except Exception:
                err_body = resp.text
                
            self.log('error', MESSAGES[self.lang]['log_engine_search_fail'].format(status=resp.status_code, err=err_body))
            raise Exception(f"API Error {resp.status_code}")

        data = resp.json()
        self.state['_searchResponse'] = data
        return data

    def filter_response(self):
        """
        API로 수신한 검색 원본 결과에서 실제로 지울 수 있는 유효 유형의 메시지만 선별합니다.
        고정된 메시지(pinned), 정규식(pattern) 매칭 조건 등을 가려내어 메시지를 필터링합니다.
        """
        data = self.state['_searchResponse']
        total = data.get('total_results', 0)
        if total > self.state['grandTotal']:
            self.state['grandTotal'] = total

        messages = data.get('messages', [])
        discovered_messages = []
        for convo in messages:
            hit_msg = next((m for m in convo if m.get('hit') is True), None)
            if hit_msg:
                discovered_messages.append(hit_msg)

        messages_to_delete = []
        for msg in discovered_messages:
            msg_type = msg.get('type', 0)
            is_valid_type = (msg_type == 0 or (6 <= msg_type <= 21))
            is_pinned = msg.get('pinned', False)

            if is_valid_type:
                if is_pinned and not self.options.get('includePinned'):
                    continue
                messages_to_delete.append(msg)

        pattern = self.options.get('pattern')
        if pattern:
            try:
                regex = re.compile(pattern, re.IGNORECASE)
                messages_to_delete = [m for m in messages_to_delete if regex.search(m.get('content', ''))]
            except Exception as e:
                self.log('warn', MESSAGES[self.lang]['log_engine_regex_fail'].format(e=e))

        skipped_messages = [msg for msg in discovered_messages if msg not in messages_to_delete]

        self.state['_messagesToDelete'] = messages_to_delete
        self.state['_skippedMessages'] = skipped_messages

    def delete_message(self, message):
        """
        단일 메시지를 삭제하기 위해 DELETE API 요청을 보냅니다.
        삭제 한도(HTTP 429) 도달 시 삭제 대기 시간을 자동으로 늘려 재검증합니다.
        """
        channel_id = message.get('channel_id')
        msg_id = message.get('id')
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{msg_id}"

        # 위조 도메인 방지용 화이트리스트 검사
        validate_discord_url(url)

        self.before_request()
        try:
            # verify=True 설정으로 HTTPS SSL 인증서 유효성 체크 강제 적용
            resp = self.session.delete(url, verify=True)
            self.after_request()
        except Exception as e:
            self.log('error', MESSAGES[self.lang]['log_engine_delete_http_err'].format(e=e))
            self.state['failCount'] += 1
            return 'FAILED'

        if resp.status_code == 429:
            try:
                retry_after = resp.json().get('retry_after', 2.0)
            except Exception:
                retry_after = 2.0
            w = int(retry_after * 1000)
            self.stats['throttledCount'] += 1
            self.stats['throttledTotalTime'] += w
            self.options['minDeleteDelay'] = w
            self.options['maxDeleteDelay'] = w + 1500
            
            self.log('warn', MESSAGES[self.lang]['log_engine_rate_limit_delete'].format(retry_after=retry_after, w=w))
            time.sleep(retry_after * 2)
            return 'RETRY'

        elif not resp.ok:
            if resp.status_code == 400:
                try:
                    err_json = resp.json()
                    # 50083: 아카이브된 스레드 등 삭제 불가 예외 처리
                    if err_json.get('code') == 50083:
                        self.log('warn', MESSAGES[self.lang]['log_engine_archive_thread'])
                        self.state['offset'] += 1
                        self.state['failCount'] += 1
                        return 'FAIL_SKIP'
                except Exception:
                    pass

            self.log('error', MESSAGES[self.lang]['log_engine_delete_fail'].format(status=resp.status_code, text=resp.text))
            self.state['failCount'] += 1
            return 'FAILED'

        self.state['delCount'] += 1
        return 'OK'

    def delete_messages_from_list(self):
        """추출된 메시지 목록을 순회하며 하나씩 삭제합니다."""
        consecutive_fails = 0
        for i, message in enumerate(self.state['_messagesToDelete']):
            if not self.state['running']:
                self.log('error', MESSAGES[self.lang]['log_engine_stop_user'])
                return

            msg_time = message.get('timestamp', '')
            author = message.get('author', {})
            username = f"{author.get('username', 'Unknown')}#{author.get('discriminator', '0000')}"
            content = message.get('content', '')
            msg_id = message.get('id', '')

            content_preview = f"{content[:40]}..." if len(content) > 40 else content
            info_text = MESSAGES[self.lang]['log_engine_info_fmt'].format(
                del_count=self.state['delCount'] + 1,
                total=self.state['grandTotal'],
                time=msg_time,
                username=username,
                content=content_preview,
                id=msg_id
            )
            self.log('info', info_text)

            attempt = 0
            max_attempt = self.options.get('maxAttempt', 2)
            success = False
            while attempt < max_attempt:
                result = self.delete_message(message)
                if result == 'RETRY':
                    attempt += 1
                    delay_sec = self.options.get('minDeleteDelay', 1500) / 1000.0
                    self.log('verb', MESSAGES[self.lang]['log_engine_retry'].format(delay=delay_sec, attempt=attempt, max_attempt=max_attempt))
                    time.sleep(delay_sec)
                elif result == 'OK':
                    success = True
                    break
                else:
                    break

            if success:
                consecutive_fails = 0
            else:
                consecutive_fails += 1
                if consecutive_fails >= 5:
                    self.log('error', MESSAGES[self.lang]['log_engine_consecutive_fails'])
                    self.stop()
                    return

            self.calc_etr()
            if self.progress_callback:
                self.progress_callback(self.state, self.stats)

            if self.state['running']:
                delay_sec = self.get_delete_delay()
                time.sleep(delay_sec)

    def run(self, is_job=False):
        """엔진의 메인 루프를 구동하여 데이터 쿼리, 확인 팝업, 삭제 작업을 순차적으로 주도합니다."""
        if self.state['running'] and not is_job:
            self.log('error', MESSAGES[self.lang]['log_engine_running'])
            return

        self.state['running'] = True
        self.stats['startTime'] = datetime.now()
        
        self.log('success', MESSAGES[self.lang]['log_engine_started'].format(time=self.stats['startTime'].strftime('%Y-%m-%d %H:%M:%S')))
        self.log('debug', MESSAGES[self.lang]['log_engine_params'].format(
            author_id=self.options['authorId'], 
            guild_id=self.options['guildId'], 
            channel_id=self.options['channelId']
        ))

        while self.state['running']:
            self.state['iterations'] += 1
            self.log('verb', MESSAGES[self.lang]['log_engine_fetching'])

            try:
                self.search()
                self.filter_response()
            except Exception as e:
                self.state['running'] = False
                self.log('error', MESSAGES[self.lang]['log_engine_loop_err'].format(e=e))
                break

            total_found = len(self.state['_searchResponse'].get('messages', []))
            self.log('verb', MESSAGES[self.lang]['log_engine_summary'].format(
                total=self.state['grandTotal'],
                found=total_found,
                to_delete=len(self.state['_messagesToDelete']),
                skipped=len(self.state['_skippedMessages']),
                offset=self.state['offset']
            ))
            self.print_stats()

            self.calc_etr()
            self.log('verb', MESSAGES[self.lang]['log_engine_etr'].format(etr=ms_to_hms(self.stats['etr'])))

            if len(self.state['_messagesToDelete']) > 0:
                if self.options.get('askForConfirmation'):
                    if self.options.get('ask_callback'):
                        preview = "\n".join([
                            f"- {m.get('author', {}).get('username', 'Unknown')}: {m.get('content', '')[:40]}"
                            for m in self.state['_messagesToDelete'][:5]
                        ])
                        msg = MESSAGES[self.lang]['log_engine_confirm_msg'].format(
                            total=self.state['grandTotal'],
                            etr=ms_to_hms(self.stats['etr']),
                            preview=preview
                        )
                        ans = self.options['ask_callback'](msg)
                        if not ans:
                            self.log('error', MESSAGES[self.lang]['log_engine_confirm_cancel'])
                            self.state['running'] = False
                            break
                    self.options['askForConfirmation'] = False

                self.delete_messages_from_list()

            elif len(self.state['_skippedMessages']) > 0:
                old_offset = self.state['offset']
                self.state['offset'] += len(self.state['_skippedMessages'])
                self.log('verb', MESSAGES[self.lang]['log_engine_skip_page'].format(old=old_offset, new=self.state['offset']))

            else:
                self.log('success', MESSAGES[self.lang]['log_engine_api_end'])
                if is_job:
                    break
                self.state['running'] = False

            if self.state['running']:
                search_delay = self.options['searchDelay'] / 1000.0
                self.log('verb', MESSAGES[self.lang]['log_engine_next_page'].format(delay=search_delay))
                time.sleep(search_delay)

        self.stats['endTime'] = datetime.now()
        duration = self.stats['endTime'] - self.stats['startTime']
        duration_ms = int(duration.total_seconds() * 1000)

        self.log('success', MESSAGES[self.lang]['log_engine_finished'].format(time=self.stats['endTime'].strftime('%Y-%m-%d %H:%M:%S')))
        self.log('success', MESSAGES[self.lang]['log_engine_time_summary'].format(
            time=ms_to_hms(duration_ms), 
            del_count=self.state['delCount'], 
            fail_count=self.state['failCount']
        ))
        self.print_stats()

        # 작업 완료 후 보안을 위해 메모리 상의 토큰 파기
        self.session.headers.pop('Authorization', None)
        if 'authToken' in self.options:
            self.options['authToken'] = ""

        if not is_job and self.stop_callback:
            self.stop_callback(self.state, self.stats)

    def run_batch(self, queue_jobs):
        """다중 채널 일괄 삭제(배치 작업) 시 리스트의 모든 채널을 순차적으로 수행합니다."""
        self.state['running'] = True
        self.log('info', MESSAGES[self.lang]['log_engine_batch_setup'].format(count=len(queue_jobs)))
        for idx, job in enumerate(queue_jobs):
            if not self.state['running']:
                break
            self.log('info', MESSAGES[self.lang]['log_engine_batch_start'].format(
                idx=idx + 1, 
                total=len(queue_jobs), 
                channel_id=job['channelId']
            ))
            
            self.options.update(job)
            self.reset_state()
            self.options['askForConfirmation'] = False
            self.state['running'] = True
            
            self.run(is_job=True)

        # 배치 작업 완료 후 최종 토큰 메모리 소멸
        self.session.headers.pop('Authorization', None)
        if 'authToken' in self.options:
            self.options['authToken'] = ""

        self.log('success', MESSAGES[self.lang]['log_engine_batch_finished'])
        self.state['running'] = False
        if self.stop_callback:
            self.stop_callback(self.state, self.stats)

    def stop(self):
        """메인 루프를 정지하여 추가적인 삭제 API 요청 수행을 보류 및 안전 중단합니다."""
        self.state['running'] = False


def fetch_guilds(token: str) -> list:
    """
    주어진 디스코드 토큰을 사용하여 사용자가 참여 중인 서버(Guild) 목록을 가져옵니다.
    """
    url = "https://discord.com/api/v9/users/@me/guilds"
    validate_discord_url(url)
    
    session = requests.Session()
    session.trust_env = False
    session.proxies = {'http': None, 'https': None}
    headers = {
        'Authorization': token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    resp = session.get(url, headers=headers, verify=True)
    if resp.status_code == 200:
        return resp.json()
    else:
        resp.raise_for_status()


def fetch_channels(token: str, guild_id: str) -> list:
    """
    특정 서버 ID에 속한 채널 목록을 가져옵니다.
    guild_id가 '@me'일 경우 개인 DM 채널 목록을 가져옵니다.
    """
    if guild_id == "@me":
        url = "https://discord.com/api/v9/users/@me/channels"
    else:
        url = f"https://discord.com/api/v9/guilds/{guild_id}/channels"
        
    validate_discord_url(url)
        
    session = requests.Session()
    session.trust_env = False
    session.proxies = {'http': None, 'https': None}
    headers = {
        'Authorization': token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    resp = session.get(url, headers=headers, verify=True)
    if resp.status_code == 200:
        return resp.json()
    else:
        resp.raise_for_status()
