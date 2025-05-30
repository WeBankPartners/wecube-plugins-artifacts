<template>
  <Modal v-model="flowRoleManageModal" width="1000" :fullscreen="fullscreen" :mask-closable="false" class="platform-base-role-transfer">
    <div slot="header" style="display: flex;align-items: center;justify-content: space-between;">
      <h6>{{ isAdd ? $t('art_add_template') : $t('art_edit_template') }}</h6>
      <!-- <Icon v-if="!fullscreen" @click="zoomModalMax" class="header-icon" type="ios-expand" />
      <Icon v-else @click="zoomModalMin" class="header-icon" type="ios-contract" /> -->
    </div>
    <div v-if="flowRoleManageModal" class="flow-role-transfer-container" :style="{ height: fileContentHeight + 'px' }">
      <Form :label-width="90">
        <FormItem :label="$t('art_name')" style="margin-bottom: 0;">
          <Input v-model="templateParams.code" @input="templateParams.code = templateParams.code.trim()" :placeholder="$t('art_name')" maxlength="30" show-word-limit style="width: 96%"></Input>
        </FormItem>
        <FormItem label="" style="display: none;">
          <Input v-model="templateParams.value" type="textarea"></Input>
        </FormItem>
      </Form>
      <div v-if="isAdd" style="margin-bottom: 0;margin: 0 50px;">
        <template v-if="customParamsName.length > 0">
          <div>
            <div style="width: 100px;display: inline-block;">{{ $t('art_template_parameter') }}</div>
            <div style="width: 320px;display: inline-block;">{{ $t('art_parameter_name') }}</div>
            <div style="width: 380px;margin-left: 40px;display: inline-block;">{{ $t('art_parameter_value') }}</div>
          </div>
          <div v-for="(item, index) in customParamsName" :key="index" style="margin-bottom: 4px;">
            <div style="width: 100px;display: inline-block;">
              <Checkbox v-model="item.isReplace" @on-change="item.newParam = item.newParamOrigin">
                {{ item.isReplace ? $t('art_parameter') : $t('art_constant') }}
              </Checkbox>
            </div>
            <div style="width: 320px;display: inline-block;">
              <span style="color:red">*</span>
              <Input v-model="item.newParam" :placeholder="$t('art_param_replace_tip')" :disabled="!item.isReplace" style="width: 90%;" maxlength="30" show-word-limit></Input>
            </div>
            <Tooltip>
              <div slot="content" style="white-space: normal;word-break: break-all;">
                {{ item.key }}
              </div>
              <div :style="item.type === 'default' ? 'font-weight: 600;' : ''" style="width: 380px;margin-left: 40px;display: inline-block;white-space: nowrap;overflow: hidden;text-overflow: ellipsis;vertical-align: middle;">
                {{ item.key }}
              </div>
            </Tooltip>
          </div>
        </template>
      </div>
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
      fileContentHeight: window.screen.availHeight * 0.4 + 140,
      fullscreen: false,
      isAdd: false,
      flowRoleManageModal: false, // 权限弹窗控制
      transferTitles: [this.$t('unselected_role'), this.$t('selected_role')],
      transferStyle: { width: '400px', height: '300px' },
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
      key: '', // 当前编辑行的属性名
      customParamsName: [], // 缓存格式化出的参数，供用户替换
      diffVariable: ''
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
    zoomModalMax () {
      this.fileContentHeight = window.screen.availHeight - 290
      this.fullscreen = true
    },
    zoomModalMin () {
      this.fileContentHeight = window.screen.availHeight * 0.4 + 100
      this.fullscreen = false
    },
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
        if (!this.paramsReplace()) return
        this.templateParams.value = this.diffVariable
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
    // 新增入口
    async startAuth (mgmtRolesKeyToFlow, useRolesKeyToFlow, diffExpr, key) {
      this.isAdd = true
      this.fullscreen = false
      this.templateParams.value = diffExpr
      this.key = key
      this.templateParams.code = ''
      this.mgmtRolesKeyToFlow = mgmtRolesKeyToFlow
      this.useRolesKeyToFlow = useRolesKeyToFlow
      await this.getRoleList()
      await this.getCurrentUserRoles()
      this.valueMgmt(this.templateParams.value)
      this.flowRoleManageModal = true
    },
    // 检测替换名是否相同
    hasDuplicateValue (array, key) {
      const seen = new Set()
      for (const item of array) {
        if (seen.has(item[key])) {
          return true // 找到重复值
        }
        seen.add(item[key])
      }
      return false // 没有重复值
    },
    // 将默认的参数替换成用户自定义的参数
    paramsReplace () {
      const customParamsName = this.customParamsName.filter(item => item.isReplace)
      // 格式校验
      const paramsValidate = customParamsName.every(item => {
        return /^[a-zA-Z][a-zA-Z0-9_]{0,28}[a-zA-Z0-9]$/.test(item.newParam.trim())
      })
      if (!paramsValidate) {
        this.$Notice.error({
          title: 'Error',
          desc: `${this.$t('art_parameter_name')} ${this.$t('art_param_replace_tip')}`
        })
        return false
      }
      // 重名校验
      const hasDuplicateValue = this.hasDuplicateValue(customParamsName, 'newParam')
      if (hasDuplicateValue) {
        this.$Notice.error({
          title: 'Error',
          desc: `${this.$t('art_parameter_name')} ${this.$t('art_cannot_be_repeated')}`
        })
        return false
      }
      this.customParamsName.forEach(item => {
        if (item.type === 'default') {
          if (item.isReplace) {
            this.diffVariable = this.diffVariable.replace(item.defaultParam, `!&${item.newParam}!&`)
          } else {
            this.diffVariable = this.diffVariable.replace(`!&${item.newParam}!&`, item.key)
          }
        } else if (item.type === 'custom') {
          if (item.isReplace) {
            this.diffVariable = this.diffVariable.replace(item.defaultParam, `$^${item.newParam}$^`)
          } else {
            this.diffVariable = this.diffVariable.replace(`$^${item.newParamOrigin}$^`, item.key)
          }
        }
      })
      return true
    },
    // 属性规则转换成模版
    valueMgmt (diffExpr) {
      this.customParamsName = []
      let input = diffExpr
      // const input = `[{"type":"rule","value":"[{\\"ciTypeId\\":\\"app_instance\\",\\"filters\\":[{\\"name\\":\\"create_user\\",\\"operator\\":\\"eq\\",\\"type\\":\\"value\\",\\"value\\":\\"test\\"},{\\"name\\":\\"code\\",\\"operator\\":\\"eq\\",\\"type\\":\\"autoFill\\",\\"value\\":\\"[{\\\\\\"type\\\\\\":\\\\\\"rule\\\\\\",\\\\\\"value\\\\\\":\\\\\\"[{\\\\\\\\\\\\\\"ciTypeId\\\\\\\\\\\\\\":\\\\\\\\\\\\\\"app_instance\\\\\\\\\\\\\\",\\\\\\\\\\\\\\"filters\\\\\\\\\\\\\\":[{\\\\\\\\\\\\\\"name\\\\\\\\\\\\\\":\\\\\\\\\\\\\\"asset_id\\\\\\\\\\\\\\",\\\\\\\\\\\\\\"operator\\\\\\\\\\\\\\":\\\\\\\\\\\\\\"eq\\\\\\\\\\\\\\",\\\\\\\\\\\\\\"type\\\\\\\\\\\\\\":\\\\\\\\\\\\\\"value\\\\\\\\\\\\\\",\\\\\\\\\\\\\\"value\\\\\\\\\\\\\\":\\\\\\\\\\\\\\"123\\\\\\\\\\\\\\"}]},{\\\\\\\\\\\\\\"ciTypeId\\\\\\\\\\\\\\":\\\\\\\\\\\\\\"app_instance\\\\\\\\\\\\\\",\\\\\\\\\\\\\\"parentRs\\\\\\\\\\\\\\":{\\\\\\\\\\\\\\"attrId\\\\\\\\\\\\\\":\\\\\\\\\\\\\\"app_instance__create_user\\\\\\\\\\\\\\",\\\\\\\\\\\\\\"isReferedFromParent\\\\\\\\\\\\\\":1}}]\\\\\\"}]\\"}]},{\\"ciTypeId\\":\\"app_instance\\",\\"parentRs\\":{\\"attrId\\":\\"app_instance__port\\",\\"isReferedFromParent\\":1}}]"}]`
      // 将表达式转成json
      const result = this.deepParseJSON(input)
      // 找出 type: 'value' 的 JSON 对象中的 value 值
      const res = this.extractValueByType(result)
      // 在表达式中找出以"+value值开始，以"结束的字符串，中间可能包含多个转义符(\)
      res.forEach((r, rIndex) => {
        const pattern = new RegExp(`"${r.value}(?:\\\\)*?"`) // 动态创建正则表达式
        const matches = input.match(pattern)
        if (!matches) {
          return
        }
        const matchStr = matches[0]
        let replaceStr = ''
        let defaultParam = 'defaultParam'
        if (matchStr.startsWith(`"${this.key}`)) {
          replaceStr = matchStr.replace(this.key, `!&defaultParam!&`)
          this.customParamsName.push({
            isReplace: true,
            type: 'default',
            key: res[rIndex].value,
            defaultParam: `!&${defaultParam}!&`,
            newParam: defaultParam,
            newParamOrigin: defaultParam
          })
        } else {
          defaultParam = r.name
          replaceStr = matchStr.replace(res[rIndex].value, `$^${defaultParam}$^`)
          this.customParamsName.push({
            isReplace: true,
            type: 'custom',
            key: res[rIndex].value,
            defaultParam: `$^${defaultParam}$^`,
            newParam: defaultParam,
            newParamOrigin: defaultParam
          })
        }
        // 替换表达式中的目标字符串
        input = input.replace(matchStr, replaceStr)
      })
      this.diffVariable = input
      return input
    },

    extractValueByType (data, targetType = 'value') {
      const result = [] // 存储所有匹配的 value 值
      function traverse (node) {
        if (Array.isArray(node)) {
          node.forEach(traverse) // 遍历数组中的每个元素
        } else if (node && typeof node === 'object') {
          if (node.type === targetType && node.hasOwnProperty('value')) {
            result.push({
              name: node.name,
              value: node.value
            }) // 提取匹配的 value 值
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
    // 编辑入口
    async editAuth (row) {
      this.isAdd = false
      this.fullscreen = false
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
.flow-role-transfer-container {
  min-width: 700px;
  overflow-y: auto;
}
.header-icon {
  font-size: 16px;
  margin-right: 24px;
  margin-bottom: 4px;
}
</style>
