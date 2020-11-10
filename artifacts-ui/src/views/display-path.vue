<template>
  <span class=" ">
    <div v-if="file.comparisonResult === 'new'" class="baseline-cmp-new">[{{ file.comparisonResult }}]</div>
    <div v-if="file.comparisonResult === 'same'" class="baseline-cmp-same">[{{ file.comparisonResult }}]</div>
    <div v-if="file.comparisonResult === 'changed'" class="baseline-cmp-changed">[{{ file.comparisonResult }}]</div>
    <div v-if="file.comparisonResult === 'deleted'" class="baseline-cmp-deleted">[{{ file.comparisonResult }}]</div>
    <Icon type="ios-move" size="18" style="cursor:move" />
  </span>
</template>

<script>
export default {
  name: '',
  data () {
    return {}
  },
  props: ['packageInput', 'file'],
  methods: {},
  components: {}
}
</script>

<style scoped lang="scss">
.common-position {
  width: 60px;
  margin: 0 8px;
  display: inline-block;
}
.baseline-cmp-new {
  color: #19be6b;
  @extend .common-position;
}
.baseline-cmp-same {
  @extend .common-position;
}
.baseline-cmp-changed {
  color: #2d8cf0;
  @extend .common-position;
}
.baseline-cmp-deleted {
  color: #cccccc;
  @extend .common-position;
}
</style>
