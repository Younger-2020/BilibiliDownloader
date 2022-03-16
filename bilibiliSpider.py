# -*- encoding = utf-8 -*-
# @Time : 2022/3/16 10:34
# @Author : Youngerr
# @File : bilibiliSpider.py
# @Software : PyCharm

import requests
import re
import json
import subprocess
from os.path import abspath,exists
from os import mkdir

headers = {
    'referer':'https://search.bilibili.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36 Edg/97.0.1072.69'
}

targetPath=""

def getUrlByBv(bv):
    url = "https://www.bilibili.com/video/" + bv
    return url

# 向url获取请求，获取响应
def getResponse(url):
    global headers
    response = requests.get(url=url, headers=headers)
    return response


#获取下载信息
def getDownloadInfo(response):
    downloadInfo={}
    downloadInfo['EpisodeTitles']=[]
    state_json = json.loads(getInitState(response))
    downloadInfo['videoTitle']=state_json['videoData']['title']
    pages=state_json['videoData']['pages']
    for page in pages:
        pageName=page['part']
        downloadInfo['EpisodeTitles'].append(pageName)
    downloadInfo['hasEpisode']= False if len(pages)==1 else True
    return downloadInfo

#设置下载位置
def setTargetPath(path):
    global targetPath
    targetPath=path

# 获取视屏播放信息
def getPlayInfo(response):
    playInfo = re.findall("<script>window.__playinfo__=(.*?)</script>", response.text)[0]
    return playInfo


# 获取视屏地址和音频地址
def getVideoAndAudioUrl(playinfo):
    playinfo_json=json.loads(playinfo)
    return playinfo_json['data']['dash']['video'][0]['baseUrl'],playinfo_json['data']['dash']['audio'][0]['baseUrl']

# 保存视屏和音频
def save(title,videoUrls,audioUrls):
    global headers,targetPath
    with open(targetPath+"/"+title+"_tmp.mp4","wb") as videoFile:
        videoFile.write(requests.get(videoUrls,headers=headers).content)
    videoFile.close()
    with open(targetPath+"/"+title+"_tmp.mp3","wb") as audioFile:
        audioFile.write(requests.get(audioUrls,headers=headers).content)
    audioFile.close()

#利用FFmpeg合成音视频
def mergeData(title):
    fullTitle=abspath(targetPath)+"\\"+title
    merge=f'ffmpeg -i "{fullTitle}_tmp.mp4" -i "{fullTitle}_tmp.mp3" -c:v copy -c:a aac -strict experimental "{fullTitle}.mp4"'
    subprocess.run(merge,shell=True)
    print(title+"合并完成！")
    delete=f'del "{fullTitle}_tmp.mp4" "{fullTitle}_tmp.mp3"'
    subprocess.run(delete,shell=True)

#获取视频的INITIAL_STATE信息
def getInitState(response):
    initState = re.findall("<script>window.__INITIAL_STATE__=(.*?});.*?</script>", response.text)[0]
    return initState

#下载分p
def downloadVideo(url,response,selectedPages,downloadInfo):
    #如果无分p，下载单个视频
    if not downloadInfo['hasEpisode']:
        playinfo = getPlayInfo(response)
        videoUrls,audioUrls = getVideoAndAudioUrl(playinfo)
        save(downloadInfo['videoTitle'],videoUrls,audioUrls)
        mergeData(downloadInfo['videoTitle'])
    #否则创建新文件夹，将选择的视频下载至文件夹中
    else:
        setTargetPath(targetPath+'/'+downloadInfo['videoTitle'])
        if not exists(targetPath):
            mkdir(targetPath)
        for page in selectedPages:
            page_url=url+"?p="+str(page)
            page_response=getResponse(page_url)
            page_playinfo = getPlayInfo(page_response)
            page_videoUrls,page_audioUrls = getVideoAndAudioUrl(page_playinfo)
            save(downloadInfo['EpisodeTitles'][page-1],page_videoUrls,page_audioUrls)
            mergeData(downloadInfo['EpisodeTitles'][page-1])
    print("视频下载完成！")

#通过bv号直接下载视频
def downloadVideoByBv(bv,selectPages):
    url=getUrlByBv(bv)
    response=getResponse(url)
    downloadInfo = getDownloadInfo(response)
    downloadVideo(url,response,selectPages,downloadInfo)


#test
if __name__ == "__main__":
    targetPath="F:/biliVideo"
    downloadVideoByBv("BV1YA411T76k",[i for i in range(1,56)])
