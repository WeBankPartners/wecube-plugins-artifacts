<template>
  <div class="main-content">
    <div class="content-search">
      <div>
        <Input v-model="variableName" style="width: 250px" clearable :placeholder="$t('art_please_enter') + $t('art_variable_name')" @on-change="onFilterConditionChange"> </Input>
        <Select v-model="bindCreateUser" style="width: 250px; margin-left: 20px" clearable filterable label-in-name @on-change="onFilterConditionChange" :placeholder="$t('art_creator')">
          <Option v-for="user in creatorList" :value="user.username" :label="user.username" :key="user.id">
            {{ user.username }}
          </Option>
        </Select>
      </div>
      <Button class="add-content-item" @click="onAddButtonClick" type="success">{{ $t('art_add_template_bind') }}</Button>
    </div>

    <div class="content-table">
      <Table size="small" :loading="remoteLoading" :columns="templateTableColumns" :data="templateBindTableData" />
    </div>
    <Page
      class="table-pagination"
      :total="pagination.total"
      @on-change="
        e => {
          pagination.currentPage = e
          this.getVariableTemplatBindList()
        }
      "
      @on-page-size-change="
        e => {
          pagination.pageSize = e
          this.getVariableTemplatBindList()
        }
      "
      :current="pagination.currentPage"
      :page-size="pagination.pageSize"
      show-total
      show-sizer
    />
    <Modal v-model="isShowBindModal" :closable="false" :width="700" :title="$t('art_add_template_bind')">
      <div style="max-height: 500px;overflow-y: auto;">
        <Form :label-width="120">
          <FormItem :label="$t('art_variable_name')">
            <Input clearable v-model="formItem.name" />
          </FormItem>
          <FormItem :label="$t('art_template_name')">
            <Select v-model="formItem.diff_conf_template_id" filterable clearable @on-change="onTemplateChange" @on-clear="onTemplateClear">
              <Option v-for="item in allTemplateList" :value="item.id" :key="item.id" :label="item.code">
                {{ item.code }}
              </Option>
            </Select>
          </FormItem>
          <FormItem :label="$t('art_template_details')">
            <div style="color:gray">
              <ArtifactsAutoFill :ciTypesObj="ciTypesObj" :ciTypeAttrsObj="ciTypeAttrsObj" :specialDelimiters="specialDelimiters" rootCiTypeId="" :isReadOnly="true" v-model="diffVariableValue" cmdbPackageName="wecmdb" />
            </div>
          </FormItem>
        </Form>
      </div>
      <div slot="footer">
        <Button type="text" @click="closeShowBindModal()">{{ $t('artifacts_cancel') }} </Button>
        <Button type="primary" :disabled="!formItem.name || !formItem.diff_conf_template_id" @click="saveBindTemplate()">{{ $t('art_ok') }} </Button>
      </div>
    </Modal>
  </div>
</template>

<script>
import { getTemplateBindList, getUserList, getTemplate, saveTemplateBind, updateTemplateBind, getAllCITypesWithAttr, getSpecialConnector, deleteTemplateBind } from '@/api/server.js'
import { debounce, isEmpty } from 'lodash'
import Vue from 'vue'
import DiffVariableTemplate from '@/components/diff-variable-template'

