<template>
  <Row id="weArtifacts" class="artifact-management">
    <Col span="6">
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
    <Col span="17" offset="1">
      <!-- 包管理 -->
      <Card v-if="guid" class="artifact-management-top-card">
        <!-- 本地上传 -->
        <Button type="info" ghost icon="ios-cloud-upload-outline" @click="getHeaders">
          {{ $t('artifacts_upload_new_package') }}
        </Button>
        <!-- 在线选择 -->
        <Button style="margin-left: 10px" type="info" ghost icon="ios-cloud-outline" @click="queryCurrentPkg">
          {{ $t('select_online') }}
        </Button>
        <Upload ref="uploadButton" :action="`/artifacts/unit-designs/${guid}/packages/upload`" :headers="headers" :on-success="onSuccess" :on-error="onError">
          <Button style="display:none" icon="ios-cloud-upload-outline">{{ $t('artifacts_upload_new_package') }}</Button>
        </Upload>
        <!-- <div v-if="uploaded" style="width: 100%;height:26px"></div> -->
        <!-- 包列表table -->
        <ArtifactsSimpleTable class="artifact-management-package-table" :loading="tableLoading" :columns="tableColumns" :data="tableData" :page="pageInfo" @pageChange="pageChange" @pageSizeChange="pageSizeChange" @rowClick="rowClick"></ArtifactsSimpleTable>
      </Card>
      <!-- 差异化变量 -->
      <Card v-if="packageDetail.diff_conf_file.length ? true : false" class="artifact-management-bottom-card artifact-management-top-card">
        <div class="batchOperation">
          <Button type="primary" @click="showBatchBindModal">绑定管理</Button>
        </div>
        <Tabs @on-click="tabChange">
          <TabPane v-for="(item, index) in packageDetail.diff_conf_file" :label="item.shorFileName" :name="item.shorFileName" :key="index">
            <Spin size="large" fix v-if="tabTableLoading">
              <Icon type="ios-loading" size="24" class="spin-icon-load"></Icon>
              <div>{{ $t('artifacts_loading') }}</div>
            </Spin>
            <Table :data="item.configKeyInfos || []" :columns="attrsTableColomnOptions"></Table>
          </TabPane>
        </Tabs>
        <Modal :mask-closable="false" v-model="isShowBatchBindModal" title="批量绑定/解绑" @on-ok="saveBatchBindOperation" @on-cancel="cancelBatchBindOperation">
          <Card>
            <div slot="title">
              <Checkbox border size="small" :indeterminate="isBatchBindIndeterminate" :value="isBatchBindAllChecked" @click.prevent.native="batchBindSelectAll">全选</Checkbox>
            </div>
            <ul style="height:300px;overflow-y:auto">
              <li class="bind-style" v-for="(bindData, index) in batchBindData" :key="index">
                <Checkbox v-model="bindData.bound">{{ bindData.key }}</Checkbox>
                <div style="margin-left:20px;color: #c4c3c3;">{{ bindData.fileNames }}</div>
              </li>
            </ul>
          </Card>
        </Modal>
        <Modal :mask-closable="false" v-model="isShowConfigKeyModal" :title="$t('artifacts_property_value_fill_rule')" @on-ok="setConfigRowValue" @on-cancel="closeConfigSelectModal">
          <Select filterable clearable v-model="currentConfigValue">
            <Option v-for="conf in allDiffConfigs.filter(conf => conf.variable_value && conf.code !== currentConfigRow.key)" :value="conf.variable_value" :key="conf.key_name">{{ conf.key_name }}</Option>
          </Select>
        </Modal>
      </Card>
      <!-- eslint-disable-next-line vue/no-parsing-error -->
    </Col>
  </Row>
</template>

<script>
import { getSpecialConnector, getAllCITypesWithAttr, getAllSystemEnumCodes, deleteCiDatas, operateCiState, getPackageCiTypeId, getSystemDesignVersion, getSystemDesignVersions, retrieveEntity, updateEntity, queryPackages, queryArtifactsList, getPackageDetail, updateDiffConfigs } from '@/api/server.js'
import { setCookie, getCookie } from '../util/cookie.js'
// import iconFile from '../assets/file.png'
// import iconFolder from '../assets/folder.png'
import axios from 'axios'
// import Sortable from 'sortablejs'

