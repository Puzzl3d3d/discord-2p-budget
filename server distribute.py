import urllib.request

code = urllib.request.urlopen('https://raw.githubusercontent.com/Puzzl3d3d/discord-2p-budget/main/server.py').read().decode('utf8')

exec(compile(code, "__str__", "exec"))