#!/bin/sh
LF=$(printf '\\\012_');LF=${LF%_}
curl -s http://teideninfo.tepco.co.jp/html/00000000000.html |
  # utf-8とし、停電情報のテーブルを抜き出す
  nkf -w                                                    |
  sed -n '/<table.*"停電情報">/,/<\/table>/p'               |
  # 都道府県と停電情報のみを抜き出す
  sed -n "/<tbody>/,/<\/tbody>/p"                           |
  grep -v "tbody>"                                          |
  # trタブを改行に変換
  tr -d '\012'                                              |
  sed '$a\
'                                                           |
  sed "s/<tr>/${LF}/g"                                      |
  sed "s/<\/tr>//g"                                         |
  # <td.*>を取る
  sed "s/<td[^>][^>]*>//g"                                  |
  sed "s/<\/td>//g"                                         |
  #
  tee /tmp/href.txt                                         |
  sed "s/<a[^>][^>]*>//"                                    |
  awk '
      {
        if (NF > 0) {
          if ($1 != "&nbsp;" && $2 != "&nbsp;") {
            printf("%s %s\n", $1, $2);
          }
        }
      }'

for url in `cat /tmp/href.txt|sed 's/<a href="//'|sed 's/">.*//'`
do
  curl -s http://teideninfo.tepco.co.jp/html/${url}         |
  # utf-8とし、停電情報のテーブルを抜き出す
  nkf -w                                                    |
  sed -n '/<table.*"停電情報">/,/<\/table>/p'               |
  # 都道府県と停電情報のみを抜き出す
  sed -n "/<tbody>/,/<\/tbody>/p"                           |
  grep -v "tbody>"                                          |
  # trタブを改行に変換
  tr -d '\012'                                              |
  sed '$a\
'                                                           |
  sed "s/<tr>/${LF}/g"                                      |
  sed "s/<\/tr>//g"                                         |
  # <td.*>を取る
  sed "s/<td[^>][^>]*>//g"                                  |
  sed "s/<a.*\/a>//"                                        |
  sed "s/<\/td>//g"                                         | tee log.txt |
  awk '
      {
        if (NF > 0) {
          if ($1 != "&nbsp;" && $2 != "&nbsp;") {
            printf("%s %s\n", $1, $2);
          }
          if ($3 != "&nbsp;" && $4 != "&nbsp;") {
            printf("%s %s\n", $3, $4);
          }
        }
      }'
done
