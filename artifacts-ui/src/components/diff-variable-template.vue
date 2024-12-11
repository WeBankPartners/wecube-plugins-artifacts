<template>
  <Modal v-model="flowRoleManageModal" width="720" :title="$t('role_drawer_title')" :mask-closable="false" class="platform-base-role-transfer">
    <Form :label-width="100">
      <FormItem :label="$t('art_name')">
        <Input v-model="templateParams.code" @input="templateParams.code = templateParams.code.trim()" :placeholder="$t('art_name')" maxlength="30" show-word-limit></Input>
      </FormItem>
      <FormItem label="" style="display: none;">
        <Input v-model="templateParams.value" type="textarea"></Input>
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
      },
      key: '' // 当前编辑行的属性名
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
      let method = null
      let params = null
      if (this.isAdd) {
        method = saveTemplate
        this.templateParams.value = this.valueMgmt(this.templateParams.value)
        params = [this.templateParams]
      } else {
        method = updateTemplate
        params = this.templateParams
      }
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
    async startAuth (mgmtRolesKeyToFlow, useRolesKeyToFlow, diffExpr, key) {
      this.isAdd = true
      this.templateParams.value = diffExpr
      this.key = key
      this.templateParams.code = ''
      this.mgmtRolesKeyToFlow = mgmtRolesKeyToFlow
      this.useRolesKeyToFlow = useRolesKeyToFlow
      await this.getRoleList()
      await this.getCurrentUserRoles()
      this.flowRoleManageModal = true
    },
    // 属性规则转换成模版
    valueMgmt (diffExpr) {
      let input = diffExpr
      // const input = `[{"type":"rule","value":"[{\\"ciTypeId\\":\\"app_instance\\",\\"filters\\":[{\\"name\\":\\"create_user\\",\\"operator\\":\\"eq\\",\\"type\\":\\"value\\",\\"value\\":\\"test\\"},{\\"name\\":\\"code\\",\\"operator\\":\\"eq\\",\\"type\\":\\"autoFill\\",\\"value\\":\\"[{\\\\\\"type\\\\\\":\\\\\\"rule\\\\\\",\\\\\\"value\\\\\\":\\\\\\"[{\\\\\\\\\\\\\\"ciTypeId\\\\\\\\\\\\\\":\\\\\\\\\\\\\\"app_instance\\\\\\\\\\\\\\",\\\\\\\\\\\\\\"filters\\\\\\\\\\\\\\":[{\\\\\\\\\\\\\\"name\\\\\\\\\\\\\\":\\\\\\\\\\\\\\"asset_id\\\\\\\\\\\\\\",\\\\\\\\\\\\\\"operator\\\\\\\\\\\\\\":\\\\\\\\\\\\\\"eq\\\\\\\\\\\\\\",\\\\\\\\\\\\\\"type\\\\\\\\\\\\\\":\\\\\\\\\\\\\\"value\\\\\\\\\\\\\\",\\\\\\\\\\\\\\"value\\\\\\\\\\\\\\":\\\\\\\\\\\\\\"123\\\\\\\\\\\\\\"}]},{\\\\\\\\\\\\\\"ciTypeId\\\\\\\\\\\\\\":\\\\\\\\\\\\\\"app_instance\\\\\\\\\\\\\\",\\\\\\\\\\\\\\"parentRs\\\\\\\\\\\\\\":{\\\\\\\\\\\\\\"attrId\\\\\\\\\\\\\\":\\\\\\\\\\\\\\"app_instance__create_user\\\\\\\\\\\\\\",\\\\\\\\\\\\\\"isReferedFromParent\\\\\\\\\\\\\\":1}}]\\\\\\"}]\\"}]},{\\"ciTypeId\\":\\"app_instance\\",\\"parentRs\\":{\\"attrId\\":\\"app_instance__port\\",\\"isReferedFromParent\\":1}}]"}]`
      // 将表达式转成json
      const result = this.deepParseJSON(input)
      // 找出 type: 'value' 的 JSON 对象中的 value 值
      const res = this.extractValueByType(result)
      // 在表达式中找出以"+value值开始，以"结束的字符串，中间可能包含多个转义符(\)
      res.forEach((r, rIndex) => {
        const pattern = new RegExp(`"${r}(?:\\\\)*?"`) // 动态创建正则表达式
        const matches = input.match(pattern)
        if (!matches) {
          return
        }
        const matchStr = matches[0]
        let replaceStr = ''
        if (matchStr.startsWith(`"${this.key}`)) {
          replaceStr = matchStr.replace(this.key, `!&defaultParam!&`)
        } else {
          replaceStr = matchStr.replace(res[rIndex], `$^${'params_' + rIndex}$^`)
        }
        // 替换表达式中的目标字符串
        input = input.replace(matchStr, replaceStr)
      })
      return input
    },

    extractValueByType (data, targetType = 'value') {
      const result = [] // 存储所有匹配的 value 值
      function traverse (node) {
        if (Array.isArray(node)) {
          node.forEach(traverse) // 遍历数组中的每个元素
        } else if (node && typeof node === 'object') {
          if (node.type === targetType && node.hasOwnProperty('value')) {
            result.push(node.value) // 提取匹配的 value 值
          }
          // 遍历对象中的所有属性
          Object.values(node).forEach(traverse)
        }
      }
      traverse(data)
      return result
    },
    stringifyFilters (obj) {
      if (Array.isArray(obj)) {
        return obj.map(item => this.stringifyFilters(item)) // 递归处理数组中的每个元素
      } else if (typeof obj === 'object' && obj !== null) {
        const newObj = {}
        for (const key in obj) {
          if (key === 'filters') {
            newObj[key] = JSON.stringify(obj[key].map(this.stringifyFilters)) // 处理 filters 字段并转为字符串
          } else {
            newObj[key] = this.stringifyFilters(obj[key]) // 递归处理其他字段
          }
        }
        return newObj
      }
      return obj // 基本类型直接返回
    },
    stringifyDeepestFirst (data) {
      // 递归处理对象
      if (Array.isArray(data)) {
        // 处理数组：遍历每个元素，并将转换后的值替换原值
        return JSON.stringify(data.map(item => this.stringifyDeepestFirst(item)))
      } else if (typeof data === 'object' && data !== null) {
        // 处理对象：遍历每个属性，递归转换后赋值
        for (const key in data) {
          data[key] = this.stringifyDeepestFirst(data[key])
        }
        return JSON.stringify(data) // 转换对象为字符串
      }
      return data // 如果是基本类型，直接返回
    },
    deepParseJSON (input) {
      if (typeof input === 'string') {
        try {
          const parsed = JSON.parse(input)
          return this.deepParseJSON(parsed) // 继续递归解析
        } catch {
          return input // 如果解析出错，返回原值（终止条件）
        }
      } else if (Array.isArray(input)) {
        return input.map(item => this.deepParseJSON(item)) // 递归解析数组
      } else if (typeof input === 'object' && input !== null) {
        for (const key in input) {
          input[key] = this.deepParseJSON(input[key]) // 递归解析对象字段
        }
        return input
      }
      return input
    },
    updateFilters (input) {
      if (Array.isArray(input)) {
        // 遍历数组中的每个元素
        return input.map(item => this.updateFilters(item))
      } else if (typeof input === 'object' && input !== null) {
        // 如果对象包含 filters 数组
        if (Array.isArray(input.filters)) {
          input.filters = input.filters.map(filter => {
            if (filter.type === 'value') {
              filter.value = 'testF' // 修改 value 字段值为 'testF'
            }
            return filter
          })
        }
        // 递归处理对象的其他字段
        for (const key in input) {
          input[key] = this.updateFilters(input[key])
        }
      }
      return input
    },
    async editAuth (row) {
      this.isAdd = false
      this.templateParams = JSON.parse(JSON.stringify(row))
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
