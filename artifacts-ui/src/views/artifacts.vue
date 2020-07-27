<template>
  <Row id="weArtifacts" class="artifact-management">
    <Col span="6">
      <Card>
        <p slot="title">{{ $t('artifacts_system_design_version') }}</p>
        <Select @on-change="selectSystemDesignVersion" label-in-name v-model="systemDesignVersion">
          <Option v-for="version in systemDesignVersions" :value="version.guid || ''" :key="version.guid">{{ version.fixed_date ? `${version.name}[${version.fixed_date}]` : version.name }}</Option>
        </Select>
      </Card>
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
      <Card v-if="guid" class="artifact-management-top-card">
        <Button type="info" ghost icon="ios-cloud-upload-outline" @click="getHeaders">
          {{ $t('artifacts_upload_new_package') }}
        </Button>
        <Button style="margin-left: 10px" type="info" ghost icon="ios-cloud-outline" @click="showPkgModal">
          {{ $t('select_online') }}
        </Button>
        <Upload ref="uploadButton" :action="`/artifacts/unit-designs/${guid}/packages/upload`" :headers="headers" :on-success="onSuccess" :on-error="onError">
          <Button style="display:none" icon="ios-cloud-upload-outline">{{ $t('artifacts_upload_new_package') }}</Button>
        </Upload>
        <!-- <div v-if="uploaded" style="width: 100%;height:26px"></div> -->
        <ArtifactsSimpleTable class="artifact-management-package-table" :loading="tableLoading" :columns="tableColumns" :data="tableData" :page="pageInfo" @pageChange="pageChange" @pageSizeChange="pageSizeChange" @rowClick="rowClick"></ArtifactsSimpleTable>
        <Modal width="70" v-model="isShowFilesModal" :title="$t('artifacts_script_configuration')" :okText="$t('artifacts_save')" :loading="loadingForSave" @on-ok="saveConfigFiles" @on-cancel="closeModal">
          <Select :placeholder="$t('configuration')" @on-change="configurationChanged" v-model="configuration">
            <Option v-for="conf in tableData.filter(conf => conf.guid !== packageId)" :value="conf.name" :key="conf.name">{{ conf.name }}</Option>
          </Select>
          <Card class="artifact-management-files-card">
            <Row>
              <Col style="text-align: right" span="5">
                <span style="margin-right: 10px">{{ $t('artifacts_config_files') }}</span>
                <Button type="info" ghost @click="() => showTreeModal(0, packageInput.diff_conf_file || '')">{{ $t('artifacts_select_file') }}</Button>
              </Col>
              <Col span="18" offset="1">
                <div id="diff_conf_file">
                  <div style="margin-bottom:5px" v-for="(file, index) in packageInput.diff_conf_file" :key="index">
                    <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" v-model="packageInput.diff_conf_file[index]" />
                    <Button type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'diff_conf_file')"></Button>
                  </div>
                </div>
                <div v-if="is_diff_conf_file.length > 0" style="font-size: 12px;color: red;">{{ $t('is_files_exist') }} {{ is_diff_conf_file.join(' | ') }}</div>
              </Col>
            </Row>
          </Card>
          <Card class="artifact-management-files-card">
            <Row>
              <Col style="text-align: right" span="5">
                <span style="margin-right: 10px">{{ $t('artifacts_start_script') }}</span>
                <Button type="info" ghost @click="() => showTreeModal(1, packageInput.start_file_path || '')">{{ $t('artifacts_select_file') }}</Button>
              </Col>
              <Col span="18" offset="1">
                <div id="start_file_path">
                  <div style="margin-bottom:5px" v-for="(file, index) in packageInput.start_file_path" :key="index">
                    <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" v-model="packageInput.start_file_path[index]" />
                    <Button type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'start_file_path')"></Button>
                  </div>
                </div>
                <div v-if="is_start_file_path.length > 0" style="font-size: 12px;color: red;">{{ $t('is_files_exist') }} {{ is_start_file_path.join(' | ') }}</div>
              </Col>
            </Row>
          </Card>
          <Card class="artifact-management-files-card">
            <Row>
              <Col style="text-align: right" span="5">
                <span style="margin-right: 10px">{{ $t('artifacts_stop_script') }}</span>
                <Button type="info" ghost @click="() => showTreeModal(2, packageInput.stop_file_path || '')">{{ $t('artifacts_select_file') }}</Button>
              </Col>
              <Col span="18" offset="1">
                <div id="stop_file_path">
                  <div style="margin-bottom:5px" v-for="(file, index) in packageInput.stop_file_path" :key="index">
                    <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" v-model="packageInput.stop_file_path[index]" />
                    <Button type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'stop_file_path')"></Button>
                  </div>
                </div>
                <div v-if="is_stop_file_path.length > 0" style="font-size: 12px;color: red;">{{ $t('is_files_exist') }} {{ is_stop_file_path.join(' | ') }}</div>
              </Col>
            </Row>
          </Card>
          <Card class="artifact-management-files-card">
            <Row>
              <Col style="text-align: right" span="5">
                <span style="margin-right: 10px">{{ $t('artifacts_deploy_script') }}</span>
                <Button type="info" ghost @click="() => showTreeModal(3, packageInput.deploy_file_path || '')">{{ $t('artifacts_select_file') }}</Button>
              </Col>
              <Col span="18" offset="1">
                <div id="deploy_file_path">
                  <div style="margin-bottom:5px" v-for="(file, index) in packageInput.deploy_file_path" :key="index">
                    <Input class="textarea-input" :rows="1" :placeholder="$t('artifacts_unselected')" type="textarea" v-model="packageInput.deploy_file_path[index]" />
                    <Button type="error" icon="md-trash" ghost @click="deleteFilePath(index, 'deploy_file_path')"></Button>
                  </div>
                </div>
                <div v-if="is_deploy_file_path.length > 0" style="font-size: 12px;color: red;">{{ $t('is_files_exist') }} {{ is_deploy_file_path.join(' | ') }}</div>
              </Col>
            </Row>
          </Card>
          <Card class="artifact-management-files-card">
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
        </Modal>
        <Modal v-model="isShowTreeModal" :title="currentTreeModal.title" @on-ok="onOk" @on-cancel="closeTreeModal">
          <RadioGroup v-model="selectFile">
            <Tree :data="filesTreeData" @on-toggle-expand="expandNode"></Tree>
          </RadioGroup>
        </Modal>
        <Modal v-model="isShowConfigKeyModal" :title="$t('artifacts_property_value_fill_rule')" @on-ok="onSetRowValue" @on-cancel="closeconfigModal">
          <Select filterable clearable v-model="currentConfigValue">
            <Option v-for="conf in allDiffConfigs.filter(conf => conf.variable_value && conf.code !== currentRow.key)" :value="conf.variable_value" :key="conf.key_name">{{ conf.key_name }}</Option>
          </Select>
        </Modal>
        <Modal v-model="isShowOnlineModal" :title="$t('select_online')" @on-ok="onUploadHandler" @on-cancel="closeOnlineModal">
          <Select filterable clearable v-model="currentUrl">
            <Option v-for="conf in currentPackageList" :value="conf.downloadUrl" :key="conf.downloadUrl">{{ conf.name }}</Option>
          </Select>
        </Modal>
      </Card>
      <Card v-if="tabData.length ? true : false" class="artifact-management-bottom-card artifact-management-top-card">
        <Tabs v-model="activeTab" @on-click="tabChange">
          <TabPane v-for="(item, index) in tabData" :label="item.title" :name="item.title" :key="index">
            <Table :data="item.tableData || []" :columns="attrsTableColomnOptions"></Table>
          </TabPane>
        </Tabs>
      </Card>
      <!-- eslint-disable-next-line vue/no-parsing-error -->
    </Col>
  </Row>
