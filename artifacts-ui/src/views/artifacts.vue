<template>
  <Row id="weArtifacts" class="artifact-management">
    <Col span="5">
      <!-- 系统设计版本 -->
      <Card>
        <p slot="title">{{ $t('artifacts_system_design_version') }}</p>
        <Select @on-change="selectSystemDesignVersion" @on-clear="clearSelectSystemDesign" label-in-name v-model="systemDesignVersion" filterable clearable>
          <Option v-for="version in systemDesignVersions" :value="version.guid || ''" :key="version.guid">{{ version.fixed_date ? `${version.name}[${version.fixed_date}]` : version.name }}</Option>
        </Select>
      </Card>
      <!-- 系统设计列表 -->
      <Card class="artifact-management-bottom-card">
        <p slot="title">{{ $t('artifacts_system_design_list') }}</p>
        <div class="artifact-management-tree-body">
          <Tree :data="treeData" @on-select-change="selectTreeNode"></Tree>
          <Spin size="large" fix v-if="treeLoading">
            <Icon type="ios-loading" size="24" class="spin-icon-load"></Icon>
            <div>{{ $t('artifacts_loading') }}</div>
          </Spin>
        </div>
      </Card>
      <!-- eslint-disable-next-line vue/no-parsing-error -->
    </Col>
    <Col span="18" style="margin-left: 35px;">
      <!-- 包管理 -->
      <Card v-if="guid" class="artifact-management-top-card">
        <!-- 本地上传 -->
        <Button type="info" ghost icon="ios-cloud-upload-outline" @click="getHeaders">
          {{ $t('artifacts_upload_new_package') }}
        </Button>
        <!-- 在线选择 -->
        <Button style="margin-left: 10px" type="info" ghost icon="ios-cloud-outline" @click="queryOnlinePackages">
          {{ $t('select_online') }}
        </Button>
        <Upload ref="uploadButton" :action="`/artifacts/unit-designs/${guid}/packages/upload`" :headers="headers" :on-success="onSuccess" :on-error="onError">
          <Button style="display:none" icon="ios-cloud-upload-outline">{{ $t('artifacts_upload_new_package') }}</Button>
        </Upload>
        <!-- <div v-if="uploaded" style="width: 100%;height:26px"></div> -->
        <!-- 包列表table -->
        <ArtifactsSimpleTable class="artifact-management-package-table" :loading="tableLoading" :columns="tableColumns" :data="tableData" :page="pageInfo" @pageChange="pageChange" @pageSizeChange="pageSizeChange" @rowClick="rowClick"></ArtifactsSimpleTable>
        <!-- 包在线上传选择 -->
        <Modal :mask-closable="false" v-model="isShowOnlineModal" :title="$t('select_online')" @on-ok="onUploadHandler" @on-cancel="closeOnlineModal">
          <Select filterable clearable v-model="selectedOnlinePackage">
            <Option v-for="conf in onlinePackages" :value="conf.downloadUrl" :key="conf.downloadUrl">{{ conf.name }}</Option>
          </Select>
        </Modal>
      </Card>
      <!-- 差异化变量 -->
      <Card v-if="packageDetail.diff_conf_file.length ? true : false" class="artifact-management-bottom-card artifact-management-top-card">
        <div class="batchOperation" style="text-align: right;">
          <Button type="primary" size="small" @click="showBatchBindModal">{{ $t('multi_bind_config') }}</Button>
        </div>
        <Spin size="large" fix v-if="tabTableLoading">
          <Icon type="ios-loading" size="24" class="spin-icon-load"></Icon>
          <div>{{ $t('artifacts_loading') }}</div>
        </Spin>
        <Tabs @on-click="changeTab">
          <TabPane v-for="(item, index) in packageDetail.diff_conf_file" :label="item.shorFileName" :name="item.shorFileName" :key="index">
            <Table :data="item.configKeyInfos || []" :columns="attrsTableColomnOptions"></Table>
          </TabPane>
        </Tabs>
        <Modal :mask-closable="false" v-model="isShowBatchBindModal" :title="$t('multi_bind_config')">
          <Card>
            <div slot="title">
              <Checkbox border size="small" :indeterminate="isBatchBindIndeterminate" :value="isBatchBindAllChecked" @click.prevent.native="batchBindSelectAll">{{ $t('check_all') }}</Checkbox>
            </div>
            <ul style="height:300px;overflow-y:auto">
              <li class="bind-style" v-for="(bindData, index) in batchBindData" :key="index">
                <Checkbox v-model="bindData.bound">{{ bindData.key }}</Checkbox>
                <div style="margin-left: 10px;color: #c4c3c3;display: inline-block;">[{{ bindData.fileNames }}]</div>
              </li>
            </ul>
          </Card>
          <div slot="footer">
            <Button @click="cancelBatchBindOperation">{{ $t('artifacts_cancel') }}</Button>
            <Button type="primary" @click="saveBatchBindOperation">{{ $t('artifacts_save') }}</Button>
          </div>
        </Modal>
        <Modal :mask-closable="false" v-model="isShowConfigKeyModal" :title="$t('artifacts_property_value_fill_rule')" @on-ok="setConfigRowValue" @on-cancel="closeConfigSelectModal">
          <Select filterable clearable v-model="currentConfigValue">
            <Option v-for="conf in allDiffConfigs.filter(conf => conf.variable_value && conf.code !== currentConfigRow.key)" :value="conf.variable_value" :key="conf.key_name">{{ conf.key_name }}</Option>
          </Select>
        </Modal>
      </Card>

      <!-- 包配置模态框 -->
      <Modal width="70" :styles="{ top: '60px' }" :mask-closable="false" v-model="isShowFilesModal" :title="$t('artifacts_script_configuration')" :okText="$t('artifacts_save')">
        <Card :bordered="false" :padding="8">
          <Row>
            <Col style="text-align: right;line-height:32px" span="5">
              <span style="margin-right: 10px">{{ $t('package_type') }}</span>
            </Col>
            <Col span="18" offset="1">
              <Select clearable :placeholder="$t('package_type')" v-model="packageType">
                <Option v-for="pkt in packageTypeOptions" :value="pkt.value" :key="pkt.value">{{ $t(pkt.label) }}</Option>
              </Select>
            </Col>
          </Row>
        </Card>
        <Card :bordered="false" :padding="8">
          <Row>
            <Col style="text-align: right;line-height:32px" span="5">
              <span style="margin-right: 10px">{{ $t('baseline_package') }}</span>
            </Col>
            <Col span="18" offset="1">
              <Select clearable :placeholder="$t('baseline_package')" @on-change="baseLinePackageChanged" v-model="packageInput.baseline_package">
                <Option v-for="conf in tableData.filter(conf => conf.guid !== packageId)" :value="conf.guid" :key="conf.name">{{ conf.name }}</Option>
              </Select>
            </Col>
          </Row>
        </Card>
        <div style="max-height: calc(100vh*0.5);overflow-y:auto;">
          <template v-if="packageType !== 'db'">
            <Card :bordered="false" :padding="8">
              <Row>
                <Col style="text-align: right" span="5">
                  <span style="margin-right: 10px">{{ $t('artifacts_config_files') }}</span>
                  <Button type="info" ghost @click="() => showTreeModal(0, packageInput.diff_conf_file || [])">{{ $t('artifacts_select_file') }}</Button>
                </Col>
                <Col span="18" offset="1">
                  <div id="diff_conf_file">
                    <div style="margin-bottom:5px" v-for="(file, index) in packageInput.diff_conf_file" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" v-model="packageInput.diff_conf_file[index].filename" />
                      <div v-if="file.comparisonResult === 'new'" class="baseline-cmp-new" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'same'" class="baseline-cmp-same" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'changed'" class="baseline-cmp-changed" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'deleted'" class="baseline-cmp-deleted" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <Icon type="ios-move" size="18" style="cursor:move" />
                      <Button style="float: right" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'diff_conf_file')"></Button>
                    </div>
                  </div>
                </Col>
              </Row>
            </Card>
            <Card :bordered="false" :padding="8">
              <Row>
                <Col style="text-align: right" span="5">
                  <span style="margin-right: 10px">{{ $t('artifacts_start_script') }}</span>
                  <Button type="info" ghost @click="() => showTreeModal(1, packageInput.start_file_path || [])">{{ $t('artifacts_select_file') }}</Button>
                </Col>
                <Col span="18" offset="1">
                  <div id="start_file_path">
                    <div style="margin-bottom:5px" v-for="(file, index) in packageInput.start_file_path" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" v-model="packageInput.start_file_path[index].filename" />
                      <div v-if="file.comparisonResult === 'new'" class="baseline-cmp-new" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'same'" class="baseline-cmp-same" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'changed'" class="baseline-cmp-changed" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'deleted'" class="baseline-cmp-deleted" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <Icon type="ios-move" size="18" style="cursor:move" />
                      <Button style="float: right" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'start_file_path')"></Button>
                    </div>
                  </div>
                </Col>
              </Row>
            </Card>
            <Card :bordered="false" :padding="8">
              <Row>
                <Col style="text-align: right" span="5">
                  <span style="margin-right: 10px">{{ $t('artifacts_stop_script') }}</span>
                  <Button type="info" ghost @click="() => showTreeModal(2, packageInput.stop_file_path || [])">{{ $t('artifacts_select_file') }}</Button>
                </Col>
                <Col span="18" offset="1">
                  <div id="stop_file_path">
                    <div style="margin-bottom:5px" v-for="(file, index) in packageInput.stop_file_path" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" v-model="packageInput.stop_file_path[index].filename" />
                      <div v-if="file.comparisonResult === 'new'" class="baseline-cmp-new" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'same'" class="baseline-cmp-same" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'changed'" class="baseline-cmp-changed" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'deleted'" class="baseline-cmp-deleted" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <Icon type="ios-move" size="18" style="cursor:move" />
                      <Button style="float: right" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'stop_file_path')"></Button>
                    </div>
                  </div>
                </Col>
              </Row>
            </Card>
            <Card :bordered="false" :padding="8">
              <Row>
                <Col style="text-align: right" span="5">
                  <span style="margin-right: 10px;">{{ $t('artifacts_deploy_script') }}</span>
                  <Button type="info" ghost @click="() => showTreeModal(3, packageInput.deploy_file_path || [])">{{ $t('artifacts_select_file') }}</Button>
                </Col>
                <Col span="18" offset="1">
                  <div id="deploy_file_path">
                    <div style="margin-bottom:5px" v-for="(file, index) in packageInput.deploy_file_path" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" v-model="packageInput.deploy_file_path[index].filename" />
                      <div v-if="file.comparisonResult === 'new'" class="baseline-cmp-new" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'same'" class="baseline-cmp-same" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'changed'" class="baseline-cmp-changed" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'deleted'" class="baseline-cmp-deleted" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <Icon type="ios-move" size="18" style="cursor:move" />
                      <Button style="float: right" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'deploy_file_path')"></Button>
                    </div>
                  </div>
                </Col>
              </Row>
            </Card>
            <Card :bordered="false" :padding="8">
              <Row>
                <Col style="text-align: right" span="5">
                  <span>{{ $t('is_decompression') }}</span>
                </Col>
                <Col span="18" offset="1">
                  <RadioGroup v-model="packageInput.is_decompression">
                    <Radio label="true"></Radio>
                    <Radio label="false"></Radio>
                  </RadioGroup>
                </Col>
              </Row>
            </Card>
          </template>
          <template v-if="packageType !== 'app'">
            <Card :bordered="false" :padding="8">
              <Row>
                <Col style="text-align: right" span="5">
                  <span style="margin-right: 10px">{{ $t('db_upgrade_directory') }}</span>
                  <Button type="info" ghost @click="() => showTreeModal(101, packageInput.db_upgrade_directory || [])">{{ $t('artifacts_select_file') }}</Button>
                </Col>
                <Col span="18" offset="1">
                  <div id="db_upgrade_directory">
                    <div style="margin-bottom:5px" v-for="(file, index) in packageInput.db_upgrade_directory" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('db_upgrade_directory')" type="textarea" v-model="packageInput.db_upgrade_directory[index].filename" />
                      <div v-if="file.comparisonResult === 'new'" class="baseline-cmp-new" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'same'" class="baseline-cmp-same" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'changed'" class="baseline-cmp-changed" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'deleted'" class="baseline-cmp-deleted" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <Icon type="ios-move" size="18" style="cursor:move" />
                      <Button style="float: right" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'db_upgrade_directory')"></Button>
                    </div>
                  </div>
                </Col>
              </Row>
            </Card>
            <Card :bordered="false" :padding="8">
              <Row>
                <Col style="text-align: right" span="5">
                  <span style="margin-right: 10px">{{ $t('db_rollback_directory') }}</span>
                  <Button type="info" ghost @click="() => showTreeModal(102, packageInput.db_rollback_directory || [])">{{ $t('artifacts_select_file') }}</Button>
                </Col>
                <Col span="18" offset="1">
                  <div id="db_rollback_directory">
                    <div style="margin-bottom:5px" v-for="(file, index) in packageInput.db_rollback_directory" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" v-model="packageInput.db_rollback_directory[index].filename" />
                      <div v-if="file.comparisonResult === 'new'" class="baseline-cmp-new" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'same'" class="baseline-cmp-same" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'changed'" class="baseline-cmp-changed" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'deleted'" class="baseline-cmp-deleted" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <Icon type="ios-move" size="18" style="cursor:move" />
                      <Button style="float: right" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'db_rollback_directory')"></Button>
                    </div>
                  </div>
                </Col>
              </Row>
            </Card>
            <Card :bordered="false" :padding="8">
              <Row>
                <Col style="text-align: right" span="5">
                  <span style="margin-right: 10px">{{ $t('db_upgrade_file_path') }}</span>
                  <Button type="info" ghost @click="() => showTreeModal(103, packageInput.db_upgrade_file_path || [])">{{ $t('artifacts_select_file') }}</Button>
                </Col>
                <Col span="18" offset="1">
                  <div id="db_upgrade_file_path">
                    <div style="margin-bottom:5px" v-for="(file, index) in packageInput.db_upgrade_file_path" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" v-model="packageInput.db_upgrade_file_path[index].filename" />
                      <div v-if="file.comparisonResult === 'new'" class="baseline-cmp-new" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'same'" class="baseline-cmp-same" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'changed'" class="baseline-cmp-changed" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'deleted'" class="baseline-cmp-deleted" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <Icon type="ios-move" size="18" style="cursor:move" />
                      <Button style="float: right" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'db_upgrade_file_path')"></Button>
                    </div>
                  </div>
                </Col>
              </Row>
            </Card>
            <Card :bordered="false" :padding="8">
              <Row>
                <Col style="text-align: right" span="5">
                  <span style="margin-right: 10px;">{{ $t('db_rollback_file_path') }}</span>
                  <Button type="info" ghost @click="() => showTreeModal(104, packageInput.db_rollback_file_path || [])">{{ $t('artifacts_select_file') }}</Button>
                </Col>
                <Col span="18" offset="1">
                  <div id="db_rollback_file_path">
                    <div style="margin-bottom:5px" v-for="(file, index) in packageInput.db_rollback_file_path" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" v-model="packageInput.db_rollback_file_path[index].filename" />
                      <div v-if="file.comparisonResult === 'new'" class="baseline-cmp-new" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'same'" class="baseline-cmp-same" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'changed'" class="baseline-cmp-changed" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'deleted'" class="baseline-cmp-deleted" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <Icon type="ios-move" size="18" style="cursor:move" />
                      <Button style="float: right" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'db_rollback_file_path')"></Button>
                    </div>
                  </div>
                </Col>
              </Row>
            </Card>
            <Card :bordered="false" :padding="8">
              <Row>
                <Col style="text-align: right" span="5">
                  <span style="margin-right: 10px;">{{ $t('db_deploy_file_path') }}</span>
                  <Button type="info" ghost @click="() => showTreeModal(105, packageInput.db_deploy_file_path || [])">{{ $t('artifacts_select_file') }}</Button>
                </Col>
                <Col span="18" offset="1">
                  <div id="db_deploy_file_path">
                    <div style="margin-bottom:5px" v-for="(file, index) in packageInput.db_deploy_file_path" :key="index">
                      <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" v-model="packageInput.db_deploy_file_path[index].filename" />
                      <div v-if="file.comparisonResult === 'new'" class="baseline-cmp-new" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'same'" class="baseline-cmp-same" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'changed'" class="baseline-cmp-changed" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <div v-if="file.comparisonResult === 'deleted'" class="baseline-cmp-deleted" style="width:60px;margin: 0 8px;display: inline-block;">[{{ file.comparisonResult }}]</div>
                      <Icon type="ios-move" size="18" style="cursor:move" />
                      <Button style="float: right" type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'db_deploy_file_path')"></Button>
                    </div>
                  </div>
                </Col>
              </Row>
            </Card>
          </template>
        </div>
        <div slot="footer">
          <Button @click="closeFilesModal">{{ $t('artifacts_cancel') }}</Button>
          <Button type="primary" @click="saveConfigFiles" :loading="saveConfigLoading">{{ $t('artifacts_save') }}</Button>
        </div>
      </Modal>

      <!-- 包配置文件选择 -->
      <Modal :styles="{ top: '60px' }" :mask-closable="false" v-model="isShowTreeModal" :title="configFileTreeTitle" @on-ok="saveConfigFileTree" @on-cancel="closeConfigFileTree" draggable width="700">
        <CheckboxGroup v-if="packageInput.baseline_package">
          <Button :style="toggleCheckFileTreeNew" type="dashed" size="small" @click="checkConfigFileTreeVis('new')"><span style="color:#18b566;">new</span></Button>
          <Button :style="toggleCheckFileTreeSame" type="dashed" size="small" @click="checkConfigFileTreeVis('same')"><span>same</span></Button>
          <Button :style="toggleCheckFileTreeChanged" type="dashed" size="small" @click="checkConfigFileTreeVis('changed')"><span style="color:#2d8cf0;">changed</span></Button>
          <Button :style="toggleCheckFileTreeDeleted" type="dashed" size="small" @click="checkConfigFileTreeVis('deleted')"><span style="color:#cccccc;">deleted</span></Button>
        </CheckboxGroup>
        <div style="height:450px;overflow-y:auto">
          <Tree ref="configTree" :data="configFileTree.treeData" :load-data="configFileTreeLoadNode" @on-toggle-expand="configFileTreeExpand" @on-check-change="changeChildChecked" show-checkbox> </Tree>
        </div>
      </Modal>

      <!-- eslint-disable-next-line vue/no-parsing-error -->
      <Modal :z-index="9999" width="1200" v-model="showFileCompare" :fullscreen="fullscreen" footer-hide>
        <p slot="header">
          <span>{{ $t('file_compare') }}</span>
          <Icon v-if="!fullscreen" @click="zoomModalMax" class="header-icon" type="ios-expand" />
          <Icon v-else @click="zoomModalMin" class="header-icon" type="ios-contract" />
        </p>
        <CompareFile ref="compareParams" :fileContentHeight="fileContentHeight"></CompareFile>
      </Modal>
    </Col>
  </Row>
