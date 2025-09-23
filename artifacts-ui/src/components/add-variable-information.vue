<template>
  <div>
    <!-- 在线上传 -->
    <Modal v-model="isVariableModalShow" :closable="false" width="900">
      <div slot="header" class="custom-modal-header">
        {{ $t('art_variable_confrim_modal_title') }}
      </div>
      <Collapse v-model="activeCollapseName">
        <Panel v-for="(item, index) in allAddVariableDetails" :key="index" :name="index + ''">
          {{ item.variable_name }}
          <template slot="content">
            <Form :label-width="120">
              <FormItem :label="$t('art_value_rule') + ':'">
                <div style="color:gray">
                  <ArtifactsAutoFill v-if="item.variable_value" :ciTypesObj="ciTypesObj" :ciTypeAttrsObj="ciTypeAttrsObj" :specialDelimiters="specialDelimiters" rootCiTypeId="" :isReadOnly="true" v-model="item.variable_value" cmdbPackageName="wecmdb" />
                  <span v-else>--</span>
                </div>
              </FormItem>
              <FormItem v-for="input in item.customInputs" :key="input.key" style="margin-bottom: 0;">
                <div slot="label" style="width: 120px;padding-right:8px;word-break: break-all;">
                  <span style="color: red;">*</span>
                  {{ input.key }}
                </div>
                <Input type="text" v-model="input.value" />
              </FormItem>
            </Form>
          </template>
        </Panel>
      </Collapse>
      <div slot="footer">
        <!-- <Button @click="isVariableModalShow = false">{{ $t('artifacts_cancel') }}</Button> -->
        <Button type="primary" @click="onVariableInfoConfirm">{{ $t('art_confirm') }}</Button>
      </div>
    </Modal>

    <Modal v-model="isFinalVariableValueModalShow" :title="$t('art_final_variable_value')" width="1000">
      <div style="height: 400px;overflow: auto;">
        <Form :label-width="250">
          <FormItem v-for="item in allAddVariableDetails" :key="item.guid" :label="item.variable_name">
            <ArtifactsAutoFill :ciTypesObj="ciTypesObj" :ciTypeAttrsObj="ciTypeAttrsObj" :specialDelimiters="specialDelimiters" rootCiTypeId="" :isReadOnly="true" v-model="item.finalValue" cmdbPackageName="wecmdb" />
          </FormItem>
        </Form>
      </div>
      <div slot="footer">
        <Button @click="isFinalVariableValueModalShow = false">{{ $t('artifacts_cancel') }}</Button>
        <Button type="primary" @click="onUpdateVariableClick">{{ $t('art_update_variable_value') }}</Button>
      </div>
    </Modal>
  </div>
</template>

<script>
// eslint-disable-next-line no-unused-vars
import { isEmpty } from 'lodash'
import Vue from 'vue'
import { getAllCITypesWithAttr, getSpecialConnector, updateEntity } from '@/api/server.js'
export default {
  name: '',
  data () {
    return {
      isVariableModalShow: false,
      allAddVariableDetails: [],
      customInputs: [],
      activeCollapseName: '0',
      ciTypesObj: {},
      ciTypeAttrsObj: {},
      specialDelimiters: [],
      ciTypes: [],
      isFinalVariableValueModalShow: false
    }
  },
  watch: {
    allAddVariableInfo: {
      handler (val) {
        if (!isEmpty(val)) {
          this.allAddVariableDetails = val
          this.handleVariableInfo()
          if (this.allAddVariableDetails.every(item => item.variable_value)) {
            this.isVariableModalShow = true
          } else {
            this.isVariableModalShow = false
          }
        }
      },
      immediate: true,
      deep: true
    }
  },
  props: ['allAddVariableInfo'],
  mounted () {
    this.getAllCITypesWithAttr()
    this.getSpecialConnector()
  },
  methods: {
    handleVariableInfo () {
      this.allAddVariableDetails.forEach(info => {
        info.customInputs = []
        const value = info.variable_value
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
          info.customInputs = temps
        }
      })
    },
    async getAllCITypesWithAttr () {
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
      }
    },
    async getSpecialConnector () {
      const res = await getSpecialConnector()
      if (res.status === 'OK') {
        this.specialDelimiters = res.data
      }
    },
    onVariableInfoConfirm () {
      let isValid = true
      this.allAddVariableDetails.forEach(item => {
        if (!isEmpty(item.customInputs)) {
          item.customInputs.forEach(customInput => {
            if (isEmpty(customInput.value)) {
              isValid = false
            }
          })
        }
      })
      if (!isValid) {
        this.$Message.error(this.$t('art_required_variable_tips'))
        return
      }
      this.allAddVariableDetails.forEach(item => {
        item.finalValue = item.variable_value
        let resultStr = item.finalValue.replaceAll(/!&(\w)*!&/g, item.variable_name)
        if (!isEmpty(item.customInputs)) {
          item.customInputs.forEach(customInput => {
            resultStr = resultStr.replaceAll(customInput.origin, customInput.value)
          })
        }
        item.finalValue = resultStr
      })
      this.isFinalVariableValueModalShow = true
    },
    async onUpdateVariableClick () {
      const params = this.allAddVariableDetails.map(item => {
        return {
          id: item.guid,
          variable_value: item.finalValue
        }
      })
      const { status } = await updateEntity('wecmdb', 'diff_configuration', params)
      if (status === 'OK') {
        this.isVariableModalShow = false
        this.isFinalVariableValueModalShow = false
        this.$emit('closeInformationModal')
      }
    }
  }
}
</script>

<style scoped lang="scss">
.custom-modal-header {
  line-height: 20px;
  font-size: 16px;
  color: #17233d;
  font-weight: 500;
  .fullscreen-icon {
    float: right;
    margin-right: 28px;
    font-size: 18px;
    cursor: pointer;
  }
}
</style>
