import requests, concurrent.futures as cf
requests.packages.urllib3.disable_warnings()
H="kicyber-2bccd62e5d76-granny-makes-food-0-0.chals.io"
URL=f"https://{H}/"
files="app.py app.py.bak app.py~ main.py run.py server.py wsgi.py views.py utils.py settings.py models.py config.py db.py database.py init.py __init__.py flask_app.py granny.py food.py index.py manage.py requirements.txt dockerfile Dockerfile Dockerfile.dockerignore .dockerignore .gitignore README.md flag.txt flag flag.phps flag.php source.txt source.py secret flag_source .flag .env env config.ini package.json gemfile Procfile venv activate python.env applications.py homepage.py views.py.tpl templates base.html index.html home.html login.html.js app.js main.js script.js config.js static.js granny.js item.js items.js sour.js pickle.js api.js bundle.js styles.css style.css main.css jsconfig.json tsconfig.json .htaccess htpasswd info.php test.py test.txt debug.log server.log access.log .log logs/log.txt pickle.py serializers.py serialization.py deserialize.py"
for f in files.split():
    paths=[f, "static/"+f, "src/"+f, "source/"+f, "app/"+f, "templates/"+f]
    def t(p):
        try:
            r=requests.get(URL+p, timeout=12, verify=False)
            if r.status_code!=404: return (p,r.status_code,len(r.content))
        except Exception as e: return (p,"ERR",str(e)[:40])
        return None
    outs=[]
    with cf.ThreadPoolExecutor(max_workers=24) as ex:
        for r in ex.map(t,paths):
            if r: outs.append(r)
    for o in outs: print(o)
print("SRCFUZZ DONE")
