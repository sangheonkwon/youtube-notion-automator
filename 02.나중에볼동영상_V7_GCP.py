# %%
import os
# import pickle # pickle은 더 이상 사용되지 않습니다.
from google.oauth2 import service_account # 서비스 계정 인증용
from googleapiclient.discovery import build
from notion_client import Client # Notion 클라이언트 추가
from datetime import datetime # 날짜 형식 변환을 위해 추가

# Google API 설정
SERVICE_ACCOUNT_FILE = "C:\\vscode_youtube_WL_automator\\youtube-watch-later-crawling-fb772b75c268.json" # 예: "path/to/your/service_account_key.json"
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"] # 읽기 전용 권한 요청

# Notion API 설정
NOTION_API_KEY = "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" # 예: "secret_xxxxxxxxxxxxxxxxxxxxxxxxxxx"
NOTION_DATABASE_ID = "1f6fe5f021b080359a53fee397a95b81" # YOUR_NOTION_DATABASE_ID 예: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Notion 데이터베이스의 제목 속성 이름 (Notion 데이터베이스 설정에 따라 다를 수 있음)
# 보통 기본값은 'Name' 또는 '이름' 입니다. 데이터베이스의 title(Title) 속성 이름을 정확히 입력해주세요.
NOTION_TITLE_PROPERTY_NAME = "title" # 실제 Notion 데이터베이스의 제목 속성 이름으로 변경하세요.

# Notion 데이터베이스의 날짜 속성 이름 (새로 추가됨)
# Notion 데이터베이스에 이 이름으로 '날짜(Date)' 타입의 속성을 만들어야 합니다.
NOTION_ADDED_AT_PROPERTY_NAME = "재생목록 추가일"
NOTION_UPLOADED_AT_PROPERTY_NAME = "비디오 업로드일"


# --- 환경 변수에서 설정값 가져오기 (클라우드 환경에 배포 시 권장) ---
# SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE_PATH')
# NOTION_API_KEY = os.environ.get('NOTION_API_KEY')
# NOTION_DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')
# WATCH_LATER_PLAYLIST_ID_OVERRIDE = os.environ.get('WATCH_LATER_PLAYLIST_ID')

def get_authenticated_service():
    """
    서비스 계정 자격 증명을 사용하여 YouTube API 서비스 객체를 반환합니다.
    """
    if 'SERVICE_ACCOUNT_FILE' not in globals() or not SERVICE_ACCOUNT_FILE:
        raise ValueError("SERVICE_ACCOUNT_FILE 경로가 설정되지 않았습니다. 스크립트 상단에서 해당 변수를 설정해주세요.")

    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"서비스 계정 키 파일을 찾을 수 없습니다: {SERVICE_ACCOUNT_FILE}")

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    return build(API_SERVICE_NAME, API_VERSION, credentials=creds)

youtube_service = None
try:
    if 'SERVICE_ACCOUNT_FILE' not in globals() or globals().get('SERVICE_ACCOUNT_FILE') == "여기에_서비스_계정_JSON_키_파일_경로를_입력하세요.json" or not globals().get('SERVICE_ACCOUNT_FILE'):
        print("주의: SERVICE_ACCOUNT_FILE 변수에 실제 서비스 계정 JSON 키 파일 경로를 설정해야 합니다.")
        print("스크립트 상단의 SERVICE_ACCOUNT_FILE = \"...\" 부분을 수정해주세요.")
    else:
        youtube_service = get_authenticated_service()
        print("YouTube API 서비스 인증 성공 (서비스 계정 사용)!")
except ValueError as ve:
    print(f"YouTube API 인증 설정 오류: {ve}")
except FileNotFoundError as fnfe:
    print(f"YouTube API 인증 오류: {fnfe}")
except Exception as e:
    print(f"YouTube API 인증 중 예상치 못한 오류 발생: {e}")
    print(f"서비스 계정 키 파일 ('{SERVICE_ACCOUNT_FILE if 'SERVICE_ACCOUNT_FILE' in globals() else '미설정'}') 경로와 파일 내용, 그리고 Google Cloud Console에서 해당 서비스 계정에 YouTube Data API v3 사용 권한이 부여되었는지 확인하세요.")

# '나중에 볼 동영상' 재생목록 ID 또는 특정 재생목록 ID
# WATCH_LATER_PLAYLIST_ID_OVERRIDE = os.environ.get('WATCH_LATER_PLAYLIST_ID') # 환경 변수 사용 시
# watch_later_playlist_id = WATCH_LATER_PLAYLIST_ID_OVERRIDE if WATCH_LATER_PLAYLIST_ID_OVERRIDE else "WL" # 기본값 'WL'
watch_later_playlist_id = "PL-hMCW0kj4eIAf6Yjz_p_dgfHjxX99ope" # 여기에 사용할 재생목록 ID를 직접 입력하세요.

