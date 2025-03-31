import requests
import json
import os
import datetime


def fetch_all_live_channels():
    base_url = "https://openapi.chzzk.naver.com/open/v1/lives"
    params = {"size": 20}  # 요청당 라이브 목록 개수, 기본값은 20
    headers = {
        "Client-Id": os.environ['CLINET_ID'],
        "Client-Secret": os.environ['CLINET_SECRET'],
        "Content-Type": "application/json"
    }

    results = []
    next_token = None

    while True:
        if next_token:
            params["next"] = next_token
        else:
            params.pop("next", None)

        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break

        json_data = response.json()
        content = json_data.get("content", {})  # content 내부에 page와 data가 있음

        # content 내 data 배열에서 원하는 필드 추출
        for item in content.get("data", []):
            channel_info = {
                "channelName": item.get("channelName"),
                "channelId": item.get("channelId"),
                "concurrentUserCount": item.get("concurrentUserCount")
            }
            results.append(channel_info)

        page = content.get("page", {})
        next_token = page.get("next")

        if not next_token:
            break

    return results

def fetch_follower_infos(channels):
    base_url = "https://openapi.chzzk.naver.com/open/v1/channels"
    headers = {
    "Client-Id": os.environ['CLINET_ID'],
    "Client-Secret": os.environ['CLINET_SECRET'],
    "Content-Type": "application/json"
    }
    
    params = {"channelIds":[]}
    
    for i in range(0,len(channels),20):
        batch = channels[i:i+20]
        channel_ids = [ch["channelId"] for ch in batch]
        params = {"channelIds": channel_ids}
        try:
            response = requests.get(base_url, headers=headers, params=params)
            if response.status_code == 200:
                json_data = response.json()
                content = json_data.get("content", {})  # content 내부에 page와 data가 있음
                mapping = {item["channelId"]: item["followerCount"] for item in content.get("data", [])}
                for ch in batch:
                    ch["followerCount"] = mapping.get(ch["channelId"], 0)
            else:
                # 실패 시 기본값 0 할당
                for ch in batch:
                    ch["followerCount"] = 0
        except Exception as e:
            print("팔로워 정보 조회 오류:", e)
            for ch in batch:
                ch["followerCount"] = 0
    return channels



if __name__ == '__main__':
    channels = fetch_all_live_channels()

    with open("channels/channels.json", "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=4)
    
    print("channels.json 파일에 결과가 저장되었습니다.")
    
    # all_channels.json 파일에서 기존 채널 데이터 로드 (파일이 없으면 빈 리스트로 초기화)
    try:
        with open("channels/all_channels.json", "r", encoding="utf-8") as f:
            all_channels = json.load(f)
    except FileNotFoundError:
        all_channels = []
    
    # 기존 채널 목록에 없는 새로운 채널만 추가 (channelId 기준)
    existing_ids = {channel["channelId"] for channel in all_channels}
    new_channels = [channel for channel in channels if channel["channelId"] not in existing_ids]
    new_channels = fetch_follower_infos(new_channels)
    
    if new_channels:
        all_channels.extend(new_channels)
        with open("channels/all_channels.json", "w", encoding="utf-8") as f:
            json.dump(all_channels, f, ensure_ascii=False, indent=4)
        print(f"all_channels.json 파일에 {len(new_channels)}개의 새로운 채널이 추가되었습니다.")
    else:
        print("추가할 새로운 채널이 없습니다.")