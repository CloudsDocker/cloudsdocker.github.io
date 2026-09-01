本机没装 google-auth-oauthlib(前面 import 失败了),所以下面是基于 poetry.lock 里锁定的 1.1.0 的源码结构讲的。有一处我标了"需要确认",给了验证命令。

一行代码,四层调用栈

auth_url, _ = self.authorization_url()
这行看着像个 getter,实际穿了四个库:


google_auth_oauthlib.flow.Flow.authorization_url()
  └─ requests_oauthlib.OAuth2Session.authorization_url()
       └─ oauthlib.oauth2.WebApplicationClient.prepare_request_uri()
            └─ oauthlib.common.generate_token()
第一层:Flow.authorization_url()

def authorization_url(self, **kwargs):
    kwargs.setdefault("access_type", "offline")
    if self.autogenerate_code_verifier:
        chars = ascii_letters + digits + "-._~"
        rnd = SystemRandom()
        random_verifier = [rnd.choice(chars) for _ in range(0, 128)]
        self.code_verifier = "".join(random_verifier)

    if self.code_verifier:
        code_hash = hashlib.sha256()
        code_hash.update(str.encode(self.code_verifier))
        unencoded_challenge = code_hash.digest()
        b64_challenge = urlsafe_b64encode(unencoded_challenge)
        code_challenge = b64_challenge.decode().split("=")[0]
        kwargs["code_challenge"] = code_challenge
        kwargs["code_challenge_method"] = "S256"

    url, state = self.oauth2session.authorization_url(
        self.client_config["auth_uri"], **kwargs
    )
    return url, state
三件事,每件都有副作用。

access_type="offline" — 决定了你有没有 refresh token
这是 Google 的私有扩展,不在 RFC 6749 里。offline 才会在 token 响应里带 refresh_token。

直接关系到 get_sheets_conn 那个分支能不能走通:


if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
没有 offline,refresh_token 就是 None,每小时 access token 过期后都要重新弹浏览器。

这里有个 Google 特有的坑: refresh_token 只在首次授权时下发。同一个 client_id + 同一个账号第二次走完流程,Google 默认不再返回 refresh_token。所以如果谁手贱删了 storage.json 但没在 Google 账号里撤销授权,重新授权拿到的 JSON 里可能就没有 refresh_token 字段了 —— 之后每次都要交互。

要强制重发得显式传 prompt="consent"。这份代码没传,靠的是 storage.json 一直在。

PKCE 分支 — ⚠️ 这里需要你确认
autogenerate_code_verifier 的默认值在 1.x 里改过,我不能凭记忆断言 1.1.0 是 True 还是 False。在他们的 venv 里跑一下:


python -c "import inspect, google_auth_oauthlib.flow as f; print(inspect.signature(f.Flow.from_client_config))"
python -c "import inspect, google_auth_oauthlib.flow as f; print(inspect.getsource(f.Flow.authorization_url))"
如果开了,URL 里会多出 code_challenge + code_challenge_method=S256。

为什么 native app 需要 PKCE: client_secret 在 desktop client 里根本不是秘密——它躺在每个人的 drive_client_id.json 里。所以"谁持有 secret 谁就是合法客户端"这个假设在这里是破的。PKCE 用一个每次随机生成的 128 字符 code_verifier 补上:攻击者就算截获了 authorization code,没有 verifier 也换不到 token。

注意那个 .split("=")[0] —— 手动剥掉 base64 padding,因为 RFC 7636 要求 base64url 无 padding。

第二层:OAuth2Session.authorization_url() —— state 在这里落地

def authorization_url(self, url, state=None, **kwargs):
    state = state or self.new_state()
    return (
        self._client.prepare_request_uri(
            url, redirect_uri=self.redirect_uri,
            scope=self.scope, state=state, **kwargs
        ),
        state,
    )

def new_state(self):
    try:
        self._state = self.state()      # state 默认是 generate_token 这个 callable
    except TypeError:
        self._state = self.state        # 传进来的是字符串就直接复用
    return self._state
关键在 self._state = ... 这个赋值。 所谓"stores it on the session",存的位置就是 OAuth2Session 实例上的一个普通属性。不是 cookie,不是 server session,就是进程内存里的一个字符串。