if watch_later_playlist_id:
    print(f"사용할 재생목록 ID: {watch_later_playlist_id}")
else:
    # 이 경우는 WATCH_LATER_PLAYLIST_ID_OVERRIDE가 None이고 기본값도 설정되지 않았을 때 발생할 수 있습니다.
    # 위에서 watch_later_playlist_id에 직접 값을 할당했으므로, 이 메시지는 거의 나타나지 않습니다.
    print("재생목록 ID를 확인하지 못했습니다. 스크립트 내 'watch_later_playlist_id' 변수를 확인하세요.")
    # 필요시 기본값 설정 또는 오류 처리
    # watch_later_playlist_id = "WL"

def format_iso_date_to_yyyymmdd(iso_date_string):
    """ISO 8601 형식의 날짜 문자열을 'YYYY-MM-DD' 형식으로 변환합니다."""
    if not iso_date_string:
        return None
    try:
        # 'Z'로 끝나는 UTC 시간을 파싱합니다. Python 3.7+ 에서는 datetime.fromisoformat으로 가능
        # 여기서는 일반성을 위해 datetime.strptime 사용
        dt_object = datetime.strptime(iso_date_string, "%Y-%m-%dT%H:%M:%S%z" if 'Z' in iso_date_string.upper() else "%Y-%m-%dT%H:%M:%S")
        return dt_object.strftime("%Y-%m-%d")
    except ValueError: # 가끔 밀리초가 포함된 형식이 올 수 있음 (예: ...000Z)
        try:
            dt_object = datetime.strptime(iso_date_string.split('.')[0] + "Z", "%Y-%m-%dT%H:%M:%SZ")
            return dt_object.strftime("%Y-%m-%d")
        except Exception:
             # 날짜 문자열 앞부분만 잘라서 사용 (YYYY-MM-DD)
            return iso_date_string[:10] if len(iso_date_string) >= 10 else None


def get_watch_later_videos(service, playlist_id):
    video_ids = []
    video_details = {} # {video_id: {"title": "...", "added_to_playlist_at": "YYYY-MM-DD", "video_upload_date": "YYYY-MM-DD"}}
    next_page_token = None

    if not playlist_id:
        print("재생목록 ID가 유효하지 않습니다.")
        return video_ids, video_details

    print(f"'{playlist_id}' 재생목록에서 동영상 정보를 가져오는 중...")
    
    playlist_items_ids_for_video_details = []
    try:
        while True:
            request = service.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                title = item["snippet"]["title"]
                # API에서 받은 ISO 날짜 형식을 "YYYY-MM-DD"로 바로 변환
                added_to_playlist_at_iso = item["snippet"]["publishedAt"]
                formatted_added_date = format_iso_date_to_yyyymmdd(added_to_playlist_at_iso)

                if video_id not in video_ids:
                    video_ids.append(video_id)
                    playlist_items_ids_for_video_details.append(video_id)
                    video_details[video_id] = {
                        "title": title,
                        "added_to_playlist_at": formatted_added_date,
                        "video_upload_date": None # 아직 비디오 업로드 날짜는 모름
                    }
            
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        print(f"총 {len(video_ids)}개의 비디오 ID 및 기본 정보를 추출했습니다.")

    except Exception as e:
        print(f"재생목록에서 동영상 기본 정보를 가져오는 중 오류 발생: {e}")
        if "playlistNotFound" in str(e):
            print("오류: 재생목록을 찾을 수 없습니다. ID를 확인하세요.")
        elif "quotaExceeded" in str(e):
            print("오류: YouTube API 할당량이 초과되었습니다.")
        else:
            print("기타 오류 발생 (playlistItems). API 응답을 확인하세요.")
        return video_ids, video_details

    if playlist_items_ids_for_video_details:
        print(f"\n추출된 {len(playlist_items_ids_for_video_details)}개 비디오의 업로드 날짜를 가져오는 중...")
        for i in range(0, len(playlist_items_ids_for_video_details), 50):
            chunk_video_ids = playlist_items_ids_for_video_details[i:i+50]
            try:
                video_list_request = service.videos().list(
                    part="snippet",
                    id=",".join(chunk_video_ids)
                )
                video_list_response = video_list_request.execute()

                for video_item in video_list_response.get("items", []):
                    vid = video_item["id"]
                    video_upload_date_iso = video_item["snippet"]["publishedAt"]
                    # API에서 받은 ISO 날짜 형식을 "YYYY-MM-DD"로 바로 변환
                    formatted_upload_date = format_iso_date_to_yyyymmdd(video_upload_date_iso)
                    if vid in video_details:
                        video_details[vid]["video_upload_date"] = formatted_upload_date
            
            except Exception as e:
                print(f"비디오 업로드 날짜를 가져오는 중 오류 발생 (ID: {chunk_video_ids}): {e}")
    
    print(f"\n모든 정보 처리가 완료되었습니다. 총 {len(video_details)}개의 비디오 상세 정보를 확보했습니다.")
    return video_ids, video_details


