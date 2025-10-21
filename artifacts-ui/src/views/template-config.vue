<template>
  <div class="main-content">
    <div class="content-search">
      <div>
        <Input v-model="templateName" style="width: 250px" clearable :placeholder="$t('art_please_enter') + $t('art_template_name')" @on-change="onFilterConditionChange"> </Input>
        <Select v-model="templateCreateUser" style="width: 250px; margin-left: 20px" clearable filterable label-in-name @on-change="onFilterConditionChange" :placeholder="$t('art_creator')">
          <Option v-for="user in creatorList" :value="user.username" :label="user.username" :key="user.id">
            {{ user.username }}
          </Option>
        </Select>
      </div>
      <Button class="add-content-item" @click="onAddButtonClick" type="success">{{ $t('art_add_template') }}</Button>
    </div>

    <div class="content-table">
      <Table size="small" :loading="remoteLoading" :columns="templateTableColumns" :data="templateTableData" />
    </div>
    <Page
      class="table-pagination"
      :total="pagination.total"
      @on-change="
        e => {
          pagination.currentPage = e
          this.getTemplateList()
        }
      "
      @on-page-size-change="
        e => {
          pagination.pageSize = e
          this.getTemplateList()
        }
      "
      :current="pagination.currentPage"
      :page-size="pagination.pageSize"
      show-total
      show-sizer
    />
    <DiffVariableTemplate ref="diffVariableTemplateRef" :useRolesRequired="true" @reloadTableData="getTemplateList" @addTableItemSuccess="getTemplateList">
      <template v-slot:formItem>
        <div style="display: flex;align-items: center;margin-left: 40px">
          <span>{{ $t('art_value_rule') + '&nbsp;&nbsp;&nbsp;' }}</span>
          <ArtifactsAutoFill v-model="currentModelValue" style="margin-top:5px; width: 800px; margin-top: 20px; margin-bottom: 20px;" :ciTypesObj="ciTypesObj" :ciTypeAttrsObj="ciTypeAttrsObj" :specialDelimiters="specialDelimiters" rootCiTypeId="app_instance" :isReadOnly="false" cmdbPackageName="wecmdb" />
        </div>
      </template>
    </DiffVariableTemplate>
  </div>
</template>

<script>
import { getTemplate, getUserList, getAllCITypesWithAttr, getSpecialConnector, deleteTemplate, getRoleList, getCurrentUserRoles, getTemplateBindList } from '@/api/server.js'
import { debounce, isEmpty } from 'lodash'
import Vue from 'vue'
import DiffVariableTemplate from '@/components/diff-variable-template'

