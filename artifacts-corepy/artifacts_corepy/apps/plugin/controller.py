# coding=utf-8
'''
plugin api input/output standard

input data:
{
    "requestId": "request-001",  //仅异步调用需要用到
    "operator": "admin",  //操作人
    "inputs": [
        {"callbackParameter": "", "xml define prop": xxx},
        {},
        {}
    ]
}

output data:
{
    "resultCode": "0",  //调用插件结果，"0"代表调用成功，"1"代表调用失败
    "resultMessage": "success",  //调用结果信息，一般用于调用失败时返回失败信息
    "results": {
        "outputs": [
            {"callbackParameter": "", "errorCode": "0", "errorMessage": "", "xml define prop": xxx},
            {},
            {}
        ]
    }
}
'''

from __future__ import absolute_import

import falcon
from talos.db import crud
from talos.common import controller
from talos.db import validator
from talos.db import converter

from artifacts_corepy.apps.plugin import api as plugin_api


class PackageFromImage(controller.Controller):
    allow_methods = ('POST', )
    param_rules = [
        crud.ColumnValidator(field='requestId',
                             rule=validator.LengthValidator(0, 255),
                             validate_on=['check:O'],
                             nullable=True),
        crud.ColumnValidator(field='operator',
                             rule=validator.LengthValidator(0, 255),
                             validate_on=['check:O'],
                             nullable=True),
        crud.ColumnValidator(field='inputs',
                             rule=validator.TypeValidator(list),
                             validate_on=['check:M'],
                             nullable=False),
    ]
    input_rules = [
        crud.ColumnValidator(field='callbackParameter',
                             rule=validator.LengthValidator(0, 255),
                             validate_on=['check:O'],
                             nullable=True),
        crud.ColumnValidator(field='unit_design',
                             rule=validator.LengthValidator(1, 255),
                             validate_on=['check:M'],
                             nullable=False),
        crud.ColumnValidator(field='image_name',
                             rule=validator.LengthValidator(1, 255),
                             validate_on=['check:M'],
                             nullable=False),
        crud.ColumnValidator(field='tag',
                             rule=validator.LengthValidator(1, 255),
                             validate_on=['check:M'],
                             nullable=False),
        crud.ColumnValidator(field='md5',
                             rule=validator.LengthValidator(0, 255),
                             validate_on=['check:O'],
                             nullable=True),
        crud.ColumnValidator(field='nexus_url',
                             rule=validator.LengthValidator(0, 255),
                             validate_on=['check:O'],
                             nullable=True),
        crud.ColumnValidator(field='connector_port',
                             rule=validator.LengthValidator(0, 255),
                             validate_on=['check:O'],
                             nullable=True),
        crud.ColumnValidator(field='baseline_package',
                             rule=validator.LengthValidator(0, 255),
                             validate_on=['check:O'],
                             nullable=True),
    ]

    def on_post(self, req, resp, **kwargs):
        self._validate_method(req)
        self._validate_data(req)
        resp.json = self.create(req, req.json, **kwargs)
        resp.status = falcon.HTTP_200

    def create(self, req, data):
        result = {'resultCode': '0', 'resultMessage': 'success', 'results': {'outputs': []}}
        try:
            clean_data = crud.ColumnValidator.get_clean_data(self.param_rules, data, 'check')
            operator = clean_data.get('operator', None) or 'N/A'
            for item in clean_data['inputs']:
                single_result = {
                    'callbackParameter': item.get('callbackParameter', None),
                    'errorCode': '0',
                    'errorMessage': 'success',
                    'guid': None,
                    'deploy_package_url': None
                }
                try:
                    clean_item = crud.ColumnValidator.get_clean_data(self.input_rules, item, 'check')
                    package = plugin_api.Package().create_from_image_name(clean_item['image_name'], clean_item['tag'],
                                                                          clean_item.get('md5', None),
                                                                          clean_item.get('nexus_url', None),
                                                                          clean_item.get('connector_port', None),
                                                                          clean_item['unit_design'],
                                                                          clean_item.get('baseline_package',
                                                                                         None), operator)
                    single_result.update(package)
                    result['results']['outputs'].append(single_result)
                except Exception as e:
                    single_result['errorCode'] = '1'
                    single_result['resultMessage'] = str(e)
                    result['results']['outputs'].append(single_result)
        except Exception as e:
            result['resultCode'] = '1'
            result['resultMessage'] = str(e)
        return result
