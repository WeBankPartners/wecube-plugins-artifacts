<template>
  <Modal v-model="flowRoleManageModal" width="720" :title="$t('role_drawer_title')" :mask-closable="false" class="platform-base-role-transfer">
    <Form :label-width="100">
      <FormItem :label="$t('art_name')">
        <Input v-model="templateParams.code" @input="templateParams.code = templateParams.code.trim()" :placeholder="$t('art_name')" maxlength="30" show-word-limit></Input>
      </FormItem>
    </Form>
    <div class="content">
      <div>
        <div class="role-transfer-title">{{ $t('mgmt_role') }}</div>
        <Transfer :titles="transferTitles" :list-style="transferStyle" :data="currentUserRoles" :target-keys="mgmtRolesKeyToFlow" :render-format="renderRoleNameForTransfer" @on-change="handleMgmtRoleTransferChange" filterable></Transfer>
      </div>
      <div style="margin-top: 30px">
        <div class="role-transfer-title">{{ $t('use_role') }}</div>
        <Transfer :titles="transferTitles" :list-style="transferStyle" :data="allRoles" :target-keys="useRolesKeyToFlow" :render-format="renderRoleNameForTransfer" @on-change="handleUseRoleTransferChange" filterable></Transfer>
      </div>
    </div>
    <div slot="footer">
      <Button type="primary" :disabled="disabled" @click="saveAsTemplate">{{ $t('artifacts_save') }}</Button>
    </div>
  </Modal>
</template>
<script>
import { getRoleList, getCurrentUserRoles, saveTemplate, updateTemplate } from '@/api/server.js'
export default {
  props: {
    useRolesRequired: {
      type: Boolean,
      default: false
    }
  },
  data () {
    return {
      isAdd: false,
      flowRoleManageModal: false, // 权限弹窗控制
      transferTitles: [this.$t('unselected_role'), this.$t('selected_role')],
      transferStyle: { width: '300px' },
      allRoles: [],
      currentUserRoles: [],
      mgmtRolesKeyToFlow: [], // 管理角色
      useRolesKeyToFlow: [], // 使用角色
      templateParams: {
        type: '',
        code: '',
        value: '',
        description: '',
        roles: {
          MGMT: [],
          USE: []
        }
      }
    }
  },
  computed: {
    disabled () {
      if (this.useRolesRequired) {
        return this.mgmtRolesKeyToFlow.length === 0 || this.useRolesKeyToFlow.length === 0 || this.templateParams.code === ''
      }
      return this.mgmtRolesKeyToFlow.length === 0 || this.templateParams.code === ''
    }
  },
  methods: {
    renderRoleNameForTransfer (item) {
      return item.label
    },
    handleMgmtRoleTransferChange (newTargetKeys) {
      if (newTargetKeys.length > 1) {
        this.$Message.warning(this.$t('chooseOne'))
      } else {
        this.mgmtRolesKeyToFlow = newTargetKeys
      }
    },
    handleUseRoleTransferChange (newTargetKeys) {
      this.useRolesKeyToFlow = newTargetKeys
    },
    async saveAsTemplate () {
      this.templateParams.roles.MGMT = this.mgmtRolesKeyToFlow
      this.templateParams.roles.USE = this.useRolesKeyToFlow
      console.log(this.templateParams)
      const method = this.isAdd ? saveTemplate : updateTemplate
      let params = this.isAdd ? [this.templateParams] : this.templateParams
      const { status } = await method(params, this.templateParams.id)
      if (status === 'OK') {
        this.$Notice.success({
          title: this.$t('artifacts_successed')
        })
        this.flowRoleManageModal = false
        if (!this.isAdd) {
          this.$emit('reloadTableData')
        }
      }
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
    },
    // 启动入口
    async startAuth (mgmtRolesKeyToFlow, useRolesKeyToFlow, diffExpr) {
      console.log(1.1, diffExpr)
      this.isAdd = true
      this.templateParams.value = diffExpr
      this.templateParams.code = ''
      this.mgmtRolesKeyToFlow = mgmtRolesKeyToFlow
      this.useRolesKeyToFlow = useRolesKeyToFlow
      await this.getRoleList()
      await this.getCurrentUserRoles()
      this.flowRoleManageModal = true
    },
    async editAuth (row) {
      this.isAdd = false
      this.templateParams = row
      this.mgmtRolesKeyToFlow = row.roles.filter(r => r.permission === 'MGMT').map(r => r.role)
      this.useRolesKeyToFlow = row.roles.filter(r => r.permission === 'USE').map(r => r.role)
      this.templateParams.roles = {}
      await this.getRoleList()
      await this.getCurrentUserRoles()
      this.flowRoleManageModal = true
    }
  }
}
</script>
<style lang="scss" scoped>
.platform-base-role-transfer {
  .content {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
}
</style>
