#!/bin/sh


cp  ../../rcv/rmf_20200804_001334_00.rmf ../../run
ls -l ../../run/rmf_20200804_001334_00.rmf

rm ../../rslt/rmf_20200804_001334_00.done

CMD="python3 ./smtp_file2.py ../../run/rmf_20200804_001334_00.rmf"
$CMD
RC=$?
if [ "${RC:?}" -ne "0" ]; then
  echo "$CMD fail." 1>&2
fi

cp  ../../rcv/slf_20200804_1.slf ../../run
ls -l ../../run/slf_20200804_1.slf

rm ../../rslt/slf_20200804_1.done

CMD="python3 ./smtp_file2.py ../../run/slf_20200804_1.slf"
$CMD
RC=$?
if [ "${RC:?}" -ne "0" ]; then
  echo "$CMD fail." 1>&2
fi
