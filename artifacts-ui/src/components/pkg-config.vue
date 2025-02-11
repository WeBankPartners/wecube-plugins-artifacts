<template>
  <div>
    <Drawer :title="pkgName" :mask-closable="false" :closable="true" v-model="openDrawer" :scrollable="false" width="1300">
      <Spin size="large" fix v-if="spinShow"></Spin>
      <Form :label-width="120" class="pkg-config">
        <FormItem :label="$t('package_type')">
          <Select clearable :placeholder="$t('package_type')" v-model="packageType" @on-change="packageTypeChanged">
            <Option v-for="pkt in packageOptions" :value="pkt.value" :key="pkt.value">{{ pkt.label }}</Option>
          </Select>
        </FormItem>
        <FormItem :label="$t('baseline_package')">
          <Select clearable filterable :placeholder="$t('baseline_package')" @on-change="baseLinePackageChanged" @on-clear="clearBaseline" v-model="packageInput.baseline_package">
            <Option v-for="conf in baselinePackageOptions" :value="conf.guid" :key="conf.name">{{ conf.name }}</Option>
          </Select>
        </FormItem>
        <FormItem :label="$t('is_decompression')">
          <i-switch v-model="packageInput.is_decompression" />
        </FormItem>
      </Form>
      <Tabs v-if="!['IMAGE', 'RULE'].includes(packageType)" :value="currentConfigTab" class="config-tab" @on-click="changeCurrentConfigTab">
        <TabPane :disabled="disableAppCard" :label="$t('APP')" name="APP">
          <div class="tab-content">
            <div style="border:1px solid #e8eaec;">
              <Table :columns="columns" :data="[]" size="small" class="table-only-have-header"></Table>
              <!-- 差异化配置文件 -->
              <div class="grid-row">
                <div class="grid-cell">
                  {{ $t('artifacts_config_files') }}
                </div>
                <div class="grid-cell">
                  <div>
                    <Tooltip :content="$t('art_select_directory')" placement="top">
                      <Icon type="ios-folder" size="16" color="white" class="ios-folder-upload" @click="() => showTreeModal(0.1, packageInput.diff_conf_directory || [])" />
                    </Tooltip>
                    <div id="diff_conf_directory_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.diff_conf_directory" :key="index">
                        <Input class="textarea-dir" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.diff_conf_directory[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="false"></DisplayPath>
                        <Button size="small" type="error" style="margin-left:4px" icon="md-trash" ghost @click="deleteFilePath(index, 'diff_conf_directory')"></Button>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="grid-cell">
                  <div style="display: flex;align-items: flex-start;">
                    <div style="width: 100px;margin-right: 8px;text-align: end;">
                      <Tooltip :content="$t('artifacts_select_file')" placement="top">
                        <Icon type="md-document" style="margin-right: 12px;" size="16" color="white" class="ios-doc-upload" @click="() => showTreeModal(0, packageInput.diff_conf_file || [])" />
                      </Tooltip>
                    </div>
                    <div id="diff_conf_file_test">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.diff_conf_file" :key="index">
                        <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.diff_conf_file[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="true"></DisplayPath>
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
                      <Icon type="ios-folder" size="16" color="white" class="ios-folder-upload" @click="() => showTreeModal(0.2, packageInput.script_file_directory || [])" />
                    </Tooltip>
                    <div id="script_file_directory_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.script_file_directory" :key="index">
                        <Input class="textarea-dir" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.script_file_directory[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="false"></DisplayPath>
                        <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'script_file_directory')"></Button>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="grid-cell">
                  <!-- 启动脚本 -->
                  <div style="display: flex;align-items: flex-start;margin: 2px 0">
                    <div style="width: 100px;margin-right: 8px;">
                      <span style="margin-right: 8px">{{ $t('artifacts_start_script') }}</span>
                      <Tooltip :content="$t('artifacts_select_file')" placement="top">
                        <Icon type="md-document" size="16" color="white" class="ios-doc-upload" @click="() => showTreeModal(1, packageInput.start_file_path || [])" />
                      </Tooltip>
                    </div>
                    <div id="start_file_path_test">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.start_file_path" :key="index">
                        <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.start_file_path[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="true"></DisplayPath>
                        <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'start_file_path')"></Button>
                      </div>
                    </div>
                  </div>
                  <!-- 停止脚本 -->
                  <div style="display: flex;align-items: flex-start;margin: 2px 0">
                    <div style="width: 100px;margin-right: 8px;">
                      <span style="margin-right: 8px">{{ $t('artifacts_stop_script') }}</span>
                      <Tooltip :content="$t('artifacts_select_file')" placement="top">
                        <Icon type="md-document" size="16" color="white" class="ios-doc-upload" @click="() => showTreeModal(2, packageInput.stop_file_path || [])" />
                      </Tooltip>
                    </div>
                    <div id="stop_file_path_test">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.stop_file_path" :key="index">
                        <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.stop_file_path[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="true"></DisplayPath>
                        <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'stop_file_path')"></Button>
                      </div>
                    </div>
                  </div>
                  <!-- 部署脚本 -->
                  <div style="display: flex;align-items: flex-start;margin: 2px 0">
                    <div style="width: 100px;margin-right: 8px;">
                      <span style="margin-right: 8px">{{ $t('artifacts_deploy_script') }}</span>
                      <Tooltip :content="$t('artifacts_select_file')" placement="top">
                        <Icon type="md-document" size="16" color="white" class="ios-doc-upload" @click="() => showTreeModal(3, packageInput.deploy_file_path || [])" />
                      </Tooltip>
                    </div>
                    <div id="deploy_file_path_test">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.deploy_file_path" :key="index">
                        <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.deploy_file_path[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="true"></DisplayPath>
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
                      <Icon type="ios-folder" size="16" color="white" class="ios-folder-upload" @click="() => showTreeModal(0.3, packageInput.log_file_directory || [])" />
                    </Tooltip>
                    <div id="log_file_directory_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.log_file_directory" :key="index">
                        <Input class="textarea-dir" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" v-model="packageInput.log_file_directory[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="false"></DisplayPath>
                        <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'log_file_directory')"></Button>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="grid-cell">
                  <div style="display: flex;align-items: flex-start;margin: 2px">
                    <div style="width: 100px; margin-right: 8px">{{ $t('art_business_metric_log') }}</div>
                    <div id="log_file_trade_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.log_file_trade" :key="index">
                        <Input class="textarea-input" :rows="1" :placeholder="$t('art_enter_log_path')" type="textarea" v-model="packageInput.log_file_trade[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="false"></DisplayPath>
                        <Button style="margin-left:20px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'log_file_trade')"></Button>
                      </div>
                    </div>
                    <Button style="margin: 4px" size="small" type="success" icon="md-add" ghost @click="addFilePath('log_file_trade')"></Button>
                  </div>
                  <div style="display: flex;align-items: flex-start;margin: 2px">
                    <div style="width: 100px; margin-right: 8px">{{ $t('art_keyword_log') }}</div>
                    <div id="log_file_keyword_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.log_file_keyword" :key="index">
                        <Input class="textarea-input" :rows="1" :placeholder="$t('art_enter_log_path')" type="textarea" v-model="packageInput.log_file_keyword[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="false"></DisplayPath>
                        <Button style="margin-left:20px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'log_file_keyword')"></Button>
                      </div>
                    </div>
                    <Button style="margin: 4px" size="small" type="success" icon="md-add" ghost @click="addFilePath('log_file_keyword')"></Button>
                  </div>
                  <div style="display: flex;align-items: flex-start;margin: 2px">
                    <div style="width: 100px; margin-right: 8px">{{ $t('art_metric_log') }}</div>
                    <div id="log_file_metric_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.log_file_metric" :key="index">
                        <Input class="textarea-input" :rows="1" :placeholder="$t('art_enter_log_path')" type="textarea" v-model="packageInput.log_file_metric[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="false"></DisplayPath>
                        <Button style="margin-left:20px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'log_file_metric')"></Button>
                      </div>
                    </div>
                    <Button style="margin: 4px" size="small" type="success" icon="md-add" ghost @click="addFilePath('log_file_metric')"></Button>
                  </div>
                  <div style="display: flex;align-items: flex-start;margin: 2px">
                    <div style="width: 100px; margin-right: 8px">{{ $t('art_trace_log') }}</div>
                    <div id="log_file_trace_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.log_file_trace" :key="index">
                        <Input class="textarea-input" :rows="1" :placeholder="$t('art_enter_log_path')" type="textarea" v-model="packageInput.log_file_trace[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="false"></DisplayPath>
                        <Button style="margin-left:20px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'log_file_trace')"></Button>
                      </div>
                    </div>
                    <Button style="margin: 4px" size="small" type="success" icon="md-add" ghost @click="addFilePath('log_file_trace')"></Button>
                  </div>
                </div>
              </div>
            </div>
            <!-- 升级清理目录 -->
            <div style="display: flex;align-items: flex-start;border: 1px solid #e8e8e8;padding: 8px 4px;margin-top: 12px;">
              <div style="width: 160px; margin-right: 8px">
                {{ $t('art_upgrade_and_clean_up') }}
                <Tooltip :content="$t('art_upgrade_and_clean_up_select')" placement="top">
                  <Icon type="md-document" style="margin-right: 12px;" size="16" color="white" class="ios-doc-upload" @click="() => showTreeModal(107, packageInput.upgrade_cleanup_file_path || [])" />
                </Tooltip>
              </div>
              <div id="upgrade_and_clean_up_test" style="display: inline-block;">
                <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.upgrade_cleanup_file_path" :key="index">
                  <Input class="textarea-input" :rows="1" :placeholder="$t('art_upgrade_and_clean_up')" type="textarea" v-model="packageInput.upgrade_cleanup_file_path[index].filename" />
                  <Button style="margin-left:20px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'upgrade_cleanup_file_path')"></Button>
                </div>
              </div>
              <Button style="margin: 4px" size="small" type="success" icon="md-add" ghost @click="addFilePath('upgrade_cleanup_file_path')"></Button>
            </div>

            <!-- 关键交易服务码 -->
            <div style="margin-top: 16px;" v-if="isShowKeyServiceCode">
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
                  <Row v-for="(item, itemIndex) in packageInput.key_service_code" :key="itemIndex" style="margin:6px 0;">
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
          </div>
        </TabPane>
        <TabPane :disabled="disableDBCard" :label="$t('DB')" name="DB">
          <div class="tab-content">
            <div style="border:1px solid #e8eaec;">
              <Table :columns="columns" :data="[]" size="small" class="table-only-have-header"></Table>
              <!-- 升级脚本 -->
              <div class="grid-row">
                <div class="grid-cell">
                  {{ $t('db_upgrade_file_path') }}
                </div>
                <div class="grid-cell">
                  <div>
                    <Tooltip :content="$t('art_select_directory')" placement="top">
                      <Icon type="ios-folder" size="16" color="white" class="ios-folder-upload" @click="() => showTreeModal(101, packageInput.db_upgrade_directory || [])" />
                    </Tooltip>
                    <div id="db_upgrade_directory_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_upgrade_directory" :key="index">
                        <Input class="textarea-dir" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_upgrade_directory[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="false"></DisplayPath>
                        <Button size="small" type="error" style="margin-left:4px" icon="md-trash" ghost @click="deleteFilePath(index, 'db_upgrade_directory')"></Button>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="grid-cell">
                  <div style="display: flex;align-items: flex-start;">
                    <Tooltip :content="$t('artifacts_select_file')" placement="top">
                      <Icon type="md-document" size="16" color="white" class="ios-doc-upload" @click="() => showTreeModal(103, packageInput.db_upgrade_file_path || [])" />
                    </Tooltip>
                    <div id="db_upgrade_file_path_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_upgrade_file_path" :key="index">
                        <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_upgrade_file_path[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="true"></DisplayPath>
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
                      <Icon type="ios-folder" size="16" color="white" class="ios-folder-upload" @click="() => showTreeModal(102, packageInput.db_rollback_directory || [])" />
                    </Tooltip>
                    <div id="db_rollback_directory_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_rollback_directory" :key="index">
                        <Input class="textarea-dir" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_rollback_directory[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="false"></DisplayPath>
                        <Button size="small" type="error" style="margin-left:4px" icon="md-trash" ghost @click="deleteFilePath(index, 'db_rollback_directory')"></Button>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="grid-cell">
                  <div style="display: flex;align-items: flex-start;">
                    <Tooltip :content="$t('artifacts_select_file')" placement="top">
                      <Icon type="md-document" size="16" color="white" class="ios-doc-upload" @click="() => showTreeModal(104, packageInput.db_rollback_file_path || [])" />
                    </Tooltip>
                    <div id="db_rollback_file_path_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_rollback_file_path" :key="index">
                        <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_rollback_file_path[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="true"></DisplayPath>
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
                      <Icon type="ios-folder" size="16" color="white" class="ios-folder-upload" @click="() => showTreeModal(0.4, packageInput.db_deploy_file_directory || [])" />
                    </Tooltip>
                    <div id="db_deploy_file_directory_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_deploy_file_directory" :key="index">
                        <Input class="textarea-dir" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_deploy_file_directory[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="false"></DisplayPath>
                        <Button size="small" type="error" style="margin-left:4px" icon="md-trash" ghost @click="deleteFilePath(index, 'db_deploy_file_directory')"></Button>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="grid-cell">
                  <div style="display: flex;align-items: flex-start;">
                    <Tooltip :content="$t('artifacts_select_file')" placement="top">
                      <Icon type="md-document" size="16" color="white" class="ios-doc-upload" @click="() => showTreeModal(105, packageInput.db_deploy_file_path || [])" />
                    </Tooltip>
                    <div id="db_deploy_file_path_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_deploy_file_path" :key="index">
                        <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_deploy_file_path[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="true"></DisplayPath>
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
                      <Icon type="ios-folder" size="16" color="white" class="ios-folder-upload" @click="() => showTreeModal(0.5, packageInput.db_diff_conf_directory || [])" />
                    </Tooltip>
                    <div id="db_diff_conf_directory_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_diff_conf_directory" :key="index">
                        <Input class="textarea-dir" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_diff_conf_directory[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="false"></DisplayPath>
                        <Button size="small" type="error" style="margin-left:4px" icon="md-trash" ghost @click="deleteFilePath(index, 'db_diff_conf_directory')"></Button>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="grid-cell">
                  <div style="display: flex;align-items: flex-start;">
                    <Tooltip :content="$t('artifacts_select_file')" placement="top">
                      <Icon type="md-document" size="16" color="white" class="ios-doc-upload" @click="() => showTreeModal(106, packageInput.db_diff_conf_file || [])" />
                    </Tooltip>
                    <div id="db_diff_conf_file_test" style="display: inline-block;">
                      <div style="margin-bottom: 5px" v-for="(file, index) in packageInput.db_diff_conf_file" :key="index">
                        <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" disabled v-model="packageInput.db_diff_conf_file[index].filename" />
                        <DisplayPath :file="file" :canBeMoved="true"></DisplayPath>
                        <Button style="margin-left:4px" size="small" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'db_diff_conf_file')"></Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </TabPane>
      </Tabs>
      <div class="drawer-footer">
        <Button @click="closeFilesModal" style="margin-right: 8px">{{ $t('artifacts_cancel') }}</Button>
        <Button @click="saveConfigFiles" type="primary">{{ $t('artifacts_save') }}</Button>
      </div>
    </Drawer>
    <!-- 包配置文件选择 -->
    <Modal :styles="{ top: '60px' }" :mask-closable="false" v-model="isShowTreeModal" :title="configFileTreeTitle" draggable width="700">
      <CheckboxGroup v-if="packageInput.baseline_package">
        <Button :style="toggleCheckFileTreeNew" type="dashed" size="small" @click="checkConfigFileTreeVis('new')"><span style="color: #18b566">new</span></Button>
        <Button :style="toggleCheckFileTreeSame" type="dashed" size="small" @click="checkConfigFileTreeVis('same')"><span>same</span></Button>
        <Button :style="toggleCheckFileTreeChanged" type="dashed" size="small" @click="checkConfigFileTreeVis('changed')"><span style="color: #5384FF">changed</span></Button>
        <Button :style="toggleCheckFileTreeDeleted" type="dashed" size="small" @click="checkConfigFileTreeVis('deleted')"><span style="color: #cccccc">deleted</span></Button>
      </CheckboxGroup>
      <div style="height: 450px; overflow-y: auto">
        <Tree ref="configTree" :multiple="false" :check-strictly="isFileSelect" :data="configFileTree.treeData" :load-data="configFileTreeLoadNode" @on-toggle-expand="configFileTreeExpand" @on-check-change="changeChildChecked" show-checkbox> </Tree>
      </div>
      <div class="drawer-footer">
        <Button @click="closeConfigFileTree" style="margin-right: 8px">{{ $t('artifacts_cancel') }}</Button>
        <Button @click="saveConfigFileTree" type="primary">{{ $t('artifacts_save') }}</Button>
      </div>
    </Modal>
    <Modal :z-index="9999" width="1200" v-model="showFileCompare" :fullscreen="fullscreen" footer-hide>
      <p slot="header">
        <span>{{ $t('file_compare') }}</span>
        <Icon v-if="!fullscreen" @click="zoomModalMax" class="header-icon" type="ios-expand" />
        <Icon v-else @click="zoomModalMin" class="header-icon" type="ios-contract" />
      </p>
      <CompareFile ref="compareParams" :fileContentHeight="fileContentHeight"></CompareFile>
    </Modal>
  </div>
</template>

<script>
import { compareBaseLineFiles, getCompareContent, getFiles, getPackageDetail, queryPackages, updatePackage } from '@/api/server.js'
import iconFile from '@/assets/file.png'
import iconFolder from '@/assets/folder.png'
import CompareFile from '@/views/compare-file.vue'
import DisplayPath from '@/views/display-path.vue'
import Sortable from 'sortablejs'
// 业务运行实例ciTypeId
const defaultAppRootCiTypeId = 'app_instance'
const defaultDBRootCiTypeId = 'rdb_instance'
export default {
  name: '',
  data () {
    return {
      spinShow: false,
      showFileCompare: false,
      compareParams: {
        originContent: '',
        newContent: ''
      },
      fullscreen: false,
      fileContentHeight: window.screen.availHeight * 0.4 + 'px',
      pkgName: '', // 当前选中的包名
      isFileSelect: false, // 是否选择文件 适配文件夹和文件二选一场景
      isFileAndFolderSelectable: false, // 适配文件夹和文件都可选场景
      isShowKeyServiceCode: false,
      columns: [
        {
          title: this.$t('artifacts_configuration'),
          key: 'name',
          width: 120
        },
        {
          title: this.$t('art_directory'),
          key: 'age',
          width: 446
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
      packageOptions: [
        { label: this.$t('APP&DB'), value: 'APP&DB', num: 0 },
        { label: this.$t('APP'), value: 'APP', num: 0 },
        { label: this.$t('DB'), value: 'DB', num: 0 },
        { label: this.$t('IMAGE'), value: 'IMAGE', num: 0 },
        { label: this.$t('RULE'), value: 'RULE', num: 0 }
      ],
      constPackageOptions: {
        db: 'DB',
        app: 'APP',
        mixed: 'APP&DB',
        image: 'IMAGE',
        rule: 'RULE'
      },
      oriPackageInput: {},
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
        key_service_code: [], // 关键交易服务码
        is_decompression: true,

        db_diff_conf_directory: [], // DB差异化变量
        db_diff_conf_file: [],
        db_upgrade_directory: [], // DB升级脚本
        db_upgrade_file_path: [],
        db_rollback_directory: [], // DB回滚脚本
        db_rollback_file_path: [],
        db_deploy_file_directory: [], // DB部署脚本
        db_deploy_file_path: [],

        upgrade_cleanup_file_path: [] // 升级清理目录
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
        key_service_code: [], // 关键交易服务码
        is_decompression: true,

        db_diff_conf_directory: [], // DB差异化变量
        db_diff_conf_file: [],
        db_upgrade_directory: [], // DB升级脚本
        db_upgrade_file_path: [],
        db_rollback_directory: [], // DB回滚脚本
        db_rollback_file_path: [],
        db_deploy_file_directory: [], // DB部署脚本
        db_deploy_file_path: [],

        upgrade_cleanup_file_path: [] // 升级清理目录
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
  watch: {
    'packageInput.log_file_trade': {
      handler (newVal, oldVal) {
        let needShow = newVal.filter(item => item.filename !== '').length > 0
        if (this.isShowKeyServiceCode !== needShow) {
          this.packageInput.key_service_code = []
          this.isShowKeyServiceCode = needShow
        }
      },
      deep: true
    }
  },
  computed: {
    disableAddCodeStringMap () {
      let res = this.packageInput.key_service_code.some(item => item.source_value === '' || item.target_value === '')
      return res
    },
    disableAppCard () {
      return this.packageType === this.constPackageOptions.db
    },
    disableDBCard () {
      return this.packageType === this.constPackageOptions.app
    }
  },
  methods: {
    zoomModalMax () {
      this.fileContentHeight = window.screen.availHeight - 310 + 'px'
      this.fullscreen = true
    },
    zoomModalMin () {
      this.fileContentHeight = window.screen.availHeight * 0.4 + 'px'
      this.fullscreen = false
    },
    packageTypeChanged (val) {
      let toTab = ''
      if (val === 'APP') {
        toTab = 'APP'
      } else if (val === 'DB') {
        toTab = 'DB'
      } else if (val === 'APP&DB') {
        toTab = 'APP'
      }
      this.currentConfigTab = toTab
      this.getbaselinePkg()
    },
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
      this.openDrawer = true
      this.spinShow = true
      this.pkgName = `${row.key_name} - ${this.$t('artifacts_script_configuration')}`
      this.guid = guid
      this.packageId = row.guid
      await this.syncPackageDetail()
      this.packageType = row.package_type || this.constPackageOptions.mixed
      this.currentConfigTab = this.packageType === this.constPackageOptions.db ? this.constPackageOptions.db : this.constPackageOptions.app
      // 以下4个变量类型为字符串
      // row从table数据中来，此时baseline_package为对象
      this.packageInput.diff_conf_directory = JSON.parse(JSON.stringify(this.packageDetail.diff_conf_directory || []))
      this.packageInput.diff_conf_file = JSON.parse(JSON.stringify(this.packageDetail.diff_conf_file))
      this.packageInput.script_file_directory = JSON.parse(JSON.stringify(this.packageDetail.script_file_directory || []))
      this.packageInput.start_file_path = JSON.parse(JSON.stringify(this.packageDetail.start_file_path))
      this.packageInput.stop_file_path = JSON.parse(JSON.stringify(this.packageDetail.stop_file_path))
      this.packageInput.deploy_file_path = JSON.parse(JSON.stringify(this.packageDetail.deploy_file_path))
      this.packageInput.log_file_directory = JSON.parse(JSON.stringify(this.packageDetail.log_file_directory))
      this.packageInput.log_file_trade = JSON.parse(JSON.stringify(this.packageDetail.log_file_trade))
      this.packageInput.log_file_keyword = JSON.parse(JSON.stringify(this.packageDetail.log_file_keyword))
      this.packageInput.log_file_metric = JSON.parse(JSON.stringify(this.packageDetail.log_file_metric))
      this.packageInput.log_file_trace = JSON.parse(JSON.stringify(this.packageDetail.log_file_trace))

      this.packageInput.is_decompression = row.is_decompression === 'true'

      this.packageInput.db_diff_conf_directory = JSON.parse(JSON.stringify(this.packageDetail.db_diff_conf_directory))
      this.packageInput.db_diff_conf_file = JSON.parse(JSON.stringify(this.packageDetail.db_diff_conf_file))
      this.packageInput.db_upgrade_directory = JSON.parse(JSON.stringify(this.packageDetail.db_upgrade_directory))
      this.packageInput.db_upgrade_file_path = JSON.parse(JSON.stringify(this.packageDetail.db_upgrade_file_path))
      this.packageInput.db_rollback_directory = JSON.parse(JSON.stringify(this.packageDetail.db_rollback_directory))
      this.packageInput.db_rollback_file_path = JSON.parse(JSON.stringify(this.packageDetail.db_rollback_file_path))
      this.packageInput.db_deploy_file_directory = JSON.parse(JSON.stringify(this.packageDetail.db_deploy_file_directory))
      this.packageInput.db_deploy_file_path = JSON.parse(JSON.stringify(this.packageDetail.db_deploy_file_path))
      this.packageInput.upgrade_cleanup_file_path =
        this.packageDetail.upgrade_cleanup_file_path.length === 0
          ? [
              {
                comparisonResult: '',
                configKeyInfos: [],
                filename: '',
                isDir: false,
                md5: '',
                exists: false
              }
            ]
          : JSON.parse(JSON.stringify(this.packageDetail.upgrade_cleanup_file_path))

      this.$nextTick(() => {
        this.packageInput.key_service_code = JSON.parse(JSON.stringify(this.packageDetail.key_service_code))
      })
      this.hideFooter = hideFooter
      await this.getbaselinePkg()
      this.packageInput.baseline_package = this.packageDetail.baseline_package ? this.packageDetail.baseline_package : ''
      this.packageId = row.guid
      this.oriPackageInput = JSON.parse(JSON.stringify(this.packageInput))
      this.spinShow = false
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
        this.packageInput.diff_conf_directory = JSON.parse(JSON.stringify(data.diff_conf_directory || []))
        this.packageInput.diff_conf_file = JSON.parse(JSON.stringify(data.diff_conf_file || []))
        this.packageInput.script_file_directory = JSON.parse(JSON.stringify(data.script_file_directory || []))
        this.packageInput.start_file_path = JSON.parse(JSON.stringify(data.start_file_path || []))
        this.packageInput.stop_file_path = JSON.parse(JSON.stringify(data.stop_file_path || []))
        this.packageInput.deploy_file_path = JSON.parse(JSON.stringify(data.deploy_file_path || []))
        this.packageInput.log_file_directory = JSON.parse(JSON.stringify(data.log_file_directory || []))
        this.packageInput.log_file_trade = JSON.parse(JSON.stringify(data.log_file_trade || []))
        this.packageInput.log_file_keyword = JSON.parse(JSON.stringify(data.log_file_keyword || []))
        this.packageInput.log_file_metric = JSON.parse(JSON.stringify(data.log_file_metric || []))
        this.packageInput.log_file_trace = JSON.parse(JSON.stringify(data.log_file_trace || []))

        this.packageInput.is_decompression = data.is_decompression === 'true'

        this.packageInput.db_diff_conf_directory = JSON.parse(JSON.stringify(data.db_diff_conf_directory || []))
        this.packageInput.db_diff_conf_file = JSON.parse(JSON.stringify(data.db_diff_conf_file || []))
        this.packageInput.db_upgrade_directory = JSON.parse(JSON.stringify(data.db_upgrade_directory || []))
        this.packageInput.db_upgrade_file_path = JSON.parse(JSON.stringify(data.db_upgrade_file_path || []))
        this.packageInput.db_rollback_directory = JSON.parse(JSON.stringify(data.db_rollback_directory || []))
        this.packageInput.db_rollback_file_path = JSON.parse(JSON.stringify(data.db_rollback_file_path || []))
        this.packageInput.db_deploy_file_directory = JSON.parse(JSON.stringify(data.db_deploy_file_directory || []))
        this.packageInput.db_deploy_file_path = JSON.parse(JSON.stringify(data.db_deploy_file_path || []))
        this.packageInput.upgrade_cleanup_file_path =
          this.packageDetail.upgrade_cleanup_file_path.length === 0
            ? [
                {
                  comparisonResult: '',
                  configKeyInfos: [],
                  filename: '',
                  isDir: false,
                  md5: '',
                  exists: false
                }
              ]
            : JSON.parse(JSON.stringify(this.packageDetail.upgrade_cleanup_file_path))

        this.$nextTick(() => {
          this.packageInput.key_service_code = JSON.parse(JSON.stringify(data.key_service_code || []))
        })
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
    clearBaseline () {
      const packageInput = JSON.parse(JSON.stringify(this.oriPackageInput))
      this.packageInput = packageInput
      this.packageInput.baseline_package = ''
      this.$nextTick(() => {
        this.packageInput.key_service_code = packageInput.key_service_code || []
      })
    },
    async baseLinePackageChanged (v) {
      if (v) {
        const found = JSON.parse(JSON.stringify(this.baselinePackageOptions.find(row => row.guid === v)))
        this.packageType = found.package_type
        this.packageInput.diff_conf_directory = found.diff_conf_directory ? JSON.parse(JSON.stringify(found.diff_conf_directory)) : []
        this.packageInput.diff_conf_file = found.diff_conf_file ? JSON.parse(JSON.stringify(found.diff_conf_file)) : []
        this.packageInput.script_file_directory = found.script_file_directory ? JSON.parse(JSON.stringify(found.script_file_directory)) : []
        this.packageInput.start_file_path = found.start_file_path ? JSON.parse(JSON.stringify(found.start_file_path)) : []
        this.packageInput.stop_file_path = found.stop_file_path ? JSON.parse(JSON.stringify(found.stop_file_path)) : []
        this.packageInput.deploy_file_path = found.deploy_file_path ? JSON.parse(JSON.stringify(found.deploy_file_path)) : []
        this.packageInput.is_decompression = found.is_decompression === 'true'
        this.packageInput.log_file_directory = found.log_file_directory ? JSON.parse(JSON.stringify(found.log_file_directory)) : []
        this.packageInput.log_file_trade = found.log_file_trade ? JSON.parse(JSON.stringify(found.log_file_trade)) : []
        this.packageInput.log_file_keyword = found.log_file_keyword ? JSON.parse(JSON.stringify(found.log_file_keyword)) : []
        this.packageInput.log_file_metric = found.log_file_metric ? JSON.parse(JSON.stringify(found.log_file_metric)) : []
        this.packageInput.log_file_trace = found.log_file_trace ? JSON.parse(JSON.stringify(found.log_file_trace)) : []

        this.packageInput.db_diff_conf_directory = found.db_diff_conf_directory ? JSON.parse(JSON.stringify(found.db_diff_conf_directory)) : []
        this.packageInput.db_diff_conf_file = found.db_diff_conf_file ? JSON.parse(JSON.stringify(found.db_diff_conf_file)) : []
        this.packageInput.db_upgrade_directory = found.db_upgrade_directory ? JSON.parse(JSON.stringify(found.db_upgrade_directory)) : []
        this.packageInput.db_upgrade_file_path = []
        this.packageInput.db_rollback_directory = found.db_rollback_directory ? JSON.parse(JSON.stringify(found.db_rollback_directory)) : []
        this.packageInput.db_rollback_file_path = []
        this.packageInput.db_deploy_file_directory = found.db_deploy_file_directory ? JSON.parse(JSON.stringify(found.db_deploy_file_directory)) : []
        this.packageInput.db_deploy_file_path = found.db_deploy_file_path ? JSON.parse(JSON.stringify(found.db_deploy_file_path)) : []
        this.packageInput.upgrade_cleanup_file_path = found.upgrade_cleanup_file_path
          ? JSON.parse(JSON.stringify(found.upgrade_cleanup_file_path))
          : [
              {
                comparisonResult: '',
                configKeyInfos: [],
                filename: '',
                isDir: false,
                md5: '',
                exists: false
              }
            ]
        this.$nextTick(() => {
          this.packageInput.key_service_code = found.key_service_code ? JSON.parse(JSON.stringify(found.key_service_code)) : []
        })
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
        key_service_code: [], // 关键交易服务码
        is_decompression: true,

        db_diff_conf_directory: [], // DB差异化变量
        db_diff_conf_file: [],
        db_upgrade_directory: [], // DB升级脚本
        db_upgrade_file_path: [],
        db_rollback_directory: [], // DB回滚脚本
        db_rollback_file_path: [],
        db_deploy_file_directory: [], // DB部署脚本
        db_deploy_file_path: [],

        upgrade_cleanup_file_path: [] // 升级清理目录
      }
    },
    // 获取基线列表
    async getbaselinePkg () {
      this.packageInput.baseline_package = ''
      this.baselinePackageOptions = []
      // resultColumns: ['guid', 'name', 'package_type', 'diff_conf_file', 'start_file_path', 'stop_file_path', 'deploy_file_path', 'is_decompression', 'db_diff_conf_file', 'db_upgrade_directory', 'db_rollback_directory', 'db_deploy_file_path', 'db_upgrade_file_path', 'db_rollback_file_path'],
      let { status, data } = await queryPackages(this.guid, {
        sorting: {
          asc: false,
          field: 'upload_time'
        },
        filters: [
          {
            name: 'guid',
            operator: 'ne',
            value: this.packageId
          },
          {
            name: 'package_type',
            operator: 'eq',
            value: this.packageType
          }
        ],
        paging: true,
        pageable: {
          pageSize: 1000,
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
      this.isFileSelect = false
      this.isFileAndFolderSelectable = false
      let queryFiles = []
      let queryFilesParent = []
      if (type === 0) {
        this.configFileTreeTitle = this.$t('artifacts_config_files')
        queryFiles = this.packageInput.diff_conf_file.map(_ => _.filename)
        queryFilesParent = this.packageInput.diff_conf_directory.map(_ => _.filename)
      } else if (type === 0.1) {
        this.isFileSelect = true
        this.configFileTreeTitle = this.$t('artifacts_config_files')
        queryFiles = this.packageInput.diff_conf_directory.map(_ => _.filename)
      } else if (type === 0.2) {
        this.isFileSelect = true
        this.configFileTreeTitle = this.$t('art_script')
        queryFiles = this.packageInput.script_file_directory.map(_ => _.filename)
      } else if (type === 1) {
        this.configFileTreeTitle = this.$t('artifacts_select_start_script')
        queryFiles = this.packageInput.start_file_path.map(_ => _.filename)
        queryFilesParent = this.packageInput.script_file_directory.map(_ => _.filename)
      } else if (type === 2) {
        this.configFileTreeTitle = this.$t('artifacts_select_stop_script')
        queryFiles = this.packageInput.stop_file_path.map(_ => _.filename)
        queryFilesParent = this.packageInput.script_file_directory.map(_ => _.filename)
      } else if (type === 3) {
        this.configFileTreeTitle = this.$t('artifacts_select_deploy_script')
        queryFiles = this.packageInput.deploy_file_path.map(_ => _.filename)
        queryFilesParent = this.packageInput.script_file_directory.map(_ => _.filename)
      } else if (type === 0.4) {
        this.isFileSelect = true
        this.configFileTreeTitle = this.$t('art_initial_deployment_script')
        queryFiles = this.packageInput.db_deploy_file_directory.map(_ => _.filename)
      } else if (type === 0.5) {
        this.isFileSelect = true
        this.configFileTreeTitle = this.$t('artifacts_config_files')
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
        queryFilesParent = this.packageInput.db_upgrade_directory.map(_ => _.filename)
      } else if (type === 104) {
        this.configFileTreeTitle = this.$t('db_rollback_file_path')
        queryFiles = this.packageInput.db_rollback_file_path.map(_ => _.filename)
        queryFilesParent = this.packageInput.db_rollback_directory.map(_ => _.filename)
      } else if (type === 105) {
        this.configFileTreeTitle = this.$t('art_initial_deployment_script')
        queryFiles = this.packageInput.db_deploy_file_path.map(_ => _.filename)
        queryFilesParent = this.packageInput.db_deploy_file_directory.map(_ => _.filename)
      } else if (type === 106) {
        this.configFileTreeTitle = this.$t('artifacts_config_files')
        queryFiles = this.packageInput.db_diff_conf_file.map(_ => _.filename)
        queryFilesParent = this.packageInput.db_diff_conf_directory.map(_ => _.filename)
      } else if (type === 107) {
        this.isFileSelect = true
        this.isFileAndFolderSelectable = true
        this.configFileTreeTitle = this.$t('art_upgrade_and_clean_up')
        queryFiles = this.packageInput.upgrade_cleanup_file_path.map(_ => _.filename)
        // queryFilesParent = this.packageInput.db_diff_conf_directory.map(_ => _.filename)
      } else if (type === 0.3) {
        this.isFileSelect = true
        this.configFileTreeTitle = this.$t('art_log')
        queryFiles = this.packageInput.log_file_directory.map(_ => _.filename)
      }
      const { data } = await getFiles(this.guid, this.packageId, {
        baselinePackage: this.packageInput.baseline_package,
        fileList: queryFiles.length > 0 ? queryFiles : queryFilesParent,
        expandAll: true
      })
      this.configFileTree.treeData = this.formatConfigFileTree(data, queryFiles)
      // 填补最后一级数据
      if (queryFiles.length === 0 && queryFilesParent.length === 1) {
        const nodeNeedExpand = this.findNodeByPath(this.configFileTree.treeData, queryFilesParent[0])
        nodeNeedExpand && this.expendLast(nodeNeedExpand)
      }
      this.isShowTreeModal = true
    },
    // 找出需要展开的节点
    findNodeByPath (tree, targetPath) {
      for (let node of tree) {
        if (node.path === targetPath) {
          return node
        } else if (node.children && node.children.length > 0) {
          const result = this.findNodeByPath(node.children, targetPath)
          if (result) return result
        }
      }
      return null
    },
    // 获取最后一级数据
    async expendLast (item) {
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
        this.configFileTree.treeData = this.replaceChildrenWithChild(this.configFileTree.treeData, item.path, treeChild)
      }
    },
    // 将最后一级数据添加进结构
    replaceChildrenWithChild (tree, targetPath, newChildren) {
      tree.forEach(node => {
        if (node.path === targetPath) {
          node.children = newChildren
          node.expand = true
        } else if (node.children && node.children.length > 0) {
          this.replaceChildrenWithChild(node.children, targetPath, newChildren) // 递归遍历子节点
        }
      })
      return tree
    },
    cleanData (data) {
      return data.filter(item => {
        return !data.some(other => other !== item && other.filename.startsWith(item.filename))
      })
    },
    saveConfigFileTree () {
      let saveData = []
      this.$refs.configTree.getCheckedNodes().forEach(_ => {
        if (this.isFileAndFolderSelectable) {
          saveData.push({ filename: _.path, isDir: _.isDir, comparisonResult: _.comparisonResult })
        } else {
          if (this.isFileSelect) {
            if (_.isDir) {
              saveData.push({ filename: _.path, isDir: _.isDir, comparisonResult: _.comparisonResult })
            }
            saveData = this.cleanData(saveData)
          } else {
            if (!_.isDir) {
              saveData.push({ filename: _.path, isDir: _.isDir, comparisonResult: _.comparisonResult })
            }
          }
        }
      })
      if (this.configFileTree.treeType === 0) {
        this.packageInput.diff_conf_file = saveData
      } else if (this.configFileTree.treeType === 0.1) {
        if (saveData.length > 1) {
          this.$Message.warning(this.$t('art_multi_dir_warn'))
          return
        } else {
          this.packageInput.diff_conf_directory = saveData
          this.packageInput.diff_conf_file = []
        }
      } else if (this.configFileTree.treeType === 0.2) {
        if (saveData.length > 1) {
          this.$Message.warning(this.$t('art_multi_dir_warn'))
          return
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
          return
        } else {
          this.packageInput.db_upgrade_directory = saveData
          this.packageInput.db_upgrade_file_path = []
        }
      } else if (this.configFileTree.treeType === 102) {
        if (saveData.length > 1) {
          this.$Message.warning(this.$t('art_multi_dir_warn'))
          return
        } else {
          this.packageInput.db_rollback_directory = saveData
          this.packageInput.db_rollback_file_path = []
        }
      } else if (this.configFileTree.treeType === 103) {
        this.packageInput.db_upgrade_file_path = saveData
      } else if (this.configFileTree.treeType === 104) {
        this.packageInput.db_rollback_file_path = saveData
      } else if (this.configFileTree.treeType === 105) {
        this.packageInput.db_deploy_file_path = saveData
      } else if (this.configFileTree.treeType === 106) {
        this.packageInput.db_diff_conf_file = saveData
      } else if (this.configFileTree.treeType === 107) {
        this.packageInput.upgrade_cleanup_file_path = saveData
      } else if (this.configFileTree.treeType === 0.3) {
        if (saveData.length > 1) {
          this.$Message.warning(this.$t('art_multi_dir_warn'))
          return
        } else {
          this.packageInput.log_file_directory = saveData
          this.packageInput.log_file_trade = []
          this.packageInput.log_file_keyword = []
          this.packageInput.log_file_metric = []
          this.packageInput.log_file_trace = []
        }
      } else if (this.configFileTree.treeType === 0.4) {
        if (saveData.length > 1) {
          this.$Message.warning(this.$t('art_multi_dir_warn'))
          return
        } else {
          this.packageInput.db_deploy_file_directory = saveData
          this.packageInput.db_deploy_file_path = []
        }
      } else if (this.configFileTree.treeType === 0.5) {
        if (saveData.length > 1) {
          this.$Message.warning(this.$t('art_multi_dir_warn'))
          return
        } else {
          this.packageInput.db_diff_conf_directory = saveData
          this.packageInput.db_diff_conf_file = []
        }
      }
      this.isShowTreeModal = false
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
        disableCheckbox: this.isFileAndFolderSelectable ? false : this.isFileSelect ? !element.isDir : false,
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
                <span style="color: #00CB91;">
                  {params.data.title}
                  <span style="font-size:10px;padding-left:4px">[{params.data.comparisonResult}]</span>
                </span>
              </span>
            )
          } else if (params.data.comparisonResult === 'changed') {
            return (
              <span>
                <img height="16" width="16" src={iconFolder} style="position:relative;top:3px;margin:0 3px;" />
                <span style="color: #5384FF">
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
                  <span style="color: #00CB91;">
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
                  <span style="color: #5384FF">
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
                  <span style="color: #00CB91;">{params.data.title}</span>
                  <Button onClick={() => this.getCompareFile(params.data)} size="small" style="margin-left:8px" icon="ios-git-compare"></Button>
                </span>
              )
            } else if (params.data.comparisonResult === 'changed') {
              return (
                <span>
                  <img height="16" width="16" src={iconFile} style="position:relative;top:3px;margin:0 3px;" />
                  <span style="color: #5384FF">{params.data.title}</span>
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
      this.packageInput.key_service_code.push({
        regulative: 0,
        source_value: '',
        target_value: ''
      })
    },
    // 删除服务码
    deleteCodeStringMap (index) {
      this.packageInput.key_service_code.splice(index, 1)
    },
    changeCodeStringMap (index) {
      this.packageInput.key_service_code[index].source_value = ''
      this.packageInput.key_service_code[index].target_value = ''
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
      this.initPackageDetail()
      this.openDrawer = false
    },
    paramsValiate () {
      let canSave = true
      const res1 = this.isLogFileStartWidthLogDir('log_file_trade')
      const res2 = this.isLogFileStartWidthLogDir('log_file_keyword')
      const res3 = this.isLogFileStartWidthLogDir('log_file_metric')
      const res4 = this.isLogFileStartWidthLogDir('log_file_trace')
      if (!res1 || !res2 || !res3 || !res4) {
        this.$Message.warning(this.$t('art_log_path_validte_tip'))
        canSave = false
      }
      if (this.isShowKeyServiceCode && this.disableAddCodeStringMap) {
        this.$Message.warning(this.$t('art_service_code_tip'))
        canSave = false
      }
      // 清理目录中不能包含../
      const res = this.packageInput.upgrade_cleanup_file_path.filter(obj => obj.filename).some(item => item.filename.includes('../') || item.filename.startsWith('/'))
      if (res) {
        this.$Message.warning(this.$t('art_path_warn'))
        canSave = false
      }
      return canSave
    },
    isLogFileStartWidthLogDir (key) {
      this.packageInput[key] = this.packageInput[key].filter(item => item.filename !== '')
      const logFileDir = this.packageInput.log_file_directory.length === 1 ? this.packageInput.log_file_directory[0].filename + '/' : ''
      let res = this.packageInput[key].every(item => item.filename.startsWith(logFileDir))
      return res
    },
    async saveConfigFiles () {
      const canSave = this.paramsValiate()
      if (!canSave) {
        return
      }
      let obj = {
        package_type: this.packageType,
        baseline_package: this.packageInput.baseline_package || null,
        diff_conf_directory: this.packageInput.diff_conf_directory,
        diff_conf_file: this.packageInput.diff_conf_file,

        script_file_directory: this.packageInput.script_file_directory,
        start_file_path: this.packageInput.start_file_path,
        stop_file_path: this.packageInput.stop_file_path,
        deploy_file_path: this.packageInput.deploy_file_path,
        log_file_directory: this.packageInput.log_file_directory,
        log_file_trade: this.packageInput.log_file_trade,
        log_file_keyword: this.packageInput.log_file_keyword,
        log_file_metric: this.packageInput.log_file_metric,
        log_file_trace: this.packageInput.log_file_trace,

        is_decompression: String(this.packageInput.is_decompression),

        db_diff_conf_directory: this.packageInput.db_diff_conf_directory,
        db_diff_conf_file: this.packageInput.db_diff_conf_file,
        db_upgrade_directory: this.packageInput.db_upgrade_directory,
        db_upgrade_file_path: this.packageInput.db_upgrade_file_path,
        db_rollback_directory: this.packageInput.db_rollback_directory,
        db_rollback_file_path: this.packageInput.db_rollback_file_path,
        db_deploy_file_directory: this.packageInput.db_deploy_file_directory,
        db_deploy_file_path: this.packageInput.db_deploy_file_path,
        upgrade_cleanup_file_path: this.packageInput.upgrade_cleanup_file_path,

        key_service_code: this.packageInput.key_service_code
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
      this.$emit('queryPackages')
    },
    async getCompareFile (file) {
      const params = {
        baselinePackage: this.packageInput.baseline_package || '',
        content_length: 1024 * 100,
        files: [{ path: file.path }]
      }
      const { status, data } = await getCompareContent(this.guid, this.packageId, params)
      if (status === 'OK') {
        this.showFileCompare = true
        this.$refs.compareParams.compareFile(data[0].baseline_content, data[0].content, file.comparisonResult)
      }
    }
  },
  components: {
    DisplayPath,
    CompareFile
  }
}
</script>

<style scoped lang="scss">
.header-icon {
  float: right;
  margin: 3px 20px 0 0 !important;
}
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

.pkg-config {
  .ivu-form-item {
    margin-bottom: 6px;
  }
}
</style>
<style lang="scss" scoped>
.textarea-dir {
  display: inline-block;
  width: 300px;
}
.textarea-input {
  display: inline-block;
  width: 400px;
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
  grid-template-columns: 120px 446px 680px;
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

.cloud-upload {
  margin-right: 4px;
  cursor: pointer;
  padding: 2px 4px;
  vertical-align: middle;
  border-radius: 4px;
}
.ios-folder-upload {
  @extend .cloud-upload;
  background-color: #b886f8;
}
.ios-doc-upload {
  @extend .cloud-upload;
  background-color: #88c4e2;
}

.tab-content {
  height: calc(100vh - 330px);
  overflow: auto;
}
.drawer-footer {
  width: 100%;
  position: absolute;
  bottom: 0;
  left: 0;
  border-top: 1px solid #e8e8e8;
  padding: 10px 16px;
  text-align: center;
  background: #fff;
}
</style>
