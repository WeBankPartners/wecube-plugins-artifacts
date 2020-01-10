<template>
  <Row id="weArtifacts" class="artifact-management">
    <Col span="6">
      <Card>
        <p slot="title">{{ $t("artifacts_system_design_version") }}</p>
        <Select
          @on-change="selectSystemDesignVersion"
          label-in-name
          v-model="systemDesignVersion"
        >
          <Option
            v-for="version in systemDesignVersions"
            :value="version.guid || ''"
            :key="version.guid"
            >{{
              version.fixed_date
                ? `${version.name}[${version.fixed_date}]`
                : version.name
            }}</Option
          >
        </Select>
      </Card>
      <Card class="artifact-management-bottom-card">
        <p slot="title">{{ $t("artifacts_system_design_list") }}</p>
        <div class="artifact-management-tree-body">
          <Tree :data="treeData" @on-select-change="selectTreeNode"></Tree>
          <Spin size="large" fix v-if="treeLoading">
            <Icon type="ios-loading" size="24" class="spin-icon-load"></Icon>
            <div>{{ $t("artifacts_loading") }}</div>
          </Spin>
        </div>
      </Card>
    </Col>
    <Col span="17" offset="1">
      <Card v-if="guid" class="artifact-management-top-card">
        <Button
          type="info"
          ghost
          icon="ios-cloud-upload-outline"
          style="margin-bottom:10px;"
          @click="getHeaders"
        >
          {{ $t("artifacts_upload_new_package") }}
        </Button>
        <Upload
          ref="uploadButton"
          show-upload-list
          :action="`/artifacts/unit-designs/${guid}/packages/upload`"
          :headers="headers"
          :on-success="onSuccess"
          :on-error="onError"
          slot="title"
        >
          <Button style="display:none" icon="ios-cloud-upload-outline">{{ $t("artifacts_upload_new_package") }}</Button>
        </Upload>
        <ArtifactsSimpleTable
          class="artifact-management-package-table"
          :loading="tableLoading"
          :columns="tableColumns"
          :data="tableData"
          :page="pageInfo"
          @pageChange="pageChange"
          @pageSizeChange="pageSizeChange"
          @rowClick="rowClick"
        ></ArtifactsSimpleTable>
        <Modal
          v-model="isShowFilesModal"
          :title="$t('artifacts_script_configuration')"
          :okText="$t('artifacts_save')"
          :loading="loadingForSave"
          @on-ok="saveConfigFiles"
          @on-cancel="closeModal"
        >
          <Card class="artifact-management-files-card">
            <div slot="title">
              <span>{{ $t("artifacts_config_files") }}</span>
              <Button @click="() => showTreeModal(0)" size="small"
                >{{ $t("artifacts_select_file") }}</Button
              >
            </div>
            <span>{{ currentPackage.diff_conf_file || $t("artifacts_unselected") }}</span>
          </Card>
          <Card class="artifact-management-files-card">
            <div slot="title">
              <span>{{ $t("artifacts_start_script") }}</span>
              <Button @click="() => showTreeModal(1)" size="small"
                >{{ $t("artifacts_select_file") }}</Button
              >
            </div>
            <span>{{ currentPackage.start_file_path || $t("artifacts_unselected") }}</span>
          </Card>
          <Card class="artifact-management-files-card">
            <div slot="title">
              <span>{{ $t("artifacts_stop_script") }}</span>
              <Button @click="() => showTreeModal(2)" size="small"
                >{{ $t("artifacts_select_file") }}</Button
              >
            </div>
            <span>{{ currentPackage.stop_file_path || $t("artifacts_unselected") }}</span>
          </Card>
          <Card class="artifact-management-files-card">
            <div slot="title">
              <span>{{ $t("artifacts_deploy_script") }}</span>
              <Button @click="() => showTreeModal(3)" size="small"
                >{{ $t("artifacts_select_file") }}</Button
              >
            </div>
            <span>{{ currentPackage.deploy_file_path || $t("artifacts_unselected") }}</span>
          </Card>
        </Modal>
        <Modal
          v-model="isShowTreeModal"
          :title="currentTreeModal.title"
          @on-ok="onOk"
          @on-cancel="closeTreeModal"
        >
          <RadioGroup v-model="selectFile">
            <Tree :data="filesTreeData" @on-toggle-expand="expandNode"></Tree>
          </RadioGroup>
        </Modal>
      </Card>
      <Card
        v-if="tabData.length ? true : false"
        class="artifact-management-bottom-card artifact-management-top-card"
      >
        <Tabs v-model="activeTab" @on-click="tabChange">
          <TabPane
            v-for="(item, index) in tabData"
            :label="item.title"
            :name="item.title"
            :key="index"
          >
            <Table
              :data="item.tableData || []"
              :columns="attrsTableColomnOptions"
            ></Table>
          </TabPane>
        </Tabs>
      </Card>
    </Col>
  </Row>
