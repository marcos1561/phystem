cd datas/explore_p0_2000

for i in {0..14}
do
    mkdir "$i"
    scp -r "lovelace:user/p0/datas/explore_p0/$i/cr" "./$i/"
done