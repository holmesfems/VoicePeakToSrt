from __future__ import annotations
import wave
import glob
import textwrap
from datetime import timedelta
import re
from os import path
from typing import List,Dict

#一部のコードはこちらのサイトから転用しました
#https://qiita.com/guneco/items/a5a9d59865062c7479d3

def get_txt_files(folder: str) -> list:
    return sorted(glob.glob(f'{folder}/*.txt'))

def get_wav_files(folder: str) -> list:
    return sorted(glob.glob(f'{folder}/*.wav'))

def get_text(txt_file: str) -> str:
    with open(txt_file, mode='r',encoding="utf-8") as f:
        text =  f.read()
    # 一行あたりの文字数が300あたりを超えるとPremiere Proがエラーを起こすので改行を挟む
    return textwrap.fill(text, 200)

def format_srttime(timedelta: timedelta) -> str:
    """timedeltaをSubRip形式の時間表示にフォーマットする"""
    ss, mi = divmod(timedelta.total_seconds(), 1)
    mi = int(round(mi, 3)*1000)
    mm, ss = divmod(ss, 60)
    hh, mm = divmod(mm, 60)
    srttime = f'{int(hh):02}:{int(mm):02}:{int(ss):02},{mi:03}'
    return srttime


def calc_playtime(wav_file: str) -> float:
    """waveファイルのフレームレートとフレーム数から再生時間を計算する"""
    with wave.open(wav_file, mode='rb') as wr:
        fr = wr.getframerate()
        fn = wr.getnframes()
        playtime = 1.0*fn/fr
        return playtime


#セリフ一つを格納するクラス
#name : キャラ名
#text : セリフ本体
#start: 開始秒数
#end  : 終了秒数
class ChrSingleTalk:
    def __init__(self,txtFile:str, wavFile:str, lastTalk:ChrSingleTalk):
        txtFile_regex = r"(\d+)\-([^\-]+)\-.+" #ファイル名からキャラ名情報を取得
        txtFileName = path.basename(txtFile)
        self.name = re.match(txtFile_regex,txtFileName).group(2)
        self.text = get_text(txtFile)
        playtime = calc_playtime(wavFile)
        playtime -= 0.008
        if(lastTalk is None):
            self.start = 0.0
            self.end = playtime
        else:
            self.start = lastTalk.end
            self.end = lastTalk.end + playtime
    
    #このセリフが対応しているSRTファイルの1ブロックを出力する関数
    def toSRTTextBlock(self,interval:float) -> str:
        startTime = format_srttime(timedelta(seconds=self.start))
        endTime = format_srttime(timedelta(seconds=self.end-interval))
        timeBlock = f'{startTime} --> {endTime}\n'
        return timeBlock + self.text + '\n\n'
    
    def __repr__(self):
        return f'{self.name}: {self.start} -> {self.end}\n{self.text}'

#セリフをキャラ別に管理するクラス
#chrTalkDict: キャラ名→キャラの全セリフ(list)
class ChrScriptInfo:
    def __init__(self,folder:str):
        txtFiles = get_txt_files(folder)
        wavFiles = get_wav_files(folder)
        lastChrTalk:ChrSingleTalk = None
        allChrTalk:List[ChrSingleTalk] = []
        for txt,wav in zip(txtFiles,wavFiles):
            chrTalk = ChrSingleTalk(txt,wav,lastChrTalk)
            allChrTalk.append(chrTalk)
            lastChrTalk = chrTalk
            print(chrTalk)

        chrTalkDict:Dict[str,List[ChrSingleTalk]] = {}
        for item in allChrTalk:
            if(chrTalkDict.get(item.name)):
                chrTalkDict[item.name].append(item)
            else:
                chrTalkDict[item.name] = [item]

        self.chrTalkDict = chrTalkDict

    #本クラスの情報を元に、SRTファイルをキャラ毎に作成&出力
    #interval: セリフ間の空白時間(秒)
    def toSrtFiles(self,folder:str='./',interval:float=0.3):
        for name,chrTalkList in self.chrTalkDict.items():
            with open(folder + name + ".srt","w",encoding="utf-8") as f:
                for index,chrTalk in enumerate(chrTalkList):
                    f.write(f'{index+1}\n') #writeは自動で改行しない、手動で改行を入れる
                    f.write(chrTalk.toSRTTextBlock(interval))

#ここにvoice&txtが入ったフォルダー名を入れる
ChrScriptInfo("voice").toSrtFiles()
