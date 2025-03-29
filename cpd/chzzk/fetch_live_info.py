import requests
import json
import os

headers = {
    "Client-Id": os.environ['CLINET_ID'],
    "Client-Secret": os.environ['CLINET_SECRET'],
    "Content-Type": "application/json"
}


def fetch_all_live_channels():
    base_url = "https://openapi.chzzk.naver.com/open/v1/lives"
    params = {"size": 20}  # 요청당 라이브 목록 개수, 기본값은 20

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


def fetch_follower_infos():
    base_url = "https://openapi.chzzk.naver.com/open/v1/channels"
if __name__ == '__main__':
    channels = fetch_all_live_channels()

    # channels 리스트를 channels.json 파일에 저장 (UTF-8 인코딩, indent 적용)
    with open("channels.json", "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=4)

    print("channels.json 파일에 결과가 저장되었습니다.")