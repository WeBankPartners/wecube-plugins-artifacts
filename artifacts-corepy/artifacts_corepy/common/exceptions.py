# coding=utf-8
"""
artifacts_corepy.common.exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

本模块提供项目定义异常

"""

from talos.core.i18n import _
from talos.core import exceptions as core_ex


class BatchPartialError(core_ex.Error):
    """批量数据操作异常"""
    code = 400

    @property
    def title(self):
        return _('Batch Operation Partial Error')

    @property
    def message_format(self):
        return _('Fail to %(action)s [%(num)s] record, detail error in the data block')


class PluginError(core_ex.Error):
    """系统间调用业务异常"""
    code = 400

    @property
    def title(self):
        return _('Plugin Business Processing Error')
