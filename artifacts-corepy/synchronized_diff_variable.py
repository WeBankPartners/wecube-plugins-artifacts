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
import copy

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from talos.server import base as talos_base
from artifacts_corepy.server import base as artifacts_base

# 初始化服务器配置系统
try:
  # 使用与wsgi_server.py相同的初始化方式
  application = talos_base.initialize_server(
      'artifacts_corepy',
      os.environ.get('ARTIFACTS_COREPY_CONF', '/etc/artifacts_corepy/artifacts_corepy.conf'),  # 在机器中使用
    #   os.environ.get('ARTIFACTS_COREPY_CONF', './etc/artifacts_corepy.conf'),   # 在本地测试使用
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
        self.batch_size = 500
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
            'errors': 0,
            'updated_0_confirmed': 0,
            'invalid_deleted': 0,
            'deleted_0_confirmed': 0,
            'failed_batches': 0
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
            # self._cleanup_invalid_variables()
            
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
        db_diff_conf_variables = package.get('db_diff_conf_variable', [])
        if not diff_conf_variables and not db_diff_conf_variables:
            LOG.info(f"物料包 {package_name} 没有差异化变量，跳过处理")
            return
        
        LOG.info(f"物料包 {package_name} 包含 {len(diff_conf_variables)} 个应用差异化变量，"
             f"{len(db_diff_conf_variables)} 个数据库差异化变量")

        # 处理应用差异化变量
        updated_app_variables = []
        app_variable_updated = False
        
        if diff_conf_variables:
            LOG.info(f"开始处理 {len(diff_conf_variables)} 个应用差异化变量")
            updated_app_variables, app_variable_updated = self._process_variable_list(
                diff_conf_variables, current_subsystem_id, package_name, "应用"
            )
        # 处理数据库差异化变量
        updated_db_variables = []
        db_variable_updated = False
        
        if db_diff_conf_variables:
            LOG.info(f"开始处理 {len(db_diff_conf_variables)} 个数据库差异化变量")
            updated_db_variables, db_variable_updated = self._process_variable_list(
                db_diff_conf_variables, current_subsystem_id, package_name, "数据库"
            )
        # 如果有变量更新，则更新物料包
        if app_variable_updated or db_variable_updated:
            self._update_package_variables(package_guid, updated_app_variables, updated_db_variables)
            self.stats['updated_packages'] += 1
            LOG.info(f"已更新物料包 {package_name} 的差异化变量")
        else:
            LOG.info(f"物料包 {package_name} 的差异化变量无需更新")

    def _process_variable_list(self, variable_list, current_subsystem_id, package_name, variable_type):
        """
        处理变量列表的通用方法
        Args:
            variable_list: 变量列表
            current_subsystem_id: 当前子系统ID
            package_name: 包名称（用于日志）
            variable_type: 变量类型（"应用"或"数据库"）
        
        Returns:
            tuple: (updated_variables, has_changes)
        """
        updated_variables = []
        has_changes = False
        
        for variable_ref in variable_list:
            variable_guid = variable_ref.get('guid')
            
            # 检查该GUID是否已在集合A中
            if variable_guid in self.processed_variables:
                LOG.debug(f"{variable_type}变量 {variable_guid} 已在公共变量集合A中，跳过处理")
                updated_variables.append(variable_ref)
                self.stats['skipped_variables'] += 1
                continue
            
            # 根据GUID获取变量详细信息
            variable_info = self._get_diff_variable(variable_guid)
            code = variable_info.get('code', '')
            if not variable_info:
                LOG.warning(f"无法获取{variable_type}变量 {variable_guid} 的详细信息，保留原GUID")
                updated_variables.append(variable_ref)
                continue
            
            # 检查是否为公有变量
            if variable_info.get('variable_type') == GLOBAL_VARIABLE_TYPE:
                LOG.debug(f"{variable_type}变量 {variable_guid} 是公有变量，添加到集合A")
                updated_variables.append(variable_ref)
                self.processed_variables.add(variable_guid)
                self.stats['global_variables'] += 1
                continue
            
            # 检查子系统设计ID是否一致
            var_subsystem_id = variable_info.get('subsystem_design', {}).get('guid') if variable_info.get('subsystem_design') else None

            if var_subsystem_id == current_subsystem_id:
                LOG.debug(f"{variable_type}变量 {variable_guid} 的子系统设计ID一致，无需处理")
                updated_variables.append(variable_ref)
            else:
                presented_variable = self._get_diff_variable_by_code(code, current_subsystem_id)
                if (presented_variable):
                    has_changes = True
                    LOG.info(f"变量已存在，无需创建")
                    updated_variables.append({'guid': presented_variable.get('guid')})
                    continue

                LOG.info(f"{variable_type}变量 {variable_guid} 的子系统设计ID不一致，需要创建新变量")
                LOG.debug(f"原子系统ID: {var_subsystem_id}, 目标子系统ID: {current_subsystem_id}")
                
                # 创建新的变量
                new_guid = self._create_new_variable(variable_info, current_subsystem_id)
                if new_guid:
                    # 更新变量引用
                    new_variable_ref = variable_ref.copy()
                    new_variable_ref['guid'] = new_guid.get('guid', '')
                    updated_variables.append(new_variable_ref)
                    has_changes = True
                    self.stats['created_variables'] += 1
                    LOG.info(f"成功创建新的{variable_type}变量 {new_guid} 替换原变量 {variable_guid}")
                else:
                    # 创建失败，保留原GUID
                    updated_variables.append(variable_ref)
                    LOG.error(f"创建新{variable_type}变量失败，保留原GUID {variable_guid}")
        return [item['guid'] for item in updated_variables], has_changes
    
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
    
    def _update_package_variables(self, package_guid, updated_variables, updated_db_variables):
        """
        更新物料包的差异化变量列表
        
        Args:
            package_guid: 物料包GUID
            updated_variables: 更新后的变量列表
        """
        update_data = {
            'guid': package_guid,
            'diff_conf_variable': updated_variables,
            'db_diff_conf_variable': updated_db_variables
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
        清理无效的差异化变量记录
        删除非公有变量且子系统设计为null的记录
        """
        LOG.info(f"开始清理无效变量，批处理大小: {self.batch_size}")
        
        base_query = {
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
            # 第一步：处理state为updated_0的数据
            self._process_updated_0_variables_in_batches(base_query)
            
            # 第二步：将所有的数据调用delete接口
            self._delete_invalid_variables_in_batches(base_query)
            
            # 第三步：对所有state为deleted_0的数据进行确认删除
            self._confirm_deleted_variables_in_batches(base_query)
            
            
        except Exception as e:
            LOG.error(f"清理无效差异化变量时出错: {str(e)}")

    def _process_batch_with_retry(self, operation_name, operation_func, batch_data, max_retries=3):
        """
        带重试机制的批处理操作
        
        Args:
            operation_name: 操作名称（用于日志）
            operation_func: 要执行的操作函数
            batch_data: 批次数据
            max_retries: 最大重试次数
        """
        for attempt in range(max_retries):
            try:
                operation_func(batch_data)
                return True
            except Exception as e:
                LOG.warning(f"{operation_name} 第 {attempt + 1} 次尝试失败: {str(e)}")
                if attempt == max_retries - 1:
                    LOG.error(f"{operation_name} 达到最大重试次数，跳过此批次")
                    self.stats['failed_batches'] += 1
                    return False
                else:
                    import time
                    time.sleep(2)  # 重试前等待2秒
        return False

    def _process_updated_0_variables_in_batches(self, base_query):
        """批量处理updated_0状态的变量"""
        LOG.info("开始处理updated_0状态的变量...")
        
        query_copy = copy.deepcopy(base_query)
        query_copy['filters'].append({
            "name": "state",
            "operator": "eq",
            "value": "updated_0"
        })
        
        variables = self._fetch_variables(query_copy, "updated_0")
        filtered_variables = [
            item for item in variables
            if item.get('subsystem_design') is None
        ]
        
        if not filtered_variables:
            LOG.info("没有找到updated_0状态需要处理的变量")
            return
        
        self._process_in_batches(
            data=filtered_variables,
            operation_name="确认updated_0变量",
            operation_func=lambda batch_data: self.cmdb_client.confirm(
                CONF.wecube.wecmdb.citypes.diff_config, batch_data
            ),
            count_key='updated_0_confirmed'
        )

    def _delete_invalid_variables_in_batches(self, base_query):
        """批量删除无效变量"""
        LOG.info("开始删除无效变量...")
        
        variables = self._fetch_variables(base_query, "需要删除")
        filtered_variables = [
            item for item in variables
            if 'Delete' in item.get('nextOperations', []) 
            and item.get('subsystem_design') is None
        ]
        
        if not filtered_variables:
            LOG.info("没有找到需要删除的无效变量")
            return
        
        self._process_in_batches(
            data=filtered_variables,
            operation_name="删除无效变量",
            operation_func=lambda batch_data: self.cmdb_client.delete(
                CONF.wecube.wecmdb.citypes.diff_config, batch_data
            ),
            count_key='invalid_deleted'
        )

    def _confirm_deleted_variables_in_batches(self, base_query):
        """批量确认删除deleted_0状态的变量"""
        LOG.info("开始确认删除deleted_0状态的变量...")
        
        query_copy = copy.deepcopy(base_query)
        query_copy['filters'].append({
            "name": "state",
            "operator": "eq",
            "value": "deleted_0"
        })
        
        variables = self._fetch_variables(query_copy, "deleted_0")
        filtered_variables = [
            item for item in variables
            if item.get('subsystem_design') is None
        ]
        
        if not filtered_variables:
            LOG.info("没有找到deleted_0状态需要确认删除的变量")
            return
        
        self._process_in_batches(
            data=filtered_variables,
            operation_name="确认删除deleted_0变量",
            operation_func=lambda batch_data: self.cmdb_client.confirm(
                CONF.wecube.wecmdb.citypes.diff_config, batch_data
            ),
            count_key='deleted_0_confirmed'
        )

    def _fetch_variables(self, query, operation_type):
        """获取变量数据"""
        try:
            resp_json = self.cmdb_client.retrieve(CONF.wecube.wecmdb.citypes.diff_config, query)
            return resp_json.get('data', {}).get('contents', [])
        except Exception as e:
            LOG.error(f"获取{operation_type}变量时失败: {str(e)}")
            return []

    def _process_in_batches(self, data, operation_name, operation_func, count_key):
        """通用的批处理方法"""
        total_count = len(data)
        LOG.info(f"找到 {total_count} 个变量需要{operation_name}")
        
        processed_count = 0
        for i in range(0, total_count, self.batch_size):
            batch = data[i:i + self.batch_size]
            batch_data = [{'guid': var['guid']} for var in batch]
            batch_number = i // self.batch_size + 1
            
            LOG.info(f"{operation_name} 第 {batch_number} 批，数量: {len(batch_data)}")
            
            success = self._process_batch_with_retry(
                f"{operation_name}第{batch_number}批",
                operation_func,
                batch_data
            )
            
            if success:
                processed_count += len(batch_data)
                self.stats[count_key] += len(batch_data)
                LOG.info(f"已{operation_name} {processed_count}/{total_count} 个变量")
            
            # 批次间的短暂延迟，避免对服务器造成压力
            if i + self.batch_size < total_count:
                import time
                time.sleep(0.5)

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
        LOG.info("=== 批处理统计信息 ===")
        LOG.info(f"Updated_0状态确认数量: {self.stats['updated_0_confirmed']}")
        LOG.info(f"无效变量删除数量: {self.stats['invalid_deleted']}")
        LOG.info(f"Deleted_0状态确认数量: {self.stats['deleted_0_confirmed']}")
        LOG.info(f"失败批次数量: {self.stats['failed_batches']}")
        LOG.info(f"批处理大小: {self.batch_size}")
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