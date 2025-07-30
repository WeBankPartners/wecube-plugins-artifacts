# coding=utf-8
"""
同步差异化变量脚本
~~~~~~~~~~~~~~~~~~

用于同步部署物料包中的差异化变量，确保变量的子系统设计ID一致性

主要功能：
1. 初始化已处理变量集合A
2. 查询所有部署物料包
3. 处理每个物料包的差异化变量（跳过已处理的变量）
4. 对于非公有变量，检查和修正子系统设计ID
5. 更新物料包和差异化变量
6. 清理无效的差异化变量记录
"""

import logging
import sys
import os
import json
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置配置文件环境变量
# os.environ.setdefault('ARTIFACTS_COREPY_CONF', os.path.join(os.path.dirname(__file__), 'etc/artifacts_corepy.conf'))
# os.environ.setdefault('ARTIFACTS_COREPY_CONF_DIR', os.path.join(os.path.dirname(__file__), 'etc/artifacts_corepy.conf.d'))

from talos.server import base as talos_base
from artifacts_corepy.server import base as artifacts_base

# 初始化服务器配置系统
try:
  # 使用与wsgi_server.py相同的初始化方式
  application = talos_base.initialize_server(
      'artifacts_corepy',
      os.environ.get('ARTIFACTS_COREPY_CONF', '/etc/artifacts_corepy/artifacts_corepy.conf'),  # 在机器中使用
      # os.environ.get('ARTIFACTS_COREPY_CONF', './etc/artifacts_corepy.conf'),   # 在本地测试使用
      conf_dir=os.environ.get('ARTIFACTS_COREPY_CONF_DIR', '/etc/artifacts_corepy/artifacts_corepy.conf.d'),
      middlewares=[]  # 独立脚本不需要中间件
  )
  print("Talos配置系统初始化成功")
except Exception as e:
  print(f"Talos配置系统初始化失败: {e}")
  sys.exit(1)


from artifacts_corepy.common import wecmdbv2 as wecmdb
from artifacts_corepy.common import wecube
from talos.core import config
from talos.core.i18n import _

LOG = logging.getLogger(__name__)
CONF = config.CONF

# 全局变量类型常量
GLOBAL_VARIABLE_TYPE = 'GLOBAL'


