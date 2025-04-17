<template>
  <div>
    <div class="parse-fail">
      <div style="display: flex;justify-content: space-between;margin-bottom: 12px;">
        <div class="ivu-notice-title">{{ $t('art_parse_fail') }}</div>
        <Icon @click="close" type="ios-close" size="24" />
      </div>
      <div>
        <Table size="small" :columns="columns" :data="parseFailMsg"></Table>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  props: {
    parseFailMsg: { default: () => [], required: true }
  },
  data () {
    return {
      columns: [
        { title: this.$t('art_file_type'), key: 'fileType', width: 100 },
        { title: this.$t('art_file'), key: 'fileName', width: 200 },
        { title: this.$t('art_variable_type'), key: 'varType', width: 100 },
        { title: this.$t('artifacts_property_name'), key: 'key', width: 200 }
      ]
    }
  },
  methods: {
    close () {
      this.$emit('close')
    }
  }
}
</script>
<style lang="scss" scoped>
.parse-fail {
  margin-right: 24px;
  position: fixed;
  top: 50px;
  right: 0px;
  z-index: 1013;
  margin-bottom: 10px;
  padding: 16px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(15, 18, 34, 0.1);
  background: #fff;
  overflow: hidden;
}
</style>
