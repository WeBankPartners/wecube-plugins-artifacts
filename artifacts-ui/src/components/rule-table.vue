<template>
  <div>
    <Table :data="data" class="artifact-simple-table" :columns="columns" :max-height="maxHeight" size="small"></Table>
    <Page :current="page.currentPage" :page-size="page.pageSize" :page-size-opts="pageSizeOptions" :total="page.total" @on-change="onChange" @on-page-size-change="onPageSizeChange" show-elevator show-sizer show-total style="position: absolute;right: 36px;bottom: 36px;z-index: 11" />
  </div>
</template>

<script>
export default {
  props: {
    data: Array,
    columns: Array,
    pagable: {
      default: true,
      required: false
    },
    page: {
      type: Object,
      default: () => {
        return {
          currentPage: 1,
          pageSize: 10,
          total: 0
        }
      }
    },
    pageSizeOptions: {
      type: Array,
      default: () => {
        return [10, 20]
      }
    },
    loading: {
      default: false,
      required: false
    }
  },
  data () {
    return {
      maxHeight: 500
    }
  },
  mounted () {
    this.maxHeight = window.innerHeight - 256
    window.addEventListener('resize', this.handleResize)
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.handleResize)
  },
  methods: {
    handleResize () {
      this.maxHeight = window.innerHeight - 256
    },
    onChange (currentPage) {
      this.$emit('reloadTableData', {
        pageSize: this.page.pageSize,
        startIndex: currentPage - 1
      })
    },
    onPageSizeChange (pageSize) {
      this.$emit('reloadTableData', {
        pageSize: pageSize,
        startIndex: 0
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.artifact-simple-table ::v-deep .ivu-table-hidden .ivu-tooltip {
  width: initial !important;
}
</style>