</template>

<script>
import {
  getPackageCiTypeId,
  getAllCITypesWithAttr,
  getSystemDesignVersions,
  getSystemDesignVersion,
  queryPackages,
  deleteCiDatas,
  operateCiState,
  getFiles,
  getKeys,
  saveConfigFiles,
  createEntity,
  updateEntity,
  retrieveEntity,
  getAllSystemEnumCodes,
  getSpecialConnector
} from "@/api/server.js";
import iconFile from "../assets/file.png"
import iconFolder from "../assets/folder.png"
import axios from 'axios'

// 业务运行实例ciTypeId
const rootCiTypeId = 14
// cmdb插件包名
const cmdbPackageName = "wecmdb"
// 差异配置key_name
const DIFF_CONFIGURATION = "diff_configuration"
// 部署包key_name
const DEPLOY_PACKAGE = "deploy_package"

export default {
  name: "artifacts",
  data() {
    return {
      headers: {},
      packageCiType: 0,
      statusOperations: [],
      systemDesignVersions: [],
      systemDesignVersion: "",
      ciTypes: [],
      specialDelimiters: [],
      treeData: [],
      treeLoading: false,
      loadingForSave: false,
      selectFile: "",
      filesTreeData: [],
      guid: "",
      currentPackage: {},
      packageId: "",
      isShowFilesModal: false,
      isShowTreeModal: false,
      treeModalOpt: [
        {
          title: this.$t("artifacts_select_config_files"),
          key: "diff_conf_file",
          inputType: "checkbox"
        },
        {
          title: this.$t("artifacts_select_start_script"),
          key: "start_file_path",
          inputType: "radio"
        },
        {
          title: this.$t("artifacts_select_stop_script"),
          key: "stop_file_path",
          inputType: "radio"
        },
        {
          title: this.$t("artifacts_select_deploy_script"),
          key: "deploy_file_path",
          inputType: "radio"
        }
      ],
      currentTreeModal: {},
      tableLoading: false,
      tableData: [],
      tableColumns: [
        {
          title: this.$t("artifacts_package_name"),
          key: "name",
          render: (h, params) => this.renderCell(params.row.name)
        },
        {
          title: this.$t("artifacts_upload_time"),
          width: 120,
          key: "upload_time"
        },
        {
          title: this.$t("artifacts_md5_value"),
          key: "md5_value",
          render: (h, params) => this.renderCell(params.row.md5_value)
        },
        {
          title: this.$t("artifacts_uploaded_by"),
          key: "upload_user",
          render: (h, params) => this.renderCell(params.row.upload_user)
        },
        {
          title: this.$t("artifacts_config_files"),
          key: "diff_conf_file",
          render: (h, params) => this.renderCell(params.row.diff_conf_file)
        },
        {
          title: this.$t("artifacts_start_script"),
          key: "start_file_path",
          render: (h, params) => this.renderCell(params.row.start_file_path)
        },
        {
          title: this.$t("artifacts_stop_script"),
          key: "stop_file_path",
          render: (h, params) => this.renderCell(params.row.stop_file_path)
        },
        {
          title: this.$t("artifacts_deploy_script"),
          key: "deploy_file_path",
          render: (h, params) => this.renderCell(params.row.deploy_file_path)
        },
        {
          title: this.$t("artifacts_action"),
          key: "state",
          width: 150,
          render: (h, params) => {
            return (
              <div style="padding-top:5px">
                {this.renderActionButton(params)}
              </div>
            );
          }
        }
      ],
      pageInfo: {
        pageSize: 5,
        currentPage: 1,
        total: 0
      },
      activeTab: "",
      diffTabData: "",
      tabData: [],
      selectNode: [],
      attrsTableColomnOptions: [
        {
          title: this.$t("artifacts_property_seq"),
          key: "index",
          width: 60
        },
        {
          title: this.$t("artifacts_line_number"),
          key: "line"
        },
        {
          title: this.$t("artifacts_property_name"),
          key: "key"
        },
        {
          title: this.$t("artifacts_property_value_fill_rule"),
          render: (h, params) => {
            return params.row.autoFillValue ? (
              <ArtifactsAutoFill
                style="margin-top:5px;"
                allCiTypes={this.ciTypes}
                specialDelimiters={this.specialDelimiters}
                rootCiTypeId={rootCiTypeId}
                isReadOnly={true}
                v-model={params.row.autoFillValue}
              />
            ) : (
              <div style="align-items:center;display:flex;">
                <ArtifactsAutoFill
                  style="margin-top:5px;width:calc(100% - 55px);"
                  allCiTypes={this.ciTypes}
                  specialDelimiters={this.specialDelimiters}
                  rootCiTypeId={rootCiTypeId}
                  v-model={params.row.variableValue}
                  onUpdateValue={val => this.updateAutoFillValue(val, params.index)}
                />
                <Button
                  disabled={!params.row.variableValue}
                  size="small"
                  type="primary"
                  style="margin-left:10px"
                  onClick={() => this.saveAttr(params.index, params.row.variableValue)}
                >
                  { this.$t("artifacts_save") }
                </Button>
              </div>
            );
          }
        }
      ]
    };
  },
  computed: {
    nowTab() {
      let result = 0;
      this.tabData.find((_, i) => {
        if (_.title === this.activeTab) {
          result = i;
          return true;
        }
      });
      return result;
    }
  },
  methods: {
    async getSpecialConnector() {
      const res = await getSpecialConnector();
      if (res.status === "OK") {
        this.specialDelimiters = res.data
      }
    },
    renderCell(content) {
      return (
        <Tooltip style="width: 100%;" >
          <span slot="content" style="white-space:normal;">{content} </span>
          <div style="width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{content}</div>
        </Tooltip>
      )
    },
    onSuccess(response, file, fileList) {
      if (response.status === "ERROR") {
        this.$Notice.error({
          title: "Error",
          desc: response.message || ""
        });
      } else {
        this.$Notice.success({
          title: 'Success',
          desc: response.message || ''
        })
        this.queryPackages();
      }
    },
    onError (file, filelist) {
      this.$Notice.error({
        title: 'Error',
        desc: file.message || ''
      })
    },

    renderActionButton(params) {
      const row = params.row;
      return this.statusOperations
        .filter(_ => row.nextOperations.indexOf(_.type) >= 0)
        .map(_ => {
          return (
            <Button
              {...{ props: { ..._.props } }}
              style="margin-right:5px;margin-bottom:5px;"
              onClick={() => this.changeStatus(row, _.type)}
            >
              {_.label}
            </Button>
          );
        });
    },
    async fetchData() {
      const [sysData, packageCiType] = await Promise.all([
        getSystemDesignVersions(),
        getPackageCiTypeId()
      ]);
      if (sysData.status === "OK" && sysData.data.contents instanceof Array) {
        this.systemDesignVersions = sysData.data.contents.map(_ => _.data);
      }
      if (packageCiType.status === "OK") {
        this.packageCiType = packageCiType.data;
      }
    },
    async getAllCITypesWithAttr() {
      let { status, data, message } = await getAllCITypesWithAttr([
        "notCreated",
        "created",
        "dirty",
        "decommissioned"
      ]);
      if (status === "OK") {
        this.ciTypes = JSON.parse(JSON.stringify(data));
      }
    },

    async getSystemDesignVersion(guid) {
      this.treeLoading = true;
      let { status, data, message } = await getSystemDesignVersion(guid);
      if (status === "OK") {
        this.treeData = this.formatTreeData(data, 1);
        this.treeLoading = false;
      }
    },
    async queryPackages() {
      this.tableLoading = true;
      let { status, data, message } = await queryPackages(this.guid, {
        sorting: {
          asc: false,
          field: "upload_time"
        },
        paging: true,
        pageable: {
          pageSize: this.pageInfo.pageSize,
          startIndex: (this.pageInfo.currentPage - 1) * this.pageInfo.pageSize
        }
      });
      if (status === "OK") {
        this.tableLoading = false;
        this.tableData = data.contents.map(_ => {
          return {
            ..._.data,
            nextOperations: _.meta.nextOperations || []
          };
        });
        const { pageSize, totalRows: total } = data.pageInfo;
        const currentPage = this.pageInfo.currentPage;
        this.pageInfo = { currentPage, pageSize, total };
      }
    },
    async getFiles(packageId, currentDir) {
      this.packageId = packageId;
      let { status, data, message } = await getFiles(this.guid, packageId, {
        currentDir
      });
      if (status === "OK") {
        this.isShowFilesModal = true;
        this.genFilesTreedata({ files: data.outputs[0].files, currentDir });
      }
    },
    async getKeys(options) {
      if (!options) return;
      let { status, data, message } = await getKeys(this.guid, this.packageId, {
        filePath: options.path
      });
      if (status === "OK") {
        const diffConfigs = await retrieveEntity(cmdbPackageName, DIFF_CONFIGURATION);
        if (diffConfigs.status === "OK") {
          let newKeys = []
          const result = data.outputs[0].configKeyInfos.map((_, i) => {
            _.index = i + 1;
            const found = diffConfigs.data.find(
              item => item.variable_name === _.key
            );
            if (found) {
              _.autoFillValue = found.variable_value;
              _.id = found.id
            }
            return _;
          });
          this.$set(options, "tableData", result);
        }
      }
    },
    async getAllKeys(tabList) {
      if (!tabList.length) return
      // 查出每个文件下的差异化变量名，并将其存在 allKeys 中
      const promiseArray = tabList.map(_ => getKeys(this.guid, this.packageId, { filePath: _.path }))
      const res = await Promise.all(promiseArray)
      let allKeys = {}
      let newDiffConfigs = []
      let tabData = res.map((tab, tabIndex) => {
        if (tab.status === "OK") {
          const tableData = tab.data.outputs[0].configKeyInfos.map((_, i) => {
            allKeys[_.key] = {
              variable_name: _.key,
              variable_value: ""
            }
            return {
              index: i + 1,
              key: _.key,
              autoFillValue: "",
              id: ""
            }
          })
          return tableData
        } else {
          return []
        }
      })
      // 查出所有差异化变量的信息
      const diffConfigs = await retrieveEntity(cmdbPackageName, DIFF_CONFIGURATION);
      if (diffConfigs.status === "OK") {
        Object.keys(allKeys).forEach(key => {
          const found = diffConfigs.data.find(diffConfig => {
            // 如果一个差异化变量已创建，则将其 id 及 variable_value 赋值给 allKeys 中对应的变量
            if (diffConfig.variable_name === key) {
              allKeys[key].id = diffConfig.id,
              allKeys[key].variable_value = diffConfig.variable_value
              return true
            }
          })
          if (!found) {
            // 如果该差异化变量未创建，则需创建一个 variable_value 值为空的变量，此处将所有未创建的变量存入 newDiffConfigs 数组
            newDiffConfigs.push({
              variable_name: key,
              variable_value: ""
            })
          }
        })
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
                this.$set(this.tabData[tabIndex], "tableData", result);
              })
              this.updatePackages(allKeys)
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
            this.$set(this.tabData[tabIndex], "tableData", result);
          })
        }
      }
    },
    updatePackages(allKeys) {
      // 更新部署包关联的所有差异配置变量
      const ids = Object.keys(allKeys).map(_ => allKeys[_].id)
      this.updateEntity({
        packageName: cmdbPackageName,
        entityName: DEPLOY_PACKAGE,
        data: [{
          id: this.packageId,
          diff_conf_variable: ids
        }]
      })
    },
    async saveConfigFiles(updatePackages) {
      this.loadingForSave = true;
      const obj = {
        configFilesWithPath: this.diffTabData.split("|"),
        startFile: this.currentPackage.start_file_path || "",
        stopFile: this.currentPackage.stop_file_path || "",
        deployFile: this.currentPackage.deploy_file_path || ""
      };
      let { status, data, message } = await saveConfigFiles(
        this.guid,
        this.packageId,
        obj
      );
      if (status === "OK") {
        this.loadingForSave = false;
        this.$Notice.success({
          title: this.$t("artifacts_successed")
        });
      }
      this.queryPackages();
      this.getTabDatas(this.diffTabData);
    },
    async createEntity(params) {
      const { packageName, entityName } = params
      const { status, data, message } = await createEntity(packageName, entityName, params.data);
      if (status === "OK") {
        params.callback && params.callback(data)
      }
    },
    async updateEntity(params) {
      const { packageName, entityName } = params
      const { status, data, message } = await updateEntity(packageName, entityName, params.data)
      if (status === "OK") {
        params.callback && params.callback(data)
      }
    },
    selectSystemDesignVersion(guid) {
      this.getSystemDesignVersion(guid);
    },
    formatTreeData(array, level) {
      return array.map(_ => {
        _.title = _.data.name;
        _.level = level;
        if (_.children && _.children.length) {
          _.expand = true;
          _.children = this.formatTreeData(_.children, level + 1);
        }
        return _;
      });
    },
    selectTreeNode(node) {
      if (node.length && node[0].level === 3) {
        this.guid = node[0].data.r_guid;
        this.queryPackages();
        this.tabData = [];
      }
    },
    pageChange(currentPage) {
      this.pageInfo.currentPage = currentPage;
      this.queryPackages();
    },
    pageSizeChange(pageSize) {
      this.pageInfo.pageSize = pageSize;
      this.queryPackages();
    },
    genFilesTreedata(data) {
      const { files, currentDir } = data;
      if (currentDir) {
        const filesArray = currentDir.split("/");
        let targetNode = this.filesTreeData;
        filesArray.forEach((dir, index) => {
          if (index) {
            targetNode = targetNode.children;
          }
          targetNode.find(_ => {
            if (dir === _.title) {
              targetNode = _;
              return true;
            }
          });
        });
        targetNode.children = this.formatChildrenData({
          files,
          currentDir,
          level: targetNode.level + 1
        });
      } else {
        this.filesTreeData = this.formatChildrenData({
          files,
          currentDir,
          level: 1
        });
      }
    },
    formatChildrenData(val) {
      const { files, currentDir, level } = val;
      if (!(files instanceof Array)) {
        return;
      }
      const tagName = this.currentTreeModal.inputType;
      return files.map(_ => {
        let obj = {
          title: _.name,
          path: currentDir ? `${currentDir}/${_.name}` : _.name,
          level: level
        };
        if (_.isDir) {
          obj.children = [{}];
          obj.render = (h, params) => (
            <span>
              <img height="16" width="16" src={iconFolder} style="position:relative;top:3px;margin:0 3px;" />
              <span>{_.name}</span>
            </span>
          )
        } else {
          obj.render = (h, params) => {
            return this.currentTreeModal.inputType === "checkbox" ? (
              <Checkbox
                style="position:relative;right:24px;"
                on-on-change={value => this.checkboxChange(value, params.data)}
              >
                <img height="16" width="16" src={iconFile} style="position:relative;top:3px;margin:0 3px;" />
                <span>{params.data.title}</span>
              </Checkbox>
            ) : (
              <Radio
                style="position:relative;right:20px;"
                label={params.data.path}>
                <img height="16" width="16" src={iconFile} style="position:relative;top:3px;margin:0 3px;" />
                <span>{params.data.title}</span>
              </Radio>
            );
          };
        }
        return obj;
      });
    },
    expandNode(node) {
      if (node.expand && !node.children[0].title) {
        this.getFiles(this.packageId, node.path);
      }
    },
    rowClick(row) {
      this.packageId = row.guid;
      this.getTabDatas(row.diff_conf_file);
    },
    changeStatus(row, status) {
      switch (status) {
        case "update":
          this.showFilesModal(row);
          break;
        case "delete":
          this.handleDelete(row, status);
          break;
        default:
          this.handleStatusChange(row, status);
          break;
      }
    },
    async handleDelete(row) {
      this.$Modal.confirm({
        title: this.$t("delete_confirm"),
        "z-index": 1000000,
        onOk: async () => {
          const { status, data, message } = await deleteCiDatas({
            id: this.packageCiType,
            deleteData: [row.guid]
          });
          if (status === "OK") {
            this.$Notice.success({
              title: this.$t("artifacts_delete_success"),
              desc: message
            });
            this.queryPackages();
          }
        }
      });
    },
    async handleStatusChange(row, state) {
      const { data, status, message } = await operateCiState(
        this.packageCiType,
        row.guid,
        state
      );
      if (status === "OK") {
        this.$Notice.success({
          title: state,
          desc: message
        });
        this.queryPackages();
      }
    },
    showFilesModal(row) {
      this.tabData = [];
      this.currentPackage = JSON.parse(JSON.stringify(row));
      this.packageId = this.currentPackage.guid;
      this.diffTabData = row.diff_conf_file || "";
      this.isShowFilesModal = true;
    },
    getTabDatas(diffFile) {
      if (diffFile) {
        const files = diffFile.split("|");
        this.tabData = files.map(_ => {
          const f = _.split("/");
          return {
            path: _,
            title: f[f.length - 1]
          };
        });
        this.activeTab = this.tabData.length ? this.tabData[0].title : "";
        this.getAllKeys(this.tabData)
      } else {
        this.tabData = [];
      }
    },
    showTreeModal(type) {
      this.currentTreeModal = this.treeModalOpt[type];
      if (!this.filesTreeData.length)
        this.getFiles(this.currentPackage.guid, "");
      this.isShowTreeModal = true;
    },
    closeModal() {
      this.currentPackage = {};
    },
    onOk() {
      if (this.currentTreeModal.key === "diff_conf_file") {
        this.diffTabData = "";
        let files = [];
        this.selectNode.forEach((_, index) => {
          index === 0 ? files.push(_.path) : files.push("/" + _.path);
        });
        this.diffTabData = files.join("|");
        this.currentPackage.diff_conf_file = files.join("|");
        this.selectNode = [];
        this.filesTreeData = [];
      } else {
        this.currentPackage[this.currentTreeModal.key] = this.selectFile;
      }
    },
    closeTreeModal() {
      this.selectNode = [];
      this.filesTreeData = [];
    },
    checkboxChange(value, data) {
      if (value) {
        this.selectNode.push(data);
      } else {
        let i = 0;
        this.selectNode.find((_, index) => {
          if (_.path === data.path) {
            i = index;
            return true;
          }
        });
        this.selectNode.splice(i, 1);
      }
    },
    tabChange(tabName) {
      this.tabData.find(_ => {
        if (_.title === tabName && !(_.tableData instanceof Array)) {
          this.getKeys(_);
          return true;
        }
      });
    },
    updateAutoFillValue(val, row) {
      this.$set(this.tabData[this.nowTab].tableData[row], "variableValue", val)
    },
    saveAttr(row, value) {
      const obj = [{
        id: this.tabData[this.nowTab].tableData[row].id,
        variable_value: value
      }]
      if (obj[0].variable_value) {
        this.updateDiffConfig(obj);
      }
    },
    updateDiffConfig(data) {
      const params = {
        packageName: cmdbPackageName,
        entityName: DIFF_CONFIGURATION,
        data,
        callback: () => {
          this.$Notice.success({
            title: this.$t("artifacts_successed")
          });
          this.getKeys(this.tabData[this.nowTab]);
        }
      }
      this.updateEntity(params)
    },
    async getAllSystemEnumCodes() {
      const { status, data, message } = await getAllSystemEnumCodes({
        filters: [
          {
            name: "cat.catName",
            operator: "eq",
            value: "state_transition_operation"
          }
        ],
        paging: false
      });
      if (status === "OK" && data.contents instanceof Array) {
        const buttonTypes = {
          confirm: "info",
          delete: "error",
          discard: "warning",
          update: "primary"
        };
        this.statusOperations = data.contents
          .filter(
            _ =>
              _.code === "confirm" ||
              _.code === "delete" ||
              _.code === "discard" ||
              _.code === "update"
          )
          .map(_ => {
            return {
              type: _.code,
              label: _.code !== "update" ? _.value : this.$t("artifacts_configuration"),
              props: {
                type: buttonTypes[_.code] || "info",
                size: "small"
              },
              actionType: _.code
            };
          });
      }
    },
    getHeaders () {
      let refreshRequest = null
      const currentTime = new Date().getTime()
      let session = window.sessionStorage
      const token = JSON.parse(session.getItem('token'))
      if (token) {
        const accessToken = token.find(t => t.tokenType === 'accessToken')
        const expiration = accessToken.expiration * 1 - currentTime
        if (expiration < 1 * 60 * 1000 && !refreshRequest) {
          refreshRequest = axios.get('/auth/v1/api/token', {
            headers: {
              Authorization:
                'Bearer ' +
                token.find(t => t.tokenType === 'refreshToken').token
            }
          })
          refreshRequest.then(
            res => {
              session.setItem('token', JSON.stringify(res.data.data))
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
      let session = window.sessionStorage
      const token = JSON.parse(session.getItem('token'))
      this.headers = {
        Authorization:
          'Bearer ' + token.find(t => t.tokenType === 'accessToken').token
      }
    }
  },
  created() {
    this.fetchData();
    this.getSpecialConnector();
    this.getAllCITypesWithAttr();
    this.getAllSystemEnumCodes();
  }
};
</script>

<style lang="scss" scoped>
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