class DiffVariableSynchronizer:
    """差异化变量同步器"""
    
    def __init__(self):
        """
        初始化同步器
        
        Args:
            server: WeCMDB服务器地址
            token: 认证令牌
        """
        self.server = CONF.wecube.server

        wecube_client = wecube.WeCubeClient(self.server, "")
        self.token = wecube_client.login_subsystem()
        self.cmdb_client = wecmdb.WeCMDBClient(self.server, self.token)
        
        # 初始化已处理变量集合A
        self.processed_variables = set()
        
        # 统计信息
        self.stats = {
            'total_packages': 0,
            'processed_packages': 0,
            'updated_packages': 0,
            'created_variables': 0,
            'deleted_variables': 0,
            'skipped_variables': 0,  # 新增：跳过的变量数量
            'global_variables': 0,   # 新增：公有变量数量
            'errors': 0
        }
    
    def run(self):
        """
        执行同步流程
        """
        LOG.info("开始同步差异化变量...")
        
        try:
            # 1. 初始化已处理变量集合A
            LOG.info("初始化已处理变量集合A")
            
            # 2. 查询所有部署物料包
            packages = self._get_all_deploy_packages()
            self.stats['total_packages'] = len(packages)
            LOG.info(f"共找到 {len(packages)} 个部署物料包")
            # 3. 处理每个物料包
            for package in packages:
                try:
                    self._process_package(package)
                    self.stats['processed_packages'] += 1
                except Exception as e:
                    LOG.error(f"处理物料包 {package.get('guid', 'unknown')} 时出错: {str(e)}")
                    self.stats['errors'] += 1
                    continue
            
            # 4. 清理无效的差异化变量
            self._cleanup_invalid_variables()
            
            # 5. 输出统计信息
            self._print_statistics()
            
        except Exception as e:
            LOG.error(f"同步过程中发生严重错误: {str(e)}")
            raise
        
        LOG.info("差异化变量同步完成")
    
    def _get_all_deploy_packages(self):
        """
        查询所有部署物料包
        
        Returns:
            list: 部署物料包列表
        """
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [],
            "paging": False
        }
        resp_json = self.cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.deploy_package, query)
        if not resp_json.get('data', {}).get('contents'):
            LOG.warning("未找到任何部署物料包")
            return []
        
        return resp_json['data']['contents']
    
    def _get_unit_design_by_id(self, unit_design_id: str):
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "guid",
                "operator": "eq",
                "value": unit_design_id
            }],
            "paging": False
        }
        resp_json = self.cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.unit_design, query)
        if not resp_json.get('data', {}).get('contents', []):
            LOG.warning("未找到unit_design")
            return []
        return resp_json['data']['contents'][0]
    def _process_package(self, package):
        """
        处理单个物料包的差异化变量
        
        Args:
            package: 物料包数据
        """
        package_guid = package.get('guid')
        package_name = package.get('name', 'unknown')
        LOG.info(f"处理物料包: {package_name} ({package_guid})")
        
        # 获取物料包的子系统设计id
        unit_design_info = package.get('unit_design', {})
        if not unit_design_info:
            LOG.warning(f"物料包 {package_name} 没有关联的单元设计，跳过处理")
            return
        unit_design = self._get_unit_design_by_id(unit_design_info.get('guid', {}))
        subsystem_design = unit_design.get('subsystem_design', {})

        if not subsystem_design:
            LOG.warning(f"物料包 {package_name} 没有关联的子系统设计，跳过处理")
            return
        
        current_subsystem_id = subsystem_design.get('guid')
        if not current_subsystem_id:
            LOG.warning(f"物料包 {package_name} 的子系统设计ID为空，跳过处理")
            return
        
        # 处理差异化变量
        diff_conf_variables = package.get('diff_conf_variable', [])
        if not diff_conf_variables:
            LOG.info(f"物料包 {package_name} 没有差异化变量，跳过处理")
            return
        
        LOG.info(f"物料包 {package_name} 包含 {len(diff_conf_variables)} 个差异化变量")
        
        # 处理每个差异化变量
        updated_variables = []
        variable_updated = False
        
        for variable_ref in diff_conf_variables:
            variable_guid = variable_ref.get('guid')
            
            # 检查该GUID是否已在集合A中
            if variable_guid in self.processed_variables:
                LOG.debug(f"变量 {variable_guid} 已在公共变量集合A中，跳过处理")
                self.stats['skipped_variables'] += 1
                updated_variables.append(variable_guid)
                continue
            
            # 获取差异化变量详细信息
            variable_data = self._get_diff_variable(variable_guid)
            if not variable_data:
                LOG.warning(f"无法获取差异化变量 {variable_guid} 的详细信息，跳过")
                continue
            
            # 处理变量
            new_variable_ref = self._process_variable(
                variable_data, current_subsystem_id, package_name
            )
            
            if new_variable_ref.get('guid', '') != variable_ref.get('guid', ''):
                variable_updated = True
            updated_variables.append(new_variable_ref.get('guid', ''))
        
        # 如果有变量更新，则更新物料包
        if variable_updated:
            self._update_package_variables(package_guid, updated_variables)
            self.stats['updated_packages'] += 1
            LOG.info(f"已更新物料包 {package_name} 的差异化变量")
        else:
            LOG.info(f"物料包 {package_name} 的差异化变量无需更新")
    
    def _get_diff_variable(self, variable_guid):
        """
        获取差异化变量详细信息
        
        Args:
            variable_guid: 变量GUID
            
        Returns:
            dict: 变量数据，如果不存在返回None
        """
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "guid",
                "operator": "eq",
                "value": variable_guid
            }],
            "paging": False
        }
        
        try:
            resp_json = self.cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.diff_config, query)
            
            if resp_json.get('data', {}).get('contents'):
                return resp_json['data']['contents'][0]
            else:
                LOG.warning(f"差异化变量 {variable_guid} 不存在")
                return None
        except Exception as e:
            LOG.error(f"查询差异化变量 {variable_guid} 时出错: {str(e)}")
            return None
        
    def _get_diff_variable_by_code(self, code, subsystem_design_id):
        """
        基于code和子系统设计id获取差异化变量详细信息
        """
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [{
                "name": "code",
                "operator": "eq",
                "value": code
            }, {
                "name": "subsystem_design",
                "operator": "eq",
                "value": subsystem_design_id
            }],
            "paging": False
        }
        
        try:
            resp_json = self.cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.diff_config, query)
            
            if resp_json.get('data', {}).get('contents'):
                return resp_json['data']['contents'][0]
            else:
                LOG.warning(f"差异化变量不存在")
                return None
        except Exception as e:
            LOG.error(f"查询差异化变量时出错: {str(e)}")
            return None
    
    def _process_variable(self, variable_data, current_subsystem_id, package_name):
        """
        处理单个差异化变量
        
        Args:
            variable_data: 变量数据
            current_subsystem_id: 当前子系统设计ID
            package_name: 物料包名称（用于日志）
            
        Returns:
            dict: 变量引用（可能是新创建的）
        """
        variable_guid = variable_data.get('guid')
        variable_name = variable_data.get('variable_name', 'unknown')
        variable_type = variable_data.get('variable_type', '')
        code = variable_data.get('code', '')

        # 如果是公有变量，不做处理，但将GUID推入集合A
        if variable_type == GLOBAL_VARIABLE_TYPE:
            LOG.debug(f"变量 {variable_name} 是公有变量，无需处理")
            self.processed_variables.add(variable_guid)
            self.stats['global_variables'] += 1
            return {'guid': variable_guid}
        
        # 检查子系统设计ID
        variable_subsystem = variable_data.get('subsystem_design', {})
        variable_subsystem_id = variable_subsystem.get('guid') if variable_subsystem else None
        # 如果子系统设计ID一致，不做处理
        if variable_subsystem_id == current_subsystem_id:
            LOG.debug(f"变量 {variable_name} 的子系统设计ID已正确，无需处理")
            return {'guid': variable_guid}
        
        LOG.info(f"变量 {variable_name} 的子系统设计ID不一致 (当前: {variable_subsystem_id}, 目标: {current_subsystem_id})，创建新变量")
        
        presented_variable = self._get_diff_variable_by_code(code, current_subsystem_id)
        if (presented_variable):
            LOG.info(f"变量 {variable_name} 已存在，无需创建")
            return {'guid': presented_variable.get('guid')}
            
        # 创建新的差异化变量
        new_variable_data = self._create_new_variable(variable_data, current_subsystem_id)
        
        if new_variable_data:
            new_guid = new_variable_data.get('guid')
            LOG.info(f"为物料包 {package_name} 创建新的差异化变量: {variable_name} (新GUID: {new_guid})")
            self.stats['created_variables'] += 1
            return {'guid': new_guid}
        else:
            LOG.error(f"创建新的差异化变量失败，保持原变量引用")
            return {'guid': variable_guid}
    
    def _create_new_variable(self, original_data, new_subsystem_id):
        """
        基于原变量数据创建新的差异化变量
        
        Args:
            original_data: 原变量数据
            new_subsystem_id: 新的子系统设计ID
            
        Returns:
            dict: 新创建的变量数据，失败返回None
        """
        # 复制原变量数据
        new_data = original_data.copy()
        
        # 移除运行时字段
        fields_to_remove = [
            'guid', 'create_time', 'create_user', 'update_time', 'update_user', 'key_name'
        ]
        
        for field in fields_to_remove:
            new_data.pop(field, None)
        
        # 设置新的子系统设计ID
        new_data['subsystem_design'] = new_subsystem_id
        
        try:
            resp_json = self.cmdb_client.create(CONF.wecube.wecmdb.citypes.diff_config, [new_data])
            
            if resp_json.get('data') and len(resp_json['data']) > 0:
                return resp_json['data'][0]
            else:
                LOG.error(f"创建差异化变量失败: {resp_json}")
                return None
        except Exception as e:
            LOG.error(f"创建差异化变量时出错: {str(e)}")
            return None
    
    def _update_package_variables(self, package_guid, updated_variables):
        """
        更新物料包的差异化变量列表
        
        Args:
            package_guid: 物料包GUID
            updated_variables: 更新后的变量列表
        """
        
        update_data = {
            'guid': package_guid,
            'diff_conf_variable': json.dumps(updated_variables)
        }
        try:
            self.cmdb_client.update(
                CONF.wecube.wecmdb.citypes.deploy_package, 
                [update_data]
            )
            LOG.debug(f"已更新物料包 {package_guid} 的差异化变量列表")
        except Exception as e:
            LOG.error(f"更新物料包 {package_guid} 的差异化变量列表时出错: {str(e)}")
            raise
    
    def _cleanup_invalid_variables(self):
        """
        清理无效的差异化变量（非公有变量且子系统设计ID为null）
        """
        LOG.info("开始清理无效的差异化变量...")
        
        # 查询所有非公有变量且子系统设计ID为null的记录
        query = {
            "dialect": {
                "queryMode": "new"
            },
            "filters": [
              {
                  "name": "variable_type",
                  "operator": "ne",
                  "value": GLOBAL_VARIABLE_TYPE
              }
            ],
            "paging": False
        }
        
        try:
            resp_json = self.cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.diff_config, query)
            all_invalid_variables = resp_json.get('data', {}).get('contents', [])
            invalid_variables = [
                item for item in all_invalid_variables
                if 'Delete' in item.get('nextOperations', []) 
                and item.get('subsystem_design') is None
            ]
            
            if not invalid_variables:
                LOG.info("没有找到需要清理的无效差异化变量")
                return
            
            LOG.info(f"找到 {len(invalid_variables)} 个无效的差异化变量，准备删除")
            
            # 批量删除
            delete_data = [{'guid': var['guid']} for var in invalid_variables]
            
            self.cmdb_client.delete(CONF.wecube.wecmdb.citypes.diff_config, delete_data)
            self.cmdb_client.confirm(CONF.wecube.wecmdb.citypes.diff_config, delete_data)

            self.stats['deleted_variables'] = len(invalid_variables)
            LOG.info(f"已删除 {len(invalid_variables)} 个无效的差异化变量")
            
        except Exception as e:
            LOG.error(f"清理无效差异化变量时出错: {str(e)}")
    
    def _print_statistics(self):
        """
        打印统计信息
        """
        LOG.info("=" * 60)
        LOG.info("差异化变量同步统计信息:")
        LOG.info(f"  总物料包数量: {self.stats['total_packages']}")
        LOG.info(f"  已处理物料包: {self.stats['processed_packages']}")
        LOG.info(f"  已更新物料包: {self.stats['updated_packages']}")
        LOG.info(f"  创建新变量数: {self.stats['created_variables']}")
        LOG.info(f"  删除无效变量: {self.stats['deleted_variables']}")
        LOG.info(f"  跳过的变量数: {self.stats['skipped_variables']}")
        LOG.info(f"  公有变量数量: {self.stats['global_variables']}")
        LOG.info(f"  处理错误数量: {self.stats['errors']}")
        LOG.info(f"  集合A大小: {len(self.processed_variables)}")
        LOG.info("=" * 60)


def main():
    """
    主函数
    """
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('diff_variable_sync.log', encoding='utf-8')
        ]
    )
    
    try:
        # 创建同步器实例
        synchronizer = DiffVariableSynchronizer()
        
        # 执行同步
        synchronizer.run()
        
        LOG.info("同步完成，程序正常退出")
        return 0
        
    except Exception as e:
        LOG.error(f"程序执行失败: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())