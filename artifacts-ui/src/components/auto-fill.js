import { getAllSystemEnumCodes, getCiTypeAttr, getEntitiesByCiType, getRefCiTypeFrom } from '@/api/server.js'
import './auto-fill.scss'

export default {
  name: 'AutoFill',
  props: {
    ciTypesObj: { default: () => {}, required: true },
    ciTypeAttrsObj: { default: () => {}, required: true },
    isReadOnly: { default: () => false, required: false },
    value: { default: () => '', required: true },
    rootCiTypeId: { type: String, required: true },
    specialDelimiters: { default: () => [], required: true },
    cmdbPackageName: { default: '', required: true }
  },
  data () {
    return {
      hoverSpan: '',
      hoverAttr: '',
      currentRule: '',
      currentAttr: '',
      activeDelimiterIndex: '',
      activeDelimiterValue: '',
      optionsDisplay: false,
      options: [],
      autoFillArray: [],
      modalDisplay: false,
      filterCiTypeId: 0,
      filters: [],
      filterCiAttrs: [],
      operatorList: [
        { code: 'in', value: 'In' },
        { code: 'contains', value: 'Contains' },
        { code: 'eq', value: 'Equal' },
        { code: 'gt', value: 'Greater' },
        { code: 'lt', value: 'Less' },
        { code: 'ne', value: 'NotEqual' },
        { code: 'notNull', value: 'NotNull' },
        { code: 'null', value: 'Null' }
      ],
      enumCodes: [],
      spinShow: false
    }
  },
  watch: {
    value () {
      this.initAutoFillArray()
    },
    ciTypesObj () {
      this.initAutoFillArray()
    },
    optionsDisplay (val) {
      if (!val) {
        this.currentRule = ''
        this.currentAttr = ''
        this.options = []
      }
    }
  },
  methods: {
    renderEditor () {
      return [
        !this.isReadOnly && this.renderOptions(),
        ...this.autoFillArray.map((_, i) => {
          switch (_.type) {
            case 'rule':
              return this.renderExpression(_.value, i)
            case 'delimiter':
              return this.renderDelimiter(_.value, i)
            case 'specialDelimiter':
              return this.renderSpecialDelimiter(_.value, i)
            default:
              break
          }
        }),
        ...this.renderAddRule(),
        this.renderCopyButton(),
        this.renderModal()
      ]
    },
    // 将过滤规则格式化为可读值
    formaFillRule (value, props) {
      let result = []
      value.forEach((_, i) => {
        switch (_.type) {
          case 'rule':
            result.push(...this.renderExpression(_.value, i, props))
            break
          case 'delimiter':
            result.push(this.renderSpan(_.value, props))
            break
          case 'specialDelimiter':
            const found = this.specialDelimiters.find(item => item.code === _.value)
            if (found) {
              result.push(this.renderSpan(found.value, props))
            } else {
              result.push(this.renderSpan(_.value, props))
            }
            break
          default:
            break
        }
      })
      return result
    },
    renderOptions () {
      return (
        <div slot="content" class="auto-fill-options">
          {[
            this.options.map(_ => {
              switch (_.type) {
                case 'option':
                  return (
                    <div class={_.class} onClick={_.fn}>
                      {_.nodeName}
                    </div>
                  )
                case 'line':
                  return <hr />
                default:
                  return <_.type class={_.class} ref={_.ref} attrs={_.attrs} on={_.on} />
              }
            }),
            this.spinShow ? <Spin fix /> : null
          ]}
        </div>
      )
    },
    mouseover (e) {
      if (e.target.className.indexOf('auto-fill-span') === -1) {
        return
      }
      this.hoverSpan = e.target.getAttribute('index')
      this.hoverAttr = e.target.getAttribute('attr-index')
    },
    mouseout (e) {
      this.hoverSpan = ''
      this.hoverAttr = ''
    },
    handleClick (e) {
      if (this.isReadOnly) {
        return
      }
      if (e.target.className.indexOf('auto-fill-span') >= 0) {
        const ruleIndex = e.target.getAttribute('index')
        if (e.target.className.indexOf('auto-fill-special-delimiter') >= 0) {
          this.showSpecialOptions(ruleIndex)
          return
        }
        let attrIndex = null
        if (e.target.hasAttribute('attr-index')) {
          attrIndex = e.target.getAttribute('attr-index')
        }
        this.showRuleOptions(ruleIndex, attrIndex)
      } else if (e.target.className.indexOf('auto-fill-add') >= 0) {
        // 选择属性表达式或连接符
        this.showAddOptions()
      } else {
      }
    },
    showAddOptions () {
      this.options = []
      this.optionsDisplay = true
      if (!this.autoFillArray.length) {
        this.options.push(
          {
            type: 'input',
            class: 'auto-fill-li auto-fill-paste-input',
            ref: 'pasteInput',
            attrs: {
              placeholder: this.$t('artifacts_please_paste_here')
            },
            on: {
              input: v => this.handlePasteInput(v),
              paste: v => this.pastePathExp(v)
            }
          },
          {
            type: 'line'
          }
        )
      }
      this.options.push(
        {
          type: 'option',
          class: 'auto-fill-li',
          nodeName: this.$t('artifacts_auto_fill_add_rule'),
          fn: () => this.addRule('rule')
        },
        {
          type: 'option',
          class: 'auto-fill-li',
          nodeName: this.$t('artifacts_auto_fill_add_delimiter'),
          fn: () => this.addRule('delimiter')
        },
        {
          type: 'option',
          class: 'auto-fill-li',
          nodeName: this.$t('artifacts_auto_fill_special_delimiter'),
          fn: () => this.addRule('specialDelimiter')
        }
      )
    },
    addRule (type) {
      this.options = []
      switch (type) {
        case 'rule':
          this.autoFillArray.push({
            type,
            value: JSON.stringify([{ ciTypeId: this.rootCiTypeId }])
          })
          this.showRuleOptions(this.autoFillArray.length - 1 + '', '0')
          break
        case 'delimiter':
          this.autoFillArray.push({
            type,
            value: ''
          })
          this.activeDelimiterIndex = this.autoFillArray.length - 1 + ''
          this.optionsDisplay = false
          break
        case 'specialDelimiter':
          this.getSpecialConnector()
          break
        default:
          break
      }
    },
    // 特殊连接符
    getSpecialConnector () {
      this.specialDelimiters.forEach(_ => {
        this.options.push({
          type: 'option',
          class: 'auto-fill-li auto-fill-li-special-delimiter',
          nodeName: _.value,
          fn: () => {
            this.autoFillArray.push({
              type: 'specialDelimiter',
              value: _.code
            })
            this.options = []
            this.optionsDisplay = false
            this.handleInput()
          }
        })
      })
    },
    showRuleOptions (ruleIndex, attrIndex) {
      this.options = []
      this.optionsDisplay = true
      const isAttrNode = attrIndex ? !!JSON.parse(this.autoFillArray[ruleIndex].value)[attrIndex].parentRs : false
      const attrInputType = isAttrNode ? this.ciTypeAttrsObj[JSON.parse(this.autoFillArray[ruleIndex].value)[attrIndex].parentRs.attrId].inputType : ''
      // 删除节点
      this.options.push({
        type: 'option',
        class: 'auto-fill-li auto-fill-li-delete',
        nodeName: this.$t('artifacts_auto_fill_delete_node'),
        fn: () => this.deleteNode(ruleIndex, attrIndex)
      })
      // 连接符
      if (!attrIndex) {
        this.options.push({
          type: 'option',
          class: 'auto-fill-li auto-fill-li-edit',
          nodeName: this.$t('artifacts_auto_fill_edit_delimiter'),
          fn: () => this.editDelimiter(ruleIndex, attrIndex)
        })
        return
      }
      // 添加过滤条件
      if (attrInputType === 'ref' || attrInputType === 'multiRef' || !attrInputType) {
        this.options.push({
          type: 'option',
          class: 'auto-fill-li auto-fill-li-filter',
          nodeName: this.$t('artifacts_auto_fill_add_filter'),
          fn: () => this.showFilterModal(ruleIndex, attrIndex)
        })
      }

      const node = JSON.parse(this.autoFillArray[ruleIndex].value)[attrIndex]
      if (!node.parentRs || this.ciTypeAttrsObj[node.parentRs.attrId].inputType === 'ref' || this.ciTypeAttrsObj[node.parentRs.attrId].inputType === 'multiRef') {
        const ciTypeId = JSON.parse(this.autoFillArray[ruleIndex].value)[attrIndex].ciTypeId
        this.getRefData(ruleIndex, attrIndex, ciTypeId)
      } else if ((node.parentRs && this.ciTypeAttrsObj[node.parentRs.attrId].inputType === 'select') || this.ciTypeAttrsObj[node.parentRs.attrId].inputType === 'multiSelect') {
        this.showEnumOptions(ruleIndex, attrIndex)
      }
      this.handleInput()
    },
    showSpecialOptions (ruleIndex) {
      this.options = [
        {
          type: 'option',
          class: 'auto-fill-li auto-fill-li-delete',
          nodeName: this.$t('artifacts_auto_fill_delete_node'),
          fn: () => this.deleteNode(ruleIndex)
        },
        {
          type: 'option',
          class: 'auto-fill-li auto-fill-li-change-special-delimiter',
          nodeName: this.$t('artifacts_auto_fill_change_special_delimiter'),
          fn: () => this.changeSpecialDelimiterNode(ruleIndex)
        }
      ]
      this.optionsDisplay = true
    },
    async getRefData (ruleIndex, attrIndex, ciTypeId) {
      this.spinShow = true
      this.currentRule = ruleIndex
      this.currentAttr = attrIndex
      const promiseArray = [getRefCiTypeFrom(ciTypeId), getCiTypeAttr(ciTypeId)]
      const [refFroms, ciAttrs] = await Promise.all(promiseArray)
      this.spinShow = false
      if (refFroms.status === 'OK' && ciAttrs.status === 'OK') {
        // 下拉框添加被引用的CI的选项
        refFroms.data.length &&
          this.options.push({
            type: 'line'
          })
        this.options = this.options.concat(
          refFroms.data.map(_ => {
            const ciTypeName = this.ciTypesObj[_.ciTypeId] ? this.ciTypesObj[_.ciTypeId].name : 'undefined'
            const attrName = this.ciTypeAttrsObj[_.ciTypeAttrId] ? this.ciTypeAttrsObj[_.ciTypeAttrId].name : 'undefined'
            const nodeObj = {
              ciTypeId: _.ciTypeId,
              parentRs: {
                attrId: _.ciTypeAttrId,
                isReferedFromParent: 0
              }
            }
            return {
              type: 'option',
              class: 'auto-fill-li auto-fill-li-ref auto-fill-li-ref-from',
              nodeName: `<-(${attrName})${ciTypeName}`,
              fn: () => this.addNode(ruleIndex, attrIndex, nodeObj)
            }
          })
        )
        // 下拉框添加属性及引用的CI的选项
        ciAttrs.data.length &&
          this.options.push({
            type: 'line'
          })
        this.options = this.options.concat(
          ciAttrs.data.map(_ => {
            const isRef = _.inputType === 'ref' || _.inputType === 'multiRef'
            const ciTypeName = isRef ? this.ciTypesObj[_.referenceId].name : this.ciTypesObj[_.ciTypeId].name
            const attrName = this.ciTypeAttrsObj[_.ciTypeAttrId].name
            const nodeName = isRef ? `->(${attrName})${ciTypeName}` : `.${attrName}`
            const nodeObj = {
              ciTypeId: isRef ? _.referenceId : _.ciTypeId,
              parentRs: {
                attrId: _.ciTypeAttrId,
                isReferedFromParent: 1
              }
            }
            return {
              type: 'option',
              class: 'auto-fill-li auto-fill-li-ref auto-fill-li-ref-to',
              nodeName,
              fn: () => this.addNode(ruleIndex, attrIndex, nodeObj)
            }
          })
        )
      }
    },
    // 显示枚举属性下拉框
    showEnumOptions (ruleIndex, attrIndex) {
      this.currentRule = ruleIndex
      this.currentAttr = attrIndex
      this.options.push({
        type: 'line'
      })
      this.options = this.options.concat(
        this.enumCodes.map(_ => {
          return {
            type: 'option',
            class: 'auto-fill-li auto-fill-li-enum',
            nodeName: _,
            fn: () => this.addEnum(ruleIndex, attrIndex, _)
          }
        })
      )
    },
    // 点击选择枚举属性
    addEnum (ruleIndex, attrIndex, code) {
      let ruleArr = JSON.parse(this.autoFillArray[ruleIndex].value)
      ruleArr[attrIndex].enumCodeAttr = code
      this.autoFillArray[ruleIndex].value = JSON.stringify(ruleArr)
      this.optionsDisplay = false
      this.handleInput()
    },
    // 点击删除节点
    deleteNode (ruleIndex, attrIndex) {
      if (!attrIndex) {
        // 删除连接符
        this.autoFillArray.splice(ruleIndex, 1)
        this.handleInput()
      } else {
        if (attrIndex === '0') {
          // 删除该属性表达式（即该花括号内的内容）
          this.autoFillArray.splice(ruleIndex, 1)
          if (ruleIndex !== '0' && this.autoFillArray[+ruleIndex - 1].type === 'delimiter' && this.autoFillArray[ruleIndex] && this.autoFillArray[ruleIndex].type === 'delimiter') {
            this.autoFillArray[+ruleIndex - 1].value += this.autoFillArray[ruleIndex].value
            this.autoFillArray.splice(ruleIndex, 1)
          }
          this.handleInput()
        } else {
          // 删除属性表达式中，该节点及之后的节点
          let ruleArr = JSON.parse(this.autoFillArray[ruleIndex].value)
          ruleArr.splice(attrIndex, ruleArr.length - attrIndex)
          this.autoFillArray[ruleIndex].value = JSON.stringify(ruleArr)
          // this.$emit('input', null)
          this.$emit('input', JSON.stringify(this.autoFillArray))
        }
      }
      this.optionsDisplay = false
    },
    // 点击更换特殊连接符节点
    changeSpecialDelimiterNode (ruleIndex) {
      this.options = []
      this.specialDelimiters.forEach(_ => {
        this.options.push({
          type: 'option',
          class: 'auto-fill-li auto-fill-li-special-delimiter',
          nodeName: _.value,
          fn: () => {
            this.autoFillArray.splice(+ruleIndex, 1, {
              type: 'specialDelimiter',
              value: _.code
            })
            this.options = []
            this.optionsDisplay = false
            this.handleInput()
          }
        })
      })
    },
    editDelimiter (ruleIndex) {
      this.activeDelimiterIndex = ruleIndex
      this.optionsDisplay = false
      this.handleInput()
    },
    async showFilterModal (ruleIndex, attrIndex) {
      this.filterCiTypeId = JSON.parse(this.autoFillArray[ruleIndex].value)[attrIndex].ciTypeId
      const filters = JSON.parse(this.autoFillArray[ruleIndex].value)[attrIndex].filters || []
      this.filterIndex = [ruleIndex, attrIndex]
      this.modalDisplay = true
      this.optionsDisplay = false
      const { data, status } = await getCiTypeAttr(this.filterCiTypeId)
      if (status === 'OK') {
        this.filterCiAttrs = data
        let promiseArray = []
        this.filters = filters.map((_, i) => {
          const found = data.find(attr => attr.propertyName === _.name)
          if (found) {
            _.inputType = found.inputType
          }
          _.options = []
          if (['ref', 'multiRef'].indexOf(_.inputType) >= 0) {
            const entityName = this.ciTypesObj[found.referenceId].ciTypeId
            promiseArray.push(getEntitiesByCiType(this.cmdbPackageName, entityName, {}))
          } else if (['select', 'multiSelect'].indexOf(_.inputType) >= 0) {
            promiseArray.push(getAllSystemEnumCodes(found.selectList))
          } else {
            promiseArray.push({ data: [] })
          }
          if (_.operator === 'in' && _.type === 'value') {
            if (['ref', 'select', 'multiRef', 'multiSelect'].indexOf(_.inputType) === -1) {
              _.value = _.value.join(',')
            }
          }
          return _
        })
        const res = await Promise.all(promiseArray)
        res.forEach((_, i) => {
          if (['ref', 'multiRef'].indexOf(this.filters[i].inputType) >= 0) {
            this.filters[i].options = _.data.map(item => {
              return {
                label: item.displayName,
                id: item.guid
              }
            })
          } else if (['select', 'multiSelect'].indexOf(this.filters[i].inputType) >= 0) {
            this.filters[i].options = _.data.map(item => {
              return {
                label: item.value,
                id: item.code
              }
            })
          }
        })
      }
    },
    async getOptions (propertyName) {
      const { status, data } = await getEntitiesByCiType(this.cmdbPackageName, propertyName, {})
      if (status === 'OK') {
        return data
      } else {
        return []
      }
    },
    addNode (ruleIndex, attrIndex, nodeObj) {
      const i = +attrIndex
      let ruleArr = JSON.parse(this.autoFillArray[ruleIndex].value)
      ruleArr.splice(i + 1, ruleArr.length - i - 1, nodeObj)
      this.autoFillArray[ruleIndex].value = JSON.stringify(ruleArr)
      const inputType = this.ciTypeAttrsObj[ruleArr[ruleArr.length - 1].parentRs.attrId].inputType
      const ciTypeId = nodeObj.ciTypeId
      if (inputType === 'ref' || inputType === 'multiRef') {
        this.options = [
          {
            type: 'option',
            class: 'auto-fill-li auto-fill-li-delete',
            nodeName: this.$t('artifacts_auto_fill_delete_node'),
            fn: () => this.deleteNode(ruleIndex, i + 1)
          },
          {
            type: 'option',
            class: 'auto-fill-li auto-fill-li-filter',
            nodeName: this.$t('artifacts_auto_fill_add_filter'),
            fn: () => this.showFilterModal(ruleIndex, i + 1)
          }
        ]
        this.getRefData(ruleIndex, i + 1 + '', ciTypeId)
      } else if (inputType === 'select' || inputType === 'multiSelect') {
        this.options = [
          {
            type: 'option',
            class: 'auto-fill-li auto-fill-li-delete',
            nodeName: this.$t('artifacts_auto_fill_delete_node'),
            fn: () => this.deleteNode(ruleIndex, i + 1)
          },
          {
            type: 'option',
            class: 'auto-fill-li auto-fill-li-filter',
            nodeName: this.$t('artifacts_auto_fill_add_filter'),
            fn: () => this.showFilterModal(ruleIndex, i + 1)
          }
        ]
        this.showEnumOptions(ruleIndex, i + 1 + '')
        this.optionsDisplay = false
      } else {
        this.optionsDisplay = false
      }
      this.handleInput()
    },
    renderSpan (value, props) {
      return <span {...props}>{value}</span>
    },
    formatClassName (classList) {
      return Object.keys(classList).map(key => {
        if (classList[key]) {
          return key
        }
      })
    },
    renderExpression (val, i, props) {
      // type === rule 时，链式属性表达式
      let result = []
      JSON.parse(val).forEach((_, attrIndex) => {
        let isLegal = true
        if (attrIndex === JSON.parse(val).length - 1) {
          const lastInputType = JSON.parse(val)[attrIndex].parentRs ? this.ciTypeAttrsObj[JSON.parse(val)[attrIndex].parentRs.attrId].inputType : ''
          if (lastInputType === 'ref' || lastInputType === 'multiRef' || !lastInputType) {
            isLegal = false
          } else if (lastInputType === 'select' || lastInputType === 'multiSelect') {
            isLegal = !!JSON.parse(val)[attrIndex].enumCodeAttr
          }
        }
        // 样式
        const classList = {
          'auto-fill-span': true,
          'auto-fill-hover': this.hoverAttr === attrIndex + '' && this.hoverSpan === i + '',
          'auto-fill-current-node': this.currentRule === i + '' && this.currentAttr === attrIndex + '',
          'auto-fill-error': !isLegal
        }
        const defaultProps = {
          class: this.formatClassName(classList),
          attrs: {
            index: i,
            'attr-index': attrIndex
          }
        }
        const _props = props || defaultProps
        const _propsWithkeyWord = {
          ..._props,
          class: [..._props.class, 'auto-fill-key-word']
        }
        // 过滤条件
        let filterNode = []
        if (_.filters) {
          const attrs = this.ciTypesObj[_.ciTypeId] ? this.ciTypesObj[_.ciTypeId].attributes : []
          filterNode = [
            <span {..._propsWithkeyWord}>{' [ '}</span>,
            ..._.filters.map((filter, filterIndex) => {
              let filterValue = []
              const operatorFound = this.operatorList.find(operator => operator.code === filter.operator)
              const operator = operatorFound ? operatorFound.value : filter.operator
              const attrFound = attrs.find(attr => attr.propertyName === filter.name)
              const filterName = attrFound ? attrFound.name : filter.name
              if (filter.type && filter.type === 'autoFill') {
                let filterInfo = Array.isArray(filter.value) ? filter.value : JSON.parse(filter.value)
                filterValue = this.formaFillRule(filterInfo, defaultProps)
              } else {
                const _filterValue = Array.isArray(filter.value) ? `[${filter.value.join(',')}]` : filter.value
                filterValue = [this.renderSpan(_filterValue, _props)]
              }
              return [filterIndex > 0 && <span {..._propsWithkeyWord}> | </span>, this.renderSpan(filterName, _props), this.renderSpan(` ${operator} `, _propsWithkeyWord), ...filterValue]
            }),
            <span {..._propsWithkeyWord}>{' ] '}</span>
          ]
        }
        const ciTypeName = this.ciTypesObj[_.ciTypeId].name
        if (!_.parentRs) {
          result.push(this.renderSpan(ciTypeName, _props), ...filterNode)
        } else {
          const inputType = this.ciTypeAttrsObj[_.parentRs.attrId].inputType
          const ref = _.parentRs.isReferedFromParent === 1 ? (inputType === 'ref' || inputType === 'multiRef' ? '->' : '.') : '<-'
          const attrName = this.ciTypeAttrsObj[_.parentRs.attrId].name
          const enumCode = _.enumCodeAttr ? `.${_.enumCodeAttr}` : ''
          if (this.ciTypeAttrsObj[_.parentRs.attrId].inputType === 'ref' || this.ciTypeAttrsObj[_.parentRs.attrId].inputType === 'multiRef') {
            result.push(this.renderSpan(` ${ref}(${attrName})${ciTypeName}`, _props), ...filterNode)
          } else {
            result.push(this.renderSpan(` ${ref}${attrName}${enumCode}`, _props), ...filterNode)
          }
        }
      })
      const bracesClassList = {
        'auto-fill-span': true,
        'auto-fill-key-word': true,
        contains: this.hoverSpan === i + ''
      }
      const propsWithBraces = props
        ? {
            ...props,
            class: [...props.class, 'auto-fill-key-word']
          }
        : {
            class: this.formatClassName(bracesClassList),
            attrs: {
              index: i
            }
          }
      return [<span {...propsWithBraces}>{' { '}</span>, ...result, <span {...propsWithBraces}>{' } '}</span>]
    },
    renderDelimiter (val, i) {
      // type === delimiter 时，连接符
      if (this.activeDelimiterIndex === i + '') {
        return <Input ref="delimiterInput" on-on-blur={() => this.confirmDelimiter(i)} on-on-enter={() => this.$refs.delimiterInput.blur()} onInput={v => this.onDelimiterInput(v, i)} value={val} />
      } else {
        const classList = {
          'auto-fill-span': true,
          hover: this.hoverSpan === i + ''
        }
        const _props = {
          class: this.formatClassName(classList),
          attrs: {
            index: i
          }
        }
        return this.renderSpan(val, _props)
      }
    },
    renderSpecialDelimiter (value, i) {
      const found = this.specialDelimiters.find(item => item.code === value)
      const specialDelimiter = found ? found.value : ''
      const classList = {
        'auto-fill-span': true,
        'auto-fill-special-delimiter': true,
        hover: this.hoverSpan === i + ''
      }
      const _props = {
        class: this.formatClassName(classList),
        attrs: {
          index: i
        }
      }
      return this.renderSpan(specialDelimiter, _props)
    },
    // 连接符输入框失焦或按回车时，需要更新 this.autoFillArray
    confirmDelimiter (i) {
      if (this.autoFillArray[i].value === '') {
        // 如果输入框没有值，则在 this.autoFillArray 中删掉该项
        this.autoFillArray.splice(i, 1)
      } else {
        // 将相邻两项 type === delimiter 合并为一项
        if (this.autoFillArray[i + 1] && this.autoFillArray[i + 1].type === 'delimiter') {
          this.autoFillArray[i].value += this.autoFillArray[i + 1].value
          this.autoFillArray.splice(i + 1, 1)
        }
        if (i > 0 && this.autoFillArray[i - 1].type === 'delimiter') {
          this.autoFillArray[i - 1].value += this.autoFillArray[i].value
          this.autoFillArray.splice(i, 1)
        }
      }
      this.activeDelimiterIndex = ''
      this.handleInput()
    },
    onDelimiterInput (v, i) {
      this.autoFillArray[i].value = v
    },
    renderAddRule () {
      if (this.isReadOnly) {
        return []
      } else {
        return [<Icon class="auto-fill-add" type="md-add-circle" />, !this.autoFillArray.length && <span class="auto-fill-add auto-fill-placeholder">{this.$t('artifacts_auto_fill_filter_placeholder')}</span>]
      }
    },
    initAutoFillArray () {
      if (!Object.keys(this.ciTypesObj).length || !this.value) {
        this.autoFillArray = []
        return
      }
      this.autoFillArray = JSON.parse(this.value)
    },
    renderCopyButton () {
      return (
        <Button disabled={!this.value} size="small" type="dashed" icon="md-copy" style={`margin-left:10px;display:${this.autoFillArray.length ? 'inline-block' : 'none'}`} onClick={this.copy}>
          {this.$t('artifacts_copy')}
        </Button>
      )
    },
    focusInput () {
      // 点击编辑连接符后，需要聚焦 Input
      if (this.activeDelimiterIndex && this.$refs.delimiterInput) {
        this.$nextTick(() => {
          this.$refs.delimiterInput.focus()
        })
      } else if (this.$refs.pasteInput) {
        this.$nextTick(() => {
          this.$refs.pasteInput.focus()
        })
      }
    },
    // 添加过滤添加的弹框
    renderModal () {
      const emptyFilter = {
        name: '',
        inputType: 'text',
        operator: 'in',
        type: 'value',
        value: ''
      }
      return (
        <Modal value={this.modalDisplay} onInput={v => (this.modalDisplay = v)} title={this.$t('artifacts_auto_fill_filter_modal_title')} width="800" on-on-ok={this.confirmFilter} on-on-cancel={this.cancelFilter}>
          {this.filters.map((_, i) => (
            <div class="auto-fill-filter-li">
              <Icon type="md-remove-circle" color="red" onClick={() => this.filters.splice(i, 1)} class="auto-fill-filter-li-icon" />
              <Select value={_.name} filterable onInput={v => this.changeAttr(v, i)} class="auto-fill-filter-li-select title">
                {this.filterCiAttrs.map(attr => (
                  <Option key={attr.ciTypeAttrId} value={attr.propertyName}>
                    {attr.name}
                  </Option>
                ))}
              </Select>
              <Select value={_.operator} onInput={v => this.changeOperator(v, i)} class="auto-fill-filter-li-select operator">
                {this.operatorList.map(o => (
                  <Option key={o.code} value={o.code}>
                    {o.value}
                  </Option>
                ))}
              </Select>
              <Select
                value={_.type}
                filterable
                onInput={v => {
                  this.filters[i].value = ''
                  this.filters[i].type = v
                }}
                class="auto-fill-filter-li-select type"
              >
                <Option key="value" value="value">
                  {this.$t('artifacts_value')}
                </Option>
                <Option key="autoFill" value="autoFill">
                  {this.$t('artifacts_auto_fill_rule')}
                </Option>
              </Select>
              {this.renderInput(_, i)}
            </div>
          ))}
          <Button type="primary" long onClick={() => this.filters.push(emptyFilter)}>
            {this.$t('artifacts_auto_fill_filter_modal_button')}
          </Button>
        </Modal>
      )
    },
    renderInput (item, index) {
      const { rootCiTypeId, ciTypesObj, ciTypeAttrsObj, specialDelimiters, cmdbPackageName } = this
      if (item.type === 'value') {
        if (['ref', 'select', 'multiRef', 'multiSelect'].indexOf(item.inputType) >= 0) {
          return (
            <Select
              class="auto-fill-filter-li-input"
              multiple={item.operator === 'in'}
              value={item.value}
              filterable
              onInput={v => {
                this.filters[index].value = v
              }}
            >
              {item.options.map(_ => (
                <Option key={_.id} value={_.id}>
                  {_.label}
                </Option>
              ))}
            </Select>
          )
        } else {
          return <Input class="auto-fill-filter-li-input" onInput={v => (this.filters[index].value = v)} value={item.value} type="textarea" autosize={true} />
        }
      } else {
        return <AutoFill class="auto-fill-filter-li-input" ciTypesObj={ciTypesObj} ciTypeAttrsObj={ciTypeAttrsObj} isReadOnly={false} onInput={v => (this.filters[index].value = v)} rootCiTypeId={rootCiTypeId} specialDelimiters={specialDelimiters} value={item.value} cmdbPackageName={cmdbPackageName} />
      }
    },
    async changeAttr (val, i) {
      this.filters[i].name = val
      const found = this.filterCiAttrs.find(_ => _.propertyName === val)
      const inputType = found.inputType
      switch (inputType) {
        case 'ref':
        case 'multiRef':
          const entityName = this.ciTypesObj[found.referenceId].ciTypeId
          const { status, data } = await getEntitiesByCiType(this.cmdbPackageName, entityName, {})
          if (status === 'OK') {
            this.filters[i].options = data.map(_ => {
              return {
                label: _.displayName,
                id: _.guid
              }
            })
          }
          break
        case 'select':
        case 'multiSelect':
          const params = found.selectList
          const res = await getAllSystemEnumCodes(params)
          if (res.status === 'OK') {
            this.filters[i].options = res.data.map(_ => {
              return {
                label: _.value,
                id: _.code
              }
            })
          }
          break
        default:
          break
      }
      this.filters[i].inputType = inputType
      this.resetFilterValue(found.operator, i)
    },
    changeOperator (v, i) {
      this.filters[i].operator = v
      this.resetFilterValue(v, i)
    },
    resetFilterValue (operator, i) {
      if (operator === 'in') {
        this.filters[i].value = []
      } else {
        this.filters[i].value = ''
      }
    },
    confirmFilter () {
      const filters = this.filters
        .filter(_ => _.name && _.operator)
        .map(_ => {
          if (_.type === 'value') {
            if (_.operator === 'in' && !Array.isArray(_.value)) {
              _.value = _.value.split(',')
            }
            if (_.inputType === 'number') {
              if (Array.isArray(_.value)) {
                _.value = _.value.map(v => Number(v) || 0)
              } else {
                _.value = Number(_.value) || 0
              }
            }
          }
          return {
            name: _.name,
            operator: _.operator,
            type: _.type,
            value: _.value
          }
        })
      let value = JSON.parse(this.autoFillArray[this.filterIndex[0]].value)
      if (filters.length) {
        value[this.filterIndex[1]].filters = filters
      } else {
        delete value[this.filterIndex[1]].filters
      }
      this.autoFillArray[this.filterIndex[0]].value = JSON.stringify(value)
      this.cancelFilter()
      this.handleInput()
    },
    cancelFilter () {
      this.filterCiTypeId = 0
      this.filters = []
      this.filterCiAttrs = []
      this.filterIndex = []
    },
    handleInput () {
      const value = this.autoFillArray.length ? JSON.stringify(this.autoFillArray) : ''
      let isLegal = true
      this.autoFillArray.forEach(_ => {
        if (_.type === 'rule') {
          const ruleArray = JSON.parse(_.value)
          const lastNode = ruleArray[ruleArray.length - 1]
          const lastAttrId = lastNode.parentRs ? lastNode.parentRs.attrId : 0
          if (!lastAttrId) {
            isLegal = false
          }
          const inputType = lastAttrId ? this.ciTypeAttrsObj[lastAttrId].inputType : ''
          if (lastNode.parentRs) {
            if (inputType === 'ref' || inputType === 'multiRef') {
              isLegal = false
            } else if (inputType === 'select' || inputType === 'multiSelect') {
              if (!lastNode.enumCodeAttr) {
                isLegal = false
              }
            }
          }
        }
      })
      if (isLegal) {
        this.$emit('input', value)
      } else {
        this.$emit('input', JSON.stringify(this.autoFillArray))
      }
    },
    copy () {
      setTimeout(() => {
        const element = document.querySelector('.content-pop')
        if (element) {
          element.style.display = 'none'
        }
      }, 20)
      let inputElement = document.createElement('input')
      inputElement.value = this.value
      document.body.appendChild(inputElement)
      inputElement.select()
      document.execCommand('copy')
      inputElement.remove()
      this.$Notice.success({
        title: 'Success',
        desc: this.$t('artifacts_copy_success')
      })
    },
    handlePasteInput () {
      this.$refs.pasteInput.value = ''
    },
    pastePathExp (e) {
      let clipboardData = e.clipboardData
      if (!clipboardData) {
        clipboardData = e.originalEvent.clipboardData
      }
      let val = clipboardData.getData('Text')
      if (this.legalityCheck(val)) {
        this.$emit('input', val)
        this.$Notice.success({
          title: 'Success',
          desc: this.$t('artifacts_paste_success')
        })
        this.optionsDisplay = false
      }
    },
    legalityCheck (str) {
      try {
        let result = true
        const arr = JSON.parse(str)
        arr.forEach((_, i) => {
          if (_.type === 'rule' || _.type === 'autoFill') {
            if (!Array.isArray(_.value) && !this.legalityCheck(_.value)) {
              result = false
            }
          }
          if (i === 0 && _.filters) {
            _.filters.forEach(item => {
              if (!Array.isArray(item.value) && !this.legalityCheck(item.value)) {
                result = false
              }
            })
          }
          if (_.parentRs && !this.ciTypeAttrsObj[_.parentRs.attrId]) {
            this.$Notice.error({
              title: 'Error',
              desc: this.$t('artifacts_attr_id_is_not_exist') + _.parentRs.attrId
            })
            result = false
          } else if (_.ciTypeId && !this.ciTypesObj[_.ciTypeId]) {
            this.$Notice.error({
              title: 'Error',
              desc: this.$t('artifacts_citype_id_is_not_exist') + _.ciTypeId
            })
            result = false
          }
        })
        return result
      } catch {
        this.$Notice.error({
          title: 'Error',
          desc: this.$t('artifacts_parse_error') + str
        })
        return false
      }
    }
  },
  mounted () {
    this.initAutoFillArray()
  },
  updated () {
    this.focusInput()
  },
  render (h) {
    return (
      <div class="auto-fill" onmouseover={this.mouseover} onmouseout={this.mouseout} onClick={this.handleClick}>
        {this.isReadOnly ? (
          // 只读状态
          this.renderEditor()
        ) : (
          // 可编辑状态
          <Poptip popper-class="content-pop" v-model={this.optionsDisplay}>
            {this.renderEditor()}
          </Poptip>
        )}
      </div>
    )
  }
}