def add_videos_to_notion(api_key, database_id, title_property_name, video_details_map):
    if not api_key or not database_id:
        print("Notion API 키 또는 데이터베이스 ID가 설정되지 않았습니다.")
        return

    notion = Client(auth=api_key)
    print(f"\nNotion 데이터베이스 '{database_id}'에 비디오 정보를 추가하는 중...")

    existing_video_ids_in_notion = set()
    try:
        # Notion 데이터베이스에서 'Video ID' 속성을 기준으로 기존 항목 조회
        # Notion DB에 'Video ID'라는 텍스트(rich_text) 속성이 있다고 가정
        print("Notion에서 기존 비디오 ID를 가져오는 중...")
        next_cursor = None
        while True:
            query_response = notion.databases.query(
                database_id=database_id,
                start_cursor=next_cursor
                # 필요시 filter 추가:
                # filter={"property": "Video ID", "rich_text": {"is_not_empty": True}}
            )
            results = query_response.get("results", [])
            for page in results:
                properties = page.get("properties", {})
                video_id_property = properties.get("Video ID", {}).get("rich_text")
                if video_id_property and len(video_id_property) > 0:
                    existing_id = video_id_property[0].get("plain_text", "")
                    if existing_id:
                        existing_video_ids_in_notion.add(existing_id.strip())
            
            next_cursor = query_response.get("next_cursor")
            if not next_cursor:
                break
        print(f"Notion 데이터베이스에서 {len(existing_video_ids_in_notion)}개의 기존 비디오 ID를 확인했습니다.")

    except Exception as e:
        print(f"Notion에서 기존 비디오 ID를 가져오는 중 오류 발생: {e}")
        print("기존 ID 조회에 실패하여 중복 추가가 발생할 수 있습니다.")


    added_count = 0
    skipped_count = 0
    # video_details_map은 {video_id: {"title": ..., "added_to_playlist_at": ..., "video_upload_date": ...}} 형식
    for video_id, details in video_details_map.items():
        if video_id in existing_video_ids_in_notion:
            skipped_count += 1
            continue

        page_title = details.get("title", f"제목 없는 비디오 ({video_id})")
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        added_date = details.get("added_to_playlist_at") # 이미 "YYYY-MM-DD" 형식
        upload_date = details.get("video_upload_date")   # 이미 "YYYY-MM-DD" 형식

        new_page_properties = {
            title_property_name: {
                "title": [{"text": {"content": page_title}}]
            },
            "Video ID": { # Notion에 "Video ID"라는 이름의 텍스트(rich_text) 속성 필요
                "rich_text": [{"text": {"content": video_id}}]
            },
            "URL": {"url": youtube_url}, # Notion에 "URL"이라는 이름의 URL 속성 필요
            "Tags": { # Notion에 "Tags"라는 이름의 다중 선택(multi_select) 속성 필요
                "multi_select": [{"name": "Watch Later"}] # 필요시 태그 이름 변경
            }
        }

        # 날짜 속성 추가 (Notion에 해당 이름의 '날짜' 타입 속성 필요)
        if added_date:
            new_page_properties[NOTION_ADDED_AT_PROPERTY_NAME] = {
                "date": {"start": added_date}
            }
        if upload_date:
            new_page_properties[NOTION_UPLOADED_AT_PROPERTY_NAME] = {
                "date": {"start": upload_date}
            }
        
        try:
            notion.pages.create(
                parent={"database_id": database_id},
                properties=new_page_properties
            )
            print(f"  추가됨: {video_id} - {page_title}")
            added_count += 1
        except Exception as e:
            print(f"Notion에 비디오 ({video_id} - {page_title}) 추가 중 오류 발생: {e}")
            error_message = str(e).lower()
            if "could not find property" in error_message or \
               "validation failed" in error_message or \
               "does not match the schema" in error_message or \
               "is not a valid date" in error_message: # 날짜 형식 오류 메시지 추가
                print("  오류 상세: Notion 데이터베이스의 속성 이름이나 타입이 코드와 일치하지 않을 수 있습니다.")
                print(f"  코드에서 사용된 제목 속성: '{title_property_name}'")
                print(f"  코드에서 사용된 날짜 속성: '{NOTION_ADDED_AT_PROPERTY_NAME}', '{NOTION_UPLOADED_AT_PROPERTY_NAME}'")
                print(f"  코드에서 사용된 기타 속성들: {list(key for key in new_page_properties if key not in [title_property_name, NOTION_ADDED_AT_PROPERTY_NAME, NOTION_UPLOADED_AT_PROPERTY_NAME])}")
                print("  Notion 데이터베이스의 실제 속성 구성(이름, 타입)을 확인하고 코드를 수정하거나 Notion DB 스키마를 맞추세요.")
                print(f"  특히 '{NOTION_ADDED_AT_PROPERTY_NAME}' 및 '{NOTION_UPLOADED_AT_PROPERTY_NAME}' 속성이 '날짜(Date)' 타입으로 존재하는지 확인하세요.")
                # 설정 오류일 가능성이 높으므로, 추가적인 API 호출을 막기 위해 중단할 수 있습니다.
                # return # 또는 break

    print(f"\nNotion에 총 {added_count}개의 새 비디오 정보를 추가했습니다.")
    print(f"{skipped_count}개의 비디오는 이미 존재하여 건너뛰었습니다.")


