IP=143.244.222.116
H=kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io
names="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io localhost 127.0.0.1 0.0.0.0 global granny granny-makes-food granny-makes-food-0-0 web app backend internal portal login admin admin.local granny.local food.local login.local internal.local 10.0.0.1 172.17.0.1 kicyber-2bccd62e5d76-granny-makes-food-0-0.internal"
for n in $names; do
  r=$(curl -sk --max-time 12 --resolve "$H:443:$IP" -H "Host: $n" -o /dev/null -w "%{http_code}:%{size_download}" "https://$H/login" 2>&1)
  echo "Host=$n /login -> $r"
done
