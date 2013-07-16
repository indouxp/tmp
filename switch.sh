#!/bin/sh
if grep "\/usr\/bin\/grep" teiden.sh 2>/dev/null
then
sed "s/\/usr\/bin\/sed/\/bin\/sed/g;s/\/usr\/bin\/grep/\/bin\/grep/g" teiden.sh > swap.sh
else
sed "s/\/bin\/sed/\/usr\/bin\/sed/g;s/\/bin\/grep/\/usr\/bin\/grep/g" teiden.sh > swap.sh
fi

mv teiden.sh teiden.sh.org
mv swap.sh teiden.sh
chmod a+x teiden.sh
