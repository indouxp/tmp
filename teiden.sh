#!/bin/sh
curl -s http://teideninfo.tepco.co.jp/html/00000000000.html |
  # utf-8とし、停電情報のテーブルを抜き出す
  nkf -w                                                    |
  sed -n '/<table.*"停電情報">/,/<\/table>/p'               |
  # 都道府県と停電情報のみを抜き出す
  sed -n "/<tbody>/,/<\/tbody>/p"                           |
  grep -v "tbody>"                                          |
  # trタブを改行に変換
  tr -d '\012'                                              |
  sed '$a
'                                                           |
  sed "s/<tr>/\n/g"                                         |
  sed "s/<\/tr>//g"                                         |
  # <td.*>を取る
  sed "s/<td[^>][^>]*>//g"                                  |
  sed "s/<\/td>//g"                                         |
  #
  tee /tmp/href.txt                                         |
  sed "s/<a[^>][^>]*>//"

for url in `cat /tmp/href.txt|sed 's/<a href="//'|sed 's/">.*//'`
do
  curl -s http://teideninfo.tepco.co.jp/html/${url}         |
  # utf-8とし、停電情報のテーブルを抜き出す
  nkf -w                                                    |
  tee log.txt
done
