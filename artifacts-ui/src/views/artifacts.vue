<template>
  <Row id="weArtifacts" class="artifact-management">
    <Col span="6">
      <Card>
        <p slot="title">系统设计版本</p>
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
        <p slot="title">系统设计列表</p>
        <div class="artifact-management-tree-body">
          <Tree :data="treeData" @on-select-change="selectTreeNode"></Tree>
          <Spin size="large" fix v-if="treeLoading">
            <Icon type="ios-loading" size="24" class="spin-icon-load"></Icon>
            <div>loading...</div>
          </Spin>
        </div>
      </Card>
    </Col>
    <Col span="17" offset="1">
      <Card v-if="guid" class="artifact-management-top-card">
        <Upload
          :action="`/artifacts/unit-designs/${guid}/packages/upload`"
          :headers="setUploadActionHeader"
          :on-success="uploadPackagesSuccess"
          slot="title"
        >
          <Button icon="ios-cloud-upload-outline">上传新包</Button>
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
          title="脚本配置"
          okText="保存"
          :loading="loadingForSave"
          @on-ok="saveConfigFiles"
          @on-cancel="closeModal"
        >
          <Card class="artifact-management-files-card">
            <div slot="title">
              <span>差异化文件</span>
              <Button @click="() => showTreeModal(0)" size="small"
                >选择文件</Button
              >
            </div>
            <span>{{ currentPackage.diff_conf_file || "未选择" }}</span>
          </Card>
          <Card class="artifact-management-files-card">
            <div slot="title">
              <span>启动脚本</span>
              <Button @click="() => showTreeModal(1)" size="small"
                >选择文件</Button
              >
            </div>
            <span>{{ currentPackage.start_file_path || "未选择" }}</span>
          </Card>
          <Card class="artifact-management-files-card">
            <div slot="title">
              <span>停止脚本</span>
              <Button @click="() => showTreeModal(2)" size="small"
                >选择文件</Button
              >
            </div>
            <span>{{ currentPackage.stop_file_path || "未选择" }}</span>
          </Card>
          <Card class="artifact-management-files-card">
            <div slot="title">
              <span>部署脚本</span>
              <Button @click="() => showTreeModal(3)" size="small"
                >选择文件</Button
              >
            </div>
            <span>{{ currentPackage.deploy_file_path || "未选择" }}</span>
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
  retrieveEntity,
  getAllSystemEnumCodes
} from "@/api/server.js";

// 业务运行实例ciTypeId
const rootCiTypeId = 14
// cmdb插件包名
const cmdbPackageName = "wecmdb"
// 差异变量key_name
const entityName = "diff_configuration"

