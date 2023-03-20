import environ

ENV = environ.Env()
PROJECT_ROOT = environ.Path(__file__)-3

env_paths = [
    PROJECT_ROOT.path('.env'),
    environ.Path('/etc/bs/bs.env'),
]

if ENV.str('BS_ENV', default='') != '':
    env_paths.insert(0, environ.Path(ENV.str('BS_ENV')))

for e in env_paths:
    try:
        e.file('')
        ENV.read_env(e())
    except FileNotFoundError:
        pass
