<template>
  <div>
    <Drawer :title="$t('artifacts_script_configuration')" :closable="false" v-model="openDrawer" width="1300">
      <Card :bordered="false" :padding="8">
        <Row>
          <Col style="text-align: right; line-height: 32px" span="5">
            <span style="margin-right: 10px">{{ $t('package_type') }}</span>
          </Col>
          <Col span="18" offset="1">
            <Select clearable :placeholder="$t('package_type')" v-model="packageType">
              <Option v-for="pkt in packageTypeOptions" :value="pkt.value" :key="pkt.value" :disabled="pkt.value === 'IMAGE'">{{ $t(pkt.label) }}</Option>
            </Select>
          </Col>
        </Row>
      </Card>
      <Card :bordered="false" :padding="8">
        <Row>
          <Col style="text-align: right; line-height: 32px" span="5">
            <span style="margin-right: 10px">{{ $t('baseline_package') }}</span>
          </Col>
          <Col span="18" offset="1">
            <Select clearable filterable :placeholder="$t('baseline_package')" @on-change="baseLinePackageChanged" v-model="packageInput.baseline_package">
              <Option v-for="conf in baselinePackageOptions" :value="conf.guid" :key="conf.name">{{ conf.name }}</Option>
            </Select>
          </Col>
        </Row>
      </Card>
      <Tabs :value="currentConfigTab" class="config-tab" @on-click="changeCurrentConfigTab">
        <TabPane :disabled="packageType === constPackageOptions.db" :label="$t('APP')" name="APP">
          <div>
            {{ $t('is_decompression') }}：
            <i-switch v-model="packageInput.is_decompression" />
          </div>
          <div style="border:1px solid #e8eaec;">
            <Table :columns="columns1" :data="[]" size="small" class="table-only-have-header"></Table>
            <!-- 差异化配置文件 -->
            <div class="grid-row">
              <div class="grid-cell">
                {{ $t('artifacts_config_files') }}
              </div>
              <div class="grid-cell">
                <div>
                  <Tooltip :content="$t('art_select_directory')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(0.1, packageInput.diff_conf_directory || [])" />
                  </Tooltip>
                  <div id="diff_conf_directory_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.diff_conf_directory" :key="index">
                      <Input class="textarea-dir" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.diff_conf_directory[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button size="small" type="error" style="margin-left:4px" icon="md-trash" ghost @click="deleteFilePath(index, 'diff_conf_directory')"></Button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="grid-cell">
                <div style="display: flex;align-items: flex-start;">
                  <Tooltip :content="$t('artifacts_select_file')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(0, packageInput.diff_conf_file || [])" />
                  </Tooltip>
                  <div id="diff_conf_file_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.diff_conf_file" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.diff_conf_file[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'diff_conf_file')"></Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <!-- 脚本 -->
            <div class="grid-row">
              <div class="grid-cell">
                {{ $t('art_script') }}
              </div>
              <div class="grid-cell">
                <div>
                  <Tooltip :content="$t('art_select_directory')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(0.2, packageInput.script_file_directory || [])" />
                  </Tooltip>
                  <div id="script_file_directory_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.script_file_directory" :key="index">
                      <Input class="textarea-dir" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.script_file_directory[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'script_file_directory')"></Button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="grid-cell">
                <!-- 启动脚本 -->
                <div style="display: flex;align-items: flex-start;">
                  <span style="margin-right: 10px">{{ $t('artifacts_start_script') }}</span>
                  <Tooltip :content="$t('artifacts_select_file')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(1, packageInput.start_file_path || [])" />
                  </Tooltip>
                  <div id="start_file_path_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.start_file_path" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.start_file_path[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'start_file_path')"></Button>
                    </div>
                  </div>
                </div>
                <!-- 停止脚本 -->
                <div style="display: flex;align-items: flex-start;">
                  <span style="margin-right: 10px">{{ $t('artifacts_stop_script') }}</span>
                  <Tooltip :content="$t('artifacts_select_file')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(2, packageInput.stop_file_path || [])" />
                  </Tooltip>
                  <div id="stop_file_path_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.stop_file_path" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.stop_file_path[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'stop_file_path')"></Button>
                    </div>
                  </div>
                </div>
                <!-- 部署脚本 -->
                <div style="display: flex;align-items: flex-start;">
                  <span style="margin-right: 10px">{{ $t('artifacts_deploy_script') }}</span>
                  <Tooltip :content="$t('artifacts_select_file')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(3, packageInput.deploy_file_path || [])" />
                  </Tooltip>
                  <div id="deploy_file_path_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.deploy_file_path" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.deploy_file_path[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'deploy_file_path')"></Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <!-- 日志 -->
            <div class="grid-row">
              <div class="grid-cell">
                {{ $t('art_log') }}
              </div>
              <div class="grid-cell">
                <div>
                  <Tooltip :content="$t('art_select_directory')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(0.3, packageInput.log_file_directory || [])" />
                  </Tooltip>
                  <div id="log_file_directory_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.log_file_directory" :key="index">
                      <Input class="textarea-dir" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.log_file_directory[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'log_file_directory')"></Button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="grid-cell">
                <div style="display: flex;align-items: flex-start;margin: 2px">
                  <div style="display: inline-block; width: 100px; margin-right: 10px">{{ $t('业务指标日志') }}</div>
                  <div id="log_file_trade_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.log_file_trade" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('art_enter_log_path')" type="textarea" v-model="packageInput.log_file_trade[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'log_file_trade')"></Button>
                    </div>
                  </div>
                  <Button style="margin: 4px" size="small" type="info" icon="md-add" ghost @click="addFilePath('log_file_trade')"></Button>
                </div>
                <div style="display: flex;align-items: flex-start;margin: 2px">
                  <div style="display: inline-block; width: 100px; margin-right: 10px">{{ $t('关键字日志') }}</div>
                  <div id="log_file_keyword_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.log_file_keyword" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('art_enter_log_path')" type="textarea" v-model="packageInput.log_file_keyword[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'log_file_keyword')"></Button>
                    </div>
                  </div>
                  <Button style="margin: 4px" size="small" type="info" icon="md-add" ghost @click="addFilePath('log_file_keyword')"></Button>
                </div>
                <div style="display: flex;align-items: flex-start;margin: 2px">
                  <div style="display: inline-block; width: 100px; margin-right: 10px">{{ $t('Metric日志') }}</div>
                  <div id="log_file_metric_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.log_file_metric" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('art_enter_log_path')" type="textarea" v-model="packageInput.log_file_metric[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'log_file_metric')"></Button>
                    </div>
                  </div>
                  <Button style="margin: 4px" size="small" type="info" icon="md-add" ghost @click="addFilePath('log_file_metric')"></Button>
                </div>
                <div style="display: flex;align-items: flex-start;margin: 2px">
                  <div style="display: inline-block; width: 100px; margin-right: 10px">{{ $t('Trace日志') }}</div>
                  <div id="log_file_trace_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.log_file_trace" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('art_enter_log_path')" type="textarea" v-model="packageInput.log_file_metric[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'log_file_trace')"></Button>
                    </div>
                  </div>
                  <Button style="margin: 4px" size="small" type="info" icon="md-add" ghost @click="addFilePath('log_file_trace')"></Button>
                </div>
              </div>
            </div>
          </div>
          <!-- 关键交易服务码 -->
          <div style="margin-top: 16px;">
            <Row>
              <Col span="3" style="margin-top: 30px">
                <span style="color:#5cadff">{{ $t('art_service_code') }}</span>
              </Col>
              <Col span="21">
                <Row>
                  <Col span="4">{{ $t('art_match_type') }}</Col>
                  <Col span="4">
                    <span style="color:red">*</span>
                    {{ $t('art_source_value') }}</Col
                  >
                  <Col span="4">
                    <span style="color:red">*</span>
                    {{ $t('art_match_value') }}
                  </Col>
                </Row>
                <Row v-for="(item, itemIndex) in packageInput.code_string_map" :key="itemIndex" style="margin:6px 0;">
                  <Col span="4">
                    <Select v-model="item.regulative" style="width:90%" @change="changeCodeStringMap(itemIndex)">
                      <Option :value="1" key="art_regular_match">{{ $t('art_regular_match') }}</Option>
                      <Option :value="0" key="art_irregular_matching">{{ $t('art_irregular_matching') }}</Option>
                    </Select>
                  </Col>
                  <Col span="4">
                    <Input v-model.trim="item.source_value" style="width:90%"></Input>
                  </Col>
                  <Col span="4">
                    <Input v-model.trim="item.target_value" style="width:90%"> </Input>
                  </Col>
                  <Col span="2" offset="1">
                    <Button type="error" ghost @click="deleteCodeStringMap(itemIndex)" size="small" style="vertical-align: sub;cursor: pointer" icon="md-trash"></Button>
                  </Col>
                </Row>
              </Col>
            </Row>
            <Row>
              <Col span="21" offset="3">
                <Row>
                  <Col span="2" offset="13">
                    <div style="cursor: pointer">
                      <Button type="success" ghost :disabled="disableAddCodeStringMap" @click="addCodeStringMap()" size="small" icon="md-add"></Button>
                    </div>
                  </Col>
                </Row>
              </Col>
            </Row>
          </div>
        </TabPane>
        <TabPane :disabled="packageType === constPackageOptions.app" :label="$t('DB')" name="DB">
          <div style="border:1px solid #e8eaec;">
            <Table :columns="columns1" :data="[]" size="small" class="table-only-have-header"></Table>
            <!-- 升级脚本 -->
            <div class="grid-row">
              <div class="grid-cell">
                {{ $t('db_upgrade_file_path') }}
              </div>
              <div class="grid-cell">
                <div>
                  <Tooltip :content="$t('art_select_directory')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(101, packageInput.db_upgrade_directory || [])" />
                  </Tooltip>
                  <div id="db_upgrade_directory_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_upgrade_directory" :key="index">
                      <Input class="textarea-dir" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_upgrade_directory[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button size="small" type="error" style="margin-left:4px" icon="md-trash" ghost @click="deleteFilePath(index, 'db_upgrade_directory')"></Button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="grid-cell">
                <div style="display: flex;align-items: flex-start;">
                  <Tooltip :content="$t('artifacts_select_file')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(103, packageInput.db_upgrade_file_path || [])" />
                  </Tooltip>
                  <div id="db_upgrade_file_path_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_upgrade_file_path" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_upgrade_file_path[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'db_upgrade_file_path')"></Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <!-- 回滚脚本 -->
            <div class="grid-row">
              <div class="grid-cell">
                {{ $t('db_rollback_directory') }}
              </div>
              <div class="grid-cell">
                <div>
                  <Tooltip :content="$t('art_select_directory')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(102, packageInput.db_rollback_directory || [])" />
                  </Tooltip>
                  <div id="db_rollback_directory_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_rollback_directory" :key="index">
                      <Input class="textarea-dir" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_rollback_directory[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button size="small" type="error" style="margin-left:4px" icon="md-trash" ghost @click="deleteFilePath(index, 'db_rollback_directory')"></Button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="grid-cell">
                <div style="display: flex;align-items: flex-start;">
                  <Tooltip :content="$t('artifacts_select_file')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(104, packageInput.db_rollback_file_path || [])" />
                  </Tooltip>
                  <div id="db_rollback_file_path_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_rollback_file_path" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_rollback_file_path[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'db_rollback_file_path')"></Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <!-- 首次部署脚本 -->
            <div class="grid-row">
              <div class="grid-cell">
                {{ $t('art_initial_deployment_script') }}
              </div>
              <div class="grid-cell">
                <div>
                  <Tooltip :content="$t('art_select_directory')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(0.4, packageInput.db_deploy_file_directory || [])" />
                  </Tooltip>
                  <div id="db_deploy_file_directory_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_deploy_file_directory" :key="index">
                      <Input class="textarea-dir" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_deploy_file_directory[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button size="small" type="error" style="margin-left:4px" icon="md-trash" ghost @click="deleteFilePath(index, 'db_deploy_file_directory')"></Button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="grid-cell">
                <div style="display: flex;align-items: flex-start;">
                  <Tooltip :content="$t('artifacts_select_file')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(105, packageInput.db_deploy_file_path || [])" />
                  </Tooltip>
                  <div id="db_deploy_file_path_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_deploy_file_path" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_deploy_file_path[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'db_deploy_file_path')"></Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <!-- 差异化配置文件 -->
            <div class="grid-row">
              <div class="grid-cell">
                {{ $t('artifacts_config_files') }}
              </div>
              <div class="grid-cell">
                <div>
                  <Tooltip :content="$t('art_select_directory')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(0.5, packageInput.db_diff_conf_directory || [])" />
                  </Tooltip>
                  <div id="db_diff_conf_directory_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_diff_conf_directory" :key="index">
                      <Input class="textarea-dir" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_diff_conf_directory[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button size="small" type="error" style="margin-left:4px" icon="md-trash" ghost @click="deleteFilePath(index, 'db_diff_conf_directory')"></Button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="grid-cell">
                <div style="display: flex;align-items: flex-start;">
                  <Tooltip :content="$t('artifacts_select_file')" placement="top">
                    <Icon type="md-cloud-upload" size="18" style="margin-right: 4px;" @click="() => showTreeModal(106, packageInput.db_diff_conf_file || [])" />
                  </Tooltip>
                  <div id="db_diff_conf_file_test" style="display: inline-block;">
                    <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_diff_conf_file" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_diff_conf_file[index].filename" />
                      <DisplayPath :file="file"></DisplayPath>
                      <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'db_diff_conf_file')"></Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </TabPane>
      </Tabs>
      <template slot="footer">
        <Button @click="closeFilesModal">{{ $t('artifacts_cancel') }}</Button>
        <Button @click="saveDrawer" type="primary">{{ $t('artifacts_save') }}</Button>
      </template>
    </Drawer>
    <!-- 包配置文件选择 -->
    <Modal :styles="{ top: '60px' }" :mask-closable="false" v-model="isShowTreeModal" :title="configFileTreeTitle" @on-ok="saveConfigFileTree" @on-cancel="closeConfigFileTree" draggable width="700">
      <CheckboxGroup v-if="packageInput.baseline_package">
        <Button :style="toggleCheckFileTreeNew" type="dashed" size="small" @click="checkConfigFileTreeVis('new')"><span style="color: #18b566">new</span></Button>
        <Button :style="toggleCheckFileTreeSame" type="dashed" size="small" @click="checkConfigFileTreeVis('same')"><span>same</span></Button>
        <Button :style="toggleCheckFileTreeChanged" type="dashed" size="small" @click="checkConfigFileTreeVis('changed')"><span style="color: #2d8cf0">changed</span></Button>
        <Button :style="toggleCheckFileTreeDeleted" type="dashed" size="small" @click="checkConfigFileTreeVis('deleted')"><span style="color: #cccccc">deleted</span></Button>
      </CheckboxGroup>
      <div style="height: 450px; overflow-y: auto">
        <Tree ref="configTree" :data="configFileTree.treeData" :load-data="configFileTreeLoadNode" @on-toggle-expand="configFileTreeExpand" @on-check-change="changeChildChecked" show-checkbox> </Tree>
      </div>
    </Modal>
  </div>
</template>

<script>
import { getPackageDetail, queryPackages, getFiles, compareBaseLineFiles, updatePackage } from '@/api/server.js'
import Sortable from 'sortablejs'
import DisplayPath from '../views/display-path.vue'
import iconFile from '../assets/file.png'
import iconFolder from '../assets/folder.png'
// 业务运行实例ciTypeId
const defaultAppRootCiTypeId = 'app_instance'
const defaultDBRootCiTypeId = 'rdb_instance'
export default {
  name: '',
  data () {
    return {
      columns1: [
        {
          title: this.$t('artifacts_configuration'),
          key: 'name',
          width: 100
        },
        {
          title: this.$t('art_directory'),
          key: 'age',
          width: 466
        },
        {
          title: this.$t('art_file'),
          key: 'address',
          width: 700
        }
      ],
      openDrawer: false,
      guid: '',
      packageId: '', // 当前选中的packageId
      packageTypeOptions: [
        { label: 'APP', value: 'APP' },
        { label: 'DB', value: 'DB' },
        { label: 'APP&DB', value: 'APP&DB' },
        { label: 'IMAGE', value: 'IMAGE' }
      ],
      constPackageOptions: {
        db: 'DB',
        app: 'APP',
        mixed: 'APP&DB',
        image: 'IMAGE'
      },
      packageInput: {
        baseline_package: null,
        diff_conf_directory: [], // 差异化变量
        diff_conf_file: [],
        script_file_directory: [], // 部署脚本
        start_file_path: [],
        stop_file_path: [],
        deploy_file_path: [],
        log_file_directory: [], // 日志文件
        log_file_trade: [],
        log_file_keyword: [],
        log_file_metric: [],
        log_file_trace: [],
        code_string_map: [], // 关键交易服务码
        is_decompression: true,

        db_diff_conf_directory: [], // DB差异化变量
        db_diff_conf_file: [],
        db_upgrade_directory: [], // DB升级脚本
        db_upgrade_file_path: [],
        db_rollback_directory: [], // DB回滚脚本
        db_rollback_file_path: [],
        db_deploy_file_directory: [], // DB部署脚本
        db_deploy_file_path: []
      },
      packageDetail: {
        baseline_package: null,
        diff_conf_directory: [], // 差异化变量
        diff_conf_file: [],
        script_file_directory: [], // 部署脚本
        start_file_path: [],
        stop_file_path: [],
        deploy_file_path: [],
        log_file_directory: [], // 日志文件
        log_file_trade: [],
        log_file_keyword: [],
        log_file_metric: [],
        log_file_trace: [],
        code_string_map: [], // 关键交易服务码
        is_decompression: true,

        db_diff_conf_directory: [], // DB差异化变量
        db_diff_conf_file: [],
        db_upgrade_directory: [], // DB升级脚本
        db_upgrade_file_path: [],
        db_rollback_directory: [], // DB回滚脚本
        db_rollback_file_path: [],
        db_deploy_file_directory: [], // DB部署脚本
        db_deploy_file_path: []
      },
      packageType: '', // 包类型
      baselinePackageOptions: [], // 基线包下拉框数据
      currentConfigTab: '',
      // 包配置文件选择模态数据
      // -------------------
      isShowTreeModal: false,
      configFileTree: {
        treeType: 0,
        treeData: []
      },
      configFileTreeTitle: '',
      toggleCheckFileTreeNew: '',
      toggleCheckFileTreeSame: '',
      toggleCheckFileTreeChanged: '',
      toggleCheckFileTreeDeleted: ''
      // -------------------
    }
  },
  computed: {
    disableAddCodeStringMap () {
      let res = this.packageInput.code_string_map.some(item => item.source_value === '' || item.target_value === '')
      return res
    }
  },
  methods: {
    initSortable (key) {
      const $ul = document.getElementById(key + '_test')
      const _this = this
      // eslint-disable-next-line no-unused-vars
      const ss = new Sortable($ul, {
        onUpdate: event => {
          const newIndex = event.newIndex
          const oldIndex = event.oldIndex
          const $li = $ul.children[newIndex]
          const $oldLi = $ul.children[oldIndex]
          $ul.removeChild($li)
          if (newIndex > oldIndex) {
            $ul.insertBefore($li, $oldLi)
          } else {
            $ul.insertBefore($li, $oldLi.nextSibling)
          }
          const item = _this.packageInput[key].splice(oldIndex, 1)
          _this.packageInput[key].splice(newIndex, 0, item[0])
        },
        animation: 150
      })
    },
    genSortable1 (key) {
      this.initSortable(key)
    },
    async open (guid, row, hideFooter) {
      this.guid = guid
      this.packageId = row.guid
      await this.syncPackageDetail()
      this.packageType = row.package_type || this.constPackageOptions.mixed
      this.currentConfigTab = this.packageType === this.constPackageOptions.db ? this.constPackageOptions.db : this.constPackageOptions.app
      // 以下4个变量类型为字符串
      // row从table数据中来，此时baseline_package为对象
      this.packageInput.baseline_package = this.packageDetail.baseline_package ? this.packageDetail.baseline_package : null
      this.packageInput.diff_conf_file = JSON.parse(JSON.stringify(this.packageDetail.diff_conf_file))
      this.packageInput.start_file_path = JSON.parse(JSON.stringify(this.packageDetail.start_file_path))
      this.packageInput.stop_file_path = JSON.parse(JSON.stringify(this.packageDetail.stop_file_path))
      this.packageInput.deploy_file_path = JSON.parse(JSON.stringify(this.packageDetail.deploy_file_path))
      this.packageInput.is_decompression = row.is_decompression || true

      this.packageInput.db_diff_conf_file = JSON.parse(JSON.stringify(this.packageDetail.db_diff_conf_file))
      this.packageInput.db_upgrade_directory = JSON.parse(JSON.stringify(this.packageDetail.db_upgrade_directory || []))
      this.packageInput.db_rollback_directory = JSON.parse(JSON.stringify(this.packageDetail.db_rollback_directory || []))
      this.packageInput.db_upgrade_file_path = JSON.parse(JSON.stringify(this.packageDetail.db_upgrade_file_path || []))
      this.packageInput.db_rollback_file_path = JSON.parse(JSON.stringify(this.packageDetail.db_rollback_file_path || []))
      this.packageInput.db_deploy_file_path = JSON.parse(JSON.stringify(this.packageDetail.db_deploy_file_path || []))

      this.packageId = row.guid
      this.hideFooter = hideFooter
      await this.getAllpkg()
      this.openDrawer = true

      this.$nextTick(() => {
        if (this.packageType !== this.constPackageOptions.db) {
          this.genSortable1('diff_conf_file')
          // 脚本
          this.genSortable1('start_file_path')
          this.genSortable1('stop_file_path')
          this.genSortable1('deploy_file_path')
          // 日志
          this.genSortable1('log_file_trade')
          this.genSortable1('log_file_keyword')
          this.genSortable1('log_file_metric')
          this.genSortable1('log_file_trace')
        }
        if (this.packageType !== this.constPackageOptions.app) {
          this.genSortable1('db_diff_conf_file')
          this.genSortable1('db_upgrade_directory')
          this.genSortable1('db_rollback_directory')
          this.genSortable1('db_upgrade_file_path')
          this.genSortable1('db_rollback_file_path')
          this.genSortable1('db_deploy_file_path')
        }
      })
    },
    async syncBaselineFileStatus () {
      if (this.packageInput.baseline_package) {
        const { data } = await compareBaseLineFiles(this.guid, this.packageId, { baselinePackage: this.packageInput.baseline_package })
        this.packageInput.diff_conf_file.forEach(el => {
          data.diff_conf_file.forEach(elRet => {
            if (elRet.filename === el.filename) {
              el.comparisonResult = elRet.comparisonResult
            }
          })
        })
        this.packageInput.start_file_path.forEach(el => {
          data.start_file_path.forEach(elRet => {
            if (elRet.filename === el.filename) {
              el.comparisonResult = elRet.comparisonResult
            }
          })
        })
        this.packageInput.stop_file_path.forEach(el => {
          data.stop_file_path.forEach(elRet => {
            if (elRet.filename === el.filename) {
              el.comparisonResult = elRet.comparisonResult
            }
          })
        })
        this.packageInput.deploy_file_path.forEach(el => {
          data.deploy_file_path.forEach(elRet => {
            if (elRet.filename === el.filename) {
              el.comparisonResult = elRet.comparisonResult
            }
          })
        })

        this.packageInput.db_diff_conf_file.forEach(el => {
          data.db_diff_conf_file.forEach(elRet => {
            if (elRet.filename === el.filename) {
              el.comparisonResult = elRet.comparisonResult
            }
          })
        })

        this.packageInput.db_upgrade_directory.forEach(el => {
          data.db_upgrade_directory.forEach(elRet => {
            if (elRet.filename === el.filename) {
              el.comparisonResult = elRet.comparisonResult
            }
          })
        })
        this.packageInput.db_rollback_directory.forEach(el => {
          data.db_rollback_directory.forEach(elRet => {
            if (elRet.filename === el.filename) {
              el.comparisonResult = elRet.comparisonResult
            }
          })
        })
        this.packageInput.db_deploy_file_path.forEach(el => {
          data.db_deploy_file_path.forEach(elRet => {
            if (elRet.filename === el.filename) {
              el.comparisonResult = elRet.comparisonResult
            }
          })
        })
        this.packageInput.db_upgrade_file_path = data.db_upgrade_file_path || []
        this.packageInput.db_rollback_file_path = data.db_rollback_file_path || []
      }
    },
    async syncPackageDetail () {
      this.initPackageDetail()
      let { status, data } = await getPackageDetail(this.guid, this.packageId)
      if (status === 'OK') {
        const tmp = this.currentDiffConfigTab === this.constPackageOptions.db ? 'db_diff_conf_file' : 'diff_conf_file'
        this.packageDetail = this.formatPackageDetail(data)
        if (this.packageDetail[tmp].length > 0) {
          this.activeTab = this.packageDetail[tmp][0].filename
          this.activeTabData = this.packageDetail[tmp][0].configKeyInfos
        } else {
          this.activeTab = ''
          this.activeTabData = {}
        }
      }
    },
    async baseLinePackageChanged (v) {
      if (v) {
        const found = JSON.parse(JSON.stringify(this.baselinePackageOptions.find(row => row.guid === v)))
        this.packageType = found.package_type
        this.packageInput.diff_conf_file = found.diff_conf_file ? JSON.parse(JSON.stringify(found.diff_conf_file)) : []
        this.packageInput.start_file_path = found.start_file_path ? JSON.parse(JSON.stringify(found.start_file_path)) : []
        this.packageInput.stop_file_path = found.stop_file_path ? JSON.parse(JSON.stringify(found.stop_file_path)) : []
        this.packageInput.deploy_file_path = found.deploy_file_path ? JSON.parse(JSON.stringify(found.deploy_file_path)) : []
        this.packageInput.is_decompression = found.is_decompression || true

        this.packageInput.db_diff_conf_file = found.db_diff_conf_file ? JSON.parse(JSON.stringify(found.db_diff_conf_file)) : []
        this.packageInput.db_upgrade_directory = found.db_upgrade_directory ? JSON.parse(JSON.stringify(found.db_upgrade_directory)) : []
        this.packageInput.db_rollback_directory = found.db_rollback_directory ? JSON.parse(JSON.stringify(found.db_rollback_directory)) : []
        this.packageInput.db_upgrade_file_path = []
        this.packageInput.db_rollback_file_path = []
        this.packageInput.db_deploy_file_path = found.db_deploy_file_path ? JSON.parse(JSON.stringify(found.db_deploy_file_path)) : []
      }
      await this.syncBaselineFileStatus()
    },
    formatPackageDetail (data) {
      let dataString = JSON.stringify(data)
      let copyData = JSON.parse(dataString)
      let diffConfVariable = copyData.diff_conf_variable || []
      let dbDiffConfVariable = copyData.db_diff_conf_variable || []
      diffConfVariable.forEach(elVar => {
        // 记录原始值
        elVar.originDiffExpr = elVar.diffExpr
        const rootCI = this.getRootCI(elVar.diffExpr, defaultAppRootCiTypeId, elVar)
        elVar.originRootCI = rootCI
        elVar.tempRootCI = rootCI
        elVar.withinFiles = []
        elVar.withinFileIndexes = []
        let index = 0
        copyData.diff_conf_file.forEach(elFile => {
          elFile.configKeyInfos = elFile.configKeyInfos || []
          elFile.configKeyInfos.forEach(elFileVar => {
            if (elVar.key.toLowerCase() === elFileVar.key.toLowerCase()) {
              let baseName = elFile.filename.split('/').slice(-1)[0]
              elVar.withinFiles.push(baseName)
              elVar.withinFileIndexes.push(index)
            }
          })
          index += 1
        })
        elVar.fileNames = elVar.withinFiles.join(', ')
      })
      copyData.diff_conf_file.forEach(elFile => {
        let index = 1
        elFile.shorFileName = elFile.filename.split('/').slice(-1)[0]
        elFile.configKeyInfos.forEach(elFileVar => {
          elFileVar.index = index
          const found = diffConfVariable.find(_ => _.key.toLowerCase() === elFileVar.key.toLowerCase())
          elFileVar.conf_variable = found
          index += 1
        })
      })

      dbDiffConfVariable.forEach(elVar => {
        // 记录原始值
        elVar.originDiffExpr = elVar.diffExpr
        const rootCI = this.getRootCI(elVar.diffExpr, defaultDBRootCiTypeId)
        elVar.originRootCI = rootCI
        elVar.tempRootCI = rootCI
        elVar.withinFiles = []
        elVar.withinFileIndexes = []
        let index = 0
        copyData.db_diff_conf_file.forEach(elFile => {
          elFile.configKeyInfos = elFile.configKeyInfos || []
          elFile.configKeyInfos.forEach(elFileVar => {
            if (elVar.key.toLowerCase() === elFileVar.key.toLowerCase()) {
              let baseName = elFile.filename.split('/').slice(-1)[0]
              elVar.withinFiles.push(baseName)
              elVar.withinFileIndexes.push(index)
            }
          })
          index += 1
        })
        elVar.fileNames = elVar.withinFiles.join(', ')
      })
      copyData.db_diff_conf_file.forEach(elFile => {
        let index = 1
        elFile.shorFileName = elFile.filename.split('/').slice(-1)[0]
        elFile.configKeyInfos.forEach(elFileVar => {
          elFileVar.index = index
          const found = dbDiffConfVariable.find(_ => _.key.toLowerCase() === elFileVar.key.toLowerCase())
          elFileVar.conf_variable = found
          index += 1
        })
      })
      return copyData
    },
    getRootCI (diffExpr, defaultRootCiTypeId, elVar) {
      let rootCI = defaultRootCiTypeId
      if (!diffExpr) {
        return rootCI
      }
      try {
        const de = JSON.parse(diffExpr)
        const rootItem = de.find(item => item.type === 'rule')
        if (rootItem) {
          const val = JSON.parse(rootItem.value)
          rootCI = val[0].ciTypeId || defaultRootCiTypeId
        }
        return rootCI
      } catch (err) {
        throw err
      }
    },
    initPackageDetail () {
      this.packageDetail = {
        baseline_package: null,
        diff_conf_directory: [], // 差异化变量
        diff_conf_file: [],
        script_file_directory: [], // 部署脚本
        start_file_path: [],
        stop_file_path: [],
        deploy_file_path: [],
        log_file_directory: [], // 日志文件
        log_file_trade: [],
        log_file_keyword: [],
        log_file_metric: [],
        log_file_trace: [],
        code_string_map: [], // 关键交易服务码
        is_decompression: true,

        db_diff_conf_directory: [], // DB差异化变量
        db_diff_conf_file: [],
        db_upgrade_directory: [], // DB升级脚本
        db_upgrade_file_path: [],
        db_rollback_directory: [], // DB回滚脚本
        db_rollback_file_path: [],
        db_deploy_file_directory: [], // DB部署脚本
        db_deploy_file_path: []
      }
    },
    // 获取基线列表
    async getAllpkg () {
      this.baselinePackageOptions = []
      let { status, data } = await queryPackages(this.guid, {
        resultColumns: ['guid', 'name', 'package_type', 'diff_conf_file', 'start_file_path', 'stop_file_path', 'deploy_file_path', 'is_decompression', 'db_diff_conf_file', 'db_upgrade_directory', 'db_rollback_directory', 'db_deploy_file_path', 'db_upgrade_file_path', 'db_rollback_file_path'],
        sorting: {
          asc: false,
          field: 'upload_time'
        },
        filters: [
          {
            name: 'guid',
            operator: 'ne',
            value: this.packageId
          }
        ],
        paging: true,
        pageable: {
          pageSize: 100,
          startIndex: 0
        }
      })
      if (status === 'OK') {
        this.baselinePackageOptions = data.contents.map(item => {
          return {
            ...item
          }
        })
      }
    },
    changeCurrentConfigTab (val) {
      this.currentConfigTab = val
    },
    async showTreeModal (type, files) {
      this.initTreeConfig(type)
      this.isShowTreeModal = true
      this.isFileSelect = false
      let queryFiles = []
      if (type === 0) {
        this.configFileTreeTitle = this.$t('artifacts_select_config_files')
        queryFiles = this.packageInput.diff_conf_file.map(_ => _.filename)
      } else if (type === 0.1) {
        this.isFileSelect = true
        this.configFileTreeTitle = this.$t('artifacts_select_start_script')
        queryFiles = this.packageInput.diff_conf_directory.map(_ => _.filename)
      } else if (type === 0.2) {
        this.isFileSelect = true
        this.configFileTreeTitle = this.$t('artifacts_select_start_script')
        queryFiles = this.packageInput.script_file_directory.map(_ => _.filename)
      } else if (type === 1) {
        this.configFileTreeTitle = this.$t('artifacts_select_start_script')
        queryFiles = this.packageInput.start_file_path.map(_ => _.filename)
      } else if (type === 2) {
        this.configFileTreeTitle = this.$t('artifacts_select_stop_script')
        queryFiles = this.packageInput.stop_file_path.map(_ => _.filename)
      } else if (type === 3) {
        this.configFileTreeTitle = this.$t('artifacts_select_deploy_script')
        queryFiles = this.packageInput.deploy_file_path.map(_ => _.filename)
      } else if (type === 0.4) {
        this.isFileSelect = true
        this.configFileTreeTitle = this.$t('artifacts_select_deploy_script')
        queryFiles = this.packageInput.db_deploy_file_directory.map(_ => _.filename)
      } else if (type === 0.5) {
        this.isFileSelect = true
        this.configFileTreeTitle = this.$t('artifacts_select_deploy_script')
        queryFiles = this.packageInput.db_diff_conf_directory.map(_ => _.filename)
      } else if (type === 101) {
        this.isFileSelect = true
        this.configFileTreeTitle = this.$t('db_upgrade_directory')
        queryFiles = this.packageInput.db_upgrade_directory.map(_ => _.filename)
      } else if (type === 102) {
        this.isFileSelect = true
        this.configFileTreeTitle = this.$t('db_rollback_directory')
        queryFiles = this.packageInput.db_rollback_directory.map(_ => _.filename)
      } else if (type === 103) {
        this.configFileTreeTitle = this.$t('db_upgrade_file_path')
        queryFiles = this.packageInput.db_upgrade_file_path.map(_ => _.filename)
      } else if (type === 104) {
        this.configFileTreeTitle = this.$t('db_rollback_file_path')
        queryFiles = this.packageInput.db_rollback_file_path.map(_ => _.filename)
      } else if (type === 105) {
        this.configFileTreeTitle = this.$t('db_deploy_file_path')
        queryFiles = this.packageInput.db_deploy_file_path.map(_ => _.filename)
      } else if (type === 106) {
        this.configFileTreeTitle = this.$t('artifacts_select_config_files')
        queryFiles = this.packageInput.db_diff_conf_file.map(_ => _.filename)
      } else if (type === 0.3) {
        this.isFileSelect = true
        this.configFileTreeTitle = this.$t('artifacts_select_config_files')
        queryFiles = this.packageInput.log_file_directory.map(_ => _.filename)
      }
      const { data } = await getFiles(this.guid, this.packageId, {
        baselinePackage: this.packageInput.baseline_package,
        fileList: queryFiles,
        expandAll: true
      })
      this.configFileTree.treeData = this.formatConfigFileTree(data, queryFiles)
    },
    saveConfigFileTree () {
      let saveData = []
      this.$refs.configTree.getCheckedNodes().forEach(_ => {
        if (this.isFileSelect) {
          if (_.isDir) {
            if (_.children) {
              const isReal = _.children.every(item => item.isDir !== true)
              if (isReal) {
                saveData.push({ filename: _.path, isDir: _.isDir, comparisonResult: _.comparisonResult })
              }
            } else {
              saveData.push({ filename: _.path, isDir: _.isDir, comparisonResult: _.comparisonResult })
            }
          }
        } else {
          if (!_.isDir) {
            saveData.push({ filename: _.path, isDir: _.isDir, comparisonResult: _.comparisonResult })
          }
        }
      })
      if (this.configFileTree.treeType === 0) {
        this.packageInput.diff_conf_file = saveData
      } else if (this.configFileTree.treeType === 0.1) {
        if (saveData.length > 1) {
          this.$Message.warning(this.$t('art_multi_dir_warn'))
        } else {
          this.packageInput.diff_conf_directory = saveData
          this.packageInput.diff_conf_file = []
        }
      } else if (this.configFileTree.treeType === 0.2) {
        if (saveData.length > 1) {
          this.$Message.warning(this.$t('art_multi_dir_warn'))
        } else {
          this.packageInput.script_file_directory = saveData
          this.packageInput.start_file_path = []
          this.packageInput.stop_file_path = []
          this.packageInput.deploy_file_path = []
        }
      } else if (this.configFileTree.treeType === 1) {
        this.packageInput.start_file_path = saveData
      } else if (this.configFileTree.treeType === 2) {
        this.packageInput.stop_file_path = saveData
      } else if (this.configFileTree.treeType === 3) {
        this.packageInput.deploy_file_path = saveData
      } else if (this.configFileTree.treeType === 101) {
        if (saveData.length > 1) {
          this.$Message.warning(this.$t('art_multi_dir_warn'))
        } else {
          this.packageInput.db_upgrade_directory = saveData
        }
      } else if (this.configFileTree.treeType === 102) {
        if (saveData.length > 1) {
          this.$Message.warning(this.$t('art_multi_dir_warn'))
        } else {
          this.packageInput.db_rollback_directory = saveData
        }
      } else if (this.configFileTree.treeType === 103) {
        this.packageInput.db_upgrade_file_path = saveData
      } else if (this.configFileTree.treeType === 104) {
        this.packageInput.db_rollback_file_path = saveData
      } else if (this.configFileTree.treeType === 105) {
        this.packageInput.db_deploy_file_path = saveData
      } else if (this.configFileTree.treeType === 106) {
        this.packageInput.db_diff_conf_file = saveData
      } else if (this.configFileTree.treeType === 0.3) {
        if (saveData.length > 1) {
          this.$Message.warning(this.$t('art_multi_dir_warn'))
        } else {
          this.packageInput.log_file_directory = saveData
        }
      } else if (this.configFileTree.treeType === 0.4) {
        if (saveData.length > 1) {
          this.$Message.warning(this.$t('art_multi_dir_warn'))
        } else {
          this.packageInput.db_deploy_file_directory = saveData
        }
      } else if (this.configFileTree.treeType === 0.5) {
        if (saveData.length > 1) {
          this.$Message.warning(this.$t('art_multi_dir_warn'))
        } else {
          this.packageInput.db_diff_conf_directory = saveData
        }
      }
    },
    async configFileTreeLoadNode (item, callback) {
      if (item.isDir && !item.disabled) {
        let baselinePackage = this.packageInput.baseline_package
        if (item.comparisonResult === 'new') {
          baselinePackage = null
        }
        const { data } = await getFiles(this.guid, this.packageId, { baselinePackage: baselinePackage, fileList: [item.path], expandAll: false })
        let treeChild = this.formatConfigFileTree(data)
        if (item.comparisonResult === 'new') {
          treeChild.forEach(_ => {
            _.comparisonResult = 'new'
          })
        }
        callback(treeChild)
      } else {
        let emptyData = []
        callback(emptyData)
      }
    },
    formatConfigFileTree (data, checkNodes = null) {
      let dataString = JSON.stringify(data)
      let copyData = JSON.parse(dataString)
      let treeData = []
      checkNodes = checkNodes || []
      copyData.forEach(el => {
        this._formatConfigFileTreeNode(treeData, el, checkNodes)
      })
      return treeData
    },
    _formatConfigFileTreeNode (tree, element, checkNodes) {
      let children = element.children || []
      let treeNode = {
        title: element.name,
        disableCheckbox: this.isFileSelect ? !element.isDir : false,
        path: element.path,
        isDir: element.isDir,
        exists: element.exists,
        md5: element.md5,
        comparisonResult: element.comparisonResult
      }
      if (treeNode.isDir) {
        treeNode.expand = children.length > 0
        treeNode.loading = false
        treeNode.children = []
        treeNode.render = (h, params) => {
          if (params.data.comparisonResult === 'new') {
            return (
              <span>
                <img height="16" width="16" src={iconFolder} style="position:relative;top:3px;margin:0 3px;" />
                <span style="color: #19be6b;">
                  {params.data.title}
                  <span style="font-size:10px;padding-left:4px">[{params.data.comparisonResult}]</span>
                </span>
              </span>
            )
          } else if (params.data.comparisonResult === 'changed') {
            return (
              <span>
                <img height="16" width="16" src={iconFolder} style="position:relative;top:3px;margin:0 3px;" />
                <span style="color: #2d8cf0;">
                  {params.data.title}
                  <span style="font-size:10px;padding-left:4px">[{params.data.comparisonResult}]</span>
                </span>
              </span>
            )
          } else if (params.data.comparisonResult === 'deleted') {
            return (
              <span>
                <img height="16" width="16" src={iconFolder} style="position:relative;top:3px;margin:0 3px;" />
                <span style="color: #cccccc;">
                  {params.data.title}
                  <span style="font-size:10px;padding-left:4px">[{params.data.comparisonResult}]</span>
                </span>
              </span>
            )
          } else if (params.data.comparisonResult === 'same') {
            return (
              <span>
                <img height="16" width="16" src={iconFolder} style="position:relative;top:3px;margin:0 3px;" />
                <span>
                  {params.data.title}
                  <span style="font-size:10px;padding-left:4px">[{params.data.comparisonResult}]</span>
                </span>
              </span>
            )
          } else {
            return (
              <span>
                <img height="16" width="16" src={iconFolder} style="position:relative;top:3px;margin:0 3px;" />
                <span>{params.data.title}</span>
              </span>
            )
          }
        }
      } else {
        treeNode.render = (h, params) => {
          if (params.data.comparisonResult) {
            if (params.data.comparisonResult === 'new') {
              return (
                <span>
                  <img height="16" width="16" src={iconFile} style="position:relative;top:3px;margin:0 3px;" />
                  <span style="color: #19be6b;">
                    {params.data.title}
                    <span style="font-size:10px;padding-left:4px">[{params.data.comparisonResult}]</span>
                    <Button onClick={() => this.getCompareFile(params.data)} size="small" style="margin-left:8px" icon="ios-git-compare"></Button>
                  </span>
                </span>
              )
            } else if (params.data.comparisonResult === 'changed') {
              return (
                <span>
                  <img height="16" width="16" src={iconFile} style="position:relative;top:3px;margin:0 3px;" />
                  <span style="color: #2d8cf0;">
                    {params.data.title}
                    <span style="font-size:10px;padding-left:4px">[{params.data.comparisonResult}]</span>
                    <Button onClick={() => this.getCompareFile(params.data)} size="small" style="margin-left:8px" icon="ios-git-compare"></Button>
                  </span>
                </span>
              )
            } else if (params.data.comparisonResult === 'deleted') {
              return (
                <span>
                  <img height="16" width="16" src={iconFile} style="position:relative;top:3px;margin:0 3px;" />
                  <span style="color: #cccccc;">
                    {params.data.title}
                    <span style="font-size:10px;padding-left:4px">[{params.data.comparisonResult}]</span>
                  </span>
                </span>
              )
            } else {
              return (
                <span>
                  <img height="16" width="16" src={iconFile} style="position:relative;top:3px;margin:0 3px;" />
                  <span>
                    {params.data.title}
                    <span style="font-size:10px;padding-left:4px">[{params.data.comparisonResult}]</span>
                    <Button onClick={() => this.getCompareFile(params.data)} size="small" style="margin-left:8px" icon="ios-git-compare"></Button>
                  </span>
                </span>
              )
            }
          } else {
            if (params.data.comparisonResult === 'new') {
              return (
                <span>
                  <img height="16" width="16" src={iconFile} style="position:relative;top:3px;margin:0 3px;" />
                  <span style="color: #19be6b;">{params.data.title}</span>
                  <Button onClick={() => this.getCompareFile(params.data)} size="small" style="margin-left:8px" icon="ios-git-compare"></Button>
                </span>
              )
            } else if (params.data.comparisonResult === 'changed') {
              return (
                <span>
                  <img height="16" width="16" src={iconFile} style="position:relative;top:3px;margin:0 3px;" />
                  <span style="color: #2d8cf0;">{params.data.title}</span>
                  <Button onClick={() => this.getCompareFile(params.data)} size="small" style="margin-left:8px" icon="ios-git-compare"></Button>
                </span>
              )
            } else if (params.data.comparisonResult === 'deleted') {
              return (
                <span>
                  <img height="16" width="16" src={iconFile} style="position:relative;top:3px;margin:0 3px;" />
                  <span style="color: #cccccc;">{params.data.title}</span>
                </span>
              )
            } else {
              return (
                <span>
                  <img height="16" width="16" src={iconFile} style="position:relative;top:3px;margin:0 3px;" />
                  <span>{params.data.title}</span>
                  <Button onClick={() => this.getCompareFile(params.data)} size="small" style="margin-left:8px" icon="ios-git-compare"></Button>
                </span>
              )
            }
          }
        }
      }
      // if (checkNodes.indexOf(element.path) >= 0 && !treeNode.isDir) {
      if (checkNodes.indexOf(element.path) >= 0) {
        treeNode.checked = true
      }
      tree.push(treeNode)
      if (children.length > 0) {
        children.forEach(el => {
          this._formatConfigFileTreeNode(treeNode.children, el, checkNodes)
        })
      }
    },
    configFileTreeExpand (item) {
      // console.log('configFileTreeExpand', item)
    },
    async changeChildChecked (checkedList, item) {
      if (item.isDir && item.checked) {
        // 获取文件夹下的子列表
        if (!item.expand) {
          let baselinePackage = this.packageInput.baseline_package
          if (item.comparisonResult === 'new') {
            baselinePackage = null
          }
          const { data } = await getFiles(this.guid, this.packageId, { baselinePackage: baselinePackage, fileList: [item.path], expandAll: false })
          let children = this.formatConfigFileTree(data)
          if (item.comparisonResult === 'new') {
            children.forEach(_ => {
              _.comparisonResult = 'new'
            })
          }
          item.children = children.map(_ => {
            if (_.isDir) {
              _.checked = false
            } else {
              _.checked = item.checked
            }
            return _
          })
          item.expand = true
        }
      }
    },
    closeConfigFileTree () {
      this.isShowTreeModal = false
    },
    deleteFilePath (index, key) {
      this.packageInput[key].splice(index, 1)
    },
    addFilePath (key) {
      this.packageInput[key].push({
        comparisonResult: '',
        configKeyInfos: [],
        filename: '',
        isDir: false,
        md5: '',
        exists: false
      })
    },
    // 新增服务码
    addCodeStringMap () {
      this.packageInput.code_string_map.push({
        regulative: 0,
        source_value: '',
        target_value: ''
      })
    },
    // 删除服务码
    deleteCodeStringMap (index) {
      this.packageInput.code_string_map.splice(index, 1)
    },
    changeCodeStringMap (index) {
      this.packageInput.code_string_map[index].source_value = ''
      this.packageInput.code_string_map[index].target_value = ''
    },
    initTreeConfig (type) {
      this.configFileTree.treeType = type
      this.configFileTree.treeData = []
      this.toggleCheckFileTreeNew = ''
      this.toggleCheckFileTreeSame = ''
      this.toggleCheckFileTreeChanged = ''
      this.toggleCheckFileTreeDeleted = ''
    },
    closeFilesModal () {
      this.initPackageInput()
      this.openDrawer = false
    },
    async saveConfigFiles () {
      let obj = {
        package_type: this.packageType,
        baseline_package: this.packageInput.baseline_package || null,
        diff_conf_file: this.packageInput.diff_conf_file,
        start_file_path: this.packageInput.start_file_path,
        stop_file_path: this.packageInput.stop_file_path,
        deploy_file_path: this.packageInput.deploy_file_path,
        is_decompression: this.packageInput.is_decompression || 'true',

        db_diff_conf_file: this.packageInput.db_diff_conf_file,
        db_upgrade_directory: this.packageInput.db_upgrade_directory,
        db_rollback_directory: this.packageInput.db_rollback_directory,
        db_upgrade_file_path: this.packageInput.db_upgrade_file_path,
        db_rollback_file_path: this.packageInput.db_rollback_file_path,
        db_deploy_file_path: this.packageInput.db_deploy_file_path
      }
      this.saveConfigLoading = true
      let { status } = await updatePackage(this.guid, this.packageId, obj)
      this.saveConfigLoading = false
      if (status === 'OK') {
        this.openDrawer = false
        this.$Notice.success({
          title: this.$t('artifacts_successed')
        })
      }
      // await this.queryPackages()
      // await this.syncPackageDetail()
    }
  },
  components: {
    DisplayPath
  }
}
</script>

<style scoped lang="scss">
.custom-modal-header {
  line-height: 20px;
  font-size: 16px;
  color: #17233d;
  font-weight: 500;
  .fullscreen-icon {
    float: right;
    margin-right: 28px;
    font-size: 18px;
    cursor: pointer;
  }
}
</style>
<style lang="scss" scoped>
.textarea-dir {
  display: inline-block;
  width: 320px;
}
.textarea-input {
  display: inline-block;
  width: 480px;
}

.config-tab :deep(.ivu-tabs-nav) {
  width: 100%;
}
.config-tab :deep(.ivu-tabs-tab) {
  width: 15%;
  text-align: center;
}

.grid-container {
  border: 1px solid #e8eaec;
  padding: 10px;
}

.table-only-have-header ::v-deep tbody {
  display: none;
}
.table-only-have-header ::v-deep th {
  border-right: 1px solid #e8eaec;
}

/* 使用 CSS Grid 布局 */
.grid-row {
  display: grid;
  grid-template-columns: 100px 466px 700px;
  border-top: 1px solid #e8eaec;
}

.grid-cell {
  display: grid;
  align-items: center;
  padding: 4px;
  border-right: 1px solid #e8eaec;
}

.grid-cell:last-child {
  border-right: none;
}
</style>