export default {
  name: "artifacts",
  data() {
    return {
      packageCiType: 0,
      statusOperations: [],
      systemDesignVersions: [],
      systemDesignVersion: "",
      ciTypes: [],
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
          title: "选择差异化文件",
          key: "diff_conf_file",
          inputType: "checkbox"
        },
        {
          title: "选择启动脚本",
          key: "start_file_path",
          inputType: "radio"
        },
        {
          title: "选择停止脚本",
          key: "stop_file_path",
          inputType: "radio"
        },
        {
          title: "选择部署脚本",
          key: "deploy_file_path",
          inputType: "radio"
        }
      ],
      currentTreeModal: {},
      tableLoading: false,
      tableData: [],
      tableColumns: [
        {
          title: "包名",
          key: "name",
          render: (h, params) => this.renderCell(params.row.name)
        },
        {
          title: "上传时间",
          width: 120,
          key: "upload_time"
        },
        {
          title: "MD5值",
          key: "md5_value",
          render: (h, params) => this.renderCell(params.row.md5_value)
        },
        {
          title: "上传人",
          key: "updated_by",
          render: (h, params) => this.renderCell(params.row.updated_by)
        },
        {
          title: "差异化文件",
          key: "diff_conf_file",
          render: (h, params) => this.renderCell(params.row.diff_conf_file)
        },
        {
          title: "启动脚本",
          key: "start_file_path",
          render: (h, params) => this.renderCell(params.row.start_file_path)
        },
        {
          title: "停止脚本",
          key: "stop_file_path",
          render: (h, params) => this.renderCell(params.row.stop_file_path)
        },
        {
          title: "部署脚本",
          key: "deploy_file_path",
          render: (h, params) => this.renderCell(params.row.deploy_file_path)
        },
        {
          title: "操作",
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
          title: "序号",
          key: "index",
          width: 60
        },
        {
          title: "文件行号",
          key: "line"
        },
        {
          title: "properties-key",
          key: "key"
        },
        {
          title: "CMDB-ATTR",
          render: (h, params) => {
            return params.row.attrInputValue ? (
              <ArtifactsAttrInput
                style="margin-top:5px;"
                allCiTypes={this.ciTypes}
                rootCiTypeId={rootCiTypeId}
                isReadOnly={true}
                v-model={params.row.attrInputValue}
              />
            ) : (
              <div style="align-items:center;display:flex;">
                <ArtifactsAttrInput
                  style="margin-top:5px;width:calc(100% - 55px);"
                  allCiTypes={this.ciTypes}
                  rootCiTypeId={rootCiTypeId}
                  v-model={params.row.attrInputValue}
                  onUpdateValue={val => this.updateAttrInputValue(val, params.index)}
                />
                <Button
                  size="small"
                  type="primary"
                  style="margin-left:10px"
                  onClick={() => this.saveAttr(params.index)}
                >
                  保存
                </Button>
              </div>
            );
          }
        }
      ]
    };
  },
  computed: {
    setUploadActionHeader() {
      let uploadToken = document.cookie
        .split(";")
        .find(i => i.indexOf("XSRF-TOKEN") !== -1);
      return {
        "X-XSRF-TOKEN": uploadToken && uploadToken.split("=")[1]
      };
    },
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
    renderCell(content) {
      return (
        <Tooltip style="width: 100%;" >
          <span slot="content" style="white-space:normal;">{content} </span>
          <div style="width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{content}</div>
        </Tooltip>
      )
    },
    uploadPackagesSuccess(response, file, fileList) {
      if (response.status === "ERROR") {
        this.$Notice.error({
          title: "Error",
          desc: response.message || ""
        });
      } else {
        this.queryPackages();
      }
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
        "dirty"
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
        const diffConfigs = await retrieveEntity(cmdbPackageName, entityName);
        if (diffConfigs.status === "OK") {
          const result = data.outputs[0].configKeyInfos.map((_, i) => {
            _.index = i + 1;
            const found = diffConfigs.data.find(
              item => item.variable_name === _.key
            );
            if (found) {
              _.attrInputValue = found.variable_value;
            }
            return _;
          });
          this.$set(options, "tableData", result);
        }
      }
    },
    async saveConfigFiles() {
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
          title: "保存成功"
        });
      }
      this.queryPackages();
      this.getTabDatas(this.diffTabData);
    },
    async createEntity(obj) {
      let { status, data, message } = await createEntity(cmdbPackageName, entityName, obj);
      if (status === "OK") {
        this.$Notice.success({
          title: "保存成功"
        });
        this.getKeys(this.tabData[this.nowTab]);
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
        } else {
          obj.render = (h, params) => {
            return this.currentTreeModal.inputType === "checkbox" ? (
              <Checkbox
                on-on-change={value => this.checkboxChange(value, params.data)}
              >
                <span>{params.data.title}</span>
              </Checkbox>
            ) : (
              <Radio label={params.data.path}>
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
        title: "确认删除？",
        "z-index": 1000000,
        onOk: async () => {
          const { status, data, message } = await deleteCiDatas({
            id: this.packageCiType,
            deleteData: [row.guid]
          });
          if (status === "OK") {
            this.$Notice.success({
              title: "Delete data Success",
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
        this.getKeys(this.tabData[0]);
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
    updateAttrInputValue(val, row) {
      this.tabData[this.nowTab].tableData[row].variableValue = val;
    },
    saveAttr(row) {
      const obj = [{
        variable_name: this.tabData[this.nowTab].tableData[row].key,
        variable_value: this.tabData[this.nowTab].tableData[row].variableValue,
      }]
      this.createEntity(obj);
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
              label: _.code !== "update" ? _.value : "配置",
              props: {
                type: buttonTypes[_.code] || "info",
                size: "small"
              },
              actionType: _.code
            };
          });
      }
    }
  },
  created() {
    this.fetchData();
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
}
</style>