</template>

<script>
import { getSpecialConnector, getAllCITypesWithAttr, getAllSystemEnumCodes, deleteCiDatas, operateCiState, getPackageCiTypeId, getSystemDesignVersion, getSystemDesignVersions, retrieveEntity, updateEntity, queryPackages, queryArtifactsList, getPackageDetail, updatePackage, getFiles, compareBaseLineFiles, uploadArtifact, getCompareContent } from '@/api/server.js'
import { setCookie, getCookie } from '../util/cookie.js'
import iconFile from '../assets/file.png'
import iconFolder from '../assets/folder.png'
import axios from 'axios'
import Sortable from 'sortablejs'
import CompareFile from './compare-file'
// 业务运行实例ciTypeId
const defaultRootCiTypeId = 50
// cmdb插件包名
const cmdbPackageName = 'wecmdb'
// 差异配置key_name
const DIFF_CONFIGURATION = 'diff_configuration'
// // 部署包key_name
// const DEPLOY_PACKAGE = 'deploy_package'
export default {
  name: 'artifacts',
  data () {
    return {
      packageType: '',
      packageTypeOptions: [
        { label: 'applications', value: 'app' },
        { label: 'db_instance', value: 'db' },
        { label: 'mixed', value: 'mixed' }
      ],
      isFileSelect: false,
      fullscreen: false,
      fileContentHeight: window.screen.availHeight * 0.4 + 'px',
      showFileCompare: false,
      compareParams: {
        originContent: '',
        newContent: ''
      },
      // ---------------
      // 系统设计树形数据
      // ---------------
      guid: '',
      systemDesignVersions: [],
      systemDesignVersion: '',
      treeData: [],
      treeLoading: false,
      // ----------------
      // 系统设计物料包数据
      // ----------------
      isShowOnlineModal: false,
      selectedOnlinePackage: '',
      onlinePackages: [],
      // 上传认证头
      headers: {},
      // 单元设计包列表table
      pageInfo: {
        pageSize: 5,
        currentPage: 1,
        total: 0
      },
      statusOperations: [],
      tableLoading: false,
      tableData: [],
      tableColumns: [
        // {
        //   title: 'GUID',
        //   width: 100,
        //   key: 'guid'
        // },
        // {
        //   title: this.$t('artifacts_package_name'),
        //   minWidth: 80,
        //   key: 'name',
        //   render: (h, params) => this.renderCell(params.row.name)
        // },
        // {
        //   title: this.$t('artifacts_upload_time'),
        //   width: 120,
        //   key: 'upload_time'
        // },
        // {
        //   title: this.$t('baseline_package'),
        //   width: 100,
        //   key: 'md5_value',
        //   render: (h, params) => {
        //     const baseLine = params.row.baseline_package.code || ''
        //     return <span>{baseLine}</span>
        //   }
        // },
        {
          title: this.$t('db_deploy_file_path'),
          minWidth: 80,
          key: 'db_deploy_file_path',
          render: (h, params) => this.renderCell(params.row.db_deploy_file_path)
        },
        {
          title: this.$t('db_rollback_directory'),
          minWidth: 80,
          key: 'db_rollback_directory',
          render: (h, params) => this.renderCell(params.row.db_rollback_directory)
        },
        {
          title: this.$t('db_rollback_file_path'),
          minWidth: 80,
          key: 'db_rollback_file_path',
          render: (h, params) => this.renderCell(params.row.db_rollback_file_path)
        },
        {
          title: this.$t('db_upgrade_directory'),
          minWidth: 80,
          key: 'db_upgrade_directory',
          render: (h, params) => this.renderCell(params.row.db_upgrade_directory)
        },
        {
          title: this.$t('db_upgrade_file_path'),
          minWidth: 80,
          key: 'db_upgrade_file_path',
          render: (h, params) => this.renderCell(params.row.db_upgrade_file_path)
        },
        {
          title: this.$t('artifacts_uploaded_by'),
          minWidth: 80,
          key: 'upload_user',
          render: (h, params) => this.renderCell(params.row.upload_user)
        },
        {
          title: this.$t('artifacts_config_files'),
          minWidth: 100,
          key: 'diff_conf_file',
          render: (h, params) => this.renderCell(params.row.diff_conf_file)
        },
        {
          title: this.$t('artifacts_start_script'),
          minWidth: 100,
          key: 'start_file_path',
          render: (h, params) => this.renderCell(params.row.start_file_path)
        },
        {
          title: this.$t('artifacts_stop_script'),
          minWidth: 100,
          key: 'stop_file_path',
          render: (h, params) => this.renderCell(params.row.stop_file_path)
        },
        {
          title: this.$t('artifacts_deploy_script'),
          minWidth: 100,
          key: 'deploy_file_path',
          render: (h, params) => this.renderCell(params.row.deploy_file_path)
        },
        {
          title: this.$t('is_decompression'),
          minWidth: 100,
          key: 'is_decompression',
          render: (h, params) => this.renderCell(params.row.is_decompression)
        },
        {
          title: this.$t('artifacts_action'),
          key: 'state',
          width: 150,
          render: (h, params) => {
            return <div style="padding-top:5px">{this.renderActionButton(params)}</div>
          }
        }
      ],
      // ----------------
      // 包配置文件模态数据
      // ----------------
      packageId: '',
      isShowFilesModal: false,
      packageInput: {
        baseline_package: null,
        diff_conf_file: [],
        start_file_path: [],
        stop_file_path: [],
        deploy_file_path: [],
        is_decompression: 'true',

        db_upgrade_directory: [],
        db_rollback_directory: [],
        db_upgrade_file_path: [],
        db_rollback_file_path: [],
        db_deploy_file_path: []
      },
      saveConfigLoading: false,
      // -------------------
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
      toggleCheckFileTreeDeleted: '',
      // -------------------
      // 差异化变量数据
      // -------------------
      packageDetail: {
        baseline_package: null,
        diff_conf_file: [],
        start_file_path: [],
        stop_file_path: [],
        deploy_file_path: [],
        is_compress: null,

        db_upgrade_directory: [],
        db_rollback_directory: [],
        db_upgrade_file_path: [],
        db_rollback_file_path: [],
        db_deploy_file_path: []
      },
      isShowBatchBindModal: false,
      batchBindData: [],
      isBatchBindIndeterminate: false,
      isBatchBindAllChecked: false,
      tabTableLoading: false,
      // 选择差异化变量临时保存值
      currentConfigValue: '',
      isShowConfigKeyModal: false,
      currentConfigRow: {},
      allDiffConfigs: [],
      attrsTableColomnOptions: [
        {
          title: this.$t('artifacts_property_isbind'),
          width: 100,
          render: (h, params) => {
            if (params.row.conf_variable.bound) {
              return (
                <span>
                  <Icon type="md-checkmark-circle" color="#2d8cf0" style="font-size: 18px;" />
                </span>
              )
            } else {
              return (
                <span>
                  <Icon type="md-close-circle" color="red" style="font-size: 18px;" />
                </span>
              )
            }
          }
        },
        {
          title: this.$t('artifacts_property_seq'),
          key: 'index',
          width: 70
        },
        {
          title: this.$t('artifacts_line_number'),
          width: 100,
          key: 'line'
        },
        {
          title: this.$t('artifacts_property_name'),
          width: 140,
          render: (h, params) => {
            // show static view only if confirmed
            return (
              <span>
                {params.row.type || ''}
                {params.row.key}
              </span>
            )
          }
        },
        {
          title: this.$t('root_ci'),
          width: 120,
          render: (h, params) => {
            if (this.activeTabData[params.row._index]) {
              params.row.rootCI = params.row.conf_variable.tempRootCI || params.row.conf_variable.originRootCI
              return (
                <div>
                  <Select value={this.activeTabData[params.row._index].conf_variable.tempRootCI} onInput={v => this.changeRootCI(v, params)} style="width:100px">
                    {this.rootCI.map(item => {
                      return <Option value={item.value}>{item.label}</Option>
                    })}
                  </Select>
                </div>
              )
            }
          }
        },
        {
          title: this.$t('artifacts_property_value_fill_rule'),
          render: (h, params) => {
            // show static view only if confirmed
            if (this.activeTabData[params.row._index]) {
              return params.row.conf_variable.fixedDate ? (
                <ArtifactsAutoFill style="margin-top:5px;" allCiTypes={this.ciTypes} specialDelimiters={this.specialDelimiters} rootCiTypeId={params.row.rootCI} isReadOnly={true} v-model={this.activeTabData[params.row._index].conf_variable.diffExpr} cmdbPackageName={cmdbPackageName} />
              ) : (
                <div style="align-items:center;display:flex;">
                  <ArtifactsAutoFill style="margin-top:5px;width:calc(100% - 10px);" allCiTypes={this.ciTypes} specialDelimiters={this.specialDelimiters} rootCiTypeId={params.row.rootCI} v-model={this.activeTabData[params.row._index].conf_variable.diffExpr} onUpdateValue={val => this.updateAutoFillValue(val, params.row)} cmdbPackageName={cmdbPackageName} />
                </div>
              )
            }
          }
        },
        {
          title: this.$t('artifacts_action'),
          key: 'state',
          width: 100,
          render: (h, params) => {
            return <div style="padding-top:5px">{this.renderConfigButton(params)}</div>
          }
        }
      ],
      rootCI: [
        { value: 50, label: this.$t('applications') },
        { value: 51, label: this.$t('db_instance') }
      ],
      activeTab: '',
      activeTabData: null
    }
  },
  computed: {},
  watch: {
    batchBindData: {
      handler (bindData) {
        this.isBatchBindAllChecked = bindData.every(bd => {
          return bd.bound === true
        })
        if (this.isBatchBindAllChecked) {
          this.isBatchBindIndeterminate = false
        } else {
          this.isBatchBindIndeterminate = bindData.some(bd => {
            return bd.bound === true
          })
        }
      },
      immediate: true,
      deep: true
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
    changeTab (tabName) {
      this.activeTab = tabName
      this.activeTabData = this.packageDetail.diff_conf_file.find(item => item.shorFileName === this.activeTab).configKeyInfos
    },
    changeRootCI (rootCI, params) {
      let activeTab = this.packageDetail.diff_conf_file.find(item => item.shorFileName === this.activeTab)
      let confVariable = activeTab.configKeyInfos[params.index].conf_variable
      confVariable.tempRootCI = rootCI
      if (confVariable.tempRootCI === confVariable.originRootCI) {
        confVariable.diffExpr = confVariable.originDiffExpr
      } else {
        confVariable.diffExpr = ''
      }
    },
    async fetchData () {
      const [sysData, packageCiType] = await Promise.all([getSystemDesignVersions(), getPackageCiTypeId()])
      if (sysData.status === 'OK' && sysData.data.contents instanceof Array) {
        this.systemDesignVersions = sysData.data.contents.map(_ => _.data)
      }
      if (packageCiType.status === 'OK') {
        this.packageCiType = packageCiType.data
      }
    },
    async getSpecialConnector () {
      const res = await getSpecialConnector()
      if (res.status === 'OK') {
        this.specialDelimiters = res.data
      }
    },
    async getAllCITypesWithAttr () {
      let { status, data } = await getAllCITypesWithAttr(['notCreated', 'created', 'dirty', 'decommissioned'])
      if (status === 'OK') {
        this.ciTypes = JSON.parse(JSON.stringify(data))
      }
    },
    async getAllSystemEnumCodes () {
      const { status, data } = await getAllSystemEnumCodes({
        filters: [
          {
            name: 'cat.catName',
            operator: 'eq',
            value: 'state_transition_operation'
          }
        ],
        paging: false
      })
      if (status === 'OK' && data.contents instanceof Array) {
        const buttonTypes = {
          confirm: 'success',
          delete: 'error',
          discard: 'warning',
          update: 'primary'
        }
        this.statusOperations = data.contents
          .filter(_ => _.code === 'confirm' || _.code === 'delete' || _.code === 'discard' || _.code === 'update')
          .map(_ => {
            return {
              type: _.code,
              label: _.code !== 'update' ? _.value : this.$t('artifacts_configuration'),
              props: {
                type: buttonTypes[_.code] || 'error',
                size: 'small'
              },
              actionType: _.code
            }
          })
      }
    },
    formatTreeData (array, level) {
      const color = {
        new: '#19be6b',
        update: '#5cadff',
        delete: '#ed4014',
        created: '#2b85e4',
        changed: 'purple',
        destroyed: '#ff9900'
      }
      return array.map(_ => {
        _.title = _.data.name
        _.level = level
        _.render = (h, params) => {
          return (
            <div style="white-space: break-spaces;">
              <div style="display:inline-block;margin-right:4px;max-width:60px;max-width:120px;overflow:hidden; text-overflow:ellipsis; white-space:nowrap;vertical-align: top;" title={_.data.code}>
                {_.data.code}
              </div>
              <div style="display:inline-block;margin-right:4px;font-size:12px;max-width:120px;overflow:hidden; text-overflow:ellipsis; white-space:nowrap;vertical-align: top;" title={_.data.name}>
                [{_.data.name}]
              </div>
              <div style={`display:inline-block;max-width:60px;font-size:12px;vertical-align:top;color:${color[_.data.state_code]}`}>{_.data.state_code}</div>
            </div>
          )
        }
        if (_.children && _.children.length) {
          _.expand = true
          _.children = this.formatTreeData(_.children, level + 1)
        }
        return _
      })
    },
    async getSystemDesignVersion (guid) {
      if (!guid) {
        return
      }
      this.treeLoading = true
      let { status, data } = await getSystemDesignVersion(guid)
      if (status === 'OK') {
        this.treeData = this.formatTreeData(data, 1)
        this.treeLoading = false
      }
    },
    selectSystemDesignVersion (guid) {
      this.getSystemDesignVersion(guid)
      this.guid = ''
      this.initPackageDetail()
      this.uploaded = false
    },
    clearSelectSystemDesign () {
      this.systemDesignVersion = ''
      this.treeData = []
    },
    async queryPackages () {
      this.tableLoading = true
      let { status, data } = await queryPackages(this.guid, {
        sorting: {
          asc: false,
          field: 'upload_time'
        },
        paging: true,
        pageable: {
          pageSize: this.pageInfo.pageSize,
          startIndex: (this.pageInfo.currentPage - 1) * this.pageInfo.pageSize
        }
      })
      if (status === 'OK') {
        this.tableLoading = false
        this.tableData = data.contents.map(_ => {
          return {
            ..._.data,
            nextOperations: _.meta.nextOperations || []
          }
        })
        const { pageSize, totalRows: total } = data.pageInfo
        const currentPage = this.pageInfo.currentPage
        this.pageInfo = { currentPage, pageSize, total }
      }
    },
    selectTreeNode (node) {
      if (node.length && node[0].level === 3) {
        this.guid = node[0].data.r_guid
        this.queryPackages()
        this.initPackageDetail()
      }
    },
    getHeaders () {
      let refreshRequest = null
      const currentTime = new Date().getTime()
      const accessToken = getCookie('accessToken')
      if (accessToken) {
        const expiration = getCookie('accessTokenExpirationTime') * 1 - currentTime
        if (expiration < 1 * 60 * 1000 && !refreshRequest) {
          refreshRequest = axios.get('/auth/v1/api/token', {
            headers: {
              Authorization: 'Bearer ' + getCookie('refreshToken')
            }
          })
          refreshRequest.then(
            res => {
              setCookie(res.data.data)
              this.setUploadActionHeader()
              this.$refs.uploadButton.handleClick()
            },
            // eslint-disable-next-line handle-callback-err
            err => {
              refreshRequest = null
              window.location.href = window.location.origin + '/#/login'
            }
          )
        } else {
          this.setUploadActionHeader()
          this.$refs.uploadButton.handleClick()
        }
      } else {
        window.location.href = window.location.origin + '/#/login'
      }
    },
    onSuccess (response, file, fileList) {
      if (response.status === 'ERROR') {
        this.$Notice.error({
          title: 'Error',
          desc: response.message || ''
        })
        this.$refs.uploadButton.clearFiles()
      } else {
        this.$refs.uploadButton.clearFiles()
        this.$Notice.success({
          title: 'Success',
          desc: response.message || ''
        })
        this.queryPackages()
      }
    },
    onError (file, filelist) {
      this.$Notice.error({
        title: 'Error',
        desc: file.message || ''
      })
      this.$refs.uploadButton.clearFiles()
    },
    setUploadActionHeader () {
      this.headers = {
        Authorization: 'Bearer ' + getCookie('accessToken')
      }
    },
    async onUploadHandler () {
      const { status } = await uploadArtifact(this.guid, this.selectedOnlinePackage)
      if (status === 'OK') {
        this.$Notice.success({
          title: 'Success',
          desc: 'This may take a while, please check later'
        })
      }
      this.closeOnlineModal()
    },
    closeOnlineModal () {
      this.selectedOnlinePackage = ''
      this.isShowOnlineModal = false
    },
    async queryOnlinePackages () {
      this.onlinePackages = []
      const { status, data } = await queryArtifactsList(this.guid, { filters: [], paging: false })
      if (status === 'OK') {
        this.onlinePackages = data
        this.isShowOnlineModal = true
      }
    },
    renderCell (content) {
      let res = ''
      if (Array.isArray(content)) {
        content.forEach(c => {
          res += c.filename + '|'
        })
        res = res.substring(0, res.length - 1)
      } else {
        res = content
      }
      return (
        <Tooltip min-width="200px" max-width="500px" style="width: 100%;">
          <span slot="content" style="white-space:normal;">
            {res}
          </span>
          <div style="width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{res}</div>
        </Tooltip>
      )
    },
    pageChange (currentPage) {
      this.pageInfo.currentPage = currentPage
      this.queryPackages()
    },
    pageSizeChange (pageSize) {
      this.pageInfo.pageSize = pageSize
      this.queryPackages()
    },
    async rowClick (row) {
      this.packageId = row.guid
      // 获取包文件及差异化变量数据
      await this.syncPackageDetail()
    },
    initPackageDetail () {
      this.packageDetail = {
        baseline_package: null,
        diff_conf_file: [],
        start_file_path: [],
        stop_file_path: [],
        deploy_file_path: [],
        is_compress: null,

        db_upgrade_directory: [],
        db_rollback_directory: [],
        db_upgrade_file_path: [],
        db_rollback_file_path: [],
        db_deploy_file_path: []
      }
    },
    getRootCI (diffExpr) {
      let rootCI = defaultRootCiTypeId
      if (!diffExpr) {
        return rootCI
      }
      const de = JSON.parse(diffExpr)
      const rootItem = de.find(item => item.type === 'rule')
      if (rootItem) {
        const val = JSON.parse(rootItem.value)
        rootCI = val[0].ciTypeId || defaultRootCiTypeId
      }
      return rootCI
    },
    formatPackageDetail (data) {
      let dataString = JSON.stringify(data)
      let copyData = JSON.parse(dataString)
      copyData.diff_conf_variable.forEach(elVar => {
        // 记录原始值
        elVar.originDiffExpr = elVar.diffExpr
        const rootCI = this.getRootCI(elVar.diffExpr)
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
          const found = copyData.diff_conf_variable.find(_ => _.key.toLowerCase() === elFileVar.key.toLowerCase())
          elFileVar.conf_variable = found
          index += 1
        })
      })
      return copyData
    },
    async syncPackageDetail () {
      this.initPackageDetail()
      let { status, data } = await getPackageDetail(this.guid, this.packageId)
      if (status === 'OK') {
        this.packageDetail = this.formatPackageDetail(data)
        if (this.packageDetail.diff_conf_file.length > 0) {
          this.activeTab = this.packageDetail.diff_conf_file[0].shorFileName
          this.activeTabData = this.packageDetail.diff_conf_file[0].configKeyInfos
        } else {
          this.activeTab = ''
          this.activeTabData = {}
        }
      }
    },
    renderActionButton (params) {
      const row = params.row
      return this.statusOperations
        .filter(_ => row.nextOperations.indexOf(_.type) >= 0)
        .map(_ => {
          return (
            <Button {...{ props: { ..._.props } }} style="margin-right:5px;margin-bottom:5px;" onClick={() => this.changeStatus(row, _.type, event)}>
              {_.label}
            </Button>
          )
        })
    },
    changeStatus (row, status, event) {
      switch (status) {
        // 配置
        case 'update':
          this.showFilesModal(row, event)
          break
        // 删除
        case 'delete':
          this.handleDelete(row, status)
          break
        // 确认
        default:
          this.handleStatusChange(row, status)
          break
      }
    },
    initPackageInput () {
      this.packageInput = {
        baseline_package: null,
        diff_conf_file: [],
        start_file_path: [],
        stop_file_path: [],
        deploy_file_path: [],
        is_decompression: 'true',

        db_upgrade_directory: [],
        db_rollback_directory: [],
        db_upgrade_file_path: [],
        db_rollback_file_path: [],
        db_deploy_file_path: []
      }
    },
    async syncBaselineFileStatus () {
      if (this.packageInput.baseline_package) {
        if (this.packageInput.diff_conf_file.length > 0 || this.packageInput.start_file_path.length > 0 || this.packageInput.stop_file_path.length > 0 || this.packageInput.deploy_file_path.length > 0) {
          // 若有文件数据，则请求对比接口
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
      }
    },
    async baseLinePackageChanged (v) {
      if (v) {
        const found = JSON.parse(JSON.stringify(this.tableData.find(row => row.guid === v)))
        this.packageInput.diff_conf_file = found.diff_conf_file ? JSON.parse(JSON.stringify(found.diff_conf_file)) : []
        this.packageInput.start_file_path = found.start_file_path ? JSON.parse(JSON.stringify(found.start_file_path)) : []
        this.packageInput.stop_file_path = found.stop_file_path ? JSON.parse(JSON.stringify(found.stop_file_path)) : []
        this.packageInput.deploy_file_path = found.deploy_file_path ? JSON.parse(JSON.stringify(found.deploy_file_path)) : []
        this.packageInput.is_decompression = found.is_decompression || 'true'

        this.packageInput.db_upgrade_directory = found.db_upgrade_directory ? JSON.parse(JSON.stringify(found.db_upgrade_directory)) : []
        this.packageInput.db_rollback_directory = found.db_rollback_directory ? JSON.parse(JSON.stringify(found.db_rollback_directory)) : []
        this.packageInput.db_upgrade_file_path = []
        this.packageInput.db_rollback_file_path = []
        this.packageInput.db_deploy_file_path = found.db_deploy_file_path ? JSON.parse(JSON.stringify(found.db_deploy_file_path)) : []
      }
      await this.syncBaselineFileStatus()
    },
    async showFilesModal (row, event) {
      event.stopPropagation()
      this.packageId = row.guid
      await this.syncPackageDetail()
      this.packageType = row.package_type || 'app'
      // 以下4个变量类型为字符串
      // row从table数据中来，此时baseline_package为对象
      this.packageInput.baseline_package = this.packageDetail.baseline_package ? this.packageDetail.baseline_package : null
      this.packageInput.diff_conf_file = JSON.parse(JSON.stringify(this.packageDetail.diff_conf_file))
      this.packageInput.start_file_path = JSON.parse(JSON.stringify(this.packageDetail.start_file_path))
      this.packageInput.stop_file_path = JSON.parse(JSON.stringify(this.packageDetail.stop_file_path))
      this.packageInput.deploy_file_path = JSON.parse(JSON.stringify(this.packageDetail.deploy_file_path))
      this.packageInput.is_decompression = row.is_decompression || 'true'

      this.packageInput.db_upgrade_directory = JSON.parse(JSON.stringify(this.packageDetail.db_upgrade_directory || []))
      this.packageInput.db_rollback_directory = JSON.parse(JSON.stringify(this.packageDetail.db_rollback_directory || []))
      this.packageInput.db_upgrade_file_path = JSON.parse(JSON.stringify(this.packageDetail.db_upgrade_file_path || []))
      this.packageInput.db_rollback_file_path = JSON.parse(JSON.stringify(this.packageDetail.db_rollback_file_path || []))
      this.packageInput.db_deploy_file_path = JSON.parse(JSON.stringify(this.packageDetail.db_deploy_file_path || []))

      this.packageId = row.guid
      // await this.syncBaselineFileStatus()
      this.isShowFilesModal = true
      this.$nextTick(() => {
        if (this.packageType !== 'db') {
          this.genSortable('diff_conf_file')
          this.genSortable('start_file_path')
          this.genSortable('stop_file_path')
          this.genSortable('deploy_file_path')
        }
        if (this.packageType !== 'app') {
          this.genSortable('db_upgrade_directory')
          this.genSortable('db_rollback_directory')
          this.genSortable('db_upgrade_file_path')
          this.genSortable('db_rollback_file_path')
          this.genSortable('db_deploy_file_path')
        }
      })
    },
    genSortable (key) {
      const _this = this
      const $ul = document.getElementById(key)
      // eslint-disable-next-line no-unused-vars
      const sortable = new Sortable($ul, {
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
    closeFilesModal () {
      this.initPackageInput()
      this.isShowFilesModal = false
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
        this.$refs.compareParams.compareFile(data[0].baseline_content, data[0].content)
      }
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
        this.isShowFilesModal = false
        this.$Notice.success({
          title: this.$t('artifacts_successed')
        })
      }
      await this.queryPackages()
      await this.syncPackageDetail()
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
                    <Button onClick={() => this.getCompareFile(params.data)} size="small" style="margin-left:8px" icon="ios-git-compare"></Button>
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
                  <Button onClick={() => this.getCompareFile(params.data)} size="small" style="margin-left:8px" icon="ios-git-compare"></Button>
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
    async showTreeModal (type, files) {
      this.initTreeConfig(type)
      this.isShowTreeModal = true
      this.isFileSelect = false
      let queryFiles = []
      if (type === 0) {
        this.configFileTreeTitle = this.$t('artifacts_select_config_files')
        queryFiles = this.packageInput.diff_conf_file.map(_ => _.filename)
      } else if (type === 1) {
        this.configFileTreeTitle = this.$t('artifacts_select_start_script')
        queryFiles = this.packageInput.start_file_path.map(_ => _.filename)
      } else if (type === 2) {
        this.configFileTreeTitle = this.$t('artifacts_select_stop_script')
        queryFiles = this.packageInput.stop_file_path.map(_ => _.filename)
      } else if (type === 3) {
        this.configFileTreeTitle = this.$t('artifacts_select_deploy_script')
        queryFiles = this.packageInput.deploy_file_path.map(_ => _.filename)
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
      }
      const { data } = await getFiles(this.guid, this.packageId, {
        baselinePackage: this.packageInput.baseline_package,
        fileList: queryFiles,
        expandAll: true
      })
      this.configFileTree.treeData = this.formatConfigFileTree(data, queryFiles)
    },
    closeConfigFileTree () {
      this.isShowTreeModal = false
    },
    deleteFilePath (index, key) {
      this.packageInput[key].splice(index, 1)
    },
    initTreeConfig (type) {
      this.configFileTree.treeType = type
      this.configFileTree.treeData = []
      this.toggleCheckFileTreeNew = ''
      this.toggleCheckFileTreeSame = ''
      this.toggleCheckFileTreeChanged = ''
      this.toggleCheckFileTreeDeleted = ''
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
      } else if (this.configFileTree.treeType === 1) {
        this.packageInput.start_file_path = saveData
      } else if (this.configFileTree.treeType === 2) {
        this.packageInput.stop_file_path = saveData
      } else if (this.configFileTree.treeType === 3) {
        this.packageInput.deploy_file_path = saveData
      } else if (this.configFileTree.treeType === 101) {
        this.packageInput.db_upgrade_directory = saveData
      } else if (this.configFileTree.treeType === 102) {
        this.packageInput.db_rollback_directory = saveData
      } else if (this.configFileTree.treeType === 103) {
        this.packageInput.db_upgrade_file_path = saveData
      } else if (this.configFileTree.treeType === 104) {
        this.packageInput.db_rollback_file_path = saveData
      } else if (this.configFileTree.treeType === 105) {
        this.packageInput.db_deploy_file_path = saveData
      }
    },
    _travelConfigFileTreeNodes (node, status, checked) {
      let changeParent = false
      if (!node.isDir && node.comparisonResult === status) {
        this.$set(node, 'checked', checked)
        if (!checked) {
          changeParent = true
        }
      }
      if (node.children && node.expand) {
        node.children.forEach(el => {
          let tmpChangeParent = this._travelConfigFileTreeNodes(el, status, checked)
          if (tmpChangeParent) {
            changeParent = tmpChangeParent
            this.$set(node, 'checked', false)
          }
        })
      }
      return changeParent
    },
    checkConfigFileTreeVis (status) {
      let checked = true
      if (status === 'new') {
        if (this.toggleCheckFileTreeNew) {
          checked = false
          this.toggleCheckFileTreeNew = ''
        } else {
          checked = true
          this.toggleCheckFileTreeNew = 'box-shadow: rgb(165 165 165) 2px 2px 2px 0px inset; background: rgb(238 238 238);'
        }
      } else if (status === 'same') {
        if (this.toggleCheckFileTreeSame) {
          checked = false
          this.toggleCheckFileTreeSame = ''
        } else {
          checked = true
          this.toggleCheckFileTreeSame = 'box-shadow: rgb(165 165 165) 2px 2px 2px 0px inset; background: rgb(238 238 238);'
        }
      } else if (status === 'changed') {
        if (this.toggleCheckFileTreeChanged) {
          checked = false
          this.toggleCheckFileTreeChanged = ''
        } else {
          checked = true
          this.toggleCheckFileTreeChanged = 'box-shadow: rgb(165 165 165) 2px 2px 2px 0px inset; background: rgb(238 238 238);'
        }
      } else if (status === 'deleted') {
        if (this.toggleCheckFileTreeDeleted) {
          checked = false
          this.toggleCheckFileTreeDeleted = ''
        } else {
          checked = true
          this.toggleCheckFileTreeDeleted = 'box-shadow: rgb(165 165 165) 2px 2px 2px 0px inset; background: rgb(238 238 238);'
        }
      }
      this.configFileTree.treeData.forEach(el => {
        let tmpChangeParent = this._travelConfigFileTreeNodes(el, status, checked)
        if (tmpChangeParent) {
          this.$set(el, 'checked', false)
        }
      })
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
    async handleDelete (row) {
      this.$Modal.confirm({
        title: this.$t('artifacts_delete_confirm'),
        'z-index': 1000000,
        onOk: async () => {
          const { status, message } = await deleteCiDatas({
            id: this.packageCiType,
            deleteData: [row.guid]
          })
          if (status === 'OK') {
            this.$Notice.success({
              title: this.$t('artifacts_delete_success'),
              desc: message
            })
            this.queryPackages()
            if (this.packageId === row.guid) {
              this.initPackageDetail()
            }
          }
        }
      })
    },
    async handleStatusChange (row, state) {
      const { status, message } = await operateCiState(this.packageCiType, row.guid, state)
      if (status === 'OK') {
        this.$Notice.success({
          title: state,
          desc: message
        })
        this.queryPackages()
        if (this.packageId === row.guid) {
          this.initPackageDetail()
        }
      }
    },
    renderConfigButton (params) {
      let row = params.row
      return [
        <Tooltip placement="top" max-width="200" content={this.$t('variable_select_key_tooltip')}>
          <Button disabled={!!row.conf_variable.fixedDate} size="small" type="primary" style="margin-right:5px;margin-bottom:5px;" onClick={async () => this.showConfigKeyModal(row)}>
            {this.$t('select_key')}
          </Button>
        </Tooltip>,
        // disable no dirty data or row is confirmed
        <Button disabled={!!(row.conf_variable.diffExpr === row.conf_variable.originDiffExpr || row.conf_variable.fixedDate)} size="small" type="info" style="margin-right:5px;margin-bottom:5px;" onClick={() => this.saveConfigVariableValue(row)}>
          {this.$t('artifacts_save')}
        </Button>
      ]
    },
    tabChange (tabName) {
      // console.log('tabChange', tabName)
    },
    showBatchBindModal () {
      // 复制一份数据用于临时使用bound勾选状态
      let tempBindData = this.formatPackageDetail(this.packageDetail)
      this.batchBindData = tempBindData.diff_conf_variable
      this.isShowBatchBindModal = true
    },
    batchBindSelectAll () {
      this.batchBindData.forEach(item => {
        item.bound = !this.isBatchBindAllChecked
      })
      this.isBatchBindAllChecked = !this.isBatchBindAllChecked
    },
    async saveBatchBindOperation () {
      this.isShowBatchBindModal = false
      this.tabTableLoading = true
      let tempData = this.formatPackageDetail(this.packageDetail)
      tempData.diff_conf_variable = this.batchBindData
      const { status, data } = await updatePackage(this.guid, this.packageId, tempData)
      if (status === 'OK') {
        let uData = this.formatPackageDetail(data)
        this.packageDetail = uData
        this.$Notice.success({
          title: this.$t('artifacts_bind_success')
        })
      }
      this.tabTableLoading = false
    },
    cancelBatchBindOperation () {
      this.isShowBatchBindModal = false
    },
    async showConfigKeyModal (row) {
      const diffConfigs = await retrieveEntity(cmdbPackageName, DIFF_CONFIGURATION)
      if (diffConfigs.status === 'OK') {
        this.allDiffConfigs = diffConfigs.data
        this.isShowConfigKeyModal = true
        this.currentConfigRow = row
      }
    },
    setConfigRowValue () {
      if (this.currentConfigValue) {
        this.packageDetail.diff_conf_file.forEach(elFile => {
          elFile.configKeyInfos.forEach(elFileVar => {
            if (this.currentConfigRow.key.toLowerCase() === elFileVar.key.toLowerCase()) {
              elFileVar.conf_variable.diffExpr = this.currentConfigValue
            }
          })
        })
        // this.$set(this.packageDetail.diff_conf_variable[this.currentConfigRow._index], 'diffExpr', this.currentConfigValue)
      }
      this.closeConfigSelectModal()
    },
    closeConfigSelectModal () {
      this.currentConfigValue = ''
      this.isShowConfigKeyModal = false
      this.currentConfigRow = {}
    },
    async updateEntity (params) {
      const { packageName, entityName } = params
      const { status, data } = await updateEntity(packageName, entityName, params.data)
      if (status === 'OK') {
        params.callback && params.callback(data)
      }
    },
    updateAutoFillValue (val, row) {
      // console.log('updateAutoFillValue', row)
    },
    checkFillRule (v) {
      if (v === null || v === undefined) {
        this.$Notice.error({
          title: 'Error',
          desc: this.$t('artifacts_auto_fill_rule_incomplete')
        })
        return false
      } else {
        return true
      }
    },
    async saveConfigVariableValue (row) {
      if (!this.checkFillRule(row.conf_variable.diffExpr)) {
        return
      }
      await this.updateEntity({
        packageName: cmdbPackageName,
        entityName: DIFF_CONFIGURATION,
        data: [
          {
            id: row.conf_variable.diffConfigGuid,
            variable_value: row.conf_variable.diffExpr
          }
        ]
      })
      this.packageDetail.diff_conf_file.forEach(elFile => {
        elFile.configKeyInfos.forEach(elFileVar => {
          if (row.key.toLowerCase() === elFileVar.key.toLowerCase()) {
            elFileVar.conf_variable.originDiffExpr = row.conf_variable.diffExpr
            elFileVar.conf_variable.diffExpr = row.conf_variable.diffExpr
          }
        })
      })
      this.$Notice.success({
        title: this.$t('artifacts_successed')
      })
    }
  },
  created () {
    this.fetchData()
    this.getSpecialConnector()
    this.getAllCITypesWithAttr()
    this.getAllSystemEnumCodes()
  },
  components: {
    CompareFile
  }
}
</script>

<style lang="scss" scoped>
.header-icon {
  float: right;
  margin: 3px 20px 0 0 !important;
}
.textarea-input {
  display: inline-block;
  width: 75%;
}
.artifact-management-files-card {
  border-color: darkgrey;
}

.artifact-management {
  padding: 20px;
  &-top-card {
    padding-bottom: 40px;
  }
  &-bottom-card {
    margin-top: 30px;
  }
  &-tree-body {
    position: relative;
  }
  &-save-button {
    float: right;
    margin-top: 10px;
  }
  &-files-card {
    // margin-top: 10px;
    &:first-of-type {
      margin-top: 0;
    }
  }
  &-icon {
    margin: 0 2px;
    position: relative;
  }
}
// .batchOperation {
//   position: absolute;
//   right: 60px;
// }
.bind-style {
  list-style: none;
  margin: 8px;
}
.baseline-cmp-new {
  color: #19be6b;
}
.baseline-cmp-changed {
  color: #2d8cf0;
}
.baseline-cmp-deleted {
  color: #cccccc;
}
</style>
