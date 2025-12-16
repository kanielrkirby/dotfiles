from qutebrowser.api import interceptor
from qutebrowser.qt.core import QUrl

config.load_autoconfig()

# Session management - restore tabs on startup
config.set("auto_save.session", True)

config.set("completion.web_history.max_items", 0)
config.set("completion.cmd_history_max_items", 0)
# config.set("content.private_browsing", True)
config.set("content.webgl", False, "*")
config.set("content.canvas_reading", False)
config.set("content.geolocation", False)
config.set("content.webrtc_ip_handling_policy", "default-public-interface-only")

# Adblock settings
config.set("content.blocking.method", "both")  # Use both hosts file and adblock
config.set(
    "content.blocking.adblock.lists",
    [
        "https://easylist.to/easylist/easylist.txt",
        "https://easylist.to/easylist/easyprivacy.txt",
        "https://secure.fanboy.co.nz/fanboy-annoyance.txt",
    ],
)

# =========

# Open video in mpv (with SponsorBlock support)
config.bind(",m", "hint links spawn mpv {hint-url}")
config.bind(",M", "spawn mpv {url}")

# =========

config.bind("<Alt-Shift-!>", "tab-move 1")
config.bind("<Alt-Shift-@>", "tab-move 2")
config.bind("<Alt-Shift-#>", "tab-move 3")
config.bind("<Alt-Shift-$>", "tab-move 4")
config.bind("<Alt-Shift-%>", "tab-move 5")
config.bind("<Alt-Shift-^>", "tab-move 6")
config.bind("<Alt-Shift-&>", "tab-move 7")
config.bind("<Alt-Shift-*>", "tab-move 8")
config.bind("<Alt-Shift-(>", "tab-move 9")

# =========


redirects = {
    "airtite.local": "http://airtite.local:7269",
    "gap.local": "http://gap.local:7369",
    "turner.local": "http://turner.local:7469",
    "dms.local": "http://dms.local:7569",
}


def redirect_handler(info: interceptor.Request):
    url = info.request_url
    host = url.host()

    if host in redirects:
        target_url = QUrl(redirects[host])
        expected_port = target_url.port()

        if url.port() != expected_port:
            new_url_str = redirects[host] + url.path()
            if url.query():
                new_url_str += "?" + url.query()
            info.redirect(QUrl(new_url_str))


interceptor.register(redirect_handler)
