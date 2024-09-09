<template>
  <div id="weArtifacts" class="artifact-management" style="display: flex;">
    <div style="width: 20%;">
      <!-- 系统设计版本 -->
      <Card>
        <BaseHeaderTitle class="custom-title" :title="$t('artifacts_system_design_version')"></BaseHeaderTitle>
        <Select @on-change="selectSystemDesignVersion" @on-clear="clearSelectSystemDesign" label-in-name v-model="systemDesignVersion" filterable clearable>
          <Option v-for="version in systemDesignVersions" :value="version.guid || ''" :key="version.guid">{{ version.confirm_time ? `${version.name}[${version.confirm_time}]` : version.name }}</Option>
        </Select>
      </Card>
      <!-- 系统设计列表 -->
      <Card style="margin-top: 16px;">
        <BaseHeaderTitle class="custom-title" :title="$t('artifacts_system_design_list')"></BaseHeaderTitle>
        <div>
          <Tree :data="treeData" @on-select-change="selectTreeNode" class="tree-size"> </Tree>
          <Spin size="large" fix v-if="treeLoading">
            <Icon type="ios-loading" size="24" class="spin-icon-load"></Icon>
            <div>{{ $t('artifacts_loading') }}</div>
          </Spin>
        </div>
      </Card>
      <!-- eslint-disable-next-line vue/no-parsing-error -->
    </div>
    <div v-if="guid" style="margin-left: 16px;border: 1px solid #e8eaec;padding: 8px;width: 79%;">
      <div>
        <BaseHeaderTitle class="custom-title" :title="$t('art_sys_artch') + treePath.join(' / ')"></BaseHeaderTitle>
        <div style="display: flex;justify-content: space-between;margin-bottom: 8px;">
          <div>
            <Input v-model="tableFilter.key_name" @on-change="queryPackages(true)" :placeholder="$t('artifacts_package_name')" clearable style="width: 200px;margin-right: 8px;" />
            <Input v-model="tableFilter.guid" @on-change="queryPackages(true)" placeholder="GUID" clearable style="width: 200px;margin-right: 8px;" />
            <Input v-model="tableFilter.baseline_package" @on-change="queryPackages(true)" :placeholder="$t('baseline_package')" clearable style="width: 200px;margin-right: 8px;" />
            <Input v-model="tableFilter.upload_user" @on-change="queryPackages(true)" :placeholder="$t('artifacts_uploaded_by')" clearable style="width: 200px;margin-right: 8px;" />
          </div>
          <div>
            <!-- 本地上传 -->
            <Button icon="md-cloud-upload" style="background: #28aef3;border-color: #28aef3;margin-right: 8px;" type="info" :disabled="!btnGroupControl.upload_enabled" @click="pkgUpload('local')">{{ $t('art_upload_import') }}</Button>
            <!-- 在线选择 -->
            <Button icon="ios-apps" type="success" :disabled="!btnGroupControl.upload_from_nexus_enabled" @click="pkgUpload('online')">{{ $t('art_online_selection') }}</Button>
          </div>
        </div>
      </div>
      <div class="artifact-management-content">
        <!-- 包管理 -->
        <!-- 包列表table -->
        <ArtifactsSimpleTable :loading="tableLoading" :columns="tableColumns" :data="tableData" :page="pageInfo" @pageChange="pageChange" @pageSizeChange="pageSizeChange"></ArtifactsSimpleTable>
      </div>

      <Modal :mask-closable="false" v-model="isShowBatchBindModal" :width="800" :title="$t('multi_bind_config')">
        <Card>
          <div slot="title">
            <Checkbox border size="small" :indeterminate="isBatchBindIndeterminate" :value="isBatchBindAllChecked" @click.prevent.native="batchBindSelectAll">{{ $t('check_all') }}</Checkbox>
          </div>
          <div style="height: 300px; overflow-y: auto">
            <div class="bind-style" v-for="(bindData, index) in batchBindData" :key="index">
              <Checkbox v-model="bindData.bound">{{ bindData.key }}</Checkbox>
              <span style="margin-left: 10px; color: #c4c3c3; word-break: break-all">[{{ bindData.fileNames }}]</span>
            </div>
          </div>
        </Card>
        <div slot="footer">
          <Button @click="cancelBatchBindOperation">{{ $t('artifacts_cancel') }}</Button>
          <Button type="primary" @click="saveBatchBindOperation">{{ $t('artifacts_save') }}</Button>
        </div>
      </Modal>
      <Modal :mask-closable="false" v-model="isShowConfigKeyModal" :title="$t('artifacts_property_value_fill_rule')" @on-ok="setConfigRowValue" @on-cancel="closeConfigSelectModal">
        <div style="display: flex">
          <Input type="text" :placeholder="$t('artifacts_unselected')" v-model="customSearch"> </Input>
          <Button type="primary" @click="remoteConfigSearch" :loading="remoteLoading">{{ $t('search') }}</Button>
        </div>
        <Select ref="ddrop" :disabled="!allDiffConfigs || allDiffConfigs.length === 0" filterable clearable v-model="currentConfigValue" style="margin-top: 10px">
          <Option v-for="conf in allDiffConfigs.filter(conf => conf.variable_value && conf.code !== currentConfigRow.key)" :value="conf.variable_value" :key="conf.key_name">{{ conf.key_name }}</Option>
        </Select>
      </Modal>
      <Modal :mask-closable="false" v-model="isShowCiConfigModal" :title="$t('artifacts_property_value_fill_rule')" @on-ok="setCIConfigRowValue" @on-cancel="closeCIConfigSelectModal">
        <Form :label-width="120">
          <FormItem :label="$t('root_ci')">
            <Select filterable clearable v-model="currentConfigValue" @on-change="handleCIConfigChange">
              <Option v-for="conf in allCIConfigs" :value="conf.code" :key="conf.code">{{ conf.code }}</Option>
            </Select>
          </FormItem>
          <FormItem v-show="currentConfigValue" v-for="input in customInputs" :key="input.key" :label="input.key">
            <Input type="text" v-model="input.value" />
          </FormItem>
        </Form>
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

      <Modal v-model="isShowHistoryModal" :title="$t('operation_data_rollback')" :fullscreen="fullscreen" width="900">
        <p slot="header">
          <span>{{ $t('file_compare') }}</span>
          <Icon v-if="!fullscreen" @click="zoomModalMax" class="header-icon" type="ios-expand" />
          <Icon v-else @click="zoomModalMin" class="header-icon" type="ios-contract" />
        </p>
        <div v-if="isShowHistoryModal">
          <Table :columns="historyTableColumns" :data="historyTableData" :max-height="fileContentHeight.slice(0, -2)"></Table>
          <!-- <ArtifactsSimpleTable :loading="historyTableLoading" :columns="historyTableColumns" :data="historyTableData" :page="historyPageInfo" :pagable="false" @pageChange="historyPageChange" @pageSizeChange="historyPageSizeChange" @rowClick="onHistoryRowClick"> </ArtifactsSimpleTable> -->
        </div>
        <div slot="footer">
          <Button type="text" @click="onHistoryCancel()" :loading="historyBtnLoading">{{ $t('artifacts_cancel') }} </Button>
          <Button type="primary" @click="onHistoryConfirm()" :loading="historyBtnLoading">{{ $t('artifacts_save') }} </Button>
        </div>
      </Modal>
      <!-- 部署包上传组件 -->
      <PkgUpload ref="pkgUploadRef" @refreshTable="queryPackages"></PkgUpload>
      <!-- 脚本配置组件 -->
      <PkgConfig ref="pkgConfigRef" @queryPackages="queryPackages" @syncPackageDetail="syncPackageDetail"></PkgConfig>
      <!-- 差异化变量配置组件 -->
      <PkgDiffVariableConfig ref="pkgDiffVariableConfigRef"></PkgDiffVariableConfig>
      <!-- 发布物料包弹窗 -->
      <Modal v-model="releaseParams.showReleaseModal" :title="releaseParams.title" :mask-closable="false">
        <Form :label-width="120">
          <FormItem :label="$t('art_select_orch')">
            <Select style="width: 80%" v-model="releaseParams.selectedFlow" filterable>
              <Option v-for="item in releaseParams.flowList" :value="item.procDefId" :key="item.procDefId">{{ item.procDefName }}[{{ item.procDefVersion }}]</Option>
            </Select>
          </FormItem>
        </Form>
        <div slot="footer">
          <Button type="text" @click="onReleaseCancel()">{{ $t('artifacts_cancel') }} </Button>
          <Button type="primary" @click="onReleaseConfirm()" :disabled="releaseParams.selectedFlow === ''">{{ $t('art_ok') }} </Button>
        </div>
      </Modal>
    </div>
  </div>