export default {
  name: '',
  data () {
    return {
      templateName: '',
      templateCreateUser: '',
      templateTableColumns: [
        {
          title: this.$t('art_template_name'),
          width: 150,
          key: 'code',
          tooltip: true,
          align: 'center'
        },
        {
          title: this.$t('art_value_rule'),
          minWidth: 300,
          key: 'value',
          align: 'center',
          render: (h, params) => {
            return <ArtifactsAutoFill style="margin-top:5px;" ciTypesObj={this.ciTypesObj} ciTypeAttrsObj={this.ciTypeAttrsObj} specialDelimiters={this.specialDelimiters} rootCiTypeId="" isReadOnly={true} v-model={params.row.value} cmdbPackageName="wecmdb" />
          }
        },
        {
          title: this.$t('mgmt_role'),
          minWidth: 150,
          align: 'center',
          render: (h, params) => {
            const mgmtRolesKeyToFlow = params.row.roles.filter(r => r.permission === 'MGMT').map(r => r.role)
            const strArray = this.allRoles.filter(item => mgmtRolesKeyToFlow.includes(item.name)).map(one => one.displayName)
            return <span>{strArray.join(',')}</span>
          }
        },
        {
          title: this.$t('use_role'),
          minWidth: 150,
          align: 'center',
          render: (h, params) => {
            const useRolesKeyToFlow = params.row.roles.filter(r => r.permission === 'USE').map(r => r.role)
            const strArray = this.allRoles.filter(item => useRolesKeyToFlow.includes(item.name)).map(one => one.displayName)
            return <span>{strArray.join(',')}</span>
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
          render: (h, params) => {
            const mgmtRolesKeyToFlow = params.row.roles.filter(r => r.permission === 'MGMT').map(r => r.role)
            const strArray = this.currentUserRoles.filter(item => mgmtRolesKeyToFlow.includes(item.name))
            const isDisabled = !(strArray.length > 0)
            return (
              <div style="display: flex;">
                <Tooltip content={this.$t('art_update')} placement="top" delay={500} transfer={true}>
                  <Button size="small" type="primary" disabled={isDisabled} onClick={() => this.templateAuth(params.row, event)} style={{ marginRight: '5px', marginBottom: '2px' }}>
                    <Icon type="md-create" />
                  </Button>
                </Tooltip>
                <Poptip confirm transfer title={this.$t('art_delConfirm_tip')} placement="left-end" on-on-ok={() => this.deleteConfirmModal(params.row)}>
                  <Button size="small" type="error" disabled={isDisabled}>
                    <Icon type="md-trash" />
                  </Button>
                </Poptip>
              </div>
            )
          }
        }
      ],
      templateTableData: [],
      pagination: {
        total: 0,
        currentPage: 1,
        pageSize: 10
      },
      remoteLoading: false,
      creatorList: [],
      ciTypes: [],
      ciTypesObj: {},
      ciTypeAttrsObj: {},
      specialDelimiters: [],
      isEmpty: isEmpty,
      currentModelValue: '',
      currentEditRow: {},
      allRoles: [],
      currentUserRoles: [],
      bindVariableNameList: []
    }
  },
  components: {
    DiffVariableTemplate
  },
  mounted () {
    this.getTemplateList()
    this.getCreatorList()
    this.getSpecialConnector()
    this.getAllCITypesWithAttr()
    this.getRoleList()
    this.getCurrentUserRoles()
  },
  watch: {
    currentModelValue: {
      handler (newVal) {
        if (newVal !== this.currentEditRow.value) {
          this.$refs.diffVariableTemplateRef.templateParams.value = newVal
          this.$refs.diffVariableTemplateRef.diffVariable = newVal
        }
      }
    }
  },
  methods: {
    async getSpecialConnector () {
      const res = await getSpecialConnector()
      if (res.status === 'OK') {
        this.specialDelimiters = res.data
      }
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
    async getCreatorList () {
      let { status, data } = await getUserList()
      if (status === 'OK') {
        this.creatorList = data || []
      }
    },
    async getTemplateList () {
      this.remoteLoading = true
      let params = {
        __offset: (this.pagination.currentPage - 1) * this.pagination.pageSize,
        __limit: this.pagination.pageSize
      }
      if (this.templateName) {
        params.code__icontains = this.templateName
      }
      if (this.templateCreateUser) {
        params.create_user = this.templateCreateUser
      }
      const queryString = new URLSearchParams(params).toString()
      const res = await getTemplate(queryString)
      if (res) {
        this.templateTableData = res.data.data
        this.pagination.total = res.data.count
      }
      if (!isEmpty(this.ciTypeAttrsObj)) {
        this.remoteLoading = false
      }
    },
    onFilterConditionChange: debounce(function () {
      this.getTemplateList()
    }, 500),
    onAddButtonClick () {
      this.currentModelValue = ''
      this.$refs.diffVariableTemplateRef.startAuth([], [], '', '')
    },
    async isTemplateBindVariable (id) {
      return new Promise(async (resolve, reject) => {
        let params = {
          __offset: 0,
          __limit: 1000,
          diff_conf_template_id: id
        }
        const queryString = new URLSearchParams(params).toString()
        const res = await getTemplateBindList(queryString)
        if (res.data.count > 0) {
          this.bindVariableNameList = res.data.data.map(item => item.name)
          resolve(true)
        } else {
          resolve(false)
        }
      })
    },
    async deleteConfirmModal (row) {
      if (await this.isTemplateBindVariable(row.id)) {
        this.$Message.error(this.$t('art_template_not_allow_delete_tips') + this.bindVariableNameList.join(',') + '; ' + this.$t('art_not_allow_delete'))
        return
      }
      const { status, message } = await deleteTemplate(row.id)
      if (status === 'OK') {
        this.$Notice.success({
          title: this.$t('artifacts_delete_success'),
          desc: message
        })
        this.getTemplateList()
      }
    },
    templateAuth (row) {
      this.currentEditRow = row
      this.currentModelValue = row.value
      this.$refs.diffVariableTemplateRef.editAuth(row)
    },
    async getRoleList () {
      const { status, data } = await getRoleList()
      if (status === 'OK') {
        this.allRoles = data.map(_ => ({
          ..._,
          key: _.name,
          label: _.displayName
        }))
      }
    },
    async getCurrentUserRoles () {
      const { status, data } = await getCurrentUserRoles()
      if (status === 'OK') {
        this.currentUserRoles = data.map(_ => ({
          ..._,
          key: _.name,
          label: _.displayName
        }))
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
