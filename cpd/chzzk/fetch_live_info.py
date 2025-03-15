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


def partition_channels(channels, k=10):
    import heapq
    """
    channels: 각 채널 정보를 담은 리스트 (각 항목은 dict로 channelName, channelId, concurrentUserCount 포함)
    k: 분배할 그룹(파일) 개수
    """
    # 시청자 수 내림차순 정렬
    sorted_channels = sorted(channels, key=lambda x: x.get("concurrentUserCount", 0), reverse=True)
    
    # 각 그룹을 (현재 총 시청자수, 그룹 번호, 채널 리스트) 형태의 튜플로 생성
    bins = [(0, i, []) for i in range(k)]
    heapq.heapify(bins)
    
    # 각 채널을 시청자 수가 가장 적은 그룹에 할당
    for channel in sorted_channels:
        current_sum, idx, bin_channels = heapq.heappop(bins)
        new_sum = current_sum + channel.get("concurrentUserCount", 0)
        bin_channels.append(channel)
        heapq.heappush(bins, (new_sum, idx, bin_channels))
    
    # 그룹 번호 순서대로 정렬
    bins_sorted = sorted(bins, key=lambda x: x[1])
    return bins_sorted

if __name__ == '__main__':
    channels = fetch_all_live_channels()

    # channels 리스트를 channels.json 파일에 저장 (UTF-8 인코딩, indent 적용)
    with open("channels.json", "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=4)

    print("channels.json 파일에 결과가 저장되었습니다.")