</template>

<script>
import { getCiTypeAttr, getFlowLists, pushPkg, getSpecialConnector, getAllCITypesWithAttr, deleteCiDatas, operateCiState, operateCiStateWithData, getPackageCiTypeId, getSystemDesignVersion, getSystemDesignVersions, updateEntity, queryPackages, getPackageDetail, updatePackage, getCompareContent, queryHistoryPackages, getCITypeOperations, getVariableRootCiTypeId, getEntitiesByCiType, btnControl } from '@/api/server.js'
import { setCookie, getCookie } from '../util/cookie.js'
import iconFile from '../assets/file.png'
import iconFolder from '../assets/folder.png'
import axios from 'axios'
import Sortable from 'sortablejs'
import CompareFile from './compare-file'
import DisplayPath from './display-path'
import PkgUpload from '../components/pkg-upload.vue'
import PkgConfig from '../components/pkg-config.vue'
import PkgDiffVariableConfig from '../components/pkg-diff-variable.vue'
import { decode } from 'js-base64'
// 业务运行实例ciTypeId
const defaultAppRootCiTypeId = 'app_instance'
const defaultDBRootCiTypeId = 'rdb_instance'
// cmdb插件包名
const cmdbPackageName = 'wecmdb'
// 差异配置key_name
const DIFF_CONFIGURATION = 'diff_configuration'
// 单元设计
const UNIT_DESIGN = 'unit_design'
// // 部署包key_name
// const DEPLOY_PACKAGE = 'deploy_package'

