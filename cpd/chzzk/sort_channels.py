import requests
import json
import os
import heapq    


def partition_channels(channels, k=10):
    """
    channels: 각 채널 정보를 담은 리스트 (각 항목은 dict로 channelName, channelId, followerCount 포함)
    k: 분배할 그룹(파일) 개수
    """
    # 팔로워 수 기준 내림차순 정렬
    sorted_channels = sorted(channels, key=lambda x: x.get("followerCount", 0), reverse=True)
    
    # 각 그룹을 (현재 총 팔로워 수, 그룹 번호, 채널 리스트) 형태의 튜플로 생성
    bins = [(0, i, []) for i in range(k)]
    heapq.heapify(bins)

    # 각 채널을 팔로워 수가 가장 적은 그룹에 할당 (팔로워 수 5000 미만인 채널은 제외)
    for channel in sorted_channels:
        if channel.get("followerCount", 0) < 5000:
            continue
        current_sum, idx, bin_channels = heapq.heappop(bins)
        new_sum = current_sum + channel.get("followerCount", 0)
        bin_channels.append(channel)
        heapq.heappush(bins, (new_sum, idx, bin_channels))

    # 그룹 번호 순서대로 정렬
    bins_sorted = sorted(bins, key=lambda x: x[1])
    return bins_sorted
   


        
    
    
if __name__ == '__main__':
    # channels.json 파일로부터 채널 데이터를 읽기
    with open("channels/channels.json", "r", encoding="utf-8") as f:
        channels = json.load(f)
    
    # 전체 시청자 수 계산
    total_viewers = sum(channel.get("concurrentUserCount", 0)
                        for channel in channels)
    print(f"전체 라이브 시청자 수: {total_viewers}")
    
    # 팔로우 정보 추가
    with open("channels/all_channels.json", "r", encoding="utf-8") as f:
        all_channels = json.load(f)
    
    

    # 10개 그룹으로 분배
    bins = partition_channels(all_channels, k=10)

    # 각 그룹을 별도의 JSON 파일로 저장 및 그룹별 시청자 수 출력
    for current_sum, idx, bin_channels in bins:
        file_name = f"channels/channel_list_{idx+1:02}.json"
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(bin_channels, f, ensure_ascii=False, indent=4)
        print(
        f"{file_name:<26}: {current_sum:>10,} 팔로워 | 총 {len(bin_channels):>3} 채널 | 대표채널 : "
        f"{bin_channels[0].get('channelName', ''):<15} {bin_channels[0].get('followerCount', 0):>6,} 팔로워"
        )

