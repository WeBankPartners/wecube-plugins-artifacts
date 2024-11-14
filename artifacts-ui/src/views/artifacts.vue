<template>
  <div id="weArtifacts" class="artifact-management" style="display: flex;">
    <div style="width: 25%">
      <!-- 系统设计版本 -->
      <Card>
        <CustomTitle :title="$t('artifacts_system_design_version')"></CustomTitle>
        <Select @on-change="selectSystemDesignVersion" @on-clear="clearSelectSystemDesign" label-in-name v-model="systemDesignVersion" filterable clearable>
          <Option v-for="version in systemDesignVersions" :value="version.guid || ''" :key="version.guid" :label="version.code + ' [' + version.name + '] ' + (version.confirm_time ? version.confirm_time : '')">
            {{ version.code }} [{{ version.name }}] <span style="float: right;color: #A7ACB5">{{ version.confirm_time ? version.confirm_time : '' }}</span></Option
          >
        </Select>
      </Card>
      <!-- 系统设计列表 -->
      <Card style="margin-top: 16px;">
        <CustomTitle :title="$t('artifacts_system_design_list')"></CustomTitle>
        <!-- <BaseHeaderTitle class="custom-title" :title="$t('artifacts_system_design_list')"></BaseHeaderTitle> -->
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
    <div v-if="guid" class="right-zone">
      <div>
        <div style="display: flex;justify-content: space-between;">
          <CustomTitle :title="customTreePath"></CustomTitle>
          <div>
            <!-- 本地上传 -->
            <Button icon="md-cloud-upload" style="background: #28aef3;border-color: #28aef3;margin-right: 8px;" type="info" :disabled="!btnGroupControl.upload_enabled" @click="pkgUpload('local')">{{ $t('art_upload_import') }}</Button>
            <!-- 在线选择 -->
            <Button icon="ios-apps" type="success" :disabled="!btnGroupControl.upload_from_nexus_enabled" @click="pkgUpload('online')">{{ $t('art_online_selection') }}</Button>
          </div>
        </div>
        <div>
          <div class="search-box">
            <div ref="container" id="search-zone" :style="{ display: 'flex', 'flex-wrap': searchConfig.expandSearch ? '' : 'wrap' }">
              <div class="seearch-pkg-variable" style="margin-right: 8px;">
                <RadioGroup v-model="tableFilter.package_type" type="button" button-style="solid" @on-change="paramsChange(true, true)">
                  <Radio v-for="pkg in packageOptions" :label="pkg.value" :disabled="pkg.num === 0" :key="pkg.value">{{ pkg.label }}({{ pkg.num }})</Radio>
                </RadioGroup>
              </div>
              <div :style="{ display: searchConfig.expandSearch && searchConfig.hideIndex <= 2 ? 'none' : 'block' }" class="search-item">
                <Input v-model="tableFilter.key_name" @on-change="paramsChange(true)" :placeholder="$t('artifacts_package_name')" style="width:100%" clearable />
              </div>
              <div :style="{ display: searchConfig.expandSearch && searchConfig.hideIndex <= 3 ? 'none' : 'block' }" class="search-item">
                <Input v-model="tableFilter.guid" @on-change="paramsChange(true)" placeholder="GUID" style="width:100%" clearable />
              </div>
              <div :style="{ display: searchConfig.expandSearch && searchConfig.hideIndex <= 4 ? 'none' : 'block' }" class="search-item">
                <Select clearable filterable @on-change="paramsChange(true)" :placeholder="$t('baseline_package')" style="width:100%" v-model="tableFilter.baseline_package">
                  <Option v-for="conf in baselinePackageOptions" :value="conf.guid" :key="conf.name">{{ conf.name }}</Option>
                </Select>
              </div>
              <div :style="{ display: searchConfig.expandSearch && searchConfig.hideIndex <= 5 ? 'none' : 'block' }" class="search-item">
                <Select clearable filterable @on-change="paramsChange(true)" @on-clear="tableFilter.upload_user = ''" :placeholder="$t('artifacts_uploaded_by')" style="width:100%" v-model="tableFilter.upload_user">
                  <Option v-for="user in userList" :value="user.username" :key="user.id">{{ user.username }}</Option>
                </Select>
              </div>
            </div>
          </div>
          <div style="display: inline-block;width:30px;vertical-align: middle;">
            <Icon v-if="searchConfig.expandSearch" @click="searchConfig.expandSearch = false" size="28" color="#2d8cf0" type="ios-arrow-down" style="cursor: pointer;" />
            <Icon v-else @click="searchConfig.expandSearch = true" size="28" color="#2d8cf0" type="ios-arrow-up" style="cursor: pointer;" />
          </div>
        </div>
      </div>
      <div class="artifact-management-content">
        <!-- 包管理 -->
        <!-- 包列表table -->
        <ArtifactsSimpleTable :loading="tableLoading" :columns="tableColumns" :data="tableData" :page="pageInfo" @pageChange="pageChange" @pageSizeChange="pageSizeChange"></ArtifactsSimpleTable>
      </div>

      <Modal v-model="isShowHistoryModal" :title="$t('operation_data_rollback')" :fullscreen="fullscreen" width="900">
        <p slot="header">
          <span>{{ $t('art_rollback') }}</span>
          <Icon v-if="!fullscreen" @click="zoomModalMax" class="header-icon" type="ios-expand" />
          <Icon v-else @click="zoomModalMin" class="header-icon" type="ios-contract" />
        </p>
        <div v-if="isShowHistoryModal">
          <Table :columns="historyTableColumns" :data="historyTableData" :max-height="fileContentHeight.slice(0, -2)" highlight-row @on-row-click="onHistoryRowClick"></Table>
          <!-- <ArtifactsSimpleTable :loading="historyTableLoading" :columns="historyTableColumns" :data="historyTableData" :page="historyPageInfo" :pagable="false" @pageChange="historyPageChange" @pageSizeChange="historyPageSizeChange" @rowClick="onHistoryRowClick"> </ArtifactsSimpleTable> -->
        </div>
        <div slot="footer">
          <Button type="text" @click="onHistoryCancel()" :loading="historyBtnLoading">{{ $t('artifacts_cancel') }} </Button>
          <Button type="primary" @click="onHistoryConfirm()" :loading="historyBtnLoading">{{ $t('artifacts_save') }} </Button>
        </div>
      </Modal>
      <!-- 部署包上传组件 -->
      <PkgUpload ref="pkgUploadRef" @refreshTable="refreshTable"></PkgUpload>
      <!-- 脚本配置组件 -->
      <PkgConfig ref="pkgConfigRef" @queryPackages="queryPackages"></PkgConfig>
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
import { getCiTypeAttr, getFlowLists, pushPkg, getAllCITypesWithAttr, deleteCiDatas, operateCiState, operateCiStateWithData, getPackageCiTypeId, getSystemDesignVersion, getSystemDesignVersions, queryPackages, queryHistoryPackages, getCITypeOperations, sysConfig, getPkgTypeNum, getUserList } from '@/api/server.js'
import { setCookie, getCookie } from '../util/cookie.js'
import axios from 'axios'
import DisplayPath from './display-path'
import CustomTitle from '../components/custom-title.vue'
import PkgUpload from '../components/pkg-upload.vue'
import PkgConfig from '../components/pkg-config.vue'
import PkgDiffVariableConfig from '../components/pkg-diff-variable.vue'
import { debounce } from 'lodash'
// 业务运行实例ciTypeId
const defaultAppRootCiTypeId = 'app_instance'
const defaultDBRootCiTypeId = 'rdb_instance'
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
      customTreePath: '',
      btnGroupControl: {
        upload_enabled: false, // 本地上传
        upload_from_nexus_enabled: false, // 在线上传
        push_to_nexus_enabled: false // 推送
      },
      searchConfig: {
        expandSearch: true,
        needCheckWarp: false,
        hideIndex: 5
      },
      userList: [],
      tableFilter: {
        key_name: '',
        package_type: '',
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
      constPackageOptions: {
        db: 'DB',
        app: 'APP',
        mixed: 'APP&DB',
        image: 'IMAGE',
        rule: 'RULE'
      },
      packageOptions: [
        { label: this.$t('APP&DB'), value: 'APP&DB', num: 0 },
        { label: this.$t('APP'), value: 'APP', num: 0 },
        { label: this.$t('DB'), value: 'DB', num: 0 },
        { label: this.$t('IMAGE'), value: 'IMAGE', num: 0 },
        { label: this.$t('RULE'), value: 'RULE', num: 0 }
      ],
      fullscreen: false,
      fileContentHeight: window.screen.availHeight * 0.4 + 'px',
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
      // 上传认证头
      headers: {},
      // 单元设计包列表table
      pageInfo: {
        pageSize: 10,
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
          minWidth: 160,
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
          title: this.$t('baseline_package'),
          key: 'baseline_package',
          width: 120,
          render: (h, params) => {
            const baseLine = params.row.baseline_package ? params.row.baseline_package.key_name : '-'
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
      hideFooter: false,
      // -------------------
      // 包配置文件选择模态数据
      // -------------------
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
      // 选择差异化变量临时保存值
      rootCI: [
        { value: defaultAppRootCiTypeId, label: this.$t('APP') },
        { value: defaultDBRootCiTypeId, label: this.$t('DB') }
      ],
      treeNodeSty: {
        display: 'inline-block',
        marginRight: '4px',
        maxWidth: '150px',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        verticalAlign: 'top'
      }
    }
  },
  computed: {},
  methods: {
    updateWrappedItems () {
      if (document.getElementById('search-zone')) {
        const widths = document.getElementById('search-zone').offsetWidth
        this.searchConfig.hideIndex = Math.floor((widths - 100) / 200)
      }
    },
    // 获取基线列表
    async getbaselinePkg () {
      this.baselinePackageOptions = []
      let params = {
        resultColumns: ['guid', 'name', 'package_type', 'diff_conf_file', 'start_file_path', 'stop_file_path', 'deploy_file_path', 'is_decompression', 'db_diff_conf_file', 'db_upgrade_directory', 'db_rollback_directory', 'db_deploy_file_path', 'db_upgrade_file_path', 'db_rollback_file_path'],
        sorting: {
          asc: false,
          field: 'upload_time'
        },
        filters: [],
        paging: true,
        pageable: {
          pageSize: 1000,
          startIndex: 0
        }
      }
      if (this.tableFilter.package_type !== '') {
        params.filters.push({
          name: 'package_type',
          operator: 'eq',
          value: this.tableFilter.package_type
        })
      }
      let { status, data } = await queryPackages(this.guid, params)
      if (status === 'OK') {
        this.baselinePackageOptions = data.contents.map(item => {
          return {
            ...item
          }
        })
      }
    },
    // #region 部署包上传
    pkgUpload (type) {
      this.$refs.pkgUploadRef.openUploadDialog(type, this.guid, this.tableFilter.package_type)
    },
    // #endregion
    zoomModalMax () {
      this.fileContentHeight = window.screen.availHeight - 310 + 'px'
      this.fullscreen = true
    },
    zoomModalMin () {
      this.fileContentHeight = window.screen.availHeight * 0.4 + 'px'
      this.fullscreen = false
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
              <div style={this.treeNodeSty} title={_.key_name}>
                {_.key_name}
              </div>
              <div style={this.treeNodeSty} title={_.name}>
                [{_.name}]
              </div>
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
      this.uploaded = false
    },
    clearSelectSystemDesign () {
      this.systemDesignVersion = ''
      this.treeData = []
    },
    paramsChange: debounce(function (resetCurrentPage, clearBaseline = false) {
      if (clearBaseline) {
        this.tableFilter.baseline_package = ''
      }
      this.queryPackages(resetCurrentPage)
      this.getbaselinePkg()
    }, 300),
    // 包上传成功后刷新列表
    refreshTable (packageType) {
      this.tableFilter.package_type = packageType
      this.queryPackages()
    },
    async getPkgTypeNum () {
      let { status, data } = await getPkgTypeNum(this.guid)
      if (status === 'OK') {
        this.packageOptions.forEach(item => {
          item.num = data[item.value]
        })
        if (this.tableFilter.package_type === '') {
          const find = this.packageOptions.find(item => item.num > 0)
          this.tableFilter.package_type = find ? find.value : 'DB'
        }
      }
    },
    async getUserList () {
      let { status, data } = await getUserList()
      if (status === 'OK') {
        this.userList = data || []
      }
    },
    async queryPackages (resetCurrentPage = false) {
      await this.getPkgTypeNum()
      this.getUserList()
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
      if (this.tableFilter.package_type !== '') {
        params.filters.push({
          name: 'package_type',
          operator: 'eq',
          value: this.tableFilter.package_type
        })
      }
      if (this.tableFilter.guid !== '') {
        params.filters.push({
          name: 'guid',
          operator: 'contains',
          value: this.tableFilter.guid
        })
      }
      if (this.tableFilter.baseline_package) {
        params.filters.push({
          name: 'baseline_package',
          operator: 'contains',
          value: this.tableFilter.baseline_package
        })
      }
      if (this.tableFilter.upload_user) {
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
        this.customTreePath = this.$t('art_sys_artch') + this.treePath.join(' / ')
        if (this.customTreePath.length > 60) {
          this.customTreePath = this.customTreePath.slice(0, 60) + '...'
        }
        this.tableFilter.package_type = ''
        this.queryPackages(true)
        this.getbaselinePkg()
        this.btnControl()
        this.$nextTick(() => {
          this.updateWrappedItems()
        })
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
      let { status, data } = await sysConfig()
      if (status === 'OK') {
        this.btnGroupControl = data
      }
    },
    setUploadActionHeader () {
      this.headers = {
        Authorization: 'Bearer ' + getCookie('accessToken')
      }
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
        case 'Execute':
          this.toRealsePkg(row, event)
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
      }
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
      const res = await getFlowLists(row.guid)
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
    }
  },
  created () {
    this.fetchData()
    this.getAllCITypesWithAttr()
    this.getCITypeOperations()
  },
  components: {
    DisplayPath,
    CustomTitle,
    PkgUpload,
    PkgConfig,
    PkgDiffVariableConfig
  },
  mounted () {
    // 初始检查元素状态
    // this.updateWrappedItems()
    // 添加窗口大小监听器
    window.addEventListener('resize', this.updateWrappedItems)
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.updateWrappedItems)
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

.custom-title {
  margin-bottom: 16px;
}
.custom-title ::v-deep .content {
  display: none;
}
.custom-title ::v-deep .ivu-icon-md-arrow-dropdown {
  display: none;
}

.right-zone {
  margin-left: 16px;
  border: 1px solid #e8eaec;
  padding: 8px;
  width: 74%;
  min-width: 500px;
}

.search-item {
  width: 200px;
  margin-right: 8px;
  margin-bottom: 8px;
}
.search-box {
  width: calc(100% - 40px);
  display: inline-block;
}
</style>
<style lang="scss">
.seearch-pkg-variable {
  min-width: 500px;
  .ivu-radio-group-button .ivu-radio-wrapper-checked {
    background: #2d8cf0;
    color: #fff;
  }
  .ivu-radio-group-button .ivu-radio-wrapper-checked:hover {
    border-color: #57a3f3;
    color: white;
  }
}
</style>
