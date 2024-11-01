<template>
  <Drawer :title="pkgName" v-model="openDrawer" class="custom-drawer" :scrollable="false" width="1300">
    <Spin size="large" fix v-if="spinShow"></Spin>
    <div v-if="showDiffConfigTab">
      <Tabs :value="currentDiffConfigTab" @on-click="changeDiffConfigTab" type="card" name="diffConfig" style="width: 100%;">
        <div slot="extra">
          <Upload :before-upload="handleUpload" action="">
            <Button type="primary" style="margin-right: 8px;">
              <img src="../assets/import.png" class="btn-img" alt="" />
              {{ $t('import') }}
            </Button>
          </Upload>
          <Button type="info" class="btn-right" @click="exportData">
            <img src="../assets/export.png" class="btn-img" alt="" />
            {{ $t('export') }}
          </Button>
        </div>
        <TabPane :disabled="packageType === constPackageOptions.db" :label="$t('APP')" name="APP" tab="diffConfig">
          <Spin size="large" fix v-if="tabTableLoading">
            <Icon type="ios-loading" size="24" class="spin-icon-load"></Icon>
            <div>{{ $t('artifacts_loading') }}</div>
          </Spin>
          <Tabs :value="activeTab" @on-click="val => changeTab(val, packageDetail.diff_conf_file)" name="APP">
            <Button type="primary" style="vertical-align: text-top;" size="small" :disabled="packageDetail.diff_conf_file.length === 0" @click="showBatchBindModal" slot="extra">{{ $t('multi_bind_config') }}</Button>
            <TabPane v-for="(item, index) in packageDetail.diff_conf_file" :disabled="item.configKeyInfos.length === 0" :label="item.shorFileName + ' (' + item.configKeyInfos.length + ')'" :name="item.filename" :key="index" tab="APP">
              <div class="pkg-variable">
                <RadioGroup v-model="prefixType" type="button" button-style="solid" @on-change="typeChange(item.configKeyInfos || [])" style="margin-right: 5px">
                  <Radio v-for="prefix in variablePrefixType" :label="prefix.key" :key="prefix.key" :disabled="getNum(item.configKeyInfos || [], prefix.filterKey) === 0">{{ prefix.label }}({{ getNum(item.configKeyInfos || [], prefix.filterKey) }})</Radio>
                </RadioGroup>
              </div>
              <Table :data="tempTableData" :height="maxHeight" :columns="attrsTableColomnOptions" size="small"></Table>
            </TabPane>
          </Tabs>
          <div v-if="packageDetail.diff_conf_file.length === 0" style="text-align: center;">
            {{ $t('art_no_data') }}
          </div>
        </TabPane>
        <TabPane :disabled="packageType === constPackageOptions.app" :label="$t('DB')" name="DB" tab="diffConfig">
          <Spin size="large" fix v-if="tabTableLoading">
            <Icon type="ios-loading" size="24" class="spin-icon-load"></Icon>
            <div>{{ $t('artifacts_loading') }}</div>
          </Spin>
          <Tabs :value="activeTab" @on-click="val => changeTab(val, packageDetail.db_diff_conf_file)" name="DB">
            <Button type="primary" style="vertical-align: text-top;" size="small" :disabled="packageDetail.db_diff_conf_file.length === 0" @click="showBatchBindModal" slot="extra">{{ $t('multi_bind_config') }}</Button>
            <TabPane v-for="(item, index) in packageDetail.db_diff_conf_file" :disabled="item.configKeyInfos.length === 0" :label="item.shorFileName + ' (' + item.configKeyInfos.length + ')'" :name="item.filename" :key="index" tab="DB">
              <div class="pkg-variable">
                <RadioGroup v-model="prefixType" type="button" button-style="solid" @on-change="typeChange(item.configKeyInfos || [])" style="margin-right: 5px">
                  <Radio v-for="prefix in variablePrefixType" :label="prefix.key" :key="prefix.key" :disabled="getNum(item.configKeyInfos || [], prefix.filterKey) === 0">{{ prefix.label }}({{ getNum(item.configKeyInfos || [], prefix.filterKey) }})</Radio>
                </RadioGroup>
              </div>
              <Table :data="tempTableData" :columns="attrsTableColomnOptions" size="small"></Table>
            </TabPane>
          </Tabs>
          <div v-if="packageDetail.db_diff_conf_file.length === 0" style="text-align: center;">
            {{ $t('art_no_data') }}
          </div>
        </TabPane>
      </Tabs>
    </div>
    <div class="drawer-footer">
      <Button @click="openDrawer = false" type="primary">{{ $t('art_close') }}</Button>
    </div>
    <Modal :mask-closable="false" v-model="isShowConfigKeyModal" :title="$t('artifacts_property_value_fill_rule')" @on-ok="setConfigRowValue" @on-cancel="closeConfigSelectModal">
      <div style="display: flex">
        <Input type="text" :placeholder="$t('artifacts_unselected')" v-model="customSearch"> </Input>
        <Button type="primary" @click="remoteConfigSearch" :loading="remoteLoading">{{ $t('search') }}</Button>
      </div>
      <Select ref="ddrop" :disabled="!allDiffConfigs || allDiffConfigs.length === 0" filterable clearable v-model="currentConfigValue" style="margin-top: 10px">
        <Option v-for="conf in allDiffConfigs.filter(conf => conf.variable_value && conf.code !== currentConfigRow.key)" :value="conf.variable_value" :key="conf.key_name">{{ conf.key_name }}</Option>
      </Select>
    </Modal>
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
  </Drawer>