</template>

<script>
import { getPackageCiTypeId, queryArtifactsList, uploadArtifact, getAllCITypesWithAttr, getSystemDesignVersions, getSystemDesignVersion, queryPackages, deleteCiDatas, operateCiState, getFiles, getKeys, saveConfigFiles, createEntity, updateEntity, retrieveEntity, getAllSystemEnumCodes, getSpecialConnector } from '@/api/server.js'
import { setCookie, getCookie } from '../util/cookie.js'
import iconFile from '../assets/file.png'
import iconFolder from '../assets/folder.png'
import axios from 'axios'
import Sortable from 'sortablejs'

// 业务运行实例ciTypeId
const rootCiTypeId = 50
// cmdb插件包名
const cmdbPackageName = 'wecmdb'
// 差异配置key_name
const DIFF_CONFIGURATION = 'diff_configuration'
// 部署包key_name
const DEPLOY_PACKAGE = 'deploy_package'

export default {
  name: 'artifacts',
  data () {
    return {
      currentUrl: '',
      isShowOnlineModal: false,
      currentPackageList: [],
      uploaded: false,
      temAciveTab: '',
      currentRow: {},
      allDiffConfigs: [],
      isShowConfigKeyModal: false,
      currentConfigValue: '',
      headers: {},
      configuration: '',
      packageCiType: 0,
      statusOperations: [],
      systemDesignVersions: [],
      systemDesignVersion: '',
      ciTypes: [],
      specialDelimiters: [],
      currentFiles: [],
      treeData: [],
      treeLoading: false,
      loadingForSave: false,
      selectFile: '',
      filesTreeData: [],
      guid: '',
      packageInput: {
        diff_conf_file: [],
        start_file_path: [],
        stop_file_path: [],
        deploy_file_path: [],
        is_decompression: ''
      },
      is_diff_conf_file: [],
      is_start_file_path: [],
      is_stop_file_path: [],
      is_deploy_file_path: [],
      packageId: '',
      isShowFilesModal: false,
      isShowTreeModal: false,
      treeModalOpt: [
        {
          title: this.$t('artifacts_select_config_files'),
          key: 'diff_conf_file',
          inputType: 'checkbox'
        },
        {
          title: this.$t('artifacts_select_start_script'),
          key: 'start_file_path',
          inputType: 'checkbox'
        },
        {
          title: this.$t('artifacts_select_stop_script'),
          key: 'stop_file_path',
          inputType: 'checkbox'
        },
        {
          title: this.$t('artifacts_select_deploy_script'),
          key: 'deploy_file_path',
          inputType: 'checkbox'
        }
      ],
      currentTreeModal: {
        title: '',
        key: '',
        input: ''
      },
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
      pageInfo: {
        pageSize: 5,
        currentPage: 1,
        total: 0
      },
      activeTab: '',
      diffTabData: '',
      tabData: [],
      selectNode: [],
      attrsTableColomnOptions: [
        {
          title: this.$t('artifacts_property_seq'),
          key: 'index',
          width: 60
        },
        {
          title: this.$t('artifacts_line_number'),
          width: 100,
          key: 'line'
        },
        {
          title: this.$t('artifacts_property_name'),
          width: 300,
          key: 'key'
        },
        {
          title: this.$t('artifacts_property_value_fill_rule'),
          render: (h, params) => {
            return params.row.autoFillValue ? (
              <ArtifactsAutoFill style="margin-top:5px;" allCiTypes={this.ciTypes} specialDelimiters={this.specialDelimiters} rootCiTypeId={rootCiTypeId} isReadOnly={true} v-model={params.row.autoFillValue} cmdbPackageName={cmdbPackageName} />
            ) : (
              <div style="align-items:center;display:flex;">
                <ArtifactsAutoFill style="margin-top:5px;width:calc(100% - 55px);" allCiTypes={this.ciTypes} specialDelimiters={this.specialDelimiters} rootCiTypeId={rootCiTypeId} v-model={params.row.variableValue} onUpdateValue={val => this.updateAutoFillValue(val, params.index)} cmdbPackageName={cmdbPackageName} />
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
  computed: {
    nowTab () {
      let result = 0
      this.tabData.find((_, i) => {
        if (_.title === this.activeTab) {
          result = i
          return true
        }
      })
      return result
    },
    ciTypesObj () {
      let obj = {}
      this.ciTypes.forEach(_ => {
        obj[_.ciTypeId] = _
      })
      return obj
    },
    ciTypeAttrsObj () {
      let obj = {}
      this.ciTypes.forEach(ciType => {
        ciType.attributes.forEach(attr => {
          obj[attr.ciTypeAttrId] = attr
        })
      })
      return obj
    }
  },
  methods: {
    showPkgModal () {
      this.isShowOnlineModal = true
    },
    async onUploadHandler () {
      const { status } = await uploadArtifact(this.guid, this.currentUrl)
      if (status === 'OK') {
        this.$Notice.success({
          title: 'Success',
          desc: 'This may take a while, please check later'
        })
      }
      this.closeOnlineModal()
    },
    closeOnlineModal () {
      this.currentUrl = ''
      this.isShowOnlineModal = false
    },
    deleteFilePath (index, key) {
      this.packageInput[key].splice(index, 1)
    },
    async getSpecialConnector () {
      const res = await getSpecialConnector()
      if (res.status === 'OK') {
        this.specialDelimiters = res.data
      }
    },
    renderCell (content) {
      return (
        <Tooltip min-width="200px" max-width="500px" style="width: 100%;">
          <span slot="content" style="white-space:normal;">
            {content && content.toString()}{' '}
          </span>
          <div style="width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{content}</div>
        </Tooltip>
      )
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

    renderActionButton (params) {
      const row = params.row
      return this.statusOperations
        .filter(_ => row.nextOperations.indexOf(_.type) >= 0)
        .map(_ => {
          return (
            <Button {...{ props: { ..._.props } }} style="margin-right:5px;margin-bottom:5px;" onClick={() => this.changeStatus(row, _.type)}>
              {_.label}
            </Button>
          )
        })
    },
    renderConfigButton (params) {
      const row = params.row
      return [
        <Button disabled={row.autoFillValue.length > 0} size="small" type="primary" style="margin-right:5px;margin-bottom:5px;" onClick={() => this.showConfigKeyModal(row)}>
          {this.$t('select_key')}
        </Button>,
        <Button disabled={!row.variableValue} size="small" type="info" style="margin-right:5px;margin-bottom:5px;" onClick={() => this.saveAttr(params.index, row.variableValue)}>
          {this.$t('artifacts_save')}
        </Button>,
        <Button disabled={row.isBinding.length > 0 || row.autoFillValue.length === 0} size="small" type="warning" style="margin-right:5px;margin-bottom:5px;" onClick={() => this.bindConfig(row)}>
          {this.$t('bind_key')}
        </Button>,
        <Button disabled={row.isBinding.length === 0 || row.autoFillValue.length === 0} size="small" type="error" style="margin-right:5px;margin-bottom:5px;" onClick={() => this.unBindConfig(row)}>
          {this.$t('untie_key')}
        </Button>
      ]
    },
    onSetRowValue () {
      if (this.currentConfigValue) {
        this.$set(this.tabData[this.nowTab].tableData[this.currentRow._index], 'variableValue', this.currentConfigValue)
      }
      this.closeconfigModal()
    },
    async unBindConfig (row) {
      const id = row.isBinding
      const found = this.tableData.find(_ => _.guid === this.packageId)
      const bindConfigIds = found.diff_conf_variable.map(i => i.guid)
      const index = bindConfigIds.indexOf(id)
      bindConfigIds.splice(index, 1)
      await this.updateEntity({
        packageName: cmdbPackageName,
        entityName: DEPLOY_PACKAGE,
        data: [
          {
            id: this.packageId,
            diff_conf_variable: bindConfigIds
          }
        ]
      })
      this.updateTabData()
    },
    async bindConfig (row) {
      const found = this.tableData.find(_ => _.guid === this.packageId)
      const bindConfigIds = found.diff_conf_variable.map(i => i.guid)
      const foundKey = this.allDiffConfigs.find(_ => _.code === row.key)
      bindConfigIds.push(foundKey.guid)
      await this.updateEntity({
        packageName: cmdbPackageName,
        entityName: DEPLOY_PACKAGE,
        data: [
          {
            id: this.packageId,
            diff_conf_variable: bindConfigIds
          }
        ]
      })
      this.updateTabData()
    },
    async updateTabData () {
      let tableData = await queryPackages(this.guid, {
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
      const currentTab = this.tabData.find(tab => tab.title === this.activeTab)
      const bindConfig = tableData.data.contents.find(_ => _.data.guid === this.packageId).data.diff_conf_variable
      const tab = await getKeys(this.guid, this.packageId, { filePath: currentTab.path })
      if (tab.status === 'OK') {
        const result = tab.data.outputs[0].configKeyInfos.map((_, i) => {
          const found = bindConfig.find(conf => conf.code === _.key)
          return {
            index: i + 1,
            key: _.key,
            line: _.line,
            autoFillValue: '',
            id: '',
            isBinding: found ? found.guid : ''
          }
        })
        result.forEach(i => {
          const key = this.allDiffConfigs.find(d => d.code === i.key)
          i.autoFillValue = key.variable_value
          i.id = key.id
        })
        this.$set(this.tabData[this.nowTab], 'tableData', result)
      }
    },
    closeconfigModal () {
      this.currentConfigValue = ''
      this.isShowConfigKeyModal = false
      this.currentRow = {}
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
    async getAllCITypesWithAttr () {
      let { status, data } = await getAllCITypesWithAttr(['notCreated', 'created', 'dirty', 'decommissioned'])
      if (status === 'OK') {
        this.ciTypes = JSON.parse(JSON.stringify(data))
      }
    },

    async getSystemDesignVersion (guid) {
      this.treeLoading = true
      let { status, data } = await getSystemDesignVersion(guid)
      if (status === 'OK') {
        this.treeData = this.formatTreeData(data, 1)
        this.treeLoading = false
      }
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
    async getFiles (packageId, currentDir) {
      this.packageId = packageId
      let { status, data } = await getFiles(this.guid, packageId, {
        currentDir
      })
      if (status === 'OK') {
        this.isShowFilesModal = true
        this.genFilesTreedata({ files: data.outputs[0].files, currentDir })
      }
    },
    async getAllEntityData () {
      const diffConfigs = await retrieveEntity(cmdbPackageName, DIFF_CONFIGURATION)
      if (diffConfigs.status === 'OK') {
        this.allDiffConfigs = diffConfigs.data
      }
    },
    showConfigKeyModal (row) {
      this.isShowConfigKeyModal = true
      this.currentRow = row
    },
    async getKeys (options) {
      if (!options) return
      let { status, data } = await getKeys(this.guid, this.packageId, {
        filePath: options.path
      })
      if (status === 'OK') {
        const diffConfigs = await retrieveEntity(cmdbPackageName, DIFF_CONFIGURATION)
        if (diffConfigs.status === 'OK') {
          const result = data.outputs[0].configKeyInfos.map((_, i) => {
            _.index = i + 1
            const found = diffConfigs.data.find(item => item.variable_name === _.key)
            if (found) {
              _.autoFillValue = found.variable_value
              _.id = found.id
            }
            _.isBinding = ''
            return _
          })
          this.$set(options, 'tableData', result)
        }
      }
    },
    async getAllKeys (tabList, isNewPage) {
      if (!tabList.length) return
      // 查出每个文件下的差异化变量名，并将其存在 allKeys 中
      const promiseArray = tabList.map(_ => getKeys(this.guid, this.packageId, { filePath: _.path }))
      const res = await Promise.all(promiseArray)
      let allKeys = {}
      let newDiffConfigs = []
      let needBinding = []
      const bindConfig = this.tableData.find(_ => _.guid === this.packageId).diff_conf_variable || []
      let tabData = res.map((tab, tabIndex) => {
        if (tab.status === 'OK') {
          const tableData = tab.data.outputs[0].configKeyInfos.map((_, i) => {
            allKeys[_.key] = {
              variable_name: _.key,
              variable_value: ''
            }
            const found = bindConfig.find(conf => conf.code === _.key)
            if (found) {
              needBinding.push(found.guid)
            }
            return {
              index: i + 1,
              key: _.key,
              line: _.line,
              autoFillValue: '',
              id: '',
              isBinding: found ? found.guid : ''
            }
          })
          return tableData
        } else {
          return []
        }
      })
      // 查出所有差异化变量的信息
      const diffConfigs = await retrieveEntity(cmdbPackageName, DIFF_CONFIGURATION)
      if (diffConfigs.status === 'OK') {
        Object.keys(allKeys).forEach(key => {
          const found = diffConfigs.data.find(diffConfig => {
            // 如果一个差异化变量已创建，则将其 id 及 variable_value 赋值给 allKeys 中对应的变量
            if (diffConfig.variable_name.toUpperCase() === key.toUpperCase()) {
              allKeys[key].id = diffConfig.id
              allKeys[key].variable_value = diffConfig.variable_value
              return true
            }
          })
          const newFound = newDiffConfigs.find(_ => _.variable_name.toUpperCase() === key.toUpperCase())
          if (!found && !newFound) {
            // 如果该差异化变量未创建，则需创建一个 variable_value 值为空的变量，此处将所有未创建的变量存入 newDiffConfigs 数组
            newDiffConfigs.push({
              variable_name: key,
              variable_value: ''
            })
          }
        })
        if (bindConfig.length === 0) {
          needBinding = Object.keys(allKeys).map(_ => allKeys[_].id)
        }
        if (newDiffConfigs.length) {
          // 将 newDiffConfigs 数组里所有未创建的差异化变量统一创建，并获取其 id
          const params = {
            packageName: cmdbPackageName,
            entityName: DIFF_CONFIGURATION,
            data: newDiffConfigs,
            callback: v => {
              v.forEach(_ => {
                allKeys[_.variable_name].id = _.id
              })
              // 更新 tabData 的信息
              tabData.forEach((tableData, tabIndex) => {
                const result = tableData.map(_ => {
                  return {
                    ..._,
                    ...allKeys[_.key],
                    autoFillValue: allKeys[_.key].variable_value
                  }
                })
                this.$set(this.tabData[tabIndex], 'tableData', result)
              })
              this.updatePackages(needBinding)
            }
          }
          this.createEntity(params)
        } else {
          tabData.forEach((tableData, tabIndex) => {
            const result = tableData.map(_ => {
              return {
                ..._,
                ...allKeys[_.key],
                autoFillValue: allKeys[_.key].variable_value
              }
            })
            this.$set(this.tabData[tabIndex], 'tableData', result)
          })
          if (isNewPage) {
            this.updatePackages(needBinding)
          }
        }
      }
    },
    async updatePackages (needBinding) {
      // 更新部署包关联的所有差异配置变量
      await this.updateEntity({
        packageName: cmdbPackageName,
        entityName: DEPLOY_PACKAGE,
        data: [
          {
            id: this.packageId,
            diff_conf_variable: needBinding
          }
        ]
      })
      const path = this.tableData.find(_ => _.guid === this.packageId).diff_conf_file
      this.getTabDatas(path)
    },
    async saveConfigFiles () {
      this.loadingForSave = true
      const obj = {
        configFilesWithPath: this.packageInput.diff_conf_file,
        startFile: this.packageInput.start_file_path.length > 0 ? this.packageInput.start_file_path.join('|') : '',
        stopFile: this.packageInput.stop_file_path.length > 0 ? this.packageInput.stop_file_path.join('|') : '',
        deployFile: this.packageInput.deploy_file_path.length > 0 ? this.packageInput.deploy_file_path.join('|') : '',
        isDecompression: this.packageInput.is_decompression || ''
      }
      let { status } = await saveConfigFiles(this.guid, this.packageId, obj)
      if (status === 'OK') {
        this.loadingForSave = false
        this.$Notice.success({
          title: this.$t('artifacts_successed')
        })
      }
      await this.queryPackages()
      this.getTabDatas(this.packageInput.diff_conf_file.join('|'), true)
    },
    async createEntity (params) {
      const { packageName, entityName } = params
      const { status, data } = await createEntity(packageName, entityName, params.data)
      if (status === 'OK') {
        params.callback && params.callback(data)
      }
    },
    async updateEntity (params) {
      const { packageName, entityName } = params
      const { status, data } = await updateEntity(packageName, entityName, params.data)
      if (status === 'OK') {
        params.callback && params.callback(data)
      }
    },
    selectSystemDesignVersion (guid) {
      this.getSystemDesignVersion(guid)
      this.guid = ''
      this.tabData = []
      this.uploaded = false
    },
    formatTreeData (array, level) {
      const color = {
        new: 'green',
        update: 'cyan',
        delete: 'red',
        created: 'geekblue',
        changed: 'purple',
        destroyed: 'volcano'
      }
      return array.map(_ => {
        _.title = _.data.name
        _.level = level
        _.render = (h, params) => {
          return (
            <div>
              <span style="margin-right:10px">{_.data.name}</span>
              <Tag color={color[_.data.state_code]}>{_.data.state_code}</Tag>
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
    selectTreeNode (node) {
      if (node.length && node[0].level === 3) {
        this.guid = node[0].data.r_guid
        this.queryPackages()
        this.tabData = []
        this.queryCurrentPkg()
      }
    },
    async queryCurrentPkg () {
      const { status, data } = await queryArtifactsList(this.guid, { filters: [], paging: false })
      if (status === 'OK') {
        this.currentPackageList = data
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
    genFilesTreedata (data) {
      const { files, currentDir } = data
      if (currentDir) {
        const filesArray = currentDir.split('/')
        let targetNode = this.filesTreeData
        filesArray.forEach((dir, index) => {
          if (index) {
            targetNode = targetNode.children
          }
          targetNode.find(_ => {
            if (dir === _.title) {
              targetNode = _
              return true
            }
          })
        })
        targetNode.children = this.formatChildrenData({
          files,
          currentDir,
          level: targetNode.level + 1
        })
      } else {
        this.filesTreeData = this.formatChildrenData({
          files,
          currentDir,
          level: 1
        })
      }
    },
    formatChildrenData (val) {
      const { files, currentDir, level } = val
      if (!(files instanceof Array)) {
        return
      }
      return files.map(_ => {
        let obj = {
          title: _.name,
          path: currentDir ? `${currentDir}/${_.name}` : _.name,
          level: level
        }
        if (_.isDir) {
          obj.children = [{}]
          obj.render = (h, params) => (
            <span>
              <img height="16" width="16" src={iconFolder} style="position:relative;top:3px;margin:0 3px;" />
              <span>{_.name}</span>
            </span>
          )
        } else {
          const selectedFile = !!this.currentFiles.find(file => file === obj.path)
          if (selectedFile && this.currentTreeModal.inputType === 'checkbox') {
            this.selectNode.push(obj)
          }
          obj.render = (h, params) => {
            return this.currentTreeModal.inputType === 'checkbox' ? (
              <Checkbox value={selectedFile} style="position:relative;right:24px;" on-on-change={value => this.checkboxChange(value, params.data)}>
                <img height="16" width="16" src={iconFile} style="position:relative;top:3px;margin:0 3px;" />
                <span>{params.data.title}</span>
              </Checkbox>
            ) : (
              <Radio value={selectedFile} style="position:relative;right:20px;" label={params.data.path}>
                <img height="16" width="16" src={iconFile} style="position:relative;top:3px;margin:0 3px;" />
                <span>{params.data.title}</span>
              </Radio>
            )
          }
        }
        return obj
      })
    },
    expandNode (node) {
      if (node.expand && !node.children[0].title) {
        this.getFiles(this.packageId, node.path)
      }
    },
    rowClick (row) {
      this.packageId = row.guid
      this.getTabDatas(row.diff_conf_file)
    },
    changeStatus (row, status) {
      switch (status) {
        case 'update':
          this.showFilesModal(row)
          break
        case 'delete':
          this.handleDelete(row, status)
          break
        default:
          this.handleStatusChange(row, status)
          break
      }
    },
    async handleDelete (row) {
      this.$Modal.confirm({
        title: this.$t('delete_confirm'),
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
              this.tabData = []
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
      }
    },
    configurationChanged (v) {
      if (v) {
        const found = this.tableData.find(row => row.name === v)
        this.packageInput.diff_conf_file = found.diff_conf_file ? found.diff_conf_file.split('|') : []
        this.packageInput.start_file_path = found.start_file_path ? found.start_file_path.split('|') : []
        this.packageInput.stop_file_path = found.stop_file_path ? found.stop_file_path.split('|') : []
        this.packageInput.deploy_file_path = found.deploy_file_path ? found.deploy_file_path.split('|') : []
        this.packageInput.is_decompression = found.is_decompression || ''
        this.checkFileExist(this.packageInput.diff_conf_file, 'is_diff_conf_file')
        this.checkFileExist(this.packageInput.start_file_path, 'is_start_file_path')
        this.checkFileExist(this.packageInput.stop_file_path, 'is_stop_file_path')
        this.checkFileExist(this.packageInput.deploy_file_path, 'is_deploy_file_path')
      }
    },
    async checkFileExist (filePath, isExist) {
      if (filePath.length === 0) {
        return
      }
      const filePathList = filePath
      filePathList.forEach(async path => {
        let dirs = path.split('/')
        await this.checkFiles(0, dirs, isExist)
      })
    },
    async checkFiles (index, fileList, isExist) {
      let currentDir = ''
      let notExist = false
      if (index > 0) {
        for (let i = 0; i < index; i++) {
          currentDir = currentDir + fileList[i] + '/'
        }
      }
      const { data } = await getFiles(this.guid, this.packageId, { currentDir: currentDir })
      if (data.outputs[0].files.find(_ => _.name === fileList[index])) {
        if (index === fileList.length - 1) {
          return notExist
        }
        this.checkFiles(index + 1, fileList, isExist)
      } else {
        notExist = true
        this[isExist].push(fileList.join('/'))
      }
      return notExist
    },
    showFilesModal (row) {
      this.tabData = []
      // 以下4个变量类型为字符串
      this.packageInput.diff_conf_file = row.diff_conf_file ? row.diff_conf_file.split('|') : []
      this.packageInput.start_file_path = row.start_file_path ? row.start_file_path.split('|') : []
      this.packageInput.stop_file_path = row.stop_file_path ? row.stop_file_path.split('|') : []
      this.packageInput.deploy_file_path = row.deploy_file_path ? row.deploy_file_path.split('|') : []
      this.packageInput.is_decompression = row.is_decompression || ''
      this.packageId = row.guid
      this.diffTabData = row.diff_conf_file || ''
      this.configuration = ''
      this.is_diff_conf_file = []
      this.is_start_file_path = []
      this.is_stop_file_path = []
      this.is_deploy_file_path = []
      this.isShowFilesModal = true
      this.checkFileExist(this.packageInput.diff_conf_file, 'is_diff_conf_file')
      this.checkFileExist(this.packageInput.start_file_path, 'is_start_file_path')
      this.checkFileExist(this.packageInput.stop_file_path, 'is_stop_file_path')
      this.checkFileExist(this.packageInput.deploy_file_path, 'is_deploy_file_path')
      this.$nextTick(() => {
        this.genSortable('diff_conf_file')
        this.genSortable('start_file_path')
        this.genSortable('stop_file_path')
        this.genSortable('deploy_file_path')
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
    getTabDatas (diffFile, isNewPage = false) {
      if (diffFile) {
        const files = diffFile.split('|')
        this.tabData = files.map(_ => {
          const f = _.split('/')
          return {
            path: _,
            title: f[f.length - 1]
          }
        })
        this.activeTab = this.tabData.length ? this.tabData[0].title : ''
        this.getAllKeys(this.tabData, isNewPage)
      } else {
        this.tabData = []
      }
    },
    showTreeModal (type, files) {
      this.filesTreeData = []
      this.currentFiles = files
      this.currentTreeModal = this.treeModalOpt[type]
      if (!this.filesTreeData.length) {
        this.getFiles(this.packageId, '')
      }
      // if (type > 0 && files) {
      //   this.selectFile = files
      // }
      this.isShowTreeModal = true
    },
    closeModal () {
      this.packageInput = {
        diff_conf_file: [],
        start_file_path: [],
        stop_file_path: [],
        deploy_file_path: [],
        is_decompression: ''
      }
    },
    onOk () {
      // if (this.currentTreeModal.key === 'diff_conf_file') {
      this.diffTabData = ''
      let files = []
      this.selectNode.forEach(_ => {
        files.push(_.path)
      })
      this.diffTabData = files.join('|')
      this.packageInput[this.currentTreeModal.key] = files
      this.selectNode = []
      this.filesTreeData = []
      // } else {
      //   this.packageInput[this.currentTreeModal.key] = this.selectFile
      // }
      const key = 'is_' + this.currentTreeModal.key
      this[key] = ''
      this.selectFile = ''
    },
    closeTreeModal () {
      this.selectFile = ''
      this.selectNode = []
      this.filesTreeData = []
    },
    checkboxChange (value, data) {
      if (value) {
        this.selectNode.push(data)
      } else {
        let i = 0
        this.selectNode.find((_, index) => {
          if (_.path === data.path) {
            i = index
            return true
          }
        })
        this.selectNode.splice(i, 1)
      }
    },
    tabChange (tabName) {
      this.tabData.find(_ => {
        if (_.title === tabName && !(_.tableData instanceof Array)) {
          this.getKeys(_)
          return true
        }
      })
      this.temAciveTab = this.activeTab
    },
    updateAutoFillValue (val, row) {
      this.$set(this.tabData[this.nowTab].tableData[row], 'variableValue', val)
    },
    saveAttr (row, value) {
      if (!this.checkFillRule(value)) {
        return
      }
      const obj = [
        {
          id: this.tabData[this.nowTab].tableData[row].id,
          variable_value: value
        }
      ]
      if (obj[0].variable_value) {
        this.updateDiffConfig(obj)
      }
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
    updateDiffConfig (data) {
      const params = {
        packageName: cmdbPackageName,
        entityName: DIFF_CONFIGURATION,
        data,
        callback: async () => {
          this.$Notice.success({
            title: this.$t('artifacts_successed')
          })
          await this.getAllEntityData()
          this.updateTabData()
        }
      }
      this.updateEntity(params)
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
          confirm: 'info',
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
                type: buttonTypes[_.code] || 'info',
                size: 'small'
              },
              actionType: _.code
            }
          })
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
    }
  },
  created () {
    this.fetchData()
    this.getSpecialConnector()
    this.getAllCITypesWithAttr()
    this.getAllSystemEnumCodes()
    this.getAllEntityData()
  }
}
</script>

<style lang="scss" scoped>
.textarea-input {
  display: inline-block;
  width: 90%;
  margin-right: 20px;
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
</style>
