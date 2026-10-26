IP=143.244.222.116
names="admin admin0 admin-0 internal internal0 login portal dashboard flag granny granny-0 food app api web backend auth service admin-portal granny-portal granny-makes-food granny-makes-food-0-0-web 0-0 kicyber-2bccd62e5d76 kicyber-2bccd62e5d76-granny-makes-food-0-0-admin"
for n in $names; do
  body=$(curl -sk --max-time 8 --resolve "$n:443:$IP" -o /dev/null -w "%{http_code}" "https://$n/" 2>&1)
  echo "$n:443 -> $body"
done