export default {
  name: '',
  data () {
    return {
      variableName: '',
      bindCreateUser: '',
      creatorList: [],
      remoteLoading: false,
      templateTableColumns: [
        {
          title: this.$t('art_variable_name'),
          width: 150,
          key: 'name',
          tooltip: true,
          align: 'center'
        },
        {
          title: this.$t('art_template_name'),
          width: 150,
          key: 'id',
          tooltip: true,
          align: 'center',
          render: (h, params) => {
            return <span>{params.row.diff_conf_template.code}</span>
          }
        },
        {
          title: this.$t('art_template_details'),
          minWidth: 300,
          key: 'diff_conf_template_id',
          align: 'center',
          render: (h, params) => {
            return <ArtifactsAutoFill style="margin-top:5px;" ciTypesObj={this.ciTypesObj} ciTypeAttrsObj={this.ciTypeAttrsObj} specialDelimiters={this.specialDelimiters} rootCiTypeId="" isReadOnly={true} v-model={params.row.diff_conf_template.value} cmdbPackageName="wecmdb" />
          }
        },
        {
          title: this.$t('art_creator'),
          minWidth: 100,
          key: 'create_user',
          align: 'center'
        },
        {
          title: this.$t('art_create_time'),
          key: 'create_time',
          minWidth: 200,
          align: 'center'
        },
        {
          title: this.$t('art_update_user'),
          key: 'update_user',
          minWidth: 100,
          align: 'center'
        },
        {
          title: this.$t('artifacts_update_time'),
          key: 'update_time',
          minWidth: 200,
          align: 'center'
        },
        {
          title: this.$t('artifacts_action'),
          key: 'action',
          width: 100,
          align: 'center',
          fixed: 'right',
          render: (h, params) => (
            <div style="display: flex;">
              <Tooltip content={this.$t('art_update')} placement="top" delay={500} transfer={true}>
                <Button size="small" type="primary" onClick={() => this.editTemplateBind(params.row, event)} style={{ marginRight: '5px', marginBottom: '2px' }}>
                  <Icon type="md-create" />
                </Button>
              </Tooltip>
              <Poptip confirm transfer title={this.$t('art_delConfirm_tip')} placement="left-end" on-on-ok={() => this.deleteConfirmModal(params.row)}>
                <Button size="small" type="error">
                  <Icon type="md-trash" />
                </Button>
              </Poptip>
            </div>
          )
        }
      ],
      templateBindTableData: [],
      pagination: {
        total: 0,
        currentPage: 1,
        pageSize: 10
      },
      isShowBindModal: false,
      formItem: {
        name: '',
        diff_conf_template_id: null,
        description: ''
      },
      allTemplateList: [],
      isAdd: true,
      ciTypesObj: {},
      ciTypeAttrsObj: {},
      specialDelimiters: [],
      ciTypes: [],
      diffVariableValue: '',
      currentId: null
    }
  },
  components: {
    DiffVariableTemplate
  },
  mounted () {
    this.getCreatorList()
    this.getVariableTemplatBindList()
    this.getAllTemplateList()
    this.getAllCITypesWithAttr()
    this.getSpecialConnector()
  },
  methods: {
    onFilterConditionChange: debounce(function () {
      this.getVariableTemplatBindList()
    }, 500),
    onAddButtonClick () {
      this.isAdd = true
      this.isShowBindModal = true
    },
    async getVariableTemplatBindList () {
      this.remoteLoading = true
      let params = {
        __offset: (this.pagination.currentPage - 1) * this.pagination.pageSize,
        __limit: this.pagination.pageSize
      }
      if (this.variableName) {
        params.name__icontains = this.variableName
      }
      if (this.bindCreateUser) {
        params.create_user = this.bindCreateUser
      }
      const queryString = new URLSearchParams(params).toString()
      const res = await getTemplateBindList(queryString)
      if (res) {
        this.templateBindTableData = res.data.data
        this.pagination.total = res.data.count
      }
      if (!isEmpty(this.ciTypeAttrsObj)) {
        this.remoteLoading = false
      }
    },
    async getCreatorList () {
      let { status, data } = await getUserList()
      if (status === 'OK') {
        this.creatorList = data || []
      }
    },
    async getAllTemplateList () {
      const queryString = '__offset=0&__limit=10000'
      const res = await getTemplate(queryString)
      if (res) {
        this.allTemplateList = res.data.data
      }
    },
    closeShowBindModal () {
      this.isShowBindModal = false
      this.resetFormItem()
    },
    resetFormItem () {
      Vue.set(this.formItem, 'name', '')
      Vue.set(this.formItem, 'diff_conf_template_id', null)
      this.diffVariableValue = ''
      this.currentId = null
    },
    async saveBindTemplate () {
      const findBindparams = {
        __offset: 0,
        __limit: 10,
        name: this.formItem.name
      }
      const queryString = new URLSearchParams(findBindparams).toString()
      const res = await getTemplateBindList(queryString)
      if (res) {
        if (res.data.data.length > 0 && res.data.data.some(item => item.id !== this.currentId)) {
          this.$Notice.warning({
            title: 'Warning',
            desc: this.$t('art_variable_template_bind_name_exist')
          })
          return
        }
      }

      let method = null
      let params = null
      if (this.isAdd) {
        method = saveTemplateBind
        params = [this.formItem]
      } else {
        method = updateTemplateBind
        params = this.formItem
      }
      const { status } = await method(params, this.currentId)
      if (status === 'OK') {
        this.$Notice.success({
          title: 'Success',
          desc: this.$t('artifacts_successed')
        })
        this.closeShowBindModal()
        this.getVariableTemplatBindList()
      }
    },
    onTemplateChange (id) {
      if (id) {
        const template = this.allTemplateList.find(item => item.id === id)
        this.diffVariableValue = template.value
      }
    },
    onTemplateClear () {
      this.diffVariableValue = ''
    },
    async getAllCITypesWithAttr () {
      this.remoteLoading = true
      let { status, data } = await getAllCITypesWithAttr(['notCreated', 'created', 'dirty', 'deleted'])
      if (status === 'OK') {
        this.ciTypes = JSON.parse(JSON.stringify(data)).map(item => {
          item.attributes = item.attributes.map(attr => {
            let res = {
              ciTypeAttrId: attr.ciTypeAttrId,
              inputType: attr.inputType,
              ciTypeId: attr.ciTypeId,
              propertyName: attr.propertyName,
              name: attr.name
            }
            return res
          })
          return item
        })
        this.ciTypes.forEach(ciType => {
          Vue.set(this.ciTypesObj, ciType.ciTypeId, ciType)
          ciType.attributes.forEach(attr => {
            this.ciTypeAttrsObj[attr.ciTypeAttrId] = attr
          })
        })
        this.remoteLoading = false
      }
    },
    async getSpecialConnector () {
      const res = await getSpecialConnector()
      if (res.status === 'OK') {
        this.specialDelimiters = res.data
      }
    },
    editTemplateBind (row) {
      this.isAdd = false
      Vue.set(this.formItem, 'name', row.name)
      Vue.set(this.formItem, 'diff_conf_template_id', row.diff_conf_template_id)
      const template = this.allTemplateList.find(item => item.id === row.diff_conf_template_id)
      this.diffVariableValue = template.value
      this.currentId = row.id
      this.isShowBindModal = true
    },
    async deleteConfirmModal (row) {
      const { status, message } = await deleteTemplateBind(row.id)
      if (status === 'OK') {
        this.$Notice.success({
          title: this.$t('artifacts_delete_success'),
          desc: message
        })
        this.getVariableTemplatBindList()
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.main-content {
  .content-search {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 20px;
  }
  .table-pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
