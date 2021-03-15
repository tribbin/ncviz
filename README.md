NetCDF visualization

March 15th 2021: https://youtu.be/87d0f3G6sgg

March 13th 2021: https://youtu.be/DT3U-GodaEs

March  2nd 2021: https://youtu.be/CLipkVb85ug

March  1st 2021: https://youtu.be/R5UTACnt9MY

$ (for i in {0..365}; do echo "`printf "%0,6f\n" $(bc -q <<< scale=2;$i*24/30)` [enter] drawtext reinit 'fontfile=FreeSerif.ttf:text=`faketime -f '2020-1-1 00:00:00' date -d "+$i day" +'%-d %B'`';"; done) > text2
$ ffmpeg -r 60 -i output/wind_%5d.png -r 60 -filter_complex "sendcmd=filename=./dates.txt,drawtext=text='':fontsize=64:fontcolor=white:x=1700:y=60" -i ~/Downloads/Exhale\ -\ Jeremy\ Blake.mp3 -b:v 68M -c:a copy -bf 2 test.mp4