对 loopback CLI 来说这是合理的:进程活着的时候值在,进程死了流程也就废了。

第三层:generate_token() —— 熵有多少

def generate_token(length=30, chars=UNICODE_ASCII_CHARACTER_SET):
    rand = random.SystemRandom()
    return "".join(rand.choice(chars) for _ in range(length))
SystemRandom → /dev/urandom(Windows 上是 CryptGenRandom),CSPRNG,不是 Mersenne Twister。这点很重要,random.choice 直接用是可预测的。
UNICODE_ASCII_CHARACTER_SET = 大小写字母 + 数字 = 62 个字符
30 位 → log₂(62) × 30 ≈ 178 bit 熵
我上一条回复里说"猜中概率约等于扔砖头砸中悉尼歌剧院那片瓦"——那个类比其实严重低估了。178 bit 大概是 2×10⁵³,比可观测宇宙里的恒星数量还多十几个数量级。

校验端:MismatchingStateError 从哪抛出来的
fetch_token 里:


if not code and authorization_response:
    self._client.parse_request_uri_response(authorization_response, state=self._state)
    code = self._client.code
一路走到 oauthlib/oauth2/rfc6749/parameters.py:


def parse_authorization_code_response(uri, state=None):
    if not is_secure_transport(uri):
        raise InsecureTransportError()
    query = urlparse.urlparse(uri).query
    params = dict(urlparse.parse_qsl(query))
    if state and params.get("state", None) != state:
        raise MismatchingStateError()
两个细节值得记:

1. if state and ... —— 短路。 self._state 是 None 或空串的话,整个校验被跳过,不报错。这是 oauthlib 的设计,不是 bug,但意味着"没报 state 错"不等于"state 校验通过了"。

2. is_secure_transport(uri) 就是 run_local_server 里那个 .replace("http", "https") 存在的原因——oauthlib 硬性拒绝明文 URI,库自己把 scheme 字符串改掉绕过去。另一条路是设 OAUTHLIB_INSECURE_TRANSPORT=1。

几个 staff 级别的观察
① 那个 _ 丢掉的返回值不是冗余,是重复

state 已经被写进 self.oauth2session._state 了,返回值只是方便调用方自己存一份(比如 web app 要塞进 cookie)。CLI 场景不需要,所以丢掉是对的。

② 但这个设计有个真实的坑:authorization_url() 不是幂等的

每调一次就覆盖 _state(还有 code_verifier)。所以:


url1, _ = flow.authorization_url()   # state = A
url2, _ = flow.authorization_url()   # state = B,A 被冲掉了
# 此时用 url1 完成授权 → MismatchingStateError
同一个 Flow 对象不能复用于两次授权。 这正好解释了你同事那个报错的一类成因——不是"卡"了,是回调对应的 flow 实例已经不是当前这个了。

③ state 在 URL 里,所以它会进浏览器历史

http://localhost:8081/?code=...&state=... 完整落在 history 里。这就是为什么"从历史记录里点开旧链接"必然触发 MismatchingStateError——旧 state 遇上新进程。

也顺带说明:state 防的是 CSRF,不是窃听。 它不需要保密,只需要不可预测且一次性。

④ scope 变更会被 oauthlib 拦下来

SCOPES 常量改了以后,拿旧 storage.json 去刷新会撞 Warning: Scope has changed from ... to ...,默认直接抛异常。改 scope 必须删 token 重新授权——这是升级这份工具时的一个隐藏 breaking change。

回到你同事的问题
从这条调用链能得出一个明确的排除法结论:

authorization_url() 是纯本地计算——生成随机数、拼 URL、写实例属性。没有任何网络 I/O。

所以"浏览器一直转圈"这个现象,state 这条线上的任何东西都不可能是原因。真正阻塞的是下游的 local_server.handle_request(),而它阻塞说明回调根本没到达。

能到达但校验失败 → MismatchingStateError(快速失败)。
到达不了 → 无限挂起。

这两个是互斥的症状。他现在是第二种,所以查网络可达性,别再查凭证了。