# --- 메인 실행 로직 ---
def main():
    if 'SERVICE_ACCOUNT_FILE' not in globals() or \
       globals().get('SERVICE_ACCOUNT_FILE') == "여기에_서비스_계정_JSON_키_파일_경로를_입력하세요.json" or \
       not globals().get('SERVICE_ACCOUNT_FILE'):
        print("오류: SERVICE_ACCOUNT_FILE 경로가 설정되지 않았습니다. 스크립트를 실행할 수 없습니다.")
        print("스크립트 상단의 SERVICE_ACCOUNT_FILE = \"...\" 부분을 실제 서비스 계정 JSON 키 파일 경로로 수정해주세요.")
        return

    if not youtube_service:
        print("YouTube 서비스가 초기화되지 않았습니다. Notion 동기화를 진행할 수 없습니다.")
        return

    if not watch_later_playlist_id: # 재생목록 ID가 유효한지 확인
        print("처리할 YouTube 재생목록 ID가 설정되지 않았습니다. 스크립트 상단의 'watch_later_playlist_id' 변수를 확인하세요.")
        return
        
    # YouTube에서 비디오 정보 가져오기
    retrieved_video_ids, retrieved_video_details = get_watch_later_videos(youtube_service, watch_later_playlist_id)

    if retrieved_video_ids:
        print(f"\n총 {len(retrieved_video_ids)}개의 비디오를 YouTube에서 추출했습니다.")
        print("추출된 비디오 상세 정보 (처음 5개):")
        for i, vid in enumerate(retrieved_video_ids[:5]):
            details = retrieved_video_details.get(vid, {})
            title = details.get('title', '제목 없음')
            added_date = details.get('added_to_playlist_at', '추가 날짜 없음')
            upload_date = details.get('video_upload_date', '업로드 날짜 없음')
            print(f"  {i+1}. ID: {vid}")
            print(f"     제목: {title}")
            print(f"     재생목록 추가일: {added_date}")
            print(f"     비디오 업로드일: {upload_date}")
    else:
        print(f"'{watch_later_playlist_id}' 재생목록에서 비디오를 찾을 수 없거나 접근할 수 없습니다.")
        # get_watch_later_videos 함수 내에서 이미 상세 메시지가 출력되었을 수 있음

    # Notion에 비디오 정보 추가
    if retrieved_video_details and NOTION_API_KEY and NOTION_DATABASE_ID and NOTION_TITLE_PROPERTY_NAME:
        # NOTION_TITLE_PROPERTY_NAME은 Notion DB의 제목 속성 실제 이름으로 설정해야 합니다.
        add_videos_to_notion(NOTION_API_KEY, NOTION_DATABASE_ID, NOTION_TITLE_PROPERTY_NAME, retrieved_video_details)
    elif not retrieved_video_details:
        print("추출된 YouTube 비디오 상세 정보가 없습니다. Notion에 추가할 데이터가 없습니다.")
    else: # API 키, DB ID, 또는 타이틀 속성 이름이 없는 경우
        missing_configs = []
        if not NOTION_API_KEY:
            missing_configs.append("NOTION_API_KEY")
        if not NOTION_DATABASE_ID:
            missing_configs.append("NOTION_DATABASE_ID")
        if not NOTION_TITLE_PROPERTY_NAME:
             missing_configs.append("NOTION_TITLE_PROPERTY_NAME (실제 Notion DB 제목 속성 이름)")
        print(f"Notion 설정 정보가 누락되었습니다: {', '.join(missing_configs)}. 스크립트 상단의 정보를 확인하세요.")

if __name__ == '__main__':
    # 스크립트 상단에서 SERVICE_ACCOUNT_FILE, NOTION_API_KEY, NOTION_DATABASE_ID,
    # NOTION_TITLE_PROPERTY_NAME, watch_later_playlist_id 등을 정확히 설정했는지 확인하세요.
    main()

# %%