</template>

<script>
import { sysConfig, getSpecialConnector, getAllCITypesWithAttr, getPackageCiTypeId, getSystemDesignVersions, updateEntity, getPackageDetail, updatePackage, getVariableRootCiTypeId, getEntitiesByCiType } from '@/api/server.js'
import { setCookie, getCookie } from '../util/cookie.js'
import axios from 'axios'
import { decode } from 'js-base64'
// 业务运行实例ciTypeId
const defaultAppRootCiTypeId = 'app_instance'
const defaultDBRootCiTypeId = 'rdb_instance'
// cmdb插件包名
const cmdbPackageName = 'wecmdb'
// 差异配置key_name
const DIFF_CONFIGURATION = 'diff_configuration'
export default {
  name: 'artifacts',
  data () {
    return {
      spinShow: false,
      pkgName: '',
      openDrawer: false,
      treePath: [], // 节点路径
      tableFilter: {
        key_name: '',
        guid: ''
      },
      packageType: '',
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
      // ----------------
      // 单元设计回滚表格配置
      // ----------------
      // ----------------
      // 包配置文件模态数据
      // ----------------
      packageId: '',
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
      attrsTableColomnOptions: [
        {
          title: this.$t('artifacts_property_isbind'),
          width: 100,
          render: (h, params) => {
            if (params.row.conf_variable.bound) {
              return (
                <span>
                  <Icon type="md-checkmark-circle" color="#2d8cf0" style="font-size: 16px;" />
                </span>
              )
            } else {
              return (
                <span>
                  <Icon type="md-close-circle" color="red" style="font-size: 16px;" />
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
          width: 100,
          render: (h, params) => {
            let row = params.row
            if (this.tempTableData[params.row._index]) {
              params.row.rootCI = params.row.conf_variable.tempRootCI || params.row.conf_variable.originRootCI
              return (
                <div>
                  <Tooltip placement="top" max-width="200" content={this.$t('variable_select_key_tooltip_1')}>
                    <Button size="small" style="margin:2px;" type="primary" ghost onClick={async () => this.showCIConfigModal(params.row)}>
                      {this.$t('art_use_template')}
                    </Button>
                  </Tooltip>
                  <Tooltip placement="top" max-width="200" content={this.$t('variable_select_key_tooltip_2')}>
                    <Button type="info" ghost size="small" style="margin:2px;" onClick={async () => this.showConfigKeyModal(row)}>
                      {this.$t('art_copy_exist')}
                    </Button>
                  </Tooltip>
                </div>
              )
            }
          }
        },
        {
          title: this.$t('artifacts_property_value_fill_rule'),
          render: (h, params) => {
            // show static view only if confirmed
            if (this.tempTableData[params.row._index]) {
              return params.row.conf_variable.fixedDate ? (
                <ArtifactsAutoFill style="margin-top:5px;" allCiTypes={this.ciTypes} specialDelimiters={this.specialDelimiters} rootCiTypeId={params.row.rootCI} isReadOnly={true} v-model={this.tempTableData[params.row._index].conf_variable.diffExpr} cmdbPackageName={cmdbPackageName} />
              ) : (
                <div style="align-items:center;display:flex;">
                  <ArtifactsAutoFill style="margin-top:5px;width:calc(100% - 10px);" allCiTypes={this.ciTypes} specialDelimiters={this.specialDelimiters} rootCiTypeId={params.row.rootCI} v-model={this.tempTableData[params.row._index].conf_variable.diffExpr} onUpdateValue={val => this.updateAutoFillValue(val, params.row)} cmdbPackageName={cmdbPackageName} />
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
        { value: defaultAppRootCiTypeId, label: this.$t('APP') },
        { value: defaultDBRootCiTypeId, label: this.$t('DB') }
      ],
      activeTab: '',
      activeTabData: null,
      currentConfigTab: '', // 配置当前tab

      showDiffConfigTab: false,
      currentDiffConfigTab: '', // 差异化变量当前tab
      packageName: '',
      maxHeight: 500,
      variablePrefixType: [
        {
          label: this.$t('art_variable_prefix_default'), // 私有变量
          key: 'variable_prefix_default',
          filterKey: []
        },
        {
          label: this.$t('art_variable_prefix_encrypt'), // 密码变量
          key: 'variable_prefix_encrypt',
          filterKey: []
        },
        {
          label: this.$t('art_variable_prefix_file'), // 文件变量
          key: 'variable_prefix_file',
          filterKey: []
        },
        {
          label: this.$t('art_variable_prefix_global'), // 公共变量
          key: 'variable_prefix_global',
          filterKey: []
        }
      ],
      prefixType: 'variable_prefix_default', // 前缀
      tempTableData: [], // 通过类型、文件、前缀过滤后的展示数据
      currentFileIndex: -1 // 缓存单签文件顺序
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
  mounted () {
    this.maxHeight = window.innerHeight - 290
    window.addEventListener('resize', this.handleResize)
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.handleResize)
  },
  methods: {
    typeChange (configKeyInfos) {
      this.tempTableData = []
      this.$nextTick(() => {
        this.getVariableTableData(configKeyInfos, this.variablePrefixType.find(item => item.key === this.prefixType).filterKey)
      })
    },
    getNum (configKeyInfos, filterKey) {
      let num = 0
      configKeyInfos.forEach(item => {
        if (filterKey.includes(item.type)) {
          num++
        }
      })
      return num
    },
    getVariableTableData (configKeyInfos, filterKey) {
      this.tempTableData = configKeyInfos.filter(item => filterKey.includes(item.type))
    },
    async initDrawer (guid, row) {
      this.openDrawer = true
      this.spinShow = true
      await this.getAllCITypesWithAttr()
      this.currentDiffConfigTab = ''
      this.pkgName = `${row.key_name} - ${this.$t('art_differentiated_variable_configuration')}`
      this.guid = guid
      this.packageName = row.code
      if (row.package_type === this.constPackageOptions.image) {
        this.showDiffConfigTab = false
        this.packageDetail = []
        return
      }
      this.packageType = row.package_type
      this.currentDiffConfigTab = this.packageType === this.constPackageOptions.db ? this.constPackageOptions.db : this.constPackageOptions.app
      this.packageId = row.guid
      this.showDiffConfigTab = true
      // 获取包文件及差异化变量数据
      await this.syncPackageDetail()
      await this.getVariablePrefix()
      this.setPrefixType()
      this.initVariableTableData(0)
      this.spinShow = false
    },
    initVariableTableData (index) {
      this.currentFileIndex = index
      if (this.currentDiffConfigTab === 'DB') {
        this.typeChange(this.packageDetail.db_diff_conf_file[index].configKeyInfos || [])
      }
      if (this.currentDiffConfigTab === 'APP') {
        this.typeChange(this.packageDetail.diff_conf_file[index].configKeyInfos || [])
      }
    },
    async getVariablePrefix () {
      let { status, data } = await sysConfig()
      if (status === 'OK') {
        this.variablePrefixType.forEach(item => {
          item.filterKey = data[item.key] || []
        })
      }
    },
    setPrefixType () {
      this.prefixType = ''
      this.$nextTick(() => {
        const tmp = this.currentDiffConfigTab === this.constPackageOptions.db ? 'db_diff_conf_file' : 'diff_conf_file'
        const tmpData = this.packageDetail[tmp].find(item => item.filename === this.activeTab).configKeyInfos || []
        for (let i = 0; i < this.variablePrefixType.length; i++) {
          const res = this.getNum(tmpData, this.variablePrefixType[i].filterKey)
          if (res > 0) {
            this.prefixType = this.variablePrefixType[i].key
            break
          }
        }
      })
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
    changeDiffConfigTab (tabName) {
      this.currentDiffConfigTab = tabName
      const tmp = this.currentDiffConfigTab === this.constPackageOptions.db ? 'db_diff_conf_file' : 'diff_conf_file'
      if (this.packageDetail[tmp].length > 0) {
        this.activeTab = this.packageDetail[tmp][0].filename
        this.activeTabData = this.packageDetail[tmp][0].configKeyInfos
        this.setPrefixType()
        this.initVariableTableData(0)
      } else {
        this.activeTab = ''
        this.activeTabData = {}
      }
    },
    changeTab (tabName, tabs) {
      this.activeTab = tabName
      const tmp = this.currentDiffConfigTab === this.constPackageOptions.db ? 'db_diff_conf_file' : 'diff_conf_file'
      // this.activeTabData = this.packageDetail.diff_conf_file.find(item => item.shorFileName === this.activeTab).configKeyInfos
      this.activeTabData = this.packageDetail[tmp].find(item => item.filename === this.activeTab).configKeyInfos
      const index = tabs.findIndex(item => item.filename === tabName)
      this.setPrefixType()
      this.initVariableTableData(index)
    },
    async fetchData () {
      const [sysData, packageCiType] = await Promise.all([getSystemDesignVersions(), getPackageCiTypeId()])
      if (sysData.status === 'OK' && sysData.data.contents instanceof Array) {
        this.systemDesignVersions = sysData.data.contents.map(_ => _)
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
      copyData.diff_conf_file.sort((a, b) => (a.configKeyInfos.length === 0 ? 1 : -1))

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
      copyData.db_diff_conf_file.sort((a, b) => (a.configKeyInfos.length === 0 ? 1 : -1))
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
    renderConfigButton (params) {
      let row = params.row
      return [
        // <Tooltip placement="top" max-width="200" content={this.$t('variable_select_key_tooltip')}>
        //   <Button disabled={!!row.conf_variable.fixedDate} size="small" type="primary" style="margin-right:5px;margin-bottom:5px;" onClick={async () => this.showConfigKeyModal(row)}>
        //     {this.$t('select_key')}
        //   </Button>
        // </Tooltip>,
        // disable no dirty data or row is confirmed
        <Button disabled={!!(row.conf_variable.diffExpr === row.conf_variable.originDiffExpr || row.conf_variable.fixedDate)} size="small" type="info" style="margin-right:5px;margin-bottom:5px;" onClick={() => this.saveConfigVariableValue(row)}>
          {this.$t('artifacts_save')}
        </Button>
      ]
    },
    showBatchBindModal () {
      // 复制一份数据用于临时使用bound勾选状态
      let tempBindData = this.formatPackageDetail(this.packageDetail)
      const tmp = this.currentDiffConfigTab === this.constPackageOptions.db ? 'db_diff_conf_variable' : 'diff_conf_variable'
      this.batchBindData = tempBindData[tmp]
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
        this.initVariableTableData(this.currentFileIndex)
      }
      this.tabTableLoading = false
    },
    cancelBatchBindOperation () {
      this.isShowBatchBindModal = false
    },
    async showConfigKeyModal (row) {
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
        console.log(1.1, value, this.customInputs)
        this.customInputs = temps
      }
    },
    async showCIConfigModal (row) {
      const res = await getVariableRootCiTypeId()
      if (res.status === 'OK') {
        const tab = this.currentDiffConfigTab.toLowerCase()
        const _template = res.data[`${tab}_template`]
        if (_template === '') {
          this.$Message.warning(this.$t('art_no_template'))
          return
        }
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
    handleResize () {
      this.maxHeight = window.innerHeight - 290
    }
  },
  created () {
    this.fetchData()
    this.getSpecialConnector()
  },
  components: {}
}
</script>

<style lang="scss" scoped>
.ivu-upload {
  display: inline-block;
}

.header-icon {
  float: right;
  margin: 3px 20px 0 0 !important;
}

.bind-style {
  margin: 8px;
}

.drawer-footer {
  width: 1300px;
  padding: 10px 16px;
  text-align: center;
  background: #fff;
  position: fixed;
  bottom: 20px;
}
.btn-img {
  width: 16px;
  vertical-align: middle;
}
</style>
<style lang="scss">
.pkg-variable {
  margin-bottom: 16px;
  .ivu-radio-group-button .ivu-radio-wrapper-checked {
    background: #2d8cf0;
    color: #fff;
  }
  .ivu-radio-group-button .ivu-radio-wrapper-checked:hover {
    border-color: #57a3f3;
    color: white;
  }
}
.custom-drawer {
  .ivu-drawer-body {
    height: calc(100% - 30px) !important;
  }
}
</style>
