#!/bin/sh
LF=$(printf '\\\012_');LF=${LF%_}

/usr/bin/curl -s http://teideninfo.tepco.co.jp/html/00000000000.html  |
  # utf-8とし、停電情報のテーブルを抜き出す
  /usr/bin/iconv -f SJIS -t UTF8                                      | tee log.txt |
  /bin/sed -n '/<table.*"停電情報">/,/<\/table>/p'                    |
  # 都道府県と停電情報のみを抜き出す
  /bin/sed -n "/<tbody>/,/<\/tbody>/p"                                |
  /bin/grep -v "tbody>"                                               |
  # trタブを改行に変換
  /usr/bin/tr -d '\012'                                               |
  /bin/sed '$a\
'                                                                     |
  /bin/sed "s/<tr>/${LF}/g"                                           |
  /bin/sed "s/<\/tr>//g"                                              |
  # <td.*>を取る
  /bin/sed "s/<td[^>][^>]*>//g"                                       |
  /bin/sed "s/<\/td>//g"                                              |
  #
  /usr/bin/tee /tmp/href.txt                                          |
  /bin/sed "s/<a[^>][^>]*>//"                                         |
  /usr/bin/awk '
      BEGIN{
        exist = 0;
      }
      {
        if (NF > 0) {
          if ($1 != "&nbsp;" && $2 != "&nbsp;") {
            if ($2 !~ "-") {
              exist = 1;
              printf("%s %s\n", $1, $2);
            }
          }
        }
      }
      END {
        if (exist == 0) {
          printf("停電なし\n");
        }
      }'

for url in `cat /tmp/href.txt|/bin/sed 's/<a href="//'|/bin/sed 's/">.*//'`
do
  /usr/bin/curl -s http://teideninfo.tepco.co.jp/html/${url}  |
  # utf-8とし、停電情報のテーブルを抜き出す
  /usr/bin/iconv -f SJIS -t UTF8                              |
  /bin/sed -n '/<table.*"停電情報">/,/<\/table>/p'            |
  # 都道府県と停電情報のみを抜き出す
  /bin/sed -n "/<tbody>/,/<\/tbody>/p"                        |
  /bin/grep -v "tbody>"                                       |
  # trタブを改行に変換
  /usr/bin/tr -d '\012'                                       |
  /bin/sed '$a\
'                                                             |
  /bin/sed "s/<tr>/${LF}/g"                                   |
  /bin/sed "s/<\/tr>//g"                                      |
  # <td.*>を取る
  /bin/sed "s/<td[^>][^>]*>//g"                               |
  /bin/sed "s/<a.*\/a>//"                                     |
  /bin/sed "s/<\/td>//g"                                      |
  /usr/bin/awk '
      BEGIN{
        exist = 0;
      }
      {
        if (NF > 0) {
          if ($1 != "&nbsp;" && $2 != "&nbsp;") {
            if ($2 !~ "-") {
              exist = 1;
              printf("%s [%s]\n", $1, $2);
            }
          }
          if ($3 != "&nbsp;" && $4 != "&nbsp;") {
            if ($4 !~ "-") {
              exist = 1;
              printf("%s [%s]\n", $3, $4);
            }
          }
        }
      }
      END {
        if (exist == 0) {
          printf("停電なし\n");
        }
      }'
done
