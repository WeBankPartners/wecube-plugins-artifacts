# coding=utf-8
"""
artifacts_corepy.server.simple_server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

本模块提供开发测试用的简单服务启动能力

"""

from wsgiref.simple_server import make_server

from talos.core import config
from artifacts_corepy.server.wsgi_server import application


CONF = config.CONF
HAS_BOOSTER = False
try:
    from gevent.pywsgi import WSGIServer
    HAS_BOOSTER = True
except ImportError as e:
    pass


def main():
    """
    主函数，启动一个基于wsgiref的测试/开发用途的wsgi服务器

    绑定地址由配置文件提供， 监听端口由配置文件提供
    """
    bind_addr = CONF.server.bind
    port = CONF.server.port
    if HAS_BOOSTER:
        print("Serving on %s:%d...[boost by gevent]" % (bind_addr, port))
        httpd = WSGIServer((bind_addr, port), application)
    else:
        print("try 'pip install gevent' to boost simple server" )
        print("Serving on %s:%d..." % (bind_addr, port))
        httpd = make_server(bind_addr, port, application)
    httpd.serve_forever()


if __name__ == '__main__':
    main()