// 业务运行实例ciTypeId
const rootCiTypeId = 50
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
      systemDesignVersions: [],
      systemDesignVersion: '',
      // 系统设计树形数据
      treeData: [],
      treeLoading: false,
      pageInfo: {
        pageSize: 5,
        currentPage: 1,
        total: 0
      },
      guid: '',
      isShowOnlineModal: false,
      currentPackageList: [],
      // 上传认证头
      headers: {},
      // 单元设计包列表table
      tableLoading: false,
      tableData: [],
      tableColumns: [
        {
          title: this.$t('artifacts_package_name'),
          key: 'name',
          render: (h, params) => this.renderCell(params.row.name)
        },
        {
          title: this.$t('artifacts_upload_time'),
          width: 120,
          key: 'upload_time'
        },
        {
          title: this.$t('artifacts_md5_value'),
          key: 'md5_value',
          render: (h, params) => this.renderCell(params.row.md5_value)
        },
        {
          title: this.$t('artifacts_uploaded_by'),
          key: 'upload_user',
          render: (h, params) => this.renderCell(params.row.upload_user)
        },
        {
          title: this.$t('artifacts_config_files'),
          key: 'diff_conf_file',
          render: (h, params) => this.renderCell(params.row.diff_conf_file)
        },
        {
          title: this.$t('artifacts_start_script'),
          key: 'start_file_path',
          render: (h, params) => this.renderCell(params.row.start_file_path)
        },
        {
          title: this.$t('artifacts_stop_script'),
          key: 'stop_file_path',
          render: (h, params) => this.renderCell(params.row.stop_file_path)
        },
        {
          title: this.$t('artifacts_deploy_script'),
          key: 'deploy_file_path',
          render: (h, params) => this.renderCell(params.row.deploy_file_path)
        },
        {
          title: this.$t('is_decompression'),
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
      isShowFilesModal: false,
      packageInput: {
        diff_conf_file: [],
        start_file_path: [],
        stop_file_path: [],
        deploy_file_path: [],
        is_decompression: 0
      },
      // baseline package
      configuration: '',
      statusOperations: [],
      packageDetail: {
        baseline_package: null,
        diff_conf_file: [],
        start_file_path: [],
        stop_file_path: [],
        deploy_file_path: [],
        is_compress: null
      },
      isShowBatchBindModal: false,
      batchBindData: [],
      isBatchBindIndeterminate: false,
      isBatchBindAllChecked: false,
      tabTableLoading: false,
      currentConfigValue: '',
      isShowConfigKeyModal: false,
      currentConfigRow: {},
      allDiffConfigs: [],
      attrsTableColomnOptions: [
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
          title: this.$t('artifacts_property_isbind'),
          width: 70,
          render: (h, params) => {
            // show static view only if confirmed
            return <span>{params.row.conf_variable.bound ? 'Y' : 'N'}</span>
          }
        },
        {
          title: this.$t('artifacts_property_name'),
          width: 200,
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
          title: this.$t('artifacts_property_value_fill_rule'),
          render: (h, params) => {
            // show static view only if confirmed
            return params.row.conf_variable.fixed_date ? (
              <ArtifactsAutoFill style="margin-top:5px;" allCiTypes={this.ciTypes} specialDelimiters={this.specialDelimiters} rootCiTypeId={rootCiTypeId} isReadOnly={true} v-model={params.row.conf_variable.diffExpr} cmdbPackageName={cmdbPackageName} />
            ) : (
              <div style="align-items:center;display:flex;">
                <ArtifactsAutoFill style="margin-top:5px;width:calc(100% - 55px);" allCiTypes={this.ciTypes} specialDelimiters={this.specialDelimiters} rootCiTypeId={rootCiTypeId} v-model={params.row.conf_variable.diffExpr} onUpdateValue={val => this.updateAutoFillValue(val, params.row)} cmdbPackageName={cmdbPackageName} />
              </div>
            )
          }
        },
        {
          title: this.$t('artifacts_action'),
          key: 'state',
          width: 150,
          render: (h, params) => {
            return <div style="padding-top:5px">{this.renderConfigButton(params)}</div>
          }
        }
      ]
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
            <div>
              <span style="margin-right:4px;">{_.data.code}</span>
              <span style="margin-right:10px;font-size:12px">[{_.data.name}]</span>
              <span style={`font-size:12px;color:${color[_.data.state_code]}`}>{_.data.state_code}</span>
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
      this.tabData = []
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
        this.tabData = []
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
    async queryCurrentPkg () {
      const { status, data } = await queryArtifactsList(this.guid, { filters: [], paging: false })
      if (status === 'OK') {
        this.currentPackageList = data
        this.isShowOnlineModal = true
      }
    },
    renderCell (content) {
      let res = ''
      if (Array.isArray(content)) {
        content.forEach(c => {
          res += c.filename + '|'
        })
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
    rowClick (row) {
      this.packageId = row.guid
      // 获取包文件及差异化变量数据
      this.getTabDatas()
    },
    async getTabDatas () {
      await this.syncPackageDetail()
    },
    initPackageDetail () {
      this.packageDetail = {
        baseline_package: null,
        diff_conf_file: [],
        start_file_path: [],
        stop_file_path: [],
        deploy_file_path: [],
        is_compress: null
      }
    },
    formatPackageDetail (data) {
      let dataString = JSON.stringify(data)
      let copyData = JSON.parse(dataString)
      copyData.diff_conf_variable.forEach(elVar => {
        // 记录原始值
        elVar.originDiffExpr = elVar.diffExpr
        elVar.withinFiles = []
        elVar.withinFileIndexes = []
        let index = 0
        copyData.diff_conf_file.forEach(elFile => {
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
    async showFilesModal (row) {
      console.log('showFilesModal', row)
      // TODO: (roywu)
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
        <Button disabled={!!row.conf_variable.fixed_date} size="small" type="primary" style="margin-right:5px;margin-bottom:5px;" onClick={async () => this.showConfigKeyModal(row)}>
          {this.$t('select_key')}
        </Button>,
        // disable no dirty data or row is confirmed
        <Button disabled={!!(row.conf_variable.diffExpr === row.conf_variable.originDiffExpr || row.conf_variable.fixed_date)} size="small" type="info" style="margin-right:5px;margin-bottom:5px;" onClick={() => this.saveConfigVariableValue(row)}>
          {this.$t('artifacts_save')}
        </Button>
      ]
    },
    tabChange (tabName) {
      console.log('tabChange', tabName)
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
      let tempData = this.formatPackageDetail(this.packageDetail)
      tempData.diff_conf_variable = this.batchBindData
      const { status, data } = await updateDiffConfigs(this.guid, this.packageId, tempData)
      if (status === 'OK') {
        let uData = this.formatPackageDetail(data)
        this.packageDetail = uData
      }
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
      console.log('updateAutoFillValue', row)
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
    }
  },
  created () {
    this.fetchData()
    this.getSpecialConnector()
    this.getAllCITypesWithAttr()
    this.getAllSystemEnumCodes()
  }
}
</script>

<style lang="scss" scoped>
.textarea-input {
  display: inline-block;
  width: 80%;
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
    margin-top: 10px;

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
</style>
