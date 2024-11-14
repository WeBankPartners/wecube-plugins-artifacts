<template>
  <div>
    <Table :data="data" class="artifact-simple-table" ref="table" :columns="columns" :height="maxHeight" :max-height="maxHeight" size="small"> </Table>
    <Page :current="page.currentPage" :page-size="page.pageSize" :page-size-opts="pageSizeOptions" :total="page.total" @on-change="onChange" @on-page-size-change="onPageSizeChange" show-sizer show-total style="position: absolute;right: 36px;bottom: 60px;z-index: 11" />
  </div>
</template>

<script>
export default {
  props: {
    maxHeight: {
      type: Number,
      default: 500
    },
    data: Array,
    columns: Array,
    pagable: {
      default: true,
      required: false
    },
    // page: {
    //   type: Object,
    //   default: () => {
    //     return {
    //       currentPage: 1,
    //       pageSize: 10,
    //       total: 0
    //     }
    //   }
    // },
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
      page: {
        currentPage: 1,
        pageSize: 10,
        total: 0
      }
    }
  },
  mounted () {
    // this.maxHeight = window.innerHeight - 400
    window.addEventListener('resize', this.handleResize)
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.handleResize)
  },
  methods: {
    setPage (page) {
      this.page = page
    },
    handleResize () {
      // this.maxHeight = window.innerHeight - 256
    },
    onChange (currentPage) {
      this.$emit('reloadTableData', {
        pageSize: this.page.pageSize,
        currentPage
      })
    },
    onPageSizeChange (pageSize) {
      this.page.pageSize = pageSize
      this.$emit('reloadTableData', {
        pageSize: pageSize,
        currentPage: 1
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.artifact-simple-table {
  margin-bottom: 36px;
}
.artifact-simple-table ::v-deep .ivu-table-hidden .ivu-tooltip {
  width: initial !important;
}
.artifact-simple-table ::v-deep thead .ivu-table-cell .ivu-checkbox {
  display: none;
}
</style>