const stateColor = {
  added_0: '#19be6b',
  added_1: '#19be6b',
  updated_0: '#5cadff',
  updated_1: '#5cadff',
  delete: '#ed4014',
  created: '#2b85e4',
  changed: 'purple',
  destroyed: '#ff9900'
}

export default {
  name: 'artifacts',
  data () {
    return {
      treePath: [], // 节点路径
      btnGroupControl: {
        upload_enabled: false, // 本地上传
        upload_from_nexus_enabled: false, // 在线上传
        push_to_nexus_enabled: false // 推送
      },
      tableFilter: {
        key_name: '',
        guid: '',
        baseline_package: '',
        upload_user: ''
      },
      releaseParams: {
        showReleaseModal: false,
        title: '',
        selectedFlow: '',
        guid: '',
        flowList: []
      },
      baselinePackageOptions: [],

      packageType: '',
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
      remoteLoading: false,
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
        {
          title: this.$t('artifacts_package_name'),
          key: 'name',
          minWidth: 100,
          render: (h, params) => {
            return <span>{params.row.name}</span>
          }
        },
        {
          title: 'GUID',
          width: 166,
          key: 'guid'
        },
        {
          title: this.$t('package_type'),
          key: 'package_type',
          width: 120,
          render: (h, params) => {
            return <span>{this.$t(params.row.package_type)}</span>
          }
        },
        {
          title: this.$t('baseline_package'),
          key: 'baseline_package',
          width: 120,
          render: (h, params) => {
            const baseLine = params.row.baseline_package ? params.row.baseline_package.key_name : ''
            return <span>{baseLine}</span>
          }
        },
        {
          title: this.$t('art_status'),
          key: 'state',
          width: 100,
          render: (h, params) => {
            const style = {
              color: stateColor[params.row.state] || '#2b85e4'
            }
            return <span style={style}>{params.row.state}</span>
          }
        },
        {
          title: this.$t('artifacts_uploaded_by'),
          key: 'upload_user',
          width: 100
        },
        {
          title: this.$t('artifacts_upload_time'),
          key: 'upload_time',
          width: 160
        },
        {
          title: this.$t('artifacts_update_by'),
          key: 'update_user',
          width: 100
        },
        {
          title: this.$t('artifacts_update_time'),
          key: 'update_time',
          width: 166
        },
        {
          title: this.$t('artifacts_action'),
          key: 'state',
          fixed: 'right',
          width: 230,
          render: (h, params) => {
            return (
              <div style="padding-top:5px">
                <div>
                  {!params.row.package_type && (
                    <Button type="warning" onClick={() => this.showFilesModal(params.row, event, true)} size="small" style="margin-right: 5px;margin-bottom: 5px;">
                      {this.$t('detail')}
                    </Button>
                  )}
                  <Tooltip content={this.$t('art_differentiated_variable_configuration')} placement="top" delay={500} transfer={true}>
                    <Button size="small" onClick={() => this.startConfigDiff(params.row, event)} style={{ marginRight: '5px', backgroundColor: '#D87093', borderColor: '#D87093', marginBottom: '2px' }}>
                      <Icon type="ios-medical" color="white" size="16"></Icon>
                    </Button>
                  </Tooltip>
                  <Tooltip content={this.$t('export')} placement="top" delay={500} transfer={true}>
                    <Button size="small" onClick={() => this.toExportPkg(params.row, event)} style={{ marginRight: '5px', backgroundColor: '#2db7f5', borderColor: '#2db7f5', marginBottom: '2px' }}>
                      <Icon type="md-cloud-download" color="white" size="16"></Icon>
                    </Button>
                  </Tooltip>
                  <Tooltip content={this.$t('push')} placement="top" delay={500} transfer={true}>
                    <Button size="small" disabled={!this.btnGroupControl.push_to_nexus_enabled} onClick={() => this.toPushPkg(params.row, event)} style={{ marginRight: '5px', backgroundColor: '#2db7f5', borderColor: '#2db7f5', marginBottom: '2px' }}>
                      <Icon type="md-cloud-upload" color="white" size="16"></Icon>
                    </Button>
                  </Tooltip>
                  <Tooltip content={this.$t('art_release_history')} placement="top" delay={500} transfer={true}>
                    <Button size="small" onClick={() => this.toRealsePkgHistory(params.row, event)} style={{ marginRight: '5px', backgroundColor: '#7728f5', borderColor: '#7728f5', marginBottom: '2px' }}>
                      <Icon type="ios-timer-outline" color="white" size="16"></Icon>
                    </Button>
                  </Tooltip>
                </div>
                <div>{this.renderActionButton(params)}</div>
              </div>
            )
          }
        }
      ],
      // ----------------
      // 单元设计回滚表格配置
      // ----------------
      isShowHistoryModal: false,
      historyTableColumns: [],
      historyTableData: [],
      historyTableLoading: false,
      historyPageInfo: {
        pageSize: 5,
        currentPage: 1,
        total: 0
      },
      tmpHistorySelected: null,
      historyBtnLoading: false,
      // ----------------
      // 包配置文件模态数据
      // ----------------
      packageId: '',
      isShowFilesModal: false,
      hideFooter: false,
      customInputs: [],
      customSearch: '',
      packageInput: {
        baseline_package: null,
        diff_conf_file: [],
        start_file_path: [],
        stop_file_path: [],
        deploy_file_path: [],
        is_decompression: 'true',

        db_diff_conf_file: [],
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

        db_diff_conf_file: [],
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
      isShowCiConfigModal: false,
      currentConfigRow: {},
      allDiffConfigs: [],
      allCIConfigs: [],
      rootCI: [
        { value: defaultAppRootCiTypeId, label: this.$t('APP') },
        { value: defaultDBRootCiTypeId, label: this.$t('DB') }
      ],
      activeTab: '',
      activeTabData: null,
      treeNodeSty: {
        display: 'inline-block',
        marginRight: '4px',
        maxWidth: '120px',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        verticalAlign: 'top'
      },
      currentConfigTab: '', // 配置当前tab

      showDiffConfigTab: false,
      currentDiffConfigTab: '', // 差异化变量当前tab
      packageName: ''
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
    },
    packageType: function (val) {
      this.currentConfigTab = val === this.constPackageOptions.db ? this.constPackageOptions.db : this.constPackageOptions.app
    }
  },
  methods: {
    // #region 部署包上传
    pkgUpload (type) {
      this.$refs.pkgUploadRef.openUploadDialog(type, this.guid)
    },
    // #endregion
    handleUpload (file) {
      var FR = new FileReader()
      FR.onload = ev => {
        if (ev.target && typeof ev.target.result === 'string') {
          const fileData = ev.target.result.split(',')
          const jsonObj = JSON.parse(decode(fileData[1]))
          const packageDetail = this.formatPackageDetail(jsonObj)
          this.packageDetail.diff_conf_file.forEach(p => {
            const findDiffFile = packageDetail.diff_conf_file.find(d => d.filename === p.filename)
            if (findDiffFile) {
              p.configKeyInfos.forEach(c => {
                const findConfVariable = findDiffFile.configKeyInfos.find(config => config.key === c.key)
                if (findConfVariable) {
                  c.conf_variable.diffExpr = findConfVariable.conf_variable.diffExpr
                }
              })
            }
          })

          this.packageDetail.db_diff_conf_file.forEach(p => {
            const findDiffFile = packageDetail.db_diff_conf_file.find(d => d.filename === p.filename)
            if (findDiffFile) {
              p.configKeyInfos.forEach(c => {
                const findConfVariable = findDiffFile.configKeyInfos.find(config => config.key === c.key)
                if (findConfVariable) {
                  c.conf_variable.diffExpr = findConfVariable.conf_variable.diffExpr
                }
              })
            }
          })
        }
      }
      FR.readAsDataURL(file)

      this.$Notice.success({
        title: 'Success',
        desc: this.$t('replaceTip')
      })

      return false
    },
    async exportData () {
      let { status, data } = await getPackageDetail(this.guid, this.packageId)
      if (status === 'OK') {
        let content = JSON.stringify(data)
        let fileName = `${this.packageName}-${new Date().getTime()}.json`
        let blob = new Blob([content])
        if ('msSaveOrOpenBlob' in navigator) {
          window.navigator.msSaveOrOpenBlob(blob, fileName)
        } else {
          if ('download' in document.createElement('a')) {
            // 非IE下载
            let elink = document.createElement('a')
            elink.download = fileName
            elink.style.display = 'none'
            elink.href = URL.createObjectURL(blob)
            document.body.appendChild(elink)
            elink.click()
            URL.revokeObjectURL(elink.href) // 释放URL 对象
            document.body.removeChild(elink)
          } else {
            // IE10+下载
            navigator.msSaveOrOpenBlob(blob, fileName)
          }
        }
      }
    },
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
    zoomModalMax () {
      this.fileContentHeight = window.screen.availHeight - 310 + 'px'
      this.fullscreen = true
    },
    zoomModalMin () {
      this.fileContentHeight = window.screen.availHeight * 0.4 + 'px'
      this.fullscreen = false
    },
    changeDiffConfigTab (tabName) {
      this.currentDiffConfigTab = tabName
      const tmp = this.currentDiffConfigTab === this.constPackageOptions.db ? 'db_diff_conf_file' : 'diff_conf_file'
      if (this.packageDetail[tmp].length > 0) {
        this.activeTab = this.packageDetail[tmp][0].filename
        this.activeTabData = this.packageDetail[tmp][0].configKeyInfos
      } else {
        this.activeTab = ''
        this.activeTabData = {}
      }
    },
    changeTab (tabName) {
      this.activeTab = tabName
      const tmp = this.currentDiffConfigTab === this.constPackageOptions.db ? 'db_diff_conf_file' : 'diff_conf_file'
      // this.activeTabData = this.packageDetail.diff_conf_file.find(item => item.shorFileName === this.activeTab).configKeyInfos
      this.activeTabData = this.packageDetail[tmp].find(item => item.filename === this.activeTab).configKeyInfos
    },
    changeRootCI (rootCI, params) {
      const tmp = this.currentDiffConfigTab === this.constPackageOptions.db ? 'db_diff_conf_file' : 'diff_conf_file'
      let activeTab = this.packageDetail[tmp].find(item => item.filename === this.activeTab)
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
        this.systemDesignVersions = sysData.data.contents.map(_ => _)
        if (this.systemDesignVersions.length > 0) {
          this.systemDesignVersion = this.systemDesignVersions[0].guid
          this.selectSystemDesignVersion(this.systemDesignVersion)
        }
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
      let { status, data } = await getAllCITypesWithAttr(['notCreated', 'created', 'dirty', 'deleted'])
      if (status === 'OK') {
        this.ciTypes = JSON.parse(JSON.stringify(data))
      }
    },
    async getCITypeOperations () {
      // TODO: fixme
      const buttonTypes = {
        Confirm: 'success',
        Rollback: 'warning',
        Delete: 'error',
        Discard: 'warning',
        Update: 'primary'
      }
      const resp = await getCITypeOperations(UNIT_DESIGN)
      this.statusOperations = resp.data.map(el => {
        if (el.operation_en === 'Update') {
          return {
            type: el.operation_en,
            label: this.$t('artifacts_configuration'),
            props: {
              type: buttonTypes[el.operation_en] || 'error',
              size: 'small'
            },
            actionType: el.operation_en
          }
        } else {
          return {
            type: el.operation_en,
            label: el.operation,
            props: {
              type: buttonTypes[el.operation_en] || 'error',
              size: 'small'
            },
            actionType: el.operation_en
          }
        }
      })
    },
    formatTreeData (array, level) {
      return array.map(_ => {
        _.title = _.name
        _.level = level
        _.render = (h, params) => {
          return (
            <div style="white-space: break-spaces;">
              <div style={this.treeNodeSty} title={_.code}>
                {_.code}
              </div>
              <div style={this.treeNodeSty} title={_.name}>
                [{_.name}]
              </div>
              <div style={`display:inline-block;max-width:60px;font-size:12px;vertical-align:top;color:${stateColor[_.state]}`}>{_.state}</div>
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
    async queryPackages (resetCurrentPage = false) {
      if (resetCurrentPage) {
        this.pageInfo.currentPage = 1
      }
      let params = {
        sorting: {
          asc: false,
          field: 'upload_time'
        },
        filters: [],
        paging: true,
        pageable: {
          pageSize: this.pageInfo.pageSize,
          startIndex: (this.pageInfo.currentPage - 1) * this.pageInfo.pageSize
        }
      }
      if (this.tableFilter.key_name !== '') {
        params.filters.push({
          name: 'key_name',
          operator: 'contains',
          value: this.tableFilter.key_name
        })
      }
      if (this.tableFilter.guid !== '') {
        params.filters.push({
          name: 'guid',
          operator: 'contains',
          value: this.tableFilter.guid
        })
      }
      if (this.tableFilter.baseline_package !== '') {
        params.filters.push({
          name: 'baseline_package',
          operator: 'contains',
          value: this.tableFilter.baseline_package
        })
      }
      if (this.tableFilter.upload_user !== '') {
        params.filters.push({
          name: 'upload_user',
          operator: 'contains',
          value: this.tableFilter.upload_user
        })
      }
      this.tableLoading = true
      let { status, data } = await queryPackages(this.guid, params)
      if (status === 'OK') {
        this.tableLoading = false
        this.tableData = data.contents.map(_ => {
          return {
            ..._
          }
        })
        const { pageSize, totalRows: total } = data.pageInfo
        const currentPage = this.pageInfo.currentPage
        this.pageInfo = { currentPage, pageSize, total }
      }
    },
    selectTreeNode (node) {
      if (node.length && node[0].level === 3) {
        this.guid = node[0].guid
        this.treePath = this.findPathByGuid(this.treeData, this.guid)
        this.queryPackages(true)
        this.initPackageDetail()
        this.btnControl()
      }
    },
    // 获取单元路径
    findPathByGuid (tree, targetGuid) {
      let path = []

      function searchTree (nodes, currentPath) {
        for (let node of nodes) {
          let newPath = currentPath.concat(`${node.code}[${node.title}]`)
          if (node.guid === targetGuid) {
            path = newPath
            return true
          }
          if (node.children && node.children.length > 0) {
            if (searchTree(node.children, newPath)) {
              return true
            }
          }
        }
        return false
      }
      searchTree(tree, [])
      return path
    },
    async btnControl () {
      let { status, data } = await btnControl()
      if (status === 'OK') {
        this.btnGroupControl = data
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
    setUploadActionHeader () {
      this.headers = {
        Authorization: 'Bearer ' + getCookie('accessToken')
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
          <div style="width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-top:4px">{res}</div>
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
    async startConfigDiff (row, event) {
      event.stopPropagation()
      this.$refs.pkgDiffVariableConfigRef.initDrawer(this.guid, row)
    },
    historyPageChange (currentPage) {
      this.historyPageInfo.currentPage = currentPage
    },
    historyPageSizeChange (pageSize) {
      this.historyPageInfo.pageSize = pageSize
    },
    onHistoryCancel () {
      this.tmpHistorySelected = null
      this.historyBtnLoading = false
      this.isShowHistoryModal = false
    },
    onHistoryRowClick (row) {
      this.tmpHistorySelected = row
    },
    async onHistoryConfirm () {
      if (this.tmpHistorySelected) {
        this.historyBtnLoading = true
        let rollBackData = JSON.parse(JSON.stringify(this.tmpHistorySelected))
        delete rollBackData.update_time
        delete rollBackData.nextOperations
        const { status } = await operateCiStateWithData(this.packageCiType, rollBackData, 'Rollback')
        if (status === 'OK') {
          this.isShowHistoryModal = false
          this.tmpHistorySelected = null
          this.queryPackages()
        }
        this.historyBtnLoading = false
      } else {
        this.$Notice.error({
          title: 'Error',
          desc: this.$t('must_select_one_item')
        })
        return false
      }
    },
    async showHistoryModal (row) {
      this.fullscreen = false
      this.isShowHistoryModal = true
      await this.getHistoryColums()
      const resp = await queryHistoryPackages(row.guid)
      this.historyTableData = resp.data || []
    },
    async getHistoryColums () {
      const { status, data } = await getCiTypeAttr(this.packageCiType)
      if (status === 'OK') {
        const lang = localStorage.getItem('lang') || 'zh-CN'
        this.historyTableColumns = data
          .filter(item => item.displayByDefault === 'yes')
          .map(item => {
            return {
              title: lang === 'zh-CN' ? item.name : item.propertyName,
              key: item.propertyName,
              width: 200,
              tooltip: true,
              ellipsis: true
            }
          })
      }
    },
    initPackageDetail () {
      this.packageDetail = {
        baseline_package: null,
        diff_conf_file: [],
        start_file_path: [],
        stop_file_path: [],
        deploy_file_path: [],
        is_compress: null,

        db_diff_conf_file: [],
        db_upgrade_directory: [],
        db_rollback_directory: [],
        db_upgrade_file_path: [],
        db_rollback_file_path: [],
        db_deploy_file_path: []
      }
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
    renderActionButton (params) {
      const row = params.row
      let operations = []
      if (row.package_type === this.constPackageOptions.image) {
        operations = this.statusOperations.filter(_ => row.nextOperations.indexOf(_.type) >= 0 && !['Update'].includes(_.type))
      } else {
        operations = this.statusOperations.filter(_ => row.nextOperations.indexOf(_.type) >= 0)
      }
      let typeToBtn = {
        Delete: {
          tip: this.$t('art_delete'),
          color: '#ed4014',
          icon: 'md-trash'
        },
        Update: {
          tip: this.$t('art_update'),
          color: '#2d8cf0',
          icon: 'md-create'
        },
        Rollback: {
          tip: this.$t('art_rollback'),
          color: 'rgb(255, 153, 0)',
          icon: 'ios-redo'
        },
        Confirm: {
          tip: this.$t('art_confirm'),
          color: '#a2ef4d',
          icon: 'ios-checkmark-circle'
        },
        Execute: {
          tip: this.$t('art_release'),
          color: '#18b55f',
          icon: 'ios-send'
        }
      }
      let res = []
      operations = operations.reverse()
      // 查找"Update"的数据项并移到数组的第一位
      let updateItemIndex = operations.findIndex(item => item.type === 'Update')

      if (updateItemIndex > -1) {
        let updateItem = operations.splice(updateItemIndex, 1)[0]
        operations.unshift(updateItem)
      }
      operations.forEach(op => {
        if (typeToBtn[op.type]) {
          res.push(
            <Tooltip content={typeToBtn[op.type].tip} placement="top" delay={500} transfer={true}>
              <Button size="small" onClick={() => this.changeStatus(row, op.type, event)} style={{ marginRight: '5px', backgroundColor: typeToBtn[op.type].color, borderColor: typeToBtn[op.type].color, marginBottom: '2px' }}>
                <Icon type={typeToBtn[op.type].icon} color="white" size="16"></Icon>
              </Button>
            </Tooltip>
          )
        }
      })
      return res
    },
    changeStatus (row, status, event) {
      event.stopPropagation()
      switch (status) {
        // 配置
        case 'Update':
          this.showFilesModal(row, event)
          break
        // 删除
        case 'Delete':
          this.handleDelete(row, status)
          break
        // 删除
        case 'Rollback':
          this.showHistoryModal(row)
          break
        // 确认
        default:
          this.handleStatusChange(row, status)
          break
      }
    },
    async showFilesModal (row, event, hideFooter = false) {
      event.stopPropagation()
      this.$refs.pkgConfigRef.open(this.guid, row, hideFooter)
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
      this.packageInput.is_decompression = row.is_decompression || 'true'

      this.packageInput.db_diff_conf_file = JSON.parse(JSON.stringify(this.packageDetail.db_diff_conf_file))
      this.packageInput.db_upgrade_directory = JSON.parse(JSON.stringify(this.packageDetail.db_upgrade_directory || []))
      this.packageInput.db_rollback_directory = JSON.parse(JSON.stringify(this.packageDetail.db_rollback_directory || []))
      this.packageInput.db_upgrade_file_path = JSON.parse(JSON.stringify(this.packageDetail.db_upgrade_file_path || []))
      this.packageInput.db_rollback_file_path = JSON.parse(JSON.stringify(this.packageDetail.db_rollback_file_path || []))
      this.packageInput.db_deploy_file_path = JSON.parse(JSON.stringify(this.packageDetail.db_deploy_file_path || []))

      this.packageId = row.guid
      this.hideFooter = hideFooter
      await this.getAllpkg()
      // this.isShowFilesModal = true

      this.$nextTick(() => {
        if (this.packageType !== this.constPackageOptions.db) {
          this.genSortable('diff_conf_file')
          this.genSortable('start_file_path')
          this.genSortable('stop_file_path')
          this.genSortable('deploy_file_path')
        }
        if (this.packageType !== this.constPackageOptions.app) {
          this.genSortable('db_diff_conf_file')
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
    batchBindSelectAll () {
      this.batchBindData.forEach(item => {
        item.bound = !this.isBatchBindAllChecked
      })
      this.isBatchBindAllChecked = !this.isBatchBindAllChecked
    },
    async saveBatchBindOperation () {
      this.isShowBatchBindModal = false
      this.tabTableLoading = true
      let params = {}
      const tmp = this.currentDiffConfigTab === this.constPackageOptions.db ? 'db_diff_conf_variable' : 'diff_conf_variable'
      params[tmp] = this.batchBindData
      const { status, data } = await updatePackage(this.guid, this.packageId, params)
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
      // const diffConfigs = await getEntitiesByCiType(cmdbPackageName, DIFF_CONFIGURATION, {})
      // if (diffConfigs.status === 'OK') {
      // this.allDiffConfigs = diffConfigs.data
      this.isShowConfigKeyModal = true
      this.currentConfigRow = row
      // }
    },
    async remoteConfigSearch () {
      const query = this.customSearch
      if (typeof query === 'string' && query.trim().length > 0) {
        this.remoteLoading = true
        const diffConfigs = await getEntitiesByCiType(cmdbPackageName, DIFF_CONFIGURATION, { criteria: {}, additionalFilters: [{ attrName: 'code', op: 'like', condition: query.trim() }] })
        if (diffConfigs) {
          this.allDiffConfigs = diffConfigs.data
          this.$nextTick(() => {
            this.$refs['ddrop'].toggleMenu(null, true)
          })
        }
        this.remoteLoading = false
      }
    },
    handleCIConfigChange (code) {
      if (code === undefined) return
      const value = this.allCIConfigs.find(ci => ci.code === code).value
      const customRegex = /\$\^(\w*)\$\^/g
      if (typeof value === 'string') {
        const temps = []
        let newSet = new Set()
        for (const matched of value.matchAll(customRegex)) {
          if (!newSet.has(matched[1])) {
            newSet.add(matched[1])
            temps.push({
              origin: matched[0],
              key: matched[1],
              value: ''
            })
          }
        }
        this.customInputs = temps
      }
    },
    async showCIConfigModal (row) {
      const res = await getVariableRootCiTypeId()
      if (res.status === 'OK') {
        const tab = this.currentDiffConfigTab.toLowerCase()
        const _template = res.data[`${tab}_template`]
        const resp = await getEntitiesByCiType(cmdbPackageName, _template, {})
        if (resp.status === 'OK') {
          if (Array.isArray(resp.data)) {
            this.allCIConfigs = resp.data.sort((first, second) => {
              const firstCode = first.code.toLowerCase()
              const secondCode = second.code.toLowerCase()
              return firstCode.localeCompare(secondCode)
            })
            this.isShowCiConfigModal = true
            this.currentConfigRow = row
          }
        }
      }
    },
    setConfigRowValue () {
      if (this.currentConfigValue) {
        const tmp = this.currentDiffConfigTab === this.constPackageOptions.db ? 'db_diff_conf_file' : 'diff_conf_file'
        this.packageDetail[tmp].forEach(elFile => {
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
    setCIConfigRowValue () {
      const currentConfigValueCodeTovalue = this.allCIConfigs.find(ci => ci.code === this.currentConfigValue).value
      if (currentConfigValueCodeTovalue) {
        const tmp = this.currentDiffConfigTab === this.constPackageOptions.db ? 'db_diff_conf_file' : 'diff_conf_file'
        this.packageDetail[tmp].forEach(elFile => {
          elFile.configKeyInfos.forEach(elFileVar => {
            if (this.currentConfigRow.key.toLowerCase() === elFileVar.key.toLowerCase()) {
              let resultStr = currentConfigValueCodeTovalue.replaceAll(/\$&(\w)*\$&/g, elFileVar.key)
              this.customInputs.forEach(item => {
                resultStr = resultStr.replaceAll(item.origin, item.value)
              })
              elFileVar.conf_variable.diffExpr = resultStr
            }
          })
        })
      }
      this.closeCIConfigSelectModal()
    },
    closeConfigSelectModal () {
      this.currentConfigValue = ''
      this.isShowConfigKeyModal = false
      this.currentConfigRow = {}
      this.customSearch = ''
      this.allDiffConfigs = []
    },
    closeCIConfigSelectModal () {
      this.currentConfigValue = ''
      this.isShowCiConfigModal = false
      this.currentConfigRow = {}
      this.customInputs = []
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
        ],
        callback: () => {
          const tmp = this.currentDiffConfigTab === this.constPackageOptions.db ? 'db_diff_conf_file' : 'diff_conf_file'
          this.packageDetail[tmp].forEach(elFile => {
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
      })
    },
    async toExportPkg (row, event) {
      event.stopPropagation()
      this.$Notice.info({
        title: `${this.$t('export')}`,
        desc: `${row.code} ${this.$t('export')} ${this.$t('senting')}`
      })
      await this.updateHeaders()
      const a = document.createElement('a')
      a.href = `/artifacts/packages/${row.guid}/download?token=${'Bearer ' + getCookie('accessToken')}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    },

    async toPushPkg (row, event) {
      event.stopPropagation()
      this.$Notice.info({
        title: `${this.$t('push')}`,
        desc: `${row.code} ${this.$t('push')} ${this.$t('senting')}`
      })
      const res = await pushPkg(this.guid, row.guid)
      if (res.status === 'OK') {
        this.$Notice.success({
          title: `${this.$t('push')}`,
          desc: `${res.data.name} ${this.$t('push')} ${this.$t('executionSuccessful')}`
        })
      }
    },
    // 发布物料包
    async toRealsePkg (row, event) {
      event.stopPropagation()
      this.releaseParams.title = this.$t('art_release_artifact_package') + ': ' + row.code
      this.releaseParams.selectedFlow = ''
      this.releaseParams.guid = row.guid
      this.releaseParams.flowList = []
      const res = await getFlowLists()
      if (res.status === 'OK') {
        this.releaseParams.flowList = res.data.data || []
        this.releaseParams.showReleaseModal = true
      }
    },
    onReleaseCancel () {
      this.releaseParams.showReleaseModal = false
    },
    onReleaseConfirm () {
      this.releaseParams.showReleaseModal = false
      window.sessionStorage.currentPath = ''
      const path = `${window.location.origin}/#/implementation/workflow-execution/normal-create?templateId=${this.releaseParams.selectedFlow}&subProc=main&targetId=${this.releaseParams.guid}`
      window.open(path, '_blank')
    },
    // 发布历史
    toRealsePkgHistory (row, event) {
      event.stopPropagation()
      window.sessionStorage.currentPath = ''
      const path = `${window.location.origin}/#/implementation/workflow-execution/normal-history?entityDisplayName=${row.key_name}&subProc=main&rootEntityGuid=${row.guid}`
      window.open(path, '_blank')
    },
    async updateHeaders () {
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
            },
            // eslint-disable-next-line handle-callback-err
            err => {
              refreshRequest = null
              window.location.href = window.location.origin + '/#/login'
            }
          )
        } else {
          this.setUploadActionHeader()
        }
      } else {
        window.location.href = window.location.origin + '/#/login'
      }
    },
    showSpin () {
      this.$Spin.show({
        render: h => {
          return h('div', [
            h('Icon', {
              class: 'demo-spin-icon-load',
              props: {
                type: 'ios-loading',
                size: 18
              }
            }),
            h('div', 'Loading')
          ])
        }
      })
      setTimeout(() => {
        this.$Spin.hide()
      }, 20000)
    }
  },
  created () {
    this.fetchData()
    this.getSpecialConnector()
    this.getAllCITypesWithAttr()
    this.getCITypeOperations()
  },
  components: {
    CompareFile,
    DisplayPath,
    PkgUpload,
    PkgConfig,
    PkgDiffVariableConfig
  }
}
</script>

<style lang="scss" scoped>
.tree-size ::v-deep .ivu-tree-title {
  font-size: 12px !important;
}
.tree-size ::v-deep .ivu-tree-empty {
  font-size: 12px !important;
}

.tree-size {
  height: calc(100vh - 300px);
  overflow-y: auto;
}
.artifact-management-content {
  // height: calc(100vh - 246px);
  // overflow-y: auto;
  padding-right: 8px;
  width: 100%;
}
.ivu-upload {
  display: inline-block;
}

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
    padding-bottom: 8px;
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
.bind-style {
  margin: 8px;
}

.config-tab :deep(.ivu-tabs-nav) {
  width: 100%;
}
.config-tab :deep(.ivu-tabs-tab) {
  width: 15%;
  text-align: center;
}
.custom-title {
  margin-bottom: 16px;
}
.custom-title ::v-deep .content {
  display: none;
}
.custom-title ::v-deep .ivu-icon-md-arrow-dropdown {
  display: none;
}
</style>
