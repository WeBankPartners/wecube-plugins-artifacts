<template>
  <div>
    <Table :data="data" class="artifact-simple-table" :columns="columns" highlight-row :loading="loading" size="small" @on-row-click="onRowClick"></Table>
    <div v-if="pagable">
      <Page :current="page.currentPage" :page-size="page.pageSize" :page-size-opts="pageSizeOptions" :total="page.total" @on-change="onChange" @on-page-size-change="onPageSizeChange" show-elevator show-sizer show-total style="float: right; margin: 10px 0;" />
    </div>
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
          pageSize: 5,
          total: 0
        }
      }
    },
    pageSizeOptions: {
      type: Array,
      default: () => {
        return [5, 10, 20]
      }
    },
    loading: {
      default: false,
      required: false
    }
  },
  methods: {
    onChange (currentPage) {
      this.$emit('pageChange', currentPage)
    },
    onPageSizeChange (pageSize) {
      this.$emit('pageSizeChange', pageSize)
    },
    onRowClick (row) {
      this.$emit('rowClick', row)
    }
  }
}
</script>

<style lang="scss" scoped>
.artifact-simple-table ::v-deep .ivu-table-hidden .ivu-tooltip {
  width: initial !important;
}
</style>
