from gluon.tools import Recaptcha2
if False:
    from gluon import *
    from db import *
    from custom import *
    from basic_custom import *
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T
    auth=current.auth

### captcha after failed login attempts
ip = request.env.remote_addr
num_login_attempts = cache.ram(ip, lambda: 0) or 0
if not (request.env.remote_addr.startswith('192.168') or request.env.remote_addr.startswith('127.0') or  request.env.remote_addr.startswith('10.8')):
    auth.settings.captcha = Recaptcha2(request,"6Lckt6MZAAAAAIuS2e2_TBBRIfBUCfGjAlAlCK5k","6Lckt6MZAAAAAHtuCdf-LyspuNkGngAKFKVPkXal") #v2 no soy un robot
def login_attempt(form):
    cache.ram.increment(ip)
auth.settings.login_onvalidation.append(login_attempt)

def login_success(form):
    cache.ram.clear(ip)

auth.settings.login_onaccept.append(login_success)
### ends captcha
