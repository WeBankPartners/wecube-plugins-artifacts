<template>
  <div class="attr_input">
    <Poptip v-if="!isReadOnly" v-model="optionsHide" placement="bottom">
      <div class="input_in">
        <textarea
          ref="textarea"
          :rows="2"
          @input="inputHandler"
          :value="inputVal"
        ></textarea>
      </div>
      <div slot="content">
        <div class="attr-ul">
          <ul v-for="opt in allCi" :key="opt.ciTypeId">
            <li @click="selectCiType(opt)">{{ opt.name }}</li>
          </ul>
          <ul v-for="opt in attrNameArray" :key="opt.attrId">
            <li @click="selectAttr(opt)">
              {{
                (opt.inputType === "ref" || opt.inputType === "multiRef")
                  ? `( ${opt.ciTypeAttrName} ) ${opt.ciTypeName}`
                  : opt.ciTypeAttrName
              }}
            </li>
          </ul>
          <ul v-if="isShowSelect" v-for="item in enumCodes" :key="item">
            <li @click="selectEnumCode(item)">{{ item }}</li>
          </ul>
        </div>
      </div>
    </Poptip>
    <span v-else>{{inputVal}}</span>
  </div>
</template>

<script>
import { getRefCiTypeFrom, getCiTypeAttr } from "@/api/server.js";
export default {
  data() {
    return {
      optionsHide: false,
      options: [],
      inputVal: "",
      optests: [],
      routine: [],
      allCi: [],
      attrNameArray: [],
      isShowSelect: false,
      enumCodes: ["id", "code", "value", "groupCodeId"],
      attrInputArray: [],
      inputRuleStatus: 1 // 0 - 花括号内 ; 1 - 花括号外
    };
  },
  props: {
    allCiTypes: {
      required: true,
      default: []
    },
    isReadOnly: {
      required: false,
      default: false
    },
    value: {
      required: true,
      default: ""
    },
    rootCiTypeId: {
      required: false
    }
  },
  computed: {
    ciTypesObj() {
      let obj = {};
      this.allCiTypes.forEach(_ => {
        obj[_.ciTypeId] = _;
      });
      return obj;
    },
    ciTypeAttrsObj() {
      let obj = {};
      this.allCiTypes.forEach(ciType => {
        ciType.attributes.forEach(attr => {
          obj[attr.ciTypeAttrId] = attr;
        });
      });
      return obj;
    },
    attrInputLastObjValue() {
      return this.attrInputArray[this.attrInputArray.length - 1].value;
    }
  },
  watch: {
    optionsHide() {
      let doms = document.getElementsByClassName("attr-ul");
      for (let i = 0; i < doms.length; i++) {
        doms[i].style.width = this.$refs.textarea.clientWidth + "px";
      }
    },
    allCiTypes() {
      this.displayInputData();
    }
  },
  mounted() {
    this.initDisplayValue()
    this.displayInputData();
  },
  methods: {
    initDisplayValue() {
      if (this.$refs && this.$refs.textarea) {
        this.$refs.textarea.value = ""
      }
    },
    inputHandler(v) {
      if (this.inputRuleStatus === 1) {
        if (v.data === "{") {
          if (this.attrInputArray.length) {
            this.$Message.error({
              content: this.$t("attr_input_save_tips")
            })
            this.$refs.textarea.value = this.inputVal;
            return
          }
          if (this.rootCiTypeId) {
            this.inputVal =
              this.$refs.textarea.value +
              " " +
              this.ciTypesObj[this.rootCiTypeId].name +
              " ";
            const val = [
              {
                ciTypeId: this.rootCiTypeId
              }
            ];
            this.attrInputArray.push({
              type: "rule",
              value: JSON.stringify(val)
            });
          }
          this.inputRuleStatus = 0;
        } else if (v.inputType === "deleteContentBackward") {
          this.attrInputArray.splice(-2, 2);
          this.inputVal = this.inputVal.substr(
            0,
            this.inputVal.lastIndexOf("{")
          );
          if (this.inputVal) {
            this.$emit("updateValue", JSON.stringify(this.attrInputArray));
          } else {
            this.attrInputArray = [];
            this.$emit("updateValue", "");
          }
        } else {
          this.$refs.textarea.value = this.inputVal;
          if (this.attrInputArray.length) {
            this.$Message.error({
              content: this.$t("attr_input_save_tips")
            })
          } else {
            this.$Message.error({
              content: this.$t("attr_input_legitimate_character_tips")
            });
          }
        }
      } else {
        if (v.data) {
          if (!this.attrInputLastObjValue) {
            this.$refs.textarea.value = this.inputVal;
            this.$Message.error({
              content: this.$t("please_select_ci_type")
            });
          } else {
            const objList = JSON.parse(this.attrInputLastObjValue);
            const obj = objList[objList.length - 1];
            if (
              !obj.parentRs ||
              this.ciTypeAttrsObj[obj.parentRs.attrId].inputType === "ref" || this.ciTypeAttrsObj[obj.parentRs.attrId].inputType === "multiRef"
            ) {
              if (v.data === "." || v.data === "-") {
                if (
                  this.inputVal[this.inputVal.length - 1] === "." ||
                  this.inputVal[this.inputVal.length - 1] === "-"
                ) {
                  this.inputVal = this.inputVal.replace(/.$/, v.data);
                } else {
                  this.inputVal = this.$refs.textarea.value;
                }
                this.optionsHide = true;
                this.getNextRef(v.data);
              } else {
                this.$refs.textarea.value = this.inputVal;
                this.$Message.error({
                  content: this.$t(
                    "attr_input_legitimate_operation_character_tips"
                  )
                });
              }
            } else if (
              !obj.parentRs ||
              ((this.ciTypeAttrsObj[obj.parentRs.attrId].inputType === "select" || this.ciTypeAttrsObj[obj.parentRs.attrId].inputType === "multiSelect") &&
                !obj.enumCodeAttr)
            ) {
              this.$refs.textarea.value = this.inputVal;
              this.$Message.error({
                content: this.$t("please_select_enum")
              });
            } else {
              if (v.data === "}") {
                this.$emit("updateValue", JSON.stringify(this.attrInputArray));
                this.inputVal = this.$refs.textarea.value;
                this.inputRuleStatus = 1;
              } else {
                this.$refs.textarea.value = this.inputVal;
                this.$Message.error({
                  content: this.$t("attr_input_close_rule_tips")
                });
              }
            }
          }
        } else if (v.inputType === "deleteContentBackward") {
          if (
            this.attrInputLastObjValue !== "[]" &&
            this.attrInputLastObjValue !== ""
          ) {
            let val = JSON.parse(this.attrInputLastObjValue);
            this.isShowSelect = false;
            if (this.rootCiTypeId && val.length === 1) {
              this.attrNameArray = [];
              this.optionsHide = false;
              this.attrInputArray.splice(-1, 1);
              this.inputVal = this.inputVal.substr(
                0,
                this.inputVal.lastIndexOf("{")
              );
              if (!this.inputVal) {
                this.attrInputArray = [];
                this.$emit("updateValue", "");
              }
              this.inputRuleStatus = 1;
              this.optionsHide = false;
              return;
            }
            let lastAttrVal = "";
            const lastAttrObj = val[val.length - 1];
            const ciTypeName = this.ciTypesObj[lastAttrObj.ciTypeId].name;
            let ciTypeAttrName = "";
            if (lastAttrObj.parentRs) {
              const attrName = this.ciTypeAttrsObj[lastAttrObj.parentRs.attrId]
                .name;
              lastAttrVal +=
                lastAttrObj.parentRs.isReferedFromParent === 1 ? "." : "-";
              if (
                this.ciTypeAttrsObj[lastAttrObj.parentRs.attrId].inputType === "ref" || this.ciTypeAttrsObj[lastAttrObj.parentRs.attrId].inputType === "multiRef"
              ) {
                ciTypeAttrName = `(${attrName})${ciTypeName} `;
              } else {
                ciTypeAttrName = `${attrName} `;
              }
              lastAttrVal += ciTypeAttrName;
            } else {
              lastAttrVal += ciTypeName;
            }
            this.inputVal = this.inputVal.substr(
              0,
              this.inputVal.lastIndexOf(lastAttrVal)
            );
            val.splice(-1, 1);
            this.attrInputArray[
              this.attrInputArray.length - 1
            ].value = JSON.stringify(val);
            if (this.inputVal[this.inputVal.length - 2] === "{") {
              this.allCi = this.allCiTypes;
              this.optionsHide = true;
            } else {
              this.attrNameArray = [];
              this.optionsHide = false;
            }
          } else {
            this.attrInputArray.splice(-1, 1);
            this.inputVal = this.inputVal.substr(
              0,
              this.inputVal.lastIndexOf("{")
            );
            this.inputRuleStatus = 1;
            this.allCi = [];
            this.optionsHide = false;
            if (!this.inputVal) {
              this.$emit("updateValue", "");
              this.attrInputArray = [];
            }
          }
        } else {
          this.$refs.textarea.value = this.inputVal;
        }
      }
    },
    setAutoData() {
      let val = this.inputVal.split(/[\{\}]/);
      this.attrInputArray[this.attrInputArray.length - 1].value =
        val[val.length - 1];
    },
    async getNextRef(operator) {
      const objList = JSON.parse(this.attrInputLastObjValue);
      const obj = objList[objList.length - 1];
      let attrArray = [];
      if (operator === ".") {
        let { status, data, message } = await getCiTypeAttr(obj.ciTypeId);
        if (status === "OK") {
          data.forEach(_ => {
            attrArray.push({
              ..._,
              ciTypeName:
                (_.inputType === "ref" || _.inputType === "multiRef")
                  ? this.allCiTypes.find(i => i.ciTypeId === _.referenceId).name
                  : this.allCiTypes.find(i => i.ciTypeId === _.ciTypeId).name,
              ciTypeAttrName: _.name,
              isReferedFromParent: 1,
              id: (_.inputType === "ref" || _.inputType === "multiRef") ? _.referenceId : _.ciTypeId
            });
          });
          this.attrNameArray = attrArray;
        }
      } else if (operator === "-") {
        let { status, data, message } = await getRefCiTypeFrom(obj.ciTypeId);
        if (status === "OK") {
          attrArray = data.map(_ => {
            return {
              ..._,
              ciTypeName: this.allCiTypes.find(i => i.ciTypeId === _.ciTypeId)
                .name,
              ciTypeAttrName: _.name,
              isReferedFromParent: 0,
              id: _.ciTypeId
            };
          });
          this.attrNameArray = attrArray;
        }
      }
    },
    selectCiType(opt) {
      this.optionsHide = false;
      this.attrInputArray[this.attrInputArray.length - 1].value = JSON.stringify([
        {
          ciTypeId: opt.ciTypeId
        }
      ]);
      this.inputVal += opt.name + " ";
      this.allCi = [];
      this.$refs.textarea.focus();
    },
    selectAttr(opt) {
      this.optionsHide = false;
      const val = {
        ciTypeId: opt.id,
        parentRs: {
          attrId: opt.ciTypeAttrId,
          isReferedFromParent: opt.isReferedFromParent
        }
      };
      let result = JSON.parse(this.attrInputLastObjValue);
      result.push(val);
      this.attrInputArray[this.attrInputArray.length - 1].value = JSON.stringify(
        result
      );
      this.inputVal +=
        (opt.inputType === "ref" || opt.inputType === "multiRef")
          ? `(${opt.ciTypeAttrName})${opt.ciTypeName} `
          : opt.ciTypeAttrName + " ";
      this.attrNameArray = [];
      this.$refs.textarea.focus();
      if (opt.inputType === "select" || opt.inputType ===  "multiSelect") {
        this.isShowSelect = true;
        this.optionsHide = true;
      }
    },
    selectEnumCode(code) {
      this.optionsHide = false;
      this.isShowSelect = false;
      this.inputVal += `.${code} `;
      let result = JSON.parse(this.attrInputLastObjValue);
      result[result.length - 1].enumCodeAttr = code;
      this.attrInputArray[this.attrInputArray.length - 1].value = JSON.stringify(
        result
      );
      this.$refs.textarea.focus();
    },
    displayInputData() {
      if (!this.allCiTypes.length || !this.value) {
        return;
      }
      this.inputVal = "";
      this.attrInputArray = JSON.parse(this.value);
      if (
        this.attrInputArray[this.attrInputArray.length - 1].type !== "delimiter"
      ) {
        this.attrInputArray.push({ type: "delimiter", value: "" });
      }
      this.attrInputArray.forEach(_ => {
        if (_.type === "delimiter") {
          this.inputVal += _.value;
        } else {
          let val = "{ ";
          let data = JSON.parse(_.value);
          data.forEach(item => {
            const ciTypeName = this.ciTypesObj[item.ciTypeId].name;
            if (item.parentRs) {
              const refType =
                item.parentRs.isReferedFromParent === 1 ? "." : "-";
              const attrName = this.ciTypeAttrsObj[item.parentRs.attrId].name;
              if (
                this.ciTypeAttrsObj[item.parentRs.attrId].inputType === "ref" || this.ciTypeAttrsObj[item.parentRs.attrId].inputType === "multiRef"
              ) {
                val += `${refType}(${attrName})${ciTypeName} `;
              } else if (
                this.ciTypeAttrsObj[item.parentRs.attrId].inputType === "select" || this.ciTypeAttrsObj[item.parentRs.attrId].inputType === "multiSelect"
              ) {
                val += `${refType}${attrName} .${item.enumCodeAttr} `;
              } else {
                val += `${refType}${attrName} `;
              }
            } else {
              val += ciTypeName + " ";
            }
          });
          val += "}";
          this.inputVal += val;
        }
      });
    }
  }
};
</script>

<style lang="scss">
.attr-ul {
  width: 100%;
  z-index: 3000;
  background: white;
  max-height: 200px;
  overflow: auto;
}
.attr_input .ivu-poptip {
  width: 100%;
}
.attr_input .ivu-poptip .ivu-poptip-rel {
  width: 100%;
}
.input_in {
  width: 100%;
}
.input_in textarea {
  font-size: 11px;
  line-height: 20px;
  width: 100%;
}
.attr-ul ul {
  width: 100%;
  border-radius: 3px;
}
.ul-li-selected {
  color: rgb(6, 130, 231);
}
.attr-ul ul li {
  width: 100%;
  height: 25px;
  line-height: 25px;
  cursor: pointer;
  &:hover {
    background-color: rgb(227, 231, 235);
  }
}
</style>
