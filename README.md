# VMT for SUBS 
## CREATING DATASET 
#### 1. Downloading Youtube Playlist
- create 'dataset' directory for dataset 
```
mkdir dataset
cd dataset
```
- download videos / subtitles from youtube by using [youtube-dl](https://github.com/ytdl-org/youtube-dl)

```
youtube-dl --get-id [playlist link] -i >> list.txt
youtube-dl -a list.txt -o '%(id)s.%(ext)s' --rm-cache-dir --all-subs --ignore-errors 
```
- if youtube-dl is way too slow, try using [yt-dlp](https://github.com/yt-dlp/yt-dlp) for downloading videos

```
yt-dlp -a id_list.txt -o '%(id)s.%(ext)s' -S ext:mp4:m4a --ignore-errors 
# youtube-dl -a list.txt -o '%(id)s.%(ext)s' --rm-cache-dir --all-subs --skip-download --ignore-errors 
```
<br>

#### 2. Constructing Dataset
- download 'create_dataset.ipynb' file to the 'dataset' directory
- construct the text pair and video dataset by running the 'create_dataset.ipynb' file <br>
  then, the 'dataset' directory would be configured as following :
```
dataset
├── create_dataset.ipynb
├── videos 
│      ├── videoid_starttime_endtime.mp4
│      ├── videoid_starttime_endtime.mp4
│      └── .....  
│
├── video 1
├── video 2
├── ....
│
├── videoid.ko.vtt
├── videoid.en.vtt
├── ...
│
├── list.txt
└── sample.json
```
<br>
<br>

in progress